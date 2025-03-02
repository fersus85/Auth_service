from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HistoryBase(BaseModel):
    id: UUID
    created_at: datetime | None = None
    device_info: str | None = None

    model_config = ConfigDict(from_attributes=True)


class HistoryRead(BaseModel):
    total: int
    page_number: int
    page_size: int
    results: List[HistoryBase]
