import type { ApiClient, CheckinResult, DailySnapshot, HomeSnapshot, ProgressData, ReportData } from "./client";
import type { DailyLog, User } from "../store/schema";
import { tasks } from "../tasks/tasks";
import { keccakProofHash, makeSaltHex, mockTxHash } from "../logic/proof";
import { reflectionTemplate } from "../logic/reflection";
import { spoonClient } from "./spoonClient";
import {
  CHALLENGE_ID,
  computeDayIndex,
  findLog,
  getUser,
  loadStore,
  normalizeText,
  peekDayIndex,
  saveStore,
  todayDateKey,
  updateStreak,
  uuid
} from "../store/localStore";

async function getHomeSnapshot(address?: string | null): Promise<HomeSnapshot> {
  let dayBtnLabel = "Day 1";
  let dayBtnTarget = 1;
  if (address) {
    const store = loadStore();
    const user = getUser(store, address);
    const dk = todayDateKey(user.timezone);
    const di = peekDayIndex(user, dk);
    dayBtnTarget = Math.min(28, Math.max(1, di));
    dayBtnLabel = `Day ${dayBtnTarget}`;
  }
  return { dayBtnLabel, dayBtnTarget };
}

async function getDailySnapshot(address: string, dayIndex: number): Promise<DailySnapshot> {
  const store = loadStore();
  const user = getUser(store, address);

  // 计算该 dayIndex 对应的 dateKey
  let dateKey: string;
  if (!user.startDateKey) {
    // 如果还没有开始日期，使用今天的日期
    dateKey = todayDateKey(user.timezone);
  } else {
    // 根据 startDateKey 和 dayIndex 计算对应的日期
    const [sy, sm, sd] = user.startDateKey.split("-").map(Number);
    const startDate = new Date(sy, sm - 1, sd);
    const targetDate = new Date(startDate);
    targetDate.setDate(startDate.getDate() + (dayIndex - 1));
    const ty = targetDate.getFullYear();
    const tm = String(targetDate.getMonth() + 1).padStart(2, "0");
    const td = String(targetDate.getDate()).padStart(2, "0");
    dateKey = `${ty}-${tm}-${td}`;
  }

  const task = tasks.find((t) => t.dayIndex === dayIndex) || tasks[0];
  const log = findLog(store, address, dateKey);

  // 只有当找到的日志的 dayIndex 匹配时才认为已完成
  const alreadyCheckedIn = !!(log && log.dayIndex === dayIndex);

  return { dateKey, task, log: alreadyCheckedIn ? log : null, alreadyCheckedIn };
}

async function checkin(params: { address: string; dayIndex: number; text: string }): Promise<CheckinResult> {
  const { address, dayIndex, text } = params;
  const store = loadStore();
  const user = getUser(store, address);

  // 计算该 dayIndex 对应的 dateKey
  let dateKey: string;
  if (!user.startDateKey) {
    // 如果还没有开始日期，使用今天的日期并设置为开始日期
    dateKey = todayDateKey(user.timezone);
    user.startDateKey = dateKey;
  } else {
    // 根据 startDateKey 和 dayIndex 计算对应的日期
    const [sy, sm, sd] = user.startDateKey.split("-").map(Number);
    const startDate = new Date(sy, sm - 1, sd);
    const targetDate = new Date(startDate);
    targetDate.setDate(startDate.getDate() + (dayIndex - 1));
    const ty = targetDate.getFullYear();
    const tm = String(targetDate.getMonth() + 1).padStart(2, "0");
    const td = String(targetDate.getDate()).padStart(2, "0");
    dateKey = `${ty}-${tm}-${td}`;
  }

  // 检查该日期和 dayIndex 是否已经有日志
  const exist = findLog(store, address, dateKey);
  if (exist && exist.dayIndex === dayIndex) {
    return { log: exist, alreadyCheckedIn: true };
  }

  const di = dayIndex;

  const normalizedText = normalizeText(text);
  const saltHex = makeSaltHex();
  const proofHash = keccakProofHash(dateKey, normalizedText, saltHex);
  const task = tasks.find((t) => t.dayIndex === di) || tasks[0];
  const { dayIndex: _taskDayIndex, ...taskBase } = task;

  // 使用 SpoonOS AI 生成反馈，如果失败则降级到模板
  let reflection;
  try {
    reflection = await spoonClient.generateReflection(
      { ...taskBase, dayIndex: di },
      normalizedText,
      di
    );
  } catch (error) {
    console.warn("SpoonOS AI failed, using fallback:", error);
    reflection = reflectionTemplate({ ...taskBase, dayIndex: di }, normalizedText);
  }

  updateStreak(user, dateKey);

  const logObj: DailyLog = {
    id: uuid(),
    address: address.toLowerCase(),
    challengeId: CHALLENGE_ID,
    dayIndex: di,
    dateKey,
    normalizedText,
    reflection,
    saltHex,
    proofHash,
    status: "CREATED",
    txHash: null,
    daySbtTxHash: null,
    nftImage: null,
    createdAt: new Date().toISOString()
  };

  store.logs.push(logObj);
  store.users[address.toLowerCase()] = user;
  saveStore(store);

  return { log: logObj, alreadyCheckedIn: false };
}

