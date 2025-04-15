"""merge multiple heads

Revision ID: ba1bf29910f5
Revises: 4fdc4f47f0fd, 97137b6afb58
Create Date: 2025-04-15 21:55:36.305124

"""

from typing import Sequence, Tuple, Union

# revision identifiers, used by Alembic.
revision: str = "ba1bf29910f5"
down_revision: Union[Tuple[str, ...], None] = ("4fdc4f47f0fd", "97137b6afb58")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
