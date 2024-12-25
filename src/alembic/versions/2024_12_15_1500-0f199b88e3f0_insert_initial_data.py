"""insert initial data

Revision ID: 0f199b88e3f0
Revises: 6d5f177189bb
Create Date: 2024-12-15 15:00:01.471291

"""

from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session

from alembic import op
from core.config import UserRoleDefault
from models.user import Role

# revision identifiers, used by Alembic.
revision: str = "0f199b88e3f0"
down_revision: Union[str, None] = "6d5f177189bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

roles = [
    Role(
        id=UUID("42966562-ec42-44a0-afd6-e72d1a839256"),
        name=UserRoleDefault.SUPERUSER,
        description="Может всё",
    ),
    Role(
        id=UUID("20afcc37-e8dc-473a-a3ce-a61e6b3d563e"),
        name=UserRoleDefault.ADMIN,
        description="Администратор",
    ),
    Role(
        id=UUID("41987fd3-88cb-412c-9085-89201470610e"),
        name=UserRoleDefault.SUBSCRIBER,
        description="Пользователь с допами",
    ),
    Role(
        id=UUID("ab1d025b-0e33-42e2-bba8-cf7125044263"),
        name=UserRoleDefault.USER,
        description="Зарегестрированный пользователь",
    ),
]


def upgrade() -> None:
    bind = op.get_bind()
    with Session(bind=bind) as session:
        session.add_all(roles)
        session.commit()


def downgrade() -> None:
    role_ids = [role.id for role in roles]

    bind = op.get_bind()
    with Session(bind=bind) as session:
        session.execute(sa.delete(Role).where(Role.id.in_(role_ids)))
        session.commit()
