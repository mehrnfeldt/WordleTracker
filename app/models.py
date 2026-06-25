from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


class Player(db.Model):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(120), nullable=False)
    phone_number: Mapped[str] = mapped_column(db.String(32), unique=True, nullable=False, index=True)

    results: Mapped[list["WordleResult"]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class WordleResult(db.Model):
    __tablename__ = "wordle_results"
    __table_args__ = (
        UniqueConstraint("player_id", "wordle_number", name="uq_player_wordle_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(db.ForeignKey("players.id"), nullable=False, index=True)
    wordle_number: Mapped[int] = mapped_column(nullable=False, index=True)
    raw_score: Mapped[str] = mapped_column(db.String(3), nullable=False)
    guesses: Mapped[int | None] = mapped_column(nullable=True)
    points: Mapped[int] = mapped_column(nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    player: Mapped[Player] = relationship(back_populates="results")
