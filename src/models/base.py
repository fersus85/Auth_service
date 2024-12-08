from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

metadata = MetaData(schema="content")


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True
    metadata = metadata
