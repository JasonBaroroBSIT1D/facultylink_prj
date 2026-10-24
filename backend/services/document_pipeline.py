"""Post-upload OCR + SET/SEF validation (Phase 2)."""
from __future__ import annotations

import json

from sqlalchemy import text

from extensions import db
from models.document import Document
from models.document_extraction import DocumentExtraction
from models.evaluation_period import EvaluationPeriod
from models.user import User
from models.validation_result import ValidationResult
from services.document_storage import absolute_path_for_key
from services.ocr.text_extractor import ENGINE_VERSION, extract_text_from_bytes
from services.validation.rule_loader import load_set_sef_rules
from services.criterion_a_set_sef_ledger import finalize_criterion_a_set_sef
from services.validation.set_sef_engine import validate_set_sef_document


def _append_audit(document_id: int, user_id: int, action: str, details: dict) -> None:
    db.session.execute(
        text(
            """
            INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details)
            VALUES (:user_id, :action, 'document', :entity_id, CAST(:details AS jsonb))
            """
        ),
        {
            "user_id": user_id,
            "action": action,
            "entity_id": str(document_id),
            "details": json.dumps(details),
        },
    )


def process_criterion_a_set_sef(document_id: int, faculty_user: User) -> None:
    """Run OCR, validation, scoring, and system approval for KRA I Criterion A SET/SEF."""
    rules = load_set_sef_rules()
    document = db.session.get(Document, document_id)
    if not document:
        return

    period = db.session.get(EvaluationPeriod, document.period_id) if document.period_id else None
    document.status = "processing"
    db.session.flush()

    path = absolute_path_for_key(document.storage_key)
    data = path.read_bytes()
    ocr = extract_text_from_bytes(data, document.mime_type or "")

    extraction = DocumentExtraction(
        document_id=document.document_id,
        extracted_text=ocr.text,
        extracted_fields={},
        ocr_confidence=ocr.confidence,
        extraction_status=ocr.status,
        engine_version=ENGINE_VERSION,
    )
    db.session.add(extraction)
    db.session.flush()

    outcome = validate_set_sef_document(
        document=document,
        period=period,
        faculty_user=faculty_user,
        ocr_text=ocr.text,
        ocr_confidence=ocr.confidence,
        ocr_method=ocr.method,
    )

    extraction.extracted_fields = {
        **outcome.extracted_fields,
        "classified_indicator_code": outcome.classified_indicator_code,
        "extraction_method": ocr.method,
        "ocr_page_methods": ocr.page_methods or None,
        "ocr_details": ocr.details or None,
        "classification_scores": next(
            (c.details.get("scores") for c in outcome.checks if c.name == "indicator_classification"),
            None,
        ),
    }

    if outcome.classified_indicator_id:
        document.indicator_id = outcome.classified_indicator_id

    checks_payload = {
        "items": [
            {
                "name": c.name,
                "passed": c.passed,
                "confidence": c.confidence,
                "message": c.message,
                "details": c.details,
            }
            for c in outcome.checks
        ],
        "classified_indicator_code": outcome.classified_indicator_code,
        "section_10_unverified": rules.get("section_10_unverified_flags"),
    }

    validation = ValidationResult(
        document_id=document.document_id,
        extraction_id=extraction.extraction_id,
        result=outcome.result,
        checks=checks_payload,
        explanation=outcome.explanation,
        rule_version=rules.get("rule_version"),
    )
    db.session.add(validation)

    if outcome.result == "failed":
        document.status = "needs_verification"
        _append_audit(
            document.document_id,
            faculty_user.user_id,
            "document.validation_completed",
            {
                "validation_result": outcome.result,
                "document_status": document.status,
                "indicator_code": outcome.classified_indicator_code,
                "rule_version": rules.get("rule_version"),
            },
        )
        return

    scoring_summary = finalize_criterion_a_set_sef(
        document=document,
        faculty_user=faculty_user,
        outcome=outcome,
        rules_json=rules,
    )

    _append_audit(
        document.document_id,
        faculty_user.user_id,
        "document.validation_completed",
        {
            "validation_result": outcome.result,
            "document_status": document.status,
            "indicator_code": outcome.classified_indicator_code,
            "rule_version": rules.get("rule_version"),
            "scoring": scoring_summary,
        },
    )
