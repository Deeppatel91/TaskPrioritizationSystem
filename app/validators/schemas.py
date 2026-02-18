from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List, Any


# ─────────────────────────────────────────────
# INPUT SCHEMA
# ─────────────────────────────────────────────

class TaskInput(BaseModel):
    """
    Schema for a single task submitted by the caller.

    Validation rules
    ────────────────
    task_id         : must be a positive integer
    title           : must be a non-empty string
    deadline_days   : must be >= 0  (0 = due today, still valid)
    estimated_hours : must be > 0
    importance      : must be an integer in [1, 10]
    """
    task_id: int
    title: str
    deadline_days: int
    estimated_hours: float
    importance: int

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("task_id must be a positive integer")
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be empty")
        return v

    @field_validator("deadline_days")
    @classmethod
    def validate_deadline(cls, v: int) -> int:
        if v < 0:
            raise ValueError("deadline_days must be 0 or greater (negative deadlines are not allowed)")
        return v

    @field_validator("estimated_hours")
    @classmethod
    def validate_hours(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("estimated_hours must be greater than 0")
        return v

    @field_validator("importance")
    @classmethod
    def validate_importance(cls, v: int) -> int:
        if not (1 <= v <= 10):
            raise ValueError("importance must be an integer between 1 and 10 (inclusive)")
        return v


# ─────────────────────────────────────────────
# OUTPUT / RESPONSE SCHEMAS
# ─────────────────────────────────────────────

class TaskResult(BaseModel):
    """A successfully prioritized task returned to the caller."""
    task_id: int
    title: str
    deadline_days: int
    estimated_hours: float
    importance: int
    urgency_score: float
    effort_penalty: float
    priority_score: float
    category: str

    model_config = {"from_attributes": True}


class RejectedTask(BaseModel):
    """An invalid task together with the reason it was rejected."""
    raw_data: Any
    error_reason: str


class PrioritizeResponse(BaseModel):
    """Response body for POST /tasks/prioritize."""
    prioritized_tasks: List[TaskResult]
    rejected_tasks: List[RejectedTask]
    total_submitted: int
    total_prioritized: int
    total_rejected: int


class ValidateResponse(BaseModel):
    """Response body for POST /tasks/validate."""
    valid_tasks: List[TaskInput]
    invalid_tasks: List[RejectedTask]
    total_submitted: int
    total_valid: int
    total_invalid: int


class HealthResponse(BaseModel):
    """Response body for GET /health."""
    status: str
    message: str