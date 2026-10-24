from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from extensions import db

CREDIT_STATES = frozenset({"none", "credited", "revoked"})


class DocumentScoreContribution(db.Model):
    """Ledger row: system, provisional, reviewer-assigned, and credited points (Phase 2+)."""

    __tablename__ = "document_score_contributions"

    contribution_id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    document_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("documents.document_id"), nullable=False)
    faculty_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("faculty_profiles.faculty_id"), nullable=False)
    kra_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("kra_configurations.kra_id"))
    indicator_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("kra_indicators.indicator_id"))
    period_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("evaluation_periods.period_id"))
    academic_year: Mapped[str] = mapped_column(String(40), nullable=False)
    semester: Mapped[str] = mapped_column(String(60), nullable=False)
    evidence_sha256: Mapped[str | None] = mapped_column(String(64))
    credit_uniqueness_mode: Mapped[str] = mapped_column(String(40), nullable=False, default="per_evidence_hash")
    credit_uniqueness_key: Mapped[str | None] = mapped_column(String(220))
    guideline_version: Mapped[str | None] = mapped_column(String(100))
    rule_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    system_calculated_points: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    provisional_points: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    reviewer_assigned_points: Mapped[float | None] = mapped_column(Numeric(12, 4))
    credited_points: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    credit_state: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    system_decision: Mapped[str | None] = mapped_column(String(40))
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    supersedes_contribution_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("document_score_contributions.contribution_id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    credited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoke_reason: Mapped[str | None] = mapped_column(Text)
    reviewer_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    reviewer_reason: Mapped[str | None] = mapped_column(Text)
