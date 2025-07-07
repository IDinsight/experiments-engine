from typing import TYPE_CHECKING

from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    pass


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""

    pass