async function submitProof(params: { address: string }): Promise<DailyLog> {
  const { address } = params;
  const store = loadStore();
  const user = getUser(store, address);

  // 获取今天的日期和对应的 dayIndex
  const todayKey = todayDateKey(user.timezone);
  const todayDayIndex = computeDayIndex(user, todayKey);

  // 查找今天的日志
  const log = findLog(store, address, todayKey);
  if (!log || log.dayIndex !== todayDayIndex) {
    throw new Error("请先 checkin 生成 proofHash");
  }
  if (log.txHash) throw new Error("已提交过 Proof（幂等）");

  log.txHash = mockTxHash(`tx:proof:${log.proofHash}:${Date.now()}`);
  log.status = "SUBMITTED";
  saveStore(store);

  return log;
}

async function mintDay(params: { address: string }): Promise<DailyLog> {
  const { address } = params;
  const store = loadStore();
  const user = getUser(store, address);

  // 获取今天的日期和对应的 dayIndex
  const todayKey = todayDateKey(user.timezone);
  const todayDayIndex = computeDayIndex(user, todayKey);

  // 查找今天的日志
  const log = findLog(store, address, todayKey);
  if (!log || log.dayIndex !== todayDayIndex) {
    throw new Error("请先 checkin");
  }
  if (!log.txHash) throw new Error("请先提交 Proof（submitProof）");
  if (log.daySbtTxHash) throw new Error("今日 DaySBT 已 mint（幂等）");

  log.daySbtTxHash = mockTxHash(`tx:sbt:day:${log.dayIndex}:${Date.now()}`);
  user.dayMintCount = Math.min(28, (user.dayMintCount || 0) + 1);

  store.users[address.toLowerCase()] = user;
  saveStore(store);

  return log;
}

async function getProgress(params: { address: string }): Promise<ProgressData> {
  const { address } = params;
  const store = loadStore();
  const user = getUser(store, address);
  const dateKey = todayDateKey(user.timezone);

  const todayLog = findLog(store, address, dateKey);
  const todayCheckedIn = !!todayLog;

  const completedDays = store.logs
    .filter((l) => l.address === address.toLowerCase() && l.challengeId === CHALLENGE_ID)
    .map((l) => l.dayIndex)
    .sort((a, b) => a - b);

  const shouldMintDay = todayCheckedIn && !todayLog?.daySbtTxHash;
  const mintableDayIndex = todayLog?.dayIndex || null;
  const shouldComposeFinal = user.dayMintCount === 28 && !user.finalMinted;

  return {
    dateKey,
    streak: user.streak || 0,
    dayMintCount: user.dayMintCount || 0,
    completedDays,
    shouldMintDay,
    mintableDayIndex,
    shouldComposeFinal,
    finalMinted: user.finalMinted,
    finalSbtTxHash: user.finalSbtTxHash
  };
}

