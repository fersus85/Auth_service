from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class HistoryBase(BaseModel):
    id: UUID
    last_logon: datetime | None = None
    device_info: str | None = None


class HistoryRead(HistoryBase):
    pass
