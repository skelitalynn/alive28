from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    error: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    version: str
    demo_mode: bool = False


class DailyPromptResponse(BaseModel):
    challengeId: int
    dayIndex: int
    title: str
    instruction: str
    hint: Optional[str]


class UserResponse(BaseModel):
    address: str
    displayName: Optional[str]
    avatarUrl: Optional[str]
    timezone: str
    challengeId: int
    createdAt: str
    updatedAt: str


class UserUpdateRequest(BaseModel):
    address: str
    displayName: Optional[str] = None
    avatarUrl: Optional[str] = None
    timezone: str


class AuthNonceRequest(BaseModel):
    address: str


class AuthNonceResponse(BaseModel):
    message: str
    expiresAt: str


class AuthVerifyRequest(BaseModel):
    address: str
    signature: str


class AuthVerifyResponse(BaseModel):
    token: str
    address: str
    expiresAt: str


class CheckinRequest(BaseModel):
    checkinId: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )
    address: str
    dayIndex: int
    text: Optional[str] = None
    timezone: Optional[str] = None
    imageUrl: Optional[str] = None


class Reflection(BaseModel):
    note: str
    next: str


class DailyTask(BaseModel):
    dayIndex: int
    title: str
    instruction: str
    hint: Optional[str] = None


class DailyLogResponse(BaseModel):
    id: str
    address: str
    challengeId: int
    dayIndex: int
    dateKey: str
    normalizedText: str
    reflection: Reflection
    saltHex: str
    proofHash: str
    proofStatus: str
    effectiveProofHash: str
    status: str
    txHash: Optional[str] = None
    dayNftTxHash: Optional[str] = None
    createdAt: str


class CheckinExecutionError(BaseModel):
    node: str
    type: str
    message: str


class CheckinExecution(BaseModel):
    promptVersion: str
    modelProvider: str
    modelName: str
    modelAttempts: int
    repairAttempts: int
    fallbackReason: Optional[str] = None
    nodeDurationsMs: Dict[str, float]
    nodeAttempts: Dict[str, int]
    lastError: Optional[CheckinExecutionError] = None


class CheckinResponse(BaseModel):
    outcome: Literal[
        "accepted",
        "already_checked_in",
        "clarify",
        "rejected",
        "crisis_redirected",
    ]
    log: Optional[DailyLogResponse] = None
    alreadyCheckedIn: bool
    message: Optional[str] = None
    reflection: Optional[Reflection] = None
    checkinId: str
    recovered: bool = False
    execution: CheckinExecution


class DailySnapshotResponse(BaseModel):
    dateKey: str
    task: DailyTask
    log: Optional[DailyLogResponse] = None
    alreadyCheckedIn: bool


class HomeSnapshotResponse(BaseModel):
    dayBtnLabel: str
    dayBtnTarget: int
    startDateKey: Optional[str] = None
    todayDateKey: str


class TxConfirmRequest(BaseModel):
    logId: str
    address: str
    txHash: str
    chainId: int
    contractAddress: str
    approvalId: Optional[str] = None


class TxConfirmResponse(BaseModel):
    ok: bool


class ProofApprovalRequest(BaseModel):
    address: str
    logId: str


class ProofApprovalResponse(BaseModel):
    approvalId: str
    deadline: int
    signature: str
    proofHash: str


class ProofCompensationRequest(BaseModel):
    address: str
    logId: str
    action: Literal["revoke", "supersede"]
    reason: str = Field(min_length=3, max_length=500)
    replacementProofHash: Optional[str] = None


class ProofCompensationResponse(BaseModel):
    id: str
    logId: str
    action: str
    reason: str
    previousProofHash: str
    replacementProofHash: Optional[str] = None
    createdAt: str


class NftConfirmRequest(BaseModel):
    address: str
    type: str  # "DAY" | "FINAL"
    dayIndex: Optional[int] = None
    txHash: str
    chainId: int
    contractAddress: str


class NftConfirmResponse(BaseModel):
    ok: bool


class MilestoneMintRequest(BaseModel):
    address: str
    milestoneId: int
    txHash: str
    chainId: int
    contractAddress: str


class MilestoneMintResponse(BaseModel):
    ok: bool
    milestones: Dict[str, Optional[str]]


class ProgressResponse(BaseModel):
    dateKey: str
    streak: int
    dayMintCount: int = 0
    completedDays: List[int]
    shouldMintDay: bool = False
    mintableDayIndex: Optional[int] = None
    shouldComposeFinal: bool = False
    finalMinted: bool = False
    finalNftTxHash: Optional[str] = None
    milestones: Dict[str, Optional[str]]
    startDateKey: Optional[str] = None


class ReportResponse(BaseModel):
    title: str
    reportText: str
    recentLogs: List[DailyLogResponse]
    chartByDay: List[int]
    range: str


class MetadataResponse(BaseModel):
    name: str
    description: str
    image: str
    attributes: List[Dict[str, Any]]


class AiReflectionRequest(BaseModel):
    task: DailyTask
    userText: str
    dayIndex: int


class AiReflectionResponse(BaseModel):
    reflection: Reflection


class GenerateNftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address: str
    logId: str


class GenerateNftResponse(BaseModel):
    success: bool
    image: str
    dayIndex: int
    message: str
