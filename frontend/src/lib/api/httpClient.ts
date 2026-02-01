import type { ApiClient, CheckinResult, DailySnapshot, HomeSnapshot, ProgressData, ReportData } from "./client";
import type { DailyLog, User } from "../store/schema";
import { encodeFunctionData } from "viem";
import { mockTxHash } from "../logic/proof";
import { tasks } from "../tasks/tasks";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
const CHAIN_ID = Number(process.env.NEXT_PUBLIC_CHAIN_ID || "11155111");
const PROOF_REGISTRY = process.env.NEXT_PUBLIC_PROOF_REGISTRY || "0x0000000000000000000000000000000000000000";
const BADGE_SBT = process.env.NEXT_PUBLIC_BADGE_SBT || "0x0000000000000000000000000000000000000000";
const MILESTONE_NFT = process.env.NEXT_PUBLIC_MILESTONE_NFT || BADGE_SBT;

const ProofRegistryAbi = [
  {
    type: "function",
    name: "submitProof",
    stateMutability: "nonpayable",
    inputs: [
      { name: "dayIndex", type: "uint16" },
      { name: "proofHash", type: "bytes32" }
    ],
    outputs: []
  }
] as const;

const RestartBadgeSbtAbi = [
  {
    type: "function",
    name: "mintDay",
    stateMutability: "nonpayable",
    inputs: [{ name: "dayIndex", type: "uint8" }],
    outputs: []
  },
  {
    type: "function",
    name: "composeFinal",
    stateMutability: "nonpayable",
    inputs: [],
    outputs: []
  }
] as const;

async function fetchJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    cache: "no-store"
  });

  const text = await res.text();
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const data = text ? JSON.parse(text) : {};
      msg = data?.error?.message || data?.message || text || msg;
    } catch {
      msg = text || msg;
    }
    throw new Error(msg);
  }
  if (!text) return {} as T;
  return JSON.parse(text) as T;
}

function getEthereum() {
  if (typeof window === "undefined") return null;
  return (window as any).ethereum || null;
}

async function ensureChain(ethereum: any) {
  const current = await ethereum.request({ method: "eth_chainId" });
  const target = "0x" + CHAIN_ID.toString(16);
  if (current !== target) {
    await ethereum.request({ method: "wallet_switchEthereumChain", params: [{ chainId: target }] });
  }
}

async function getWalletAddress(ethereum: any) {
  const accounts = await ethereum.request({ method: "eth_requestAccounts" });
  if (!accounts || !accounts.length) throw new Error("未连接钱包");
  return accounts[0] as string;
}

async function sendTx(params: { to: string; data: string }): Promise<string> {
  const ethereum = getEthereum();
  if (!ethereum) throw new Error("未检测到钱包（window.ethereum）");
  await ensureChain(ethereum);
  const from = await getWalletAddress(ethereum);
  const txHash = await ethereum.request({
    method: "eth_sendTransaction",
    params: [{ from, to: params.to, data: params.data, value: "0x0" }]
  });
  return txHash as string;
}

function mapLog(raw: any): DailyLog {
  return {
    id: raw.id,
    address: raw.address,
    challengeId: raw.challengeId ?? raw.challenge_id,
    dayIndex: raw.dayIndex ?? raw.day_index,
    dateKey: raw.dateKey ?? raw.date_key,
    normalizedText: raw.normalizedText ?? raw.normalized_text ?? "",
    reflection: raw.reflection ?? { note: "", next: "" },
    saltHex: raw.saltHex ?? raw.salt_hex,
    proofHash: raw.proofHash ?? raw.proof_hash,
    status: raw.status,
    txHash: raw.txHash ?? raw.tx_hash ?? null,
    daySbtTxHash: raw.daySbtTxHash ?? raw.day_sbt_tx_hash ?? null,
    nftImage: raw.nftImage ?? raw.nft_image ?? null,
    createdAt: raw.createdAt ?? raw.created_at
  };
}

function mapMilestones(raw: any): Record<number, string> {
  const result: Record<number, string> = {};
  if (!raw || typeof raw !== "object") return result;
  for (const [k, v] of Object.entries(raw)) {
    if (v) result[Number(k)] = String(v);
  }
  return result;
}

async function getHomeSnapshot(address?: string | null): Promise<HomeSnapshot> {
  if (!address) return { dayBtnLabel: "Day 1", dayBtnTarget: 1 };
  const res = await fetchJson<HomeSnapshot>(`/homeSnapshot?address=${encodeURIComponent(address)}`);
  return res;
}

async function getDailySnapshot(address: string, dayIndex: number): Promise<DailySnapshot> {
  const res = await fetchJson<any>(
    `/dailySnapshot?address=${encodeURIComponent(address)}&dayIndex=${encodeURIComponent(dayIndex)}`
  );
  return {
    dateKey: res.dateKey ?? res.date_key,
    task: res.task,
    log: res.log ? mapLog(res.log) : null,
    alreadyCheckedIn: res.alreadyCheckedIn ?? res.already_checked_in ?? false
  };
}

async function checkin(params: { address: string; dayIndex: number; text: string }): Promise<CheckinResult> {
  const res = await fetchJson<any>("/checkin", {
    method: "POST",
    body: JSON.stringify({
      address: params.address,
      dayIndex: params.dayIndex,
      text: params.text
    })
  });
  return {
    log: mapLog(res.log ?? res),
    alreadyCheckedIn: res.alreadyCheckedIn ?? res.already_checked_in ?? false
  };
}

async function getTodaySnapshot(address: string): Promise<DailySnapshot> {
  const home = await getHomeSnapshot(address);
  return getDailySnapshot(address, home.dayBtnTarget);
}

