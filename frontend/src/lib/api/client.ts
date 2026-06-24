import type { DailyLog, DailyTask, User } from "../domain/schema";

export type HomeSnapshot = {
  dayBtnLabel: string;
  dayBtnTarget: number;
};

export type DailySnapshot = {
  dateKey: string;
  task: DailyTask;
  log: DailyLog | null;
  alreadyCheckedIn: boolean;
};

export type CheckinOutcome =
  | "accepted"
  | "already_checked_in"
  | "clarify"
  | "rejected"
  | "crisis_redirected";

export type CheckinExecution = {
  promptVersion: string;
  modelProvider: string;
  modelName: string;
  modelAttempts: number;
  repairAttempts: number;
  fallbackReason?: string | null;
  nodeDurationsMs: Record<string, number>;
  nodeAttempts: Record<string, number>;
  lastError?: {
    node: string;
    type: string;
    message: string;
  } | null;
};

export type CheckinResult = {
  outcome: CheckinOutcome;
  log: DailyLog | null;
  alreadyCheckedIn: boolean;
  message?: string | null;
  reflection?: DailyLog["reflection"] | null;
  checkinId: string;
  recovered: boolean;
  execution: CheckinExecution;
};

export type ProgressData = {
  dateKey: string;
  streak: number;
  dayMintCount: number;
  completedDays: number[];
  shouldMintDay: boolean;
  mintableDayIndex: number | null;
  shouldComposeFinal: boolean;
  finalMinted: boolean;
  finalNftTxHash: string | null;
};

export type ReportData = {
  title: string;
  reportText: string;
  recentLogs: DailyLog[];
  chartByDay: number[];
  range: "week" | "final";
};

export type ConfigIssue = {
  code: string;
  message: string;
};

export type ConfigData = {
  status: string;
  version: string;
  demo_mode: boolean;
  mode: "demo" | "production";
  ready: boolean;
  checks: Record<string, boolean>;
  blockingIssues: ConfigIssue[];
};

export type GenerateNftResult = {
  success: boolean;
  image: string;
  dayIndex: number;
  message: string;
};

export type MilestoneMintPreparation = {
  milestoneId: number;
  requiredDays: number;
  completedDays: number;
  tokenId: string;
  tokenUri: string;
};

export interface ApiClient {
  authenticateWallet: (
    address: string,
    signMessage?: (message: string) => Promise<string>
  ) => Promise<void>;
  clearWalletSession: () => void;
  getConfig: () => Promise<ConfigData>;
  getHomeSnapshot: (address?: string | null) => Promise<HomeSnapshot>;
  getDailySnapshot: (address: string, dayIndex: number) => Promise<DailySnapshot>;
  checkin: (params: { address: string; dayIndex: number; text: string; checkinId?: string }) => Promise<CheckinResult>;
  submitProof: (params: { address: string; logId: string }) => Promise<DailyLog>;
  mintDay: (params: {
    address: string;
    logId: string;
    dayIndex: number;
  }) => Promise<DailyLog>;
  getProgress: (params: { address: string }) => Promise<ProgressData>;
  composeFinal: (params: { address: string }) => Promise<User>;
  prepareMilestone: (params: {
    address: string;
    milestoneId: number;
  }) => Promise<MilestoneMintPreparation>;
  mintMilestone: (params: { address: string; milestoneId: number; txHash?: string }) => Promise<User>;
  getReport: (params: { address: string; range: "week" | "final" }) => Promise<ReportData>;
  generateNft: (params: {
    address: string;
    logId: string;
  }) => Promise<GenerateNftResult>;
}
