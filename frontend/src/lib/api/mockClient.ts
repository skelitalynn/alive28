import type { ApiClient, CheckinResult, DailySnapshot, HomeSnapshot, ProgressData, ReportData } from "./client";
import type { DailyLog, User } from "../store/schema";
import { tasks } from "../tasks/tasks";
import { keccakProofHash, makeSaltHex, mockTxHash } from "../logic/proof";
import { reflectionTemplate } from "../logic/reflection";
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
  const dateKey = todayDateKey(user.timezone);
  const task = tasks.find((t) => t.dayIndex === dayIndex) || tasks[0];
  const log = findLog(store, address, dateKey);
  return { dateKey, task, log, alreadyCheckedIn: !!log };
}

async function checkin(params: { address: string; dayIndex: number; text: string }): Promise<CheckinResult> {
  const { address, dayIndex, text } = params;
  const store = loadStore();
  const user = getUser(store, address);
  const dateKey = todayDateKey(user.timezone);

  const exist = findLog(store, address, dateKey);
  if (exist) {
    return { log: exist, alreadyCheckedIn: true };
  }

  computeDayIndex(user, dateKey);
  const di = dayIndex;

  const normalizedText = normalizeText(text);
  const saltHex = makeSaltHex();
  const proofHash = keccakProofHash(dateKey, normalizedText, saltHex);
  const task = tasks.find((t) => t.dayIndex === di) || tasks[0];
  const { dayIndex: _taskDayIndex, ...taskBase } = task;
  const reflection = reflectionTemplate({ ...taskBase, dayIndex: di }, normalizedText);

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
  const dateKey = todayDateKey(user.timezone);
  const log = findLog(store, address, dateKey);
  if (!log) throw new Error("请先 checkin 生成 proofHash");
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
  const dateKey = todayDateKey(user.timezone);
  const log = findLog(store, address, dateKey);
  if (!log) throw new Error("请先 checkin");
  if (!log.txHash) throw new Error("请先模拟提交 Proof（submitProof）");
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

  const title = range === "final" ? "结营报告（模拟）" : "周报（模拟）";
  const recentLogs = logs.slice(-6).reverse();

  const total = logs.length;
  const minted = logs.filter((l) => l.daySbtTxHash).length;
  const streak = store.users[address.toLowerCase()]?.streak || 0;
  const reportText = (() => {
    if (!total) return "你还没有打卡记录。先去 Daily 页写一句话。";
    if (range === "final") {
      return `你累计记录了 ${total} 天，已模拟铸造 ${minted} 枚 DaySBT，当前 streak 为 ${streak}。结营版本建议：挑一条你最想保留的“边界”，把它写成一句固定句，接下来每周读一遍。`;
    }
    return `这段时间你记录了 ${total} 天，已模拟铸造 ${minted} 枚 DaySBT。你的节奏更像“先做一小步再往下走”。如果要继续：每天只保留一句最关键的句子。`;
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
