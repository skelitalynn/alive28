from typing import TypedDict, Optional, Dict, Any, List


class GraphState(TypedDict, total=False):
    flow: str
    address: str
    timezone: str
    challengeId: int
    dateKey: str
    dayIndex: int
    text: Optional[str]
    imageUrl: Optional[str]
    normalizedText: str
    imageDesc: Optional[str]
    task: Dict[str, Any]
    reflection: Dict[str, str]
    saltHex: str
    proofHash: str
    inputHash: Optional[str]
    submitHint: Dict[str, Any]
    logId: Optional[str]
    txHash: Optional[str]
    txStatus: Optional[str]
    chainId: Optional[int]
    contractAddress: Optional[str]
    streak: int
    completedDays: List[int]
    todayCheckedIn: bool
    reportRange: Optional[str]
    reportText: Optional[str]
    chartByDay: Optional[List[int]]
    recentLogs: Optional[List[Any]]
    title: Optional[str]
    startDateKey: Optional[str]
    milestones: Optional[Dict[str, Optional[str]]]
    eligibleMilestones: Optional[List[int]]
    alreadyCheckedIn: bool
    db: Any
