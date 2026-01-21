from datetime import datetime
from sqlmodel import SQLModel

class Status():
    INIT: int
    PENDING: int
    FINISHED: int
    CANCELED: int
    FAILED: int

class Record(SQLModel, table=True):
    __tablename__ = 'records'

    id: int
    prompt: str
    picture_url: str

    status: Status
    operator_id: int
    created_at: datetime
    updated_at: datetime


    def create(self, session, prompt: str, url: str) -> 'Record':
        pass