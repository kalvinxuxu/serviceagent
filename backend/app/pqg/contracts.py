from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class PQGStatus(str, Enum):
    READY = "READY"
    EMPTY = "EMPTY"
    SUPPRESSED = "SUPPRESSED"
    DEGRADED = "DEGRADED"


class CandidateSource(str, Enum):
    RETRIEVAL = "RETRIEVAL"
    LLM = "LLM"
    HYBRID = "HYBRID"


class PQGRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str = Field(min_length=1, max_length=128)
    assistant_message_id: str = Field(min_length=1, max_length=128)
    context: str = Field(default="", max_length=6000)
    reply: str = Field(default="", max_length=4000)
    force_refresh: bool = False
    policy_version: str = Field(default="default-v1", max_length=40)


class QuestionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: str
    text: str = Field(min_length=2, max_length=120)
    source: CandidateSource
    relevance_score: float | None = Field(default=None, ge=0, le=1)
    confidence: float | None = Field(default=None, ge=0, le=1)
    rank: int = Field(ge=1, le=3)
    evidence_ids: list[str] = Field(default_factory=list)


class LLMQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=2, max_length=120)
    reason: str = Field(default="", max_length=200)


class LLMGenerationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str
    questions: list[LLMQuestion] = Field(max_length=3)


class PQGResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "pqg.v1"
    request_id: str
    session_id: str
    assistant_message_id: str
    status: PQGStatus
    questions: list[QuestionCandidate] = Field(default_factory=list, max_length=3)
    generated_at: str
    latency_ms: float
    error_code: str | None = None