async function composeFinal(params: { address: string }): Promise<User> {
  const { address } = params;
  const store = loadStore();
  const user = getUser(store, address);

  if (user.finalMinted) throw new Error("已合成（幂等）");
  if (user.dayMintCount !== 28) throw new Error("dayMintCount 未到 28");

  const logs = store.logs.filter((l) => l.address === address.toLowerCase() && l.challengeId === CHALLENGE_ID);
  const mintedDays = new Set(logs.filter((l) => l.daySbtTxHash).map((l) => l.dayIndex));
  for (let i = 1; i <= 28; i += 1) {
    if (!mintedDays.has(i)) throw new Error(`缺少 Day ${i} 的 DaySBT mint 记录`);
  }

  user.finalMinted = true;
  user.finalSbtTxHash = mockTxHash(`tx:sbt:final:${Date.now()}`);
  store.users[address.toLowerCase()] = user;
  saveStore(store);

  return user;
}

async function mintMilestone(params: { address: string; milestoneId: number }): Promise<User> {
  const { address, milestoneId } = params;
  const store = loadStore();
  const user = getUser(store, address);

  if (user.milestones && user.milestones[milestoneId]) throw new Error(`Milestone ${milestoneId} 已铸造`);

  // Simple validation: check if enough days are completed
  const logs = store.logs.filter((l) => l.address === address.toLowerCase() && l.challengeId === CHALLENGE_ID);
  const count = logs.length;
  const required = milestoneId === 1 ? 7 : milestoneId === 2 ? 14 : 28;

  if (count < required) throw new Error(`打卡天数不足（需 ${required} 天）`);

  if (!user.milestones) user.milestones = {};
  user.milestones[milestoneId] = mockTxHash(`tx:sbt:milestone:${milestoneId}:${Date.now()}`);

  store.users[address.toLowerCase()] = user;
  saveStore(store);
  return user;
}

async function getReport(params: { address: string; range: "week" | "final" }): Promise<ReportData> {
  const { address, range } = params;
  const store = loadStore();
  const logs = store.logs
    .filter((l) => l.address === address.toLowerCase() && l.challengeId === CHALLENGE_ID)
    .sort((a, b) => a.dateKey.localeCompare(b.dateKey));

  const title = range === "final" ? "结营报告" : "周报";
  const recentLogs = logs.slice(-6).reverse();

  const total = logs.length;
  const minted = logs.filter((l) => l.daySbtTxHash).length;
  const streak = store.users[address.toLowerCase()]?.streak || 0;
  const reportText = (() => {
    if (!total) return "你还没有记录，去开始你的第一天吧！每一小步都是成长。";
    if (range === "final") {
      return `恭喜你完成了28天的旅程！在这 ${total} 天里，你完成了 ${minted} 个任务，连续坚持了 ${streak} 天。\n\n这段旅程中，你记录下的每一个感受都是珍贵的。建议你挑选一条最触动你的感悟，把它写下来，在未来的日子里时常回顾。成长不是一蹴而就的，而是每一天的小小坚持累积而成的。\n\n你已经拥有了持续成长的能力，继续前行吧！✨`;
    }
    return `这段时间你记录了 ${total} 天，完成了 ${minted} 个任务。\n\n你的节奏很好，就像"先做一小步再往下走"。这种渐进的方式正是持续成长的关键。\n\n继续加油！每天记录下最真实的感受，哪怕只是一句话，也是在为自己积累力量。💪`;
  })();

  const byDay = new Array(28).fill(0);
  for (const l of logs) {
    if (l.dayIndex >= 1 && l.dayIndex <= 28) byDay[l.dayIndex - 1] += 1;
  }

  return { title, reportText, recentLogs, chartByDay: byDay, range };
}

export const mockClient: ApiClient = {
  getHomeSnapshot,
  getDailySnapshot,
  checkin,
  submitProof,
  mintDay,
  getProgress,
  composeFinal,
  mintMilestone,
  getReport
};
