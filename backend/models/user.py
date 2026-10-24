from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    must_set_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    credentials_delivery_pending: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    faculty_profile = relationship("FacultyProfile", back_populates="user", uselist=False)
    password_tokens = relationship("PasswordToken", back_populates="user")
    password_reset_otps = relationship("PasswordResetOtp", back_populates="user")

    def to_public_dict(self, include_profile: bool = False) -> dict:
        data = {
            "user_id": self.user_id,
            "email": self.email,
            "role": self.role,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "must_set_password": self.must_set_password,
            "must_change_password": self.must_set_password,
            "credentials_delivery_pending": self.credentials_delivery_pending,
        }
        if include_profile and self.faculty_profile:
            data["faculty_profile"] = self.faculty_profile.to_dict()
        return data
