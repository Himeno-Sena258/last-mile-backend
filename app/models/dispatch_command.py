import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class DispatchCommand(BaseModel):
    __tablename__ = "dispatch_commands"

    command_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), unique=True, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    attempts = Column(Integer, nullable=False, default=0)
    last_sent_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    interrupted_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)

    task = relationship("Task", back_populates="dispatch_command")
    car = relationship("Car")
