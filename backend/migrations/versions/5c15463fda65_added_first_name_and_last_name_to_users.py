"""added first name and last name to users

Revision ID: 5c15463fda65
Revises: 28adf347e68d
Create Date: 2025-04-26 15:47:23.199751

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c15463fda65"
down_revision: Union[str, None] = "28adf347e68d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns as nullable first
    op.add_column("users", sa.Column("first_name", sa.String(), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(), nullable=True))

    # Set default values for existing records
    op.execute("UPDATE users SET first_name = '', last_name = ''")

    # Make columns non-nullable
    op.alter_column("users", "first_name", nullable=False)
    op.alter_column("users", "last_name", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
