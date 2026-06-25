from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(128), default="")
    first_name: Mapped[str] = mapped_column(String(128), default="")
    last_name: Mapped[str] = mapped_column(String(128), default="")
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Jerusalem")

    workouts: Mapped[list[WorkoutSession]] = relationship(back_populates="user")


class Exercise(TimestampMixin, Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    workout_type: Mapped[str] = mapped_column(String(32), default="")
    block: Mapped[str] = mapped_column(String(128), default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
    planned_sets: Mapped[str] = mapped_column(String(64), default="")
    planned_reps: Mapped[str] = mapped_column(String(128), default="")
    rest_seconds: Mapped[int] = mapped_column(Integer, default=0)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class WorkoutSession(TimestampMixin, Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    workout_date: Mapped[date] = mapped_column(Date, index=True)
    workout_type: Mapped[str] = mapped_column(String(32), default="")
    start_time: Mapped[str] = mapped_column(String(16), default="")
    end_time: Mapped[str] = mapped_column(String(16), default="")
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    body_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy_level: Mapped[str] = mapped_column(String(32), default="")
    status: Mapped[str] = mapped_column(String(64), default="started")
    general_notes: Mapped[str] = mapped_column(Text, default="")

    user: Mapped[User] = relationship(back_populates="workouts")
    sets: Mapped[list[ExerciseSet]] = relationship(back_populates="workout", cascade="all, delete-orphan")


class ExerciseSet(TimestampMixin, Base):
    __tablename__ = "sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id", ondelete="CASCADE"), index=True)
    exercise_name: Mapped[str] = mapped_column(String(255), index=True)
    set_index: Mapped[int] = mapped_column(Integer, default=1)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rir: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pain_level: Mapped[int] = mapped_column(Integer, default=0)
    technique_ok: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_result: Mapped[str] = mapped_column(String(255), default="")
    progression_status: Mapped[str] = mapped_column(String(64), default="")
    recommendation: Mapped[str] = mapped_column(Text, default="")

    workout: Mapped[WorkoutSession] = relationship(back_populates="sets")


class Readiness(TimestampMixin, Base):
    __tablename__ = "readiness"
    __table_args__ = (UniqueConstraint("user_id", "readiness_date", name="uq_readiness_user_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    readiness_date: Mapped[date] = mapped_column(Date, index=True)
    body_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy_level: Mapped[str] = mapped_column(String(32), default="")


class PainEvent(TimestampMixin, Base):
    __tablename__ = "pain_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    workout_id: Mapped[int | None] = mapped_column(ForeignKey("workouts.id", ondelete="SET NULL"), nullable=True)
    exercise_name: Mapped[str] = mapped_column(String(255), default="")
    pain_level: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")


class Goal(TimestampMixin, Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(80), default="")
    target: Mapped[str] = mapped_column(String(255), default="")
    current_result: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(32), default="active")
    notes: Mapped[str] = mapped_column(Text, default="")


class CoachNote(TimestampMixin, Base):
    __tablename__ = "coach_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(32), default="manual")
    title: Mapped[str] = mapped_column(String(255), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)


class Recommendation(TimestampMixin, Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    workout_id: Mapped[int | None] = mapped_column(ForeignKey("workouts.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="new")
    priority: Mapped[str] = mapped_column(String(32), default="normal")
    title: Mapped[str] = mapped_column(String(255), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(32), default="rules")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
