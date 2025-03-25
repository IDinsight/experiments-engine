"""merge divergent heads

Revision ID: d95b5c0590c3
Revises: 4876b8412959, bcb06fb6e15d
Create Date: 2025-03-09 22:04:07.679614

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "d95b5c0590c3"
down_revision: tuple[str, str] = ("4876b8412959", "bcb06fb6e15d")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
