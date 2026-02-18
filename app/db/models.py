from datetime import datetime 
from sqlalchemy import Column, Integer, Float, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.db.database import Base 

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True) #primary key for internal database use set to autoincrement 
    task_id = Column(Integer, nullable=False, index=True) #this task id is provided by the user 
    title = Column(Text, nullable=False)
    deadline_days = Column(Integer, nullable=False)
    estimated_hours = Column(Float, nullable=False) #Estimated time to complete the task in hours
    importance = Column(Integer, nullable=False) # importance is set from scale of (1 to 10)..
    urgency_score = Column(Float, nullable=False) #urgency scrore logic ccreated by me 
    effort_penalty = Column(Float, nullable=False) #effort penalty logic created by me
    priority_score = Column(Float, nullable=False) #priority score calculated using weighted formula
    category = Column(String(10), nullable=False) #here string is choosen because it is divided in to HIGH/MEDIUM and LOW.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False) ##auto filled time stamp 




#invalid tasks are stored in this table 
class InvalidTask(Base):
    __tablename__ = "invalid_tasks"
    id = Column(Integer, primary_key=True, autoincrement=True) #primary key for internal DB usee..
    raw_data = Column(JSONB, nullable=False)#Store the original invalid request data previously entered 
    error_reason = Column(Text, nullable=False) #
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False) #auto time stamps