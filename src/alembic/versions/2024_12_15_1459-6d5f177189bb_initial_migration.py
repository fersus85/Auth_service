"""Initial migration

Revision ID: 6d5f177189bb
Revises:
Create Date: 2024-12-15 14:59:24.539277

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6d5f177189bb"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "role",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="content",
    )
    op.create_index(
        op.f("ix_content_role_name"),
        "role",
        ["name"],
        unique=True,
        schema="content",
    )
    op.create_table(
        "user",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("login", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=255), nullable=False),
        sa.Column("last_name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="content",
    )
    op.create_index(
        op.f("ix_content_user_login"),
        "user",
        ["login"],
        unique=True,
        schema="content",
    )
    op.create_table(
        "active_session",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("refresh_token_id", sa.Uuid(), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("device_info", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["content.user.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="content",
    )
    op.create_index(
        "btree_user_id_device_info",
        "active_session",
        ["user_id", "device_info"],
        unique=False,
        schema="content",
    )
    op.create_index(
        op.f("ix_content_active_session_user_id"),
        "active_session",
        ["user_id"],
        unique=False,
        schema="content",
    )
    op.create_table(
        "session_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "name",
            sa.Enum(
                "LOGIN_WITH_PASSWORD",
                "REFRESH_TOKEN_UPDATE",
                "USER_LOGOUT",
                name="sessionhistorychoices",
            ),
            nullable=False,
        ),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("refresh_token_id", sa.Uuid(), nullable=True),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("device_info", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["content.user.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="content",
    )
    op.create_index(
        op.f("ix_content_session_history_user_id"),
        "session_history",
        ["user_id"],
        unique=False,
        schema="content",
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"], ["content.role.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["content.user.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
        schema="content",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("user_roles", schema="content")
    op.drop_index(
        op.f("ix_content_session_history_user_id"),
        table_name="session_history",
        schema="content",
    )
    op.drop_table("session_history", schema="content")
    op.drop_index(
        op.f("ix_content_active_session_user_id"),
        table_name="active_session",
        schema="content",
    )
    op.drop_index(
        "btree_user_id_device_info",
        table_name="active_session",
        schema="content",
    )
    op.drop_table("active_session", schema="content")
    op.drop_index(
        op.f("ix_content_user_login"), table_name="user", schema="content"
    )
    op.drop_table("user", schema="content")
    op.drop_index(
        op.f("ix_content_role_name"), table_name="role", schema="content"
    )
    op.drop_table("role", schema="content")
    op.execute("DROP TYPE IF EXISTS public.sessionhistorychoices CASCADE")
    # ### end Alembic commands ###
