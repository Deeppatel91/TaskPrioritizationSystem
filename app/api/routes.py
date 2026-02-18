from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

# Importing for database access and Pydantic schemas
from app.db.database import get_db
from app.validators.schemas import (
    TaskInput,
    TaskResult,
    RejectedTask,
    PrioritizeResponse,
    ValidateResponse,
    HealthResponse,
)
from app.services.scoring_logic import prioritize_tasks
from app.services.db_service import (
    save_prioritized_tasks,
    save_invalid_tasks,
    get_all_tasks,
    get_all_invalid_tasks,
)

router = APIRouter() # Initializing the FastAPI router for backend 

def _separate_tasks(raw_list: List[Any]):
    """
    Helper function to validate the input list and separate valid 
    tasks from rejected ones with error reasons.
    """
    valid: List[TaskInput] = []
    rejected: List[RejectedTask] = []
    for item in raw_list:
        if not isinstance(item, dict):
            rejected.append(
                RejectedTask(
                    raw_data=item,
                    error_reason="Task must be a JSON object, not a value.",
                )
            )
            continue

        try:
            valid.append(TaskInput(**item))
        except ValidationError as exc:
            messages = "; ".join(
                f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}"
                for e in exc.errors()
            )
            rejected.append(RejectedTask(raw_data=item, error_reason=messages))

    return valid, rejected

@router.post(
    "/tasks/prioritize",
    response_model=PrioritizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate, score, and store tasks",
    tags=["Tasks"],
)
def prioritize(
    payload: List[Any],
    db: Session = Depends(get_db), 
):
    """
    Processes the list of tasks and validate them and to calculate the priority scores, 
    and process both invalid and valid tasks to the database. 
    """
    if not isinstance(payload, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body must be a JSON array of task objects.",
        )

    if len(payload) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body must contain at least one task.",
        )

    # Separate sorted valid and invalid tasks buckets
    valid_tasks, rejected_tasks = _separate_tasks(payload)

    # Final logic to calculate the scores 
    prioritized = prioritize_tasks(valid_tasks) if valid_tasks else []
    
    if prioritized:
        save_prioritized_tasks(db, prioritized)
    if rejected_tasks:
        save_invalid_tasks(db, rejected_tasks)

    return PrioritizeResponse(
        prioritized_tasks=prioritized,
        rejected_tasks=rejected_tasks,
        total_submitted=len(payload),
        total_prioritized=len(prioritized),
        total_rejected=len(rejected_tasks),
    )

@router.post(
    "/tasks/validate",
    response_model=ValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate tasks without scoring",
    tags=["Tasks"],
)
def validate(payload: List[Any]):
    """
    Practice check to see if tasks meet the schema requirements 
    without calculating scores or saving to the database.
    """
    if not isinstance(payload, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body must be a JSON array of task objects.",
        )

    valid_tasks, rejected_tasks = _separate_tasks(payload)

    return ValidateResponse(
        valid_tasks=valid_tasks,
        invalid_tasks=rejected_tasks,
        total_submitted=len(payload),
        total_valid=len(valid_tasks),
        total_invalid=len(rejected_tasks),
    )

# RESTful API endpoints 
@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    tags=["System"],
)
def health():
    """Simple connectivity check to confirm the API is reachable."""
    return HealthResponse(status="ok", message="Task Prioritization API is running.")


# Database retrieval 
@router.get(
    "/tasks",
    response_model=List[TaskResult],
    status_code=status.HTTP_200_OK,
    summary="List all stored prioritized tasks",
    tags=["Tasks"],
)
def list_tasks(db: Session = Depends(get_db)):
    """Fetches all successfully prioritized tasks from the database."""
    rows = get_all_tasks(db)
    return [
        TaskResult(
            task_id=r.task_id,
            title=r.title,
            deadline_days=r.deadline_days,
            estimated_hours=r.estimated_hours,
            importance=r.importance,
            urgency_score=r.urgency_score,
            effort_penalty=r.effort_penalty,
            priority_score=r.priority_score,
            category=r.category,
        )
        for r in rows
    ]

# Endpoint for invalid and rejected tasks data retrieval
@router.get(
    "/tasks/invalid",
    response_model=List[RejectedTask],
    status_code=status.HTTP_200_OK,
    summary="List all rejected / invalid tasks",
    tags=["Tasks"],
)
def list_invalid_tasks(db: Session = Depends(get_db)):
    """Fetches the audit log of failed task submissions."""
    rows = get_all_invalid_tasks(db)
    return [RejectedTask(raw_data=r.raw_data, error_reason=r.error_reason) for r in rows]