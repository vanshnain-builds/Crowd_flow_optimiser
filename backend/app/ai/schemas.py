from __future__ import annotations

"""
Pydantic schemas for AI inputs and outputs.
These are the validated shapes the AI layer must produce.
"""

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


# ── AI Call 1: Scenario Intelligence output ──────────────────────────────────

class EntryDistributionItem(BaseModel):
    gateId: str
    fraction: float = Field(ge=0.0, le=1.0)


class EventTimingInfo(BaseModel):
    startMinutesOfDay: int = Field(ge=0, le=1439)
    durationMin: int = Field(ge=1, le=1440)
    arrivalPattern: Literal["gradual", "surge", "sustained", "peak-early"] = "surge"
    departurePattern: Literal["gradual", "surge", "sustained"] = "surge"


class CrowdGroupInfo(BaseModel):
    id: str
    name: str
    size: int = Field(ge=1)
    entryGateId: str
    destinationNodeId: str
    arrivalStartMin: float
    arrivalEndMin: float


class ParsedScenario(BaseModel):
    """Structured scenario extracted by AI — must be validated before simulation."""
    name: str = "Event"
    venueId: str = "venue-stadium-a"
    crowdSize: int = Field(ge=1, le=500000)
    entryDistribution: list[EntryDistributionItem] = Field(default_factory=list)
    crowdGroups: list[CrowdGroupInfo] = Field(default_factory=list)
    timing: EventTimingInfo = Field(default_factory=EventTimingInfo)
    entryRate: float = Field(default=500.0, ge=1.0)
    exitRate: float = Field(default=800.0, ge=1.0)
    specialConditions: list[dict] = Field(default_factory=list)
    naturalLanguage: str = ""
    notes: list[str] = Field(default_factory=list)

    @field_validator("entryDistribution")
    @classmethod
    def validate_fractions(cls, v: list[EntryDistributionItem]) -> list[EntryDistributionItem]:
        if v:
            total = sum(item.fraction for item in v)
            if abs(total - 1.0) > 0.05:
                # Normalize fractions
                for item in v:
                    item.fraction = item.fraction / total
        return v


class ScenarioParseResult(BaseModel):
    """Result of AI scenario parsing — includes both structured data and metadata."""
    success: bool
    parsed: ParsedScenario | None = None
    stage: Literal["idle", "understanding", "extracting", "validating", "ready"] = "idle"
    notes: list[str] = Field(default_factory=list)
    error: str | None = None
    raw_text: str = ""


# ── AI Call 2: Safety Analyst output ─────────────────────────────────────────

class SafetyAnalysis(BaseModel):
    """Structured safety analysis output from AI — explains deterministic results."""
    summary: str
    risk_explanation: str
    affected_locations: list[str] = Field(default_factory=list)
    contributing_factors: list[str] = Field(default_factory=list)
    recommended_action: str
    urgency: Literal["low", "moderate", "high", "critical", "emergency"]
    supporting_metrics: dict[str, Any] = Field(default_factory=dict)
    generated_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    confidence: Literal["low", "medium", "high"] = "medium"


# ── Frontend AI recommendation format ────────────────────────────────────────

class AIRecommendation(BaseModel):
    """Maps SafetyAnalysis to frontend AIRecommendation type."""
    id: str
    atMinute: float
    riskLevel: str
    headline: str
    explanation: str
    recommendedAction: str
    confidence: Literal["low", "medium", "high"]
    basis: str

    def to_frontend_dict(self) -> dict:
        return self.model_dump()
