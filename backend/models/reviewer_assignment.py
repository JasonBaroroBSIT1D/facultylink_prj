from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Identity, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from extensions import db


class ReviewerAssignment(db.Model):
    __tablename__ = "reviewer_assignments"

    assignment_id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    reviewer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    faculty_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("faculty_profiles.faculty_id"), nullable=False)
    assigned_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    faculty_profile = relationship("FacultyProfile", foreign_keys=[faculty_id])
