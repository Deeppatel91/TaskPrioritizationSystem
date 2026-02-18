from sqlalchemy.orm import Session
from app.db.models import Task, InvalidTask
from app.db.database import engine, Base
from app.db import models  # Important: loads models into Base.metadata

def save_prioritized_tasks(db: Session, prioritized_tasks):
    for t in prioritized_tasks:
        db_task = Task(
            task_id=t.task_id,
            title=t.title,
            deadline_days=t.deadline_days,
            estimated_hours=t.estimated_hours,
            importance=t.importance,
            urgency_score=t.urgency_score,
            effort_penalty=t.effort_penalty,
            priority_score=t.priority_score,
            category=t.category
        )
        db.add(db_task)
    db.commit()

def save_invalid_tasks(db: Session, rejected_tasks):
    for r in rejected_tasks:
        db_invalid = InvalidTask(
            raw_data=r.raw_data,
            error_reason=r.error_reason
        )
        db.add(db_invalid)
    db.commit()

def get_all_tasks(db: Session):
    return db.query(Task).order_by(Task.priority_score.desc()).all()

def get_all_invalid_tasks(db: Session):
    return db.query(InvalidTask).all()

def init_db():
    # This creates the tables in Postgres
    Base.metadata.create_all(bind=engine)