from typing import List, Dict, Any #importing libraries for data handling
from app.validators.schemas import TaskInput, TaskResult 



"""
scoring_logic.py

This module contains the core business logic for the Task Prioritization System.
It computes urgency, importance normalization, effort penalty, and final priority
scores for tasks in a deterministic and explainable way.
"""



#weight for proirity formula 
URGENCY_WEIGHT = 0.50 # urgency has the high impact
IMPORTANCE_WEIGHT = 0.30 #importance has medium impact
EFFORT_WEIGHT = 0.20 # effort reduces score 


#set thresholds for categorization
HIGH_THRESHOLD = 60.0
MEDIUM_THRESHOLD = 40.0

#taking working hour assumption to 8 hrs a day fixed 
WORKING_HOURS_PER_DAY = 8


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    """Return value clamped to [low, high]."""
    return max(low, min(high, value))

#urgency calculation logic
def compute_urgency(deadline_days: int) -> float:
    return _clamp(100.0 - deadline_days * 3.0)
    """
    examples 
    Higher urgency for tasks with fewer days remaining.
    deadline = 0 (days) → 100
    deadline = 33 (days)→ 1
    deadline > 33 (days) → 0
    """

#importance normalization logic
def compute_importance_norm(importance: int) -> float:
    """Normalise importance (1-10) to a 0-100 scale."""
    return ((importance - 1) / 9.0) * 100.0


#effort penalty logic calculation
def compute_effort_penalty(deadline_days: int, estimated_hours: float) -> float:
    """
    example.
    Penalise tasks that cannot realistically be completed before the deadline.
    If deadline is today (0 days), any non-zero estimated_hours yields a
    full penalty of 100.
    """
    if deadline_days == 0:
        return 100.0 if estimated_hours > 0 else 0.0
    available_hours = deadline_days * WORKING_HOURS_PER_DAY
    raw = (estimated_hours / available_hours) * 100.0
    return _clamp(raw)



#finale priority score calculation 
def compute_priority_score(
    urgency: float, importance_norm: float, effort_penalty: float
) -> float:
    """Apply weighted formula and clamp result to [0, 100].
    formula = priority = (0.50 * urgency) + (0.30 * importance_norm) - (0.20 * effort_penalty)
    """
    raw = (
        URGENCY_WEIGHT * urgency
        + IMPORTANCE_WEIGHT * importance_norm
        - EFFORT_WEIGHT * effort_penalty
    )
    return round(_clamp(raw), 2)



"""mapping set for category labels (high medium and low
Convert numeric score into priority category.

    ≥ 70  → High
    ≥ 40  → Medium
    < 40  → Low)
    """
def categorise(score: float) -> str:
    if score >= HIGH_THRESHOLD:
        return "High"
    if score >= MEDIUM_THRESHOLD:
        return "Medium"
    return "Low"



#Score Single Task
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



#sorting priority logic for multiple tasks
def prioritize_tasks(tasks: List[TaskInput]) -> List[TaskResult]:
    """
    Score and sort a list of validated tasks.
    Sorting:
      1.  priority_score (highest priority first)
      2. deadline_days ASC    (tie-break: sooner deadline first)
      3. task_id ASC          (tie-break: lower ID first — deterministic)
    """


    
    results = [score_task(t) for t in tasks]
    results.sort(
        key=lambda r: (-r.priority_score, r.deadline_days, r.task_id)
    )
    return results