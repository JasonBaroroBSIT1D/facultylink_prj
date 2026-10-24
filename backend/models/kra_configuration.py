from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from extensions import db


class KraConfiguration(db.Model):
    __tablename__ = "kra_configurations"

    kra_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    kra_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    kra_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    guideline_version: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    criteria: Mapped[list[KraCriterion]] = relationship(
        "KraCriterion",
        back_populates="kra",
        order_by="KraCriterion.display_order",
    )


class KraCriterion(db.Model):
    __tablename__ = "kra_criteria"

    criterion_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    kra_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("kra_configurations.kra_id"), nullable=False)
    criterion_code: Mapped[str] = mapped_column(String(30), nullable=False)
    criterion_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    kra: Mapped[KraConfiguration] = relationship("KraConfiguration", back_populates="criteria")
    indicators: Mapped[list[KraIndicator]] = relationship(
        "KraIndicator",
        back_populates="criterion",
        order_by="KraIndicator.display_order",
    )


class KraIndicator(db.Model):
    __tablename__ = "kra_indicators"

    indicator_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    criterion_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("kra_criteria.criterion_id"), nullable=False)
    indicator_code: Mapped[str] = mapped_column(String(30), nullable=False)
    indicator_name: Mapped[str] = mapped_column(String(200), nullable=False)
    required_evidence: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    criterion: Mapped[KraCriterion] = relationship("KraCriterion", back_populates="indicators")
    scoring_rules: Mapped[list[ScoringRule]] = relationship(
        "ScoringRule",
        back_populates="indicator",
    )


class ScoringRule(db.Model):
    __tablename__ = "scoring_rules"

    rule_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    indicator_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("kra_indicators.indicator_id"), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(160), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(60), nullable=False)
    rule_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    guideline_version: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[object | None] = mapped_column(Date)
    effective_to: Mapped[object | None] = mapped_column(Date)

    indicator: Mapped[KraIndicator] = relationship("KraIndicator", back_populates="scoring_rules")