async function submitProof(params: { address: string }): Promise<DailyLog> {
  const snapshot = await getTodaySnapshot(params.address);
  const log = snapshot.log;
  if (!log) throw new Error("请先 checkin 生成 proofHash");
  if (log.txHash) throw new Error("已提交过 Proof（幂等）");

  const data = encodeFunctionData({
    abi: ProofRegistryAbi,
    functionName: "submitProof",
    args: [log.dayIndex, log.proofHash as `0x${string}`]
  });
  const txHash = await sendTx({ to: PROOF_REGISTRY, data });

  await fetchJson("/tx/confirm", {
    method: "POST",
    body: JSON.stringify({
      logId: log.id,
      address: params.address,
      txHash,
      chainId: CHAIN_ID,
      contractAddress: PROOF_REGISTRY
    })
  });

  const refreshed = await getTodaySnapshot(params.address);
  if (!refreshed.log) throw new Error("log not found after submit");
  return refreshed.log;
}

async function mintDay(params: { address: string }): Promise<DailyLog> {
  const snapshot = await getTodaySnapshot(params.address);
  const log = snapshot.log;
  if (!log) throw new Error("请先 checkin");
  if (!log.txHash) throw new Error("请先提交 Proof（submitProof）");
  if (log.daySbtTxHash) throw new Error("今日 DaySBT 已 mint（幂等）");

  const data = encodeFunctionData({
    abi: RestartBadgeSbtAbi,
    functionName: "mintDay",
    args: [log.dayIndex]
  });
  const txHash = await sendTx({ to: BADGE_SBT, data });

  await fetchJson("/sbt/confirm", {
    method: "POST",
    body: JSON.stringify({
      address: params.address,
      type: "DAY",
      dayIndex: log.dayIndex,
      txHash,
      chainId: CHAIN_ID,
      contractAddress: BADGE_SBT
    })
  });

  const refreshed = await getTodaySnapshot(params.address);
  if (!refreshed.log) throw new Error("log not found after mintDay");
  return refreshed.log;
}

async function getProgressRaw(address: string): Promise<any> {
  return fetchJson<any>(`/progress?address=${encodeURIComponent(address)}`);
}

async function getProgress(params: { address: string }): Promise<ProgressData> {
  const res = await getProgressRaw(params.address);
  return {
    dateKey: res.dateKey ?? res.date_key,
    streak: res.streak ?? 0,
    dayMintCount: res.dayMintCount ?? res.day_mint_count ?? 0,
    completedDays: res.completedDays ?? res.completed_days ?? [],
    shouldMintDay: res.shouldMintDay ?? res.should_mint_day ?? false,
    mintableDayIndex: res.mintableDayIndex ?? res.mintable_day_index ?? null,
    shouldComposeFinal: res.shouldComposeFinal ?? res.should_compose_final ?? false,
    finalMinted: res.finalMinted ?? res.final_minted ?? false,
    finalSbtTxHash: res.finalSbtTxHash ?? res.final_sbt_tx_hash ?? null
  };
}

function toUser(progress: any): User {
  return {
    timezone: progress.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
    startDateKey: progress.startDateKey ?? progress.start_date_key ?? null,
    streak: progress.streak ?? 0,
    lastDateKey: progress.lastDateKey ?? progress.last_date_key ?? null,
    dayMintCount: progress.dayMintCount ?? progress.day_mint_count ?? 0,
    finalMinted: progress.finalMinted ?? progress.final_minted ?? false,
    finalSbtTxHash: progress.finalSbtTxHash ?? progress.final_sbt_tx_hash ?? null,
    milestones: mapMilestones(progress.milestones)
  };
}

async function composeFinal(params: { address: string }): Promise<User> {
  const data = encodeFunctionData({
    abi: RestartBadgeSbtAbi,
    functionName: "composeFinal",
    args: []
  });
  const txHash = await sendTx({ to: BADGE_SBT, data });

  await fetchJson("/sbt/confirm", {
    method: "POST",
    body: JSON.stringify({
      address: params.address,
      type: "FINAL",
      txHash,
      chainId: CHAIN_ID,
      contractAddress: BADGE_SBT
    })
  });
  const progress = await getProgressRaw(params.address);
  return toUser(progress);
}

async function mintMilestone(params: { address: string; milestoneId: number; txHash?: string }): Promise<User> {
  // DEMO_MODE: 若未传 txHash，则生成 mockTxHash 上报后端
  const txHash = params.txHash || mockTxHash(`tx:milestone:${params.milestoneId}:${Date.now()}`);
  await fetchJson("/milestone/mint", {
    method: "POST",
    body: JSON.stringify({
      address: params.address,
      milestoneId: params.milestoneId,
      txHash,
      chainId: CHAIN_ID,
      contractAddress: MILESTONE_NFT
    })
  });
  const progress = await getProgressRaw(params.address);
  return toUser(progress);
}

async function getReport(params: { address: string; range: "week" | "final" }): Promise<ReportData> {
  const res = await fetchJson<any>(
    `/report?address=${encodeURIComponent(params.address)}&range=${encodeURIComponent(params.range)}`
  );
  return {
    title: res.title || (params.range === "final" ? "结营报告（模拟）" : "周报（模拟）"),
    reportText: res.reportText ?? res.report_text ?? "",
    recentLogs: (res.recentLogs ?? res.recent_logs ?? []).map(mapLog),
    chartByDay: res.chartByDay ?? res.chart_by_day ?? [],
    range: params.range
  };
}

async function getConfig(): Promise<{ demo_mode: boolean }> {
  const res = await fetchJson<{ status: string; version: string; demo_mode?: boolean }>("/health");
  return { demo_mode: res.demo_mode ?? false };
}

export const httpClient: ApiClient = {
  getConfig,
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
