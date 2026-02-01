from typing import Optional, Dict
from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy import UniqueConstraint
from datetime import datetime


class UserProgress(SQLModel, table=True):
    address: str = Field(primary_key=True, max_length=42, index=True)
    display_name: Optional[str] = Field(default=None, max_length=32, index=True)
    avatar_url: Optional[str] = Field(default=None, max_length=512)
    timezone: str = Field(default="Asia/Shanghai", max_length=64)
    challenge_id: int = Field(default=1, index=True)
    start_date_key: str = Field(max_length=10)
    streak: int = Field(default=0)
    last_date_key: Optional[str] = Field(default=None, max_length=10)
    last_day_index: Optional[int] = Field(default=None)
    day_mint_count: int = Field(default=0)
    final_minted: bool = Field(default=False)
    final_sbt_tx_hash: Optional[str] = Field(default=None, max_length=66)
    milestones: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {"1": None, "2": None, "3": None},
        sa_column=Column(JSON)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DailyLog(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("address", "challenge_id", "date_key", name="uq_dailylog_address_challenge_date"),
    )
    id: str = Field(primary_key=True, max_length=36)
    address: str = Field(max_length=42, index=True)
    challenge_id: int = Field(default=1, index=True)
    day_index: int = Field(index=True)
    date_key: str = Field(max_length=10, index=True)
    input_hash: Optional[str] = Field(default=None, max_length=64)
    normalized_text: Optional[str] = Field(default=None)
    reflection: dict = Field(sa_column=Column(JSON))
    salt_hex: str = Field(max_length=128)
    proof_hash: str = Field(max_length=66)
    status: str = Field(default="CREATED", max_length=24, index=True)
    chain_id: Optional[int] = Field(default=None)
    contract_address: Optional[str] = Field(default=None, max_length=42)
    tx_hash: Optional[str] = Field(default=None, max_length=66)
    block_number: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
