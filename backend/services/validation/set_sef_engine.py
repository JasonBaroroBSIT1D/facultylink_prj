"""Rule-based validation for KRA I Criterion A SET/SEF."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlalchemy import select

from extensions import db
from models.document import Document
from models.document_extraction import DocumentExtraction
from models.evaluation_period import EvaluationPeriod
from models.kra_configuration import KraConfiguration, KraCriterion, KraIndicator
from models.user import User
from services.validation.rule_loader import load_set_sef_rules


@dataclass
class CheckOutcome:
    name: str
    passed: bool
    confidence: float
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class ValidationOutcome:
    result: str
    explanation: str
    checks: list[CheckOutcome]
    classified_indicator_code: str | None
    classified_indicator_id: int | None
    extracted_fields: dict


def _normalize_semester(raw: str) -> str:
    text = raw.lower().strip()
    if "first" in text or "1st" in text:
        return "first"
    if "second" in text or "2nd" in text:
        return "second"
    if "summer" in text:
        return "summer"
    if "midyear" in text or "mid-year" in text:
        return "midyear"
    return text


def _normalize_ocr_text(text: str) -> str:
    """Light cleanup for common OCR noise without inventing values."""
    if not text:
        return ""
    out = text.replace("\r", "\n")
    out = out.replace("–", "-").replace("—", "-")
    out = re.sub(r"[ \t]+", " ", out)

    out = re.sub(r"(?<=[12])O(?=\d)", "0", out, flags=re.IGNORECASE)
    out = re.sub(r"(?<=\d)O(?=\d)", "0", out, flags=re.IGNORECASE)
    return out


def _parse_fields(text: str, rule: dict) -> tuple[dict, dict]:
    """Return (fields, per-field confidence 0..1)."""
    fields: dict = {}
    field_confidence: dict[str, float] = {}
    patterns = rule.get("patterns") or {}
    normalized = _normalize_ocr_text(text)
    for field_name, pattern_list in patterns.items():
        matched = False
        for pattern in pattern_list:
            for source, conf_base in ((text, 0.88), (normalized, 0.72)):
                match = re.search(pattern, source, re.MULTILINE | re.IGNORECASE)
                if match:
                    raw = match.group(1).strip()
                    if field_name == "semester":
                        raw = re.sub(r"\s+", " ", raw)
                    fields[field_name] = raw
                    field_confidence[field_name] = conf_base
                    matched = True
                    break
            if matched:
                break
    if "overall_rating" in fields:
        rating_raw = str(fields["overall_rating"]).replace("O", "0").replace("o", "0")
        rating_raw = re.sub(r"[^0-9.]", "", rating_raw)
        if not rating_raw:
            fields.pop("overall_rating", None)
            field_confidence.pop("overall_rating", None)
        else:
            try:
                fields["overall_rating"] = float(rating_raw)
            except ValueError:
                fields.pop("overall_rating", None)
                field_confidence["overall_rating"] = 0.25
    return fields, field_confidence


def classify_indicator(text: str, rules: dict) -> tuple[str | None, float, dict]:
    lowered = text.lower()
    scores: dict[str, int] = {}
    for code, cfg in (rules.get("indicators") or {}).items():
        score = 0
        for kw in cfg.get("classification_keywords") or []:
            if kw.lower() in lowered:
                score += 1
        scores[code] = score
    if not scores:
        return None, 0.0, scores
    best_code = max(scores, key=scores.get)
    best_score = scores[best_code]
    min_score = (rules.get("indicators") or {}).get(best_code, {}).get("classification_min_score", 2)
    if best_score < min_score:
        return None, 0.4, scores
    confidence = min(0.95, 0.5 + 0.15 * best_score)
    return best_code, confidence, scores


def _name_match_score(account_name: str, extracted: str | None) -> tuple[bool, float]:
    if not extracted:
        return False, 0.0
    account_tokens = {t.lower() for t in re.findall(r"[a-zA-Z]+", account_name) if len(t) > 1}
    extracted_tokens = {t.lower() for t in re.findall(r"[a-zA-Z]+", extracted) if len(t) > 1}
    if not account_tokens:
        return False, 0.0
    overlap = account_tokens & extracted_tokens
    ratio = len(overlap) / len(account_tokens)
    return ratio >= 0.5, ratio


def _duplicate_semester_exists(
    faculty_id: int,
    indicator_id: int,
    academic_year: str,
    semester_norm: str,
    exclude_document_id: int,
) -> bool:
    rows = db.session.scalars(
        select(Document).where(
            Document.faculty_id == faculty_id,
            Document.indicator_id == indicator_id,
            Document.document_id != exclude_document_id,
            Document.status.in_(("system_approved", "needs_verification", "processing")),
        )
    ).all()
    for doc in rows:
        extraction = (
            db.session.query(DocumentExtraction)
            .filter_by(document_id=doc.document_id)
            .order_by(DocumentExtraction.extracted_at.desc())
            .first()
        )
        if not extraction:
            continue
        fields = extraction.extracted_fields or {}
        if (
            fields.get("academic_year") == academic_year
            and _normalize_semester(str(fields.get("semester", ""))) == semester_norm
        ):
            return True
    return False


def validate_set_sef_document(
    *,
    document: Document,
    period: EvaluationPeriod,
    faculty_user: User,
    ocr_text: str,
    ocr_confidence: float,
    ocr_method: str | None = None,
) -> ValidationOutcome:
    rules = load_set_sef_rules()
    thresholds = rules.get("confidence_thresholds") or {}
    checks: list[CheckOutcome] = []

    criterion = db.session.scalar(
        select(KraCriterion)
        .join(KraConfiguration, KraConfiguration.kra_id == KraCriterion.kra_id)
        .where(KraCriterion.criterion_id == document.criterion_id, KraConfiguration.kra_code == rules["kra_code"])
    )
    if not criterion or criterion.criterion_code != rules["criterion_code"]:
        checks.append(
            CheckOutcome(
                "criterion_eligibility",
                False,
                1.0,
                "Document must be uploaded under KRA I Criterion A for SET/SEF processing.",
            )
        )
        return ValidationOutcome(
            "failed",
            "Wrong criterion for SET/SEF pipeline.",
            checks,
            None,
            None,
            {},
        )

    checks.append(
        CheckOutcome(
            "authenticity_notice",
            True,
            1.0,
            "OCR and keyword classification do not prove document authenticity or eligibility.",
            {"policy": rules.get("authenticity_policy")},
        )
    )

    for flag in rules.get("section_10_unverified_flags") or []:
        checks.append(
            CheckOutcome(
                "section_10_flag",
                True,
                0.0,
                f"Unverified for automated processing: {flag}",
                {"verified": False},
            )
        )

    ocr_norm = _normalize_ocr_text(ocr_text)
    classify_text = ocr_norm or ocr_text

    if ocr_method:
        checks.append(
            CheckOutcome(
                "ocr_extraction_method",
                True,
                min(1.0, ocr_confidence / 100.0),
                f"Extraction method: {ocr_method}",
                {"method": ocr_method},
            )
        )

    ocr_conf_ratio = min(1.0, max(0.0, ocr_confidence / 100.0))
    field_min_ocr = float(thresholds.get("ocr_mean_min", 0.35))
    if ocr_conf_ratio < field_min_ocr:
        checks.append(
            CheckOutcome(
                "ocr_confidence_threshold",
                False,
                ocr_conf_ratio,
                "Overall OCR confidence is too low to treat extracted values as reliable.",
            )
        )

    if len(classify_text.strip()) < 10:
        checks.append(
            CheckOutcome(
                "ocr_sufficient_text",
                False,
                ocr_conf_ratio,
                "Insufficient extractable text (possible scanned document without OCR).",
            )
        )

    code, class_conf, score_map = classify_indicator(classify_text, rules)
    if document.indicator_id:
        ind = db.session.get(KraIndicator, document.indicator_id)
        if ind:
            code = ind.indicator_code
            class_conf = max(class_conf, 0.85)
    checks.append(
        CheckOutcome(
            "indicator_classification",
            code is not None,
            class_conf,
            f"Classified indicator: {code or 'uncertain'}",
            {"scores": score_map, "indicator_code": code},
        )
    )

    indicator_id = None
    rule_cfg = None
    if code:
        indicator = db.session.scalar(
            select(KraIndicator)
            .join(KraCriterion, KraCriterion.criterion_id == KraIndicator.criterion_id)
            .where(KraIndicator.indicator_code == code, KraCriterion.criterion_id == document.criterion_id)
        )
        if indicator:
            indicator_id = indicator.indicator_id
            rule_cfg = rules["indicators"][code]
            req_evidence = (indicator.required_evidence or "").strip()
            if req_evidence:
                missing_lines: list[str] = []
                for line in req_evidence.splitlines():
                    snippet = line.strip().lstrip("-•*").strip()
                    if not snippet or len(snippet) < 4:
                        continue
                    if snippet.lower() not in classify_text.lower():
                        missing_lines.append(snippet)
                checks.append(
                    CheckOutcome(
                        "admin_evidence_requirements",
                        len(missing_lines) == 0,
                        0.85 if not missing_lines else 0.4,
                        "Admin-configured evidence requirements compared to OCR text.",
                        {"missing_snippets": missing_lines[:8]},
                    )
                )
        else:
            checks.append(
                CheckOutcome(
                    "indicator_registered",
                    False,
                    1.0,
                    f"Indicator code {code} is not configured in the database.",
                )
            )

    extracted: dict = {}
    field_confidence: dict[str, float] = {}
    field_min = float(thresholds.get("field_min", 0.6))
    if rule_cfg:
        extracted, field_confidence = _parse_fields(classify_text, rule_cfg)
        if "overall_rating" in extracted:
            extracted[rule_cfg["rating_field_key"]] = extracted["overall_rating"]
        for req in rule_cfg.get("required_fields") or []:
            present = req in extracted and extracted[req] not in (None, "")
            fconf = field_confidence.get(req, 0.0 if not present else 0.5)
            combined = fconf * ocr_conf_ratio if present else 0.0
            uncertain_field = present and combined < field_min
            checks.append(
                CheckOutcome(
                    f"required_{req}",
                    present and not uncertain_field,
                    combined if present else 0.0,
                    f"Field '{req}' {'found' if present else 'missing'}"
                    + (" (low confidence)" if uncertain_field else "")
                    + ".",
                    {"field_confidence": fconf, "combined_confidence": combined},
                )
            )

        rating = extracted.get("overall_rating")
        if rating is not None:
            rmin = rule_cfg.get("rating_min", 0)
            rmax = rule_cfg.get("rating_max", 100)
            ok = rmin <= float(rating) <= rmax
            rconf = field_confidence.get("overall_rating", 0.5) * ocr_conf_ratio
            rating_trusted = ok and rconf >= field_min
            checks.append(
                CheckOutcome(
                    "rating_range",
                    rating_trusted,
                    rconf if ok else 0.2,
                    f"Rating {rating} must be between {rmin} and {rmax}."
                    + ("" if rating_trusted else " (missing, out of range, or uncertain OCR)."),
                )
            )

    identity_ok, identity_score = _name_match_score(faculty_user.full_name, extracted.get("faculty_name"))
    id_min = float(thresholds.get("identity_min", 0.65))
    checks.append(
        CheckOutcome(
            "faculty_identity",
            identity_ok,
            identity_score,
            "Extracted name alignment with authenticated faculty account.",
            {"account_name": faculty_user.full_name, "extracted_name": extracted.get("faculty_name")},
        )
    )
    if identity_score < id_min:
        checks.append(
            CheckOutcome(
                "faculty_identity_confidence",
                False,
                identity_score,
                f"Identity match below threshold ({id_min}).",
            )
        )

    if period and extracted.get("semester"):
        sem_norm = _normalize_semester(str(extracted["semester"]))
        period_norm = _normalize_semester(period.semester)
        sem_ok = sem_norm == period_norm or sem_norm in period.semester.lower()
        checks.append(
            CheckOutcome(
                "semester_alignment",
                sem_ok,
                0.8 if sem_ok else 0.3,
                "Extracted semester compared to evaluation period semester.",
                {"extracted": extracted.get("semester"), "period_semester": period.semester},
            )
        )

    if period and extracted.get("academic_year"):
        ay_ok = extracted["academic_year"].replace(" ", "") == period.academic_year.replace(" ", "")
        checks.append(
            CheckOutcome(
                "academic_year_alignment",
                ay_ok,
                0.85 if ay_ok else 0.35,
                "Extracted academic year compared to evaluation period.",
                {"extracted": extracted["academic_year"], "period_academic_year": period.academic_year},
            )
        )

    if indicator_id and extracted.get("academic_year") and extracted.get("semester"):
        dup = _duplicate_semester_exists(
            document.faculty_id,
            indicator_id,
            str(extracted["academic_year"]),
            _normalize_semester(str(extracted["semester"])),
            document.document_id,
        )
        checks.append(
            CheckOutcome(
                "duplicate_semester_evidence",
                not dup,
                0.9 if not dup else 0.5,
                "Another active document may already cover this indicator and semester.",
                {"duplicate_suspected": dup},
            )
        )

    class_min = float(thresholds.get("classification_min", 0.55))
    mandatory_fail = any(
        not c.passed
        for c in checks
        if c.name
        in (
            "criterion_eligibility",
            "indicator_registered",
            "ocr_sufficient_text",
            "ocr_confidence_threshold",
            "rating_range",
            "faculty_identity",
            "faculty_identity_confidence",
        )
    )
    uncertain = (
        mandatory_fail
        or code is None
        or class_conf < class_min
        or any(c.name.startswith("required_") and not c.passed for c in checks)
        or any(c.name == "admin_evidence_requirements" and not c.passed for c in checks)
        or any(c.name == "duplicate_semester_evidence" and not c.passed for c in checks)
        or (
            period
            and any(
                c.name in ("semester_alignment", "academic_year_alignment") and not c.passed for c in checks
            )
        )
    )

    if any(c.name == "criterion_eligibility" and not c.passed for c in checks):
        result = "failed"
        explanation = "Document is not eligible for SET/SEF processing."
    elif uncertain:
        result = "needs_verification"
        explanation = "Document requires reviewer verification; automatic approval disabled."
    else:
        result = "passed"
        explanation = "Extracted fields meet configured rules; eligible for automatic scoring and system approval."

    if field_confidence:
        extracted = {**extracted, "_field_confidence": field_confidence}

    return ValidationOutcome(
        result,
        explanation,
        checks,
        code,
        indicator_id,
        extracted,
    )
