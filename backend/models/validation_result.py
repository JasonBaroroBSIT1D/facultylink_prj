from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from extensions import db


class ValidationResult(db.Model):
    __tablename__ = "validation_results"

    validation_id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    document_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("documents.document_id"), nullable=False)
    extraction_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("document_extractions.extraction_id"))
    result: Mapped[str] = mapped_column(String(40), nullable=False)
    checks: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    explanation: Mapped[str | None] = mapped_column(Text)
    rule_version: Mapped[str | None] = mapped_column(String(100))
    validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
