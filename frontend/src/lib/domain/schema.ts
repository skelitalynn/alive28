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
export type ProofStatus = "ACTIVE" | "REVOKED" | "SUPERSEDED";

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
  proofStatus: ProofStatus;
  effectiveProofHash: string;
  status: DailyLogStatus;
  txHash: string | null;
  dayNftTxHash: string | null;
  nftImage: string | null;
  createdAt: string;
};

export type User = {
  timezone: string;
  startDateKey: string | null;
  streak: number;
  lastDateKey: string | null;
  dayMintCount: number;
  finalMinted: boolean;
  finalNftTxHash: string | null;
  milestones: Record<number, string>;
};
