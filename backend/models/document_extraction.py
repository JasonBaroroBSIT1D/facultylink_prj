from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from extensions import db


class DocumentExtraction(db.Model):
    __tablename__ = "document_extractions"

    extraction_id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    document_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("documents.document_id"), nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    extracted_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    ocr_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2))
    extraction_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    engine_version: Mapped[str | None] = mapped_column(String(80))
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
