"""merge client id and usernames migrations

Revision ID: 78d2ce32b911
Revises: 275ff74c0866, 5c15463fda65
Create Date: 2025-04-30 19:07:42.449694

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "78d2ce32b911"
down_revision: tuple[str, str] = ("275ff74c0866", "5c15463fda65")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
