from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Identity, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from extensions import db


class FacultyProfile(db.Model):
    __tablename__ = "faculty_profiles"

    faculty_id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), unique=True, nullable=False)
    employee_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    college: Mapped[str | None] = mapped_column(String(160))
    department: Mapped[str | None] = mapped_column(String(160))
    current_rank: Mapped[str | None] = mapped_column(String(120))
    employment_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="faculty_profile")

    def to_dict(self) -> dict:
        return {
            "faculty_id": self.faculty_id,
            "user_id": self.user_id,
            "employee_number": self.employee_number,
            "college": self.college,
            "department": self.department,
            "current_rank": self.current_rank,
            "employment_date": self.employment_date.isoformat() if self.employment_date else None,
        }
