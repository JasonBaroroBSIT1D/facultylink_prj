from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from extensions import db

DOCUMENT_STATUSES = frozenset(
    {
        "uploaded",
        "processing",
        "system_approved",
        "needs_verification",
        "needs_revision",
        "rejected",
        "upload_failed",
    }
)


class Document(db.Model):
    __tablename__ = "documents"

    document_id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    faculty_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("faculty_profiles.faculty_id"), nullable=False)
    criterion_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("kra_criteria.criterion_id"), nullable=False)
    indicator_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("kra_indicators.indicator_id"))
    period_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("evaluation_periods.period_id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    sha256_hash: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="uploaded")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def to_api_dict(self) -> dict:
        return {
            "id": str(self.document_id),
            "documentId": self.document_id,
            "facultyId": self.faculty_id,
            "criterionId": self.criterion_id,
            "indicatorId": self.indicator_id,
            "periodId": self.period_id,
            "title": self.title,
            "originalFilename": self.original_filename,
            "mimeType": self.mime_type,
            "fileSizeBytes": self.file_size_bytes,
            "sha256Hash": self.sha256_hash,
            "status": self.status,
            "uploadedAt": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
