"""
scoring_logic.py
════════════════
Core prioritization engine.

Priority Formula
────────────────
priority_score = (0.50 × urgency_score)
               + (0.30 × importance_norm)
               − (0.20 × effort_penalty)

Where every intermediate value is normalised to [0, 100] before blending.

Urgency Score
─────────────
urgency_score = clamp(100 − deadline_days × 3, 0, 100)

• deadline = 0  → urgency = 100  (task is overdue / due today)
• deadline = 33 → urgency = 1    (distant deadline)
• deadline > 33 → urgency = 0    (very distant deadline)

Importance Normalisation
────────────────────────
importance_norm = ((importance − 1) / 9) × 100

Maps the 1-10 importance scale linearly to [0, 100].

Effort Penalty
──────────────
available_hours = deadline_days × 8       (8 working hours per day)

if deadline_days == 0:
    effort_penalty = 100 if estimated_hours > 0 else 0

else:
    raw = (estimated_hours / available_hours) × 100
    effort_penalty = clamp(raw, 0, 100)

A penalty of 100 means the task *cannot realistically be finished* before the
deadline — it still appears in the output but receives a heavy score reduction.

Conflict Resolution
───────────────────
The weighted formula handles conflicts automatically:
  • High importance + far deadline  → importance boosts score, low urgency
    reduces it → usually Medium priority.
  • Low importance + near deadline  → high urgency pushes it to Medium; it
    cannot reach High without importance.
  • Impossible task (hours > available) → effort_penalty = 100, heavily
    reduces priority_score → Low priority.

Deterministic Tie-Breaking
───────────────────────────
Tasks with equal priority_score are sorted by:
  1. deadline_days ASC  (sooner deadline comes first)
  2. task_id ASC        (lower ID comes first — stable, predictable)

Categorisation
──────────────
  ≥ 70  → High
  ≥ 40  → Medium
  <  40 → Low
"""

from typing import List, Dict, Any
from app.validators.schemas import TaskInput, TaskResult


# ── Weights ──────────────────────────────────────────────────────────────────
URGENCY_WEIGHT = 0.50
IMPORTANCE_WEIGHT = 0.30
EFFORT_WEIGHT = 0.20

# ── Thresholds ────────────────────────────────────────────────────────────────
HIGH_THRESHOLD = 70.0
MEDIUM_THRESHOLD = 40.0

# ── Working hours assumed per day ─────────────────────────────────────────────
WORKING_HOURS_PER_DAY = 8


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    """Return value clamped to [low, high]."""
    return max(low, min(high, value))


def compute_urgency(deadline_days: int) -> float:
    """
    Higher urgency for tasks with fewer days remaining.
    deadline = 0  → 100
    deadline = 33 → 1
    deadline > 33 → 0
    """
    return _clamp(100.0 - deadline_days * 3.0)


def compute_importance_norm(importance: int) -> float:
    """Normalise importance (1-10) to a 0-100 scale."""
    return ((importance - 1) / 9.0) * 100.0


def compute_effort_penalty(deadline_days: int, estimated_hours: float) -> float:
    """
    Penalise tasks that cannot realistically be completed before the deadline.

    If deadline is today (0 days), any non-zero estimated_hours yields a
    full penalty of 100.
    """
    if deadline_days == 0:
        return 100.0 if estimated_hours > 0 else 0.0

    available_hours = deadline_days * WORKING_HOURS_PER_DAY
    raw = (estimated_hours / available_hours) * 100.0
    return _clamp(raw)


def compute_priority_score(
    urgency: float, importance_norm: float, effort_penalty: float
) -> float:
    """Apply weighted formula and clamp result to [0, 100]."""
    raw = (
        URGENCY_WEIGHT * urgency
        + IMPORTANCE_WEIGHT * importance_norm
        - EFFORT_WEIGHT * effort_penalty
    )
    return round(_clamp(raw), 2)


def categorise(score: float) -> str:
    """Map a priority score to a category label."""
    if score >= HIGH_THRESHOLD:
        return "High"
    if score >= MEDIUM_THRESHOLD:
        return "Medium"
    return "Low"


def score_task(task: TaskInput) -> TaskResult:
    """
    Compute all intermediate values and the final priority score for one task.
    Returns a TaskResult ready for storage and API response.
    """
    urgency = compute_urgency(task.deadline_days)
    importance_norm = compute_importance_norm(task.importance)
    effort_penalty = compute_effort_penalty(task.deadline_days, task.estimated_hours)
    priority_score = compute_priority_score(urgency, importance_norm, effort_penalty)
    category = categorise(priority_score)

    return TaskResult(
        task_id=task.task_id,
        title=task.title,
        deadline_days=task.deadline_days,
        estimated_hours=task.estimated_hours,
        importance=task.importance,
        urgency_score=round(urgency, 2),
        effort_penalty=round(effort_penalty, 2),
        priority_score=priority_score,
        category=category,
    )


def prioritize_tasks(tasks: List[TaskInput]) -> List[TaskResult]:
    """
    Score and sort a list of validated tasks.

    Sorting:
      1. priority_score DESC  (highest priority first)
      2. deadline_days ASC    (tie-break: sooner deadline first)
      3. task_id ASC          (tie-break: lower ID first — deterministic)
    """
    results = [score_task(t) for t in tasks]
    results.sort(
        key=lambda r: (-r.priority_score, r.deadline_days, r.task_id)
    )
    return results