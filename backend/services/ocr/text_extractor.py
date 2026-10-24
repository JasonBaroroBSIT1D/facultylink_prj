"""Text extraction from uploaded evidence (PDF / image). Phase 2.1: mixed PDF + Tesseract."""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

from services.ocr.tesseract_config import configure_pytesseract, resolve_tesseract_executable

ENGINE_VERSION = "facultylink-ocr-2.1"

# Pages with fewer printable characters are treated as scanned / image-only.
MIN_PAGE_TEXT_CHARS = 25
PDF_RENDER_DPI = 220
MIN_OCR_CONFIDENCE_ACCEPT = 35.0


@dataclass
class OcrExtractionResult:
    text: str
    confidence: float
    method: str
    status: str  # completed | failed
    page_methods: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)


def extract_text_from_bytes(data: bytes, mime_type: str) -> OcrExtractionResult:
    mime = (mime_type or "").lower()
    if mime == "application/pdf":
        return _extract_pdf(data)
    if mime in ("image/png", "image/jpeg", "image/jpg"):
        return _extract_image(data)
    return OcrExtractionResult("", 0.0, "unsupported", "failed")


def _printable_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def _ocr_image_pil(image) -> tuple[str, float, str]:
    """Run Tesseract with optional rotation correction; return text, confidence, sub_method."""
    try:
        import pytesseract
        from PIL import ImageOps
    except ImportError:
        return "", 0.0, "tesseract_unavailable"

    if not configure_pytesseract():
        return "", 0.0, "tesseract_not_installed"

    best_text = ""
    best_conf = 0.0
    best_rot = 0

    rotations = (0, 90, 180, 270)
    try:
        osd = pytesseract.image_to_osd(image)
        match = re.search(r"Rotate:\s*(\d+)", osd)
        if match:
            rotate = int(match.group(1))
            if rotate in rotations:
                rotations = (rotate,) + tuple(r for r in rotations if r != rotate)
    except Exception:
        pass

    for angle in rotations:
        rotated = image if angle == 0 else image.rotate(-angle, expand=True)
        try:
            data = pytesseract.image_to_data(rotated, output_type=pytesseract.Output.DICT)
            confs = [int(c) for c in data.get("conf", []) if str(c).lstrip("-").isdigit() and int(c) >= 0]
            mean_conf = sum(confs) / len(confs) if confs else 0.0
            text = pytesseract.image_to_string(rotated) or ""
            text = text.strip()
            if mean_conf > best_conf or (mean_conf == best_conf and len(text) > len(best_text)):
                best_conf = mean_conf
                best_text = text
                best_rot = angle
        except Exception:
            continue

    if best_rot:
        sub = f"tesseract_rot{best_rot}"
    else:
        sub = "tesseract"
    return best_text, best_conf, sub


def _extract_image(data: bytes) -> OcrExtractionResult:
    try:
        from PIL import Image, ImageEnhance, ImageFilter
    except ImportError:
        return OcrExtractionResult("", 0.0, "pillow_missing", "failed")

    try:
        image = Image.open(io.BytesIO(data))
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        # Mild sharpen / contrast for blurry scans
        image = ImageEnhance.Contrast(image).enhance(1.15)
        image = image.filter(ImageFilter.SHARPEN)
        text, conf, sub = _ocr_image_pil(image)
        status = "completed" if text else "completed"
        if conf < MIN_OCR_CONFIDENCE_ACCEPT and len(text) < 15:
            conf = min(conf, 25.0)
        return OcrExtractionResult(
            text,
            conf,
            sub,
            status,
            page_methods=[sub],
            details={"tesseract_path": resolve_tesseract_executable()},
        )
    except Exception:
        return OcrExtractionResult("", 0.0, "tesseract_error", "failed")


def _extract_pdf(data: bytes) -> OcrExtractionResult:
    try:
        from pypdf import PdfReader
    except ImportError:
        return OcrExtractionResult("", 0.0, "pypdf_missing", "failed")

    tess_ok = configure_pytesseract()
    page_methods: list[str] = []
    parts: list[str] = []
    page_confidences: list[float] = []

    try:
        reader = PdfReader(io.BytesIO(data))
        num_pages = len(reader.pages)
    except Exception:
        return OcrExtractionResult("", 0.0, "pypdf_error", "failed")

    fitz_doc = None
    if tess_ok and num_pages > 0:
        try:
            import pymupdf
        except ImportError:
            tess_ok = False
        else:
            try:
                fitz_doc = pymupdf.open(stream=data, filetype="pdf")
            except Exception:
                fitz_doc = None
                tess_ok = False

    for idx in range(num_pages):
        page_num = idx + 1
        try:
            page_text = (reader.pages[idx].extract_text() or "").strip()
        except Exception:
            page_text = ""

        if _printable_len(page_text) >= MIN_PAGE_TEXT_CHARS:
            parts.append(page_text)
            page_methods.append(f"pypdf_text:p{page_num}")
            page_confidences.append(92.0)
            continue

        if fitz_doc is not None and idx < len(fitz_doc):
            try:
                from PIL import Image
            except ImportError:
                fitz_doc = None
            else:
                try:
                    pix = fitz_doc[idx].get_pixmap(dpi=PDF_RENDER_DPI, alpha=False)
                    mode = "RGB" if pix.n >= 3 else "L"
                    image = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
                    ocr_text, ocr_conf, sub = _ocr_image_pil(image)
                    if ocr_text:
                        parts.append(ocr_text)
                        page_methods.append(f"{sub}:p{page_num}")
                        page_confidences.append(ocr_conf)
                        continue
                    page_methods.append(f"tesseract_empty:p{page_num}")
                    page_confidences.append(ocr_conf)
                except Exception:
                    page_methods.append(f"tesseract_error:p{page_num}")
                    page_confidences.append(0.0)

        if page_text:
            parts.append(page_text)
            page_methods.append(f"pypdf_sparse:p{page_num}")
            page_confidences.append(55.0)
        else:
            page_methods.append(f"empty:p{page_num}")
            page_confidences.append(10.0)

    if fitz_doc is not None:
        fitz_doc.close()

    text = "\n".join(parts).strip()
    if not page_confidences:
        page_confidences = [15.0]

    if page_methods:
        used_pypdf = sum(1 for m in page_methods if m.startswith("pypdf_text"))
        used_ocr = sum(1 for m in page_methods if "tesseract" in m)
        if used_pypdf and used_ocr:
            method = "pdf_mixed_pypdf_tesseract"
        elif used_ocr:
            method = "pdf_tesseract"
        elif used_pypdf:
            method = "pypdf_text"
        elif any(m.startswith("pypdf_sparse") for m in page_methods):
            method = "pypdf_sparse"
        else:
            method = "pypdf_scanned_or_empty"
    else:
        method = "pypdf_scanned_or_empty"

    if page_confidences:
        confidence = sum(page_confidences) / len(page_confidences)
    else:
        confidence = 15.0 if not text else 55.0

    if not tess_ok and _printable_len(text) < MIN_PAGE_TEXT_CHARS:
        method = "pypdf_scanned_tesseract_unavailable"

    return OcrExtractionResult(
        text,
        confidence,
        method,
        "completed",
        page_methods=page_methods,
        details={
            "page_count": num_pages,
            "tesseract_path": resolve_tesseract_executable(),
            "tesseract_available": bool(resolve_tesseract_executable()),
        },
    )
