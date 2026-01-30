from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

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
    timezone: str
    text: Optional[str] = None
    imageUrl: Optional[str] = None

class Reflection(BaseModel):
    note: str
    next: str

class CheckinResponse(BaseModel):
    logId: str
    challengeId: int
    dateKey: str
    dayIndex: int
    reflection: Reflection
    proofHash: str
    streak: int
    milestoneEligible: int
    alreadyCheckedIn: bool

class TxConfirmRequest(BaseModel):
    logId: str
    address: str
    txHash: str
    chainId: int
    contractAddress: str

class TxConfirmResponse(BaseModel):
    ok: bool

class ProgressResponse(BaseModel):
    address: str
    challengeId: int
    timezone: str
    streak: int
    lastDateKey: Optional[str]
    todayCheckedIn: bool
    completedDays: List[int]
    milestonesEligible: Dict[str, bool]
    badgesMinted: Dict[str, bool]

class ReportResponse(BaseModel):
    address: str
    challengeId: int
    range: str
    fromDate: str = Field(alias="from")
    to: str
    reportText: str
    chartData: Dict[str, Any]
