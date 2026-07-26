from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Run(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task: str
    status: str = Field(default="running")  # running | paused_for_approval | completed | failed
    model: str = Field(default="gpt-4o")
    messages_json: str = Field(default="[]")  # serialized Anthropic message history, used to resume after approval
    total_tokens_in: int = Field(default=0)
    total_tokens_out: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Step(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="run.id", index=True)
    seq: int
    type: str  # reasoning | tool_call | tool_result | approval_pending | approval_granted | approval_denied | final | error
    content: str = Field(default="")
    tool_name: Optional[str] = None
    tool_input: Optional[str] = None  # JSON string
    tool_output: Optional[str] = None  # JSON string
    tool_use_id: Optional[str] = None
    requires_approval: bool = Field(default=False)
    latency_ms: Optional[int] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
