from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    foo: Mapped[int]
    bar: Mapped[int]

    __table_args__ = (UniqueConstraint("foo", "bar"),)
