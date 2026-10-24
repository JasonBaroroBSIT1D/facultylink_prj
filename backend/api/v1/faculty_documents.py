from __future__ import annotations

import hashlib

from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from auth.access_control import faculty_profile_for_user
from auth.decorators import roles_required
from extensions import db
from models.document import Document
from models.evaluation_period import EvaluationPeriod
from models.kra_configuration import KraCriterion, KraIndicator
from models.document_extraction import DocumentExtraction
from models.validation_result import ValidationResult
from services.document_pipeline import process_criterion_a_set_sef
from services.document_storage import build_storage_key, save_bytes
from services.submission_period import submission_block_message, submissions_allowed

bp = Blueprint("faculty_documents_v1", __name__)

_ALLOWED_MIME = frozenset(
    {
        "application/pdf",
        "image/png",
        "image/jpeg",
    }
)


def _parse_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@bp.get("/faculty/documents")
@roles_required("faculty")
def list_documents():
    profile = faculty_profile_for_user(g.current_user)
    if not profile:
        return jsonify({"error": "not_found", "message": "Faculty profile not found."}), 404
    rows = (
        db.session.scalars(
            select(Document)
            .where(Document.faculty_id == profile.faculty_id)
            .order_by(Document.uploaded_at.desc())
        )
        .all()
    )
    return jsonify({"documents": [d.to_api_dict() for d in rows]})


@bp.get("/faculty/documents/<int:document_id>")
@roles_required("faculty")
def get_document(document_id: int):
    profile = faculty_profile_for_user(g.current_user)
    if not profile:
        return jsonify({"error": "not_found", "message": "Faculty profile not found."}), 404
    doc = db.session.get(Document, document_id)
    if not doc or doc.faculty_id != profile.faculty_id:
        return jsonify({"error": "not_found", "message": "Document not found."}), 404
    payload = doc.to_api_dict()
    extraction = (
        db.session.query(DocumentExtraction)
        .filter_by(document_id=document_id)
        .order_by(DocumentExtraction.extracted_at.desc())
        .first()
    )
    validation = (
        db.session.query(ValidationResult)
        .filter_by(document_id=document_id)
        .order_by(ValidationResult.validated_at.desc())
        .first()
    )
    if extraction:
        fields = extraction.extracted_fields if isinstance(extraction.extracted_fields, dict) else {}
        payload["extraction"] = {
            "extractionId": extraction.extraction_id,
            "status": extraction.extraction_status,
            "ocrConfidence": float(extraction.ocr_confidence) if extraction.ocr_confidence is not None else None,
            "engineVersion": extraction.engine_version,
            "extractedText": extraction.extracted_text,
            "extractionMethod": fields.get("extraction_method"),
            "extractedFields": fields,
        }
    if validation:
        payload["validation"] = {
            "validationId": validation.validation_id,
            "result": validation.result,
            "explanation": validation.explanation,
            "ruleVersion": validation.rule_version,
            "checks": validation.checks,
        }
    return jsonify({"document": payload})


@bp.post("/faculty/documents")
@roles_required("faculty")
def upload_document():
    profile = faculty_profile_for_user(g.current_user)
    if not profile:
        return jsonify({"error": "not_found", "message": "Faculty profile not found."}), 404

    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return jsonify({"error": "validation", "message": "A file is required."}), 400

    title = (request.form.get("title") or "").strip()
    if not title:
        title = upload.filename.rsplit(".", 1)[0][:255]

    period_id = _parse_int(request.form.get("period_id") or request.form.get("periodId"))
    criterion_id = _parse_int(request.form.get("criterion_id") or request.form.get("criterionId"))
    indicator_id = _parse_int(request.form.get("indicator_id") or request.form.get("indicatorId"))

    if period_id is None:
        return jsonify({"error": "validation", "message": "period_id is required."}), 400
    if criterion_id is None:
        return jsonify({"error": "validation", "message": "criterion_id is required."}), 400

    period = db.session.get(EvaluationPeriod, period_id)
    if not period:
        return jsonify({"error": "not_found", "message": "Evaluation period not found."}), 404

    block = submission_block_message(period)
    if block:
        return jsonify({"error": "submission_closed", "message": block}), 403

    criterion = db.session.get(KraCriterion, criterion_id)
    if not criterion:
        return jsonify({"error": "not_found", "message": "KRA criterion not found."}), 404

    if indicator_id is not None:
        indicator = db.session.get(KraIndicator, indicator_id)
        if not indicator or indicator.criterion_id != criterion_id:
            return jsonify({"error": "validation", "message": "indicator_id is invalid for criterion."}), 400

    data = upload.read()
    max_bytes = int(current_app.config["DOCUMENT_UPLOAD_MAX_BYTES"])
    if len(data) > max_bytes:
        return jsonify({"error": "validation", "message": "File exceeds maximum upload size."}), 413

    mime = (upload.mimetype or "").split(";")[0].strip().lower()
    if mime not in _ALLOWED_MIME:
        return jsonify({"error": "validation", "message": "File type is not allowed."}), 400

    digest = hashlib.sha256(data).hexdigest()
    storage_key = build_storage_key(profile.faculty_id, period_id, upload.filename)

    doc = Document(
        faculty_id=profile.faculty_id,
        criterion_id=criterion_id,
        indicator_id=indicator_id,
        period_id=period_id,
        title=title[:255],
        original_filename=upload.filename[:255],
        storage_key=storage_key,
        mime_type=mime,
        file_size_bytes=len(data),
        sha256_hash=digest,
        status="uploaded",
    )
    db.session.add(doc)
    try:
        db.session.flush()
        save_bytes(storage_key, data)
        process_criterion_a_set_sef(doc.document_id, g.current_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return (
            jsonify(
                {
                    "error": "duplicate_evidence",
                    "message": "This file was already submitted and is still active for your account.",
                }
            ),
            409,
        )
    except OSError:
        db.session.rollback()
        return jsonify({"error": "storage", "message": "Unable to store uploaded file."}), 500

    return jsonify({"document": doc.to_api_dict()}), 201
