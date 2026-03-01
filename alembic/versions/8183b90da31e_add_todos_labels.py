"""Add todos.labels

Revision ID: 8183b90da31e
Revises:
Create Date: 2026-02-26 08:39:18.642034

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8183b90da31e"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("todos", sa.Column("label", sa.String))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("todos", "label")
