"""SQLAlchemy mapping for app_meta. Coaching tables stay in app.models for now."""

from sqlalchemy import Identity, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AppMeta(Base):
    """Persistence mapping for the starting non-coaching table."""

    __tablename__ = "app_meta"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
