from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    version: str


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


class CheckinRequest(BaseModel):
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
    status: str
    txHash: Optional[str] = None
    daySbtTxHash: Optional[str] = None
    createdAt: str


class CheckinResponse(BaseModel):
    log: DailyLogResponse
    alreadyCheckedIn: bool


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


class TxConfirmResponse(BaseModel):
    ok: bool


class SbtConfirmRequest(BaseModel):
    address: str
    type: str
    dayIndex: Optional[int] = None
    txHash: str
    chainId: int
    contractAddress: str


class SbtConfirmResponse(BaseModel):
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
    dayMintCount: int
    completedDays: List[int]
    shouldMintDay: bool
    mintableDayIndex: Optional[int]
    shouldComposeFinal: bool
    finalMinted: bool
    finalSbtTxHash: Optional[str] = None
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
