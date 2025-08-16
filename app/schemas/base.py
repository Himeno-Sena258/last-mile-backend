from pydantic import BaseModel
from datetime import datetime

class BaseSchema:
    __abstract__ = True
    id: int 
    created_at: datetime
    updated_at: datetime


