"""Human agent data models and types."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class HumanAgentStatus(str, Enum):
    """Status of a human agent."""
    AVAILABLE = "available"
    BUSY = "busy"
    BREAK = "break"
    OFFLINE = "offline"


class Specialization(str, Enum):
    """Agent specialization areas."""
    GENERAL = "general"
    CLAIMS = "claims"
    BILLING = "billing"
    POLICY = "policy"
    ESCALATION = "escalation"
    TECHNICAL = "technical"


class WorkloadMetrics(BaseModel):
    """Current workload metrics for an agent."""
    active_conversations: int = Field(default=0, ge=0)
    queue_length: int = Field(default=0, ge=0)
    avg_response_time_minutes: float = Field(default=0.0, ge=0.0)
    satisfaction_score: float = Field(default=5.0, ge=1.0, le=10.0)
    stress_level: float = Field(default=1.0, ge=1.0, le=10.0)


class HumanAgent(BaseModel):
    """Human agent model."""
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent full name")
    email: str = Field(..., description="Agent email address")
    status: HumanAgentStatus = Field(default=HumanAgentStatus.OFFLINE)
    specializations: List[Specialization] = Field(default_factory=list)
    max_concurrent_conversations: int = Field(default=3, ge=1, le=10)
    experience_level: int = Field(default=1, ge=1, le=5, description="1=Junior, 5=Senior")
    languages: List[str] = Field(default_factory=lambda: ["en"])
    workload: WorkloadMetrics = Field(default_factory=WorkloadMetrics)
    last_activity: Optional[datetime] = None
    shift_start: Optional[str] = Field(None, description="Shift start time in HH:MM format")
    shift_end: Optional[str] = Field(None, description="Shift end time in HH:MM format")
    metadata: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        use_enum_values = True