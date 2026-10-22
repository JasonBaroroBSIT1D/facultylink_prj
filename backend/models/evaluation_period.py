from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from extensions import db


class EvaluationPeriod(db.Model):
    __tablename__ = "evaluation_periods"

    period_id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    period_code: Mapped[str | None] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(40), nullable=False)
    semester: Mapped[str] = mapped_column(String(60), nullable=False)
    opens_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Manila")
    description: Mapped[str | None] = mapped_column(Text)
    submission_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    review_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
