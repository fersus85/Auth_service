from typing import List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class HistoryBase(BaseModel):
    id: UUID
    created_at: datetime | None = None
    device_info: str | None = None

    class Config:
        from_attributes = True


class HistoryRead(BaseModel):
    total: int
    page_number: int
    page_size: int
    results: List[HistoryBase]
