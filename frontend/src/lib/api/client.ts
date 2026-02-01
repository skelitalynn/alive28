import type { DailyLog, DailyTask, User } from "../store/schema";

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

export type CheckinResult = {
  log: DailyLog;
  alreadyCheckedIn: boolean;
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
  finalSbtTxHash: string | null;
};

export type ReportData = {
  title: string;
  reportText: string;
  recentLogs: DailyLog[];
  chartByDay: number[];
  range: "week" | "final";
};

export interface ApiClient {
  getHomeSnapshot: (address?: string | null) => Promise<HomeSnapshot>;
  getDailySnapshot: (address: string, dayIndex: number) => Promise<DailySnapshot>;
  checkin: (params: { address: string; dayIndex: number; text: string }) => Promise<CheckinResult>;
  submitProof: (params: { address: string }) => Promise<DailyLog>;
  mintDay: (params: { address: string }) => Promise<DailyLog>;
  getProgress: (params: { address: string }) => Promise<ProgressData>;
  composeFinal: (params: { address: string }) => Promise<User>;
  mintMilestone: (params: { address: string; milestoneId: number; txHash?: string }) => Promise<User>;
  getReport: (params: { address: string; range: "week" | "final" }) => Promise<ReportData>;
}
