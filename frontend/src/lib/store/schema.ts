export type Reflection = {
  note: string;
  next: string;
};

export type DailyTask = {
  dayIndex: number;
  title: string;
  instruction: string;
  hint?: string;
};

export type DailyLogStatus = "CREATED" | "SUBMITTED";

export type DailyLog = {
  id: string;
  address: string;
  challengeId: number;
  dayIndex: number;
  dateKey: string;
  normalizedText: string;
  reflection: Reflection;
  saltHex: string;
  proofHash: string;
  status: DailyLogStatus;
  txHash: string | null;
  daySbtTxHash: string | null;
  nftImage: string | null; // 生成的NFT图片 base64 数据
  createdAt: string;
};

export type User = {
  timezone: string;
  startDateKey: string | null;
  streak: number;
  lastDateKey: string | null;
  dayMintCount: number;
  finalMinted: boolean;
  finalSbtTxHash: string | null;
  milestones: Record<number, string>; // key: 1 (Week 1), 2 (Week 2), value: txHash
};

export type Store = {
  users: Record<string, User>;
  logs: DailyLog[];
};
