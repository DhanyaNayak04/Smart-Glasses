"""Clean OCR implementation used by ocr.py shim.

Keep this module self-contained so it can be edited safely.
"""
from typing import List, Optional
import os
import re
import cv2
import numpy as np
from PIL import Image

try:
    import pytesseract
except Exception:
    pytesseract = None


def _ensure_tesseract_on_windows() -> None:
    if pytesseract is None:
        return
    if os.name == 'nt':
        common = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(common):
            try:
                pytesseract.pytesseract.tesseract_cmd = common
            except Exception:
                pass


def _to_pil(img: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def _preprocess_crop(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    if max(h, w) < 800:
        img = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 5, 75, 75)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th


def _tesseract_extract_words(pil_img: Image.Image, psm: int = 6, conf_thresh: int = 50) -> List[str]:
    if pytesseract is None:
        return []
    cfg = f"--oem 3 --psm {psm}"
    try:
        data = pytesseract.image_to_data(pil_img, config=cfg, output_type=pytesseract.Output.DICT)
    except Exception:
        return []
    words: List[str] = []
    for t, c in zip(data.get('text', []), data.get('conf', [])):
        if not t or not t.strip():
            continue
        try:
            conf = int(float(c))
        except Exception:
            conf = -1
        if conf >= conf_thresh:
            words.append(t.strip())
    return words


_easyocr_reader = None


def _easyocr_read(img: np.ndarray) -> List[str]:
    global _easyocr_reader
    try:
        import easyocr
    except Exception:
        return []
    if _easyocr_reader is None:
        try:
            _easyocr_reader = easyocr.Reader(['en'], gpu=False)
        except Exception:
            return []
    try:
        out = _easyocr_reader.readtext(img, detail=0)
        return [o.strip() for o in out if o and o.strip()]
    except Exception:
        return []


def _strip_timestamps(text: str) -> str:
    """Remove common timestamp patterns from OCR text."""
    if not text:
        return text
    # remove patterns like 12:22, 12:22:12, 12:22:12 PM, 12:22:12HM etc.
    text = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm|HM|hm)?\b", "", text)
    # remove standalone dates/times like 2025-09-12
    text = re.sub(r"\b\d{4}-\d{1,2}-\d{1,2}\b", "", text)
    # compact whitespace
    return re.sub(r"\s+", " ", text).strip()


def _detect_droidcam_overlay(text: str) -> bool:
    """Detect if text likely comes from a DroidCam overlay/header.

    Heuristic: presence of 'droid' and 'cam' or variants plus a timestamp.
    """
    if not text:
        return False
    s = text.lower()
    # common misspellings/spacing
    if ("droid" in s or "droi" in s) and "cam" in s:
        return True
    # phrases like 'droidcam', 'droid cam', 'droid cam video', 'video feed'
    if re.search(r"droid\s*cam|droidcam|video\s*feed", s):
        return True
    # if a timestamp exists in the text it's likely an overlay
    if re.search(r"\d{1,2}:\d{2}(?::\d{2})?", s):
        # but ignore pure content that looks like time only if other words exist
        return True
    return False


def _postprocess_text_and_maybe_rerun(best: str, frame: np.ndarray) -> str:
    """Post-process OCR result and, if overlay detected, rerun OCR on cropped frame.

    Strategy:
    - Strip timestamps from the best result.
    - If result looks like a DroidCam overlay (header/timestamp), crop out the top
      ~15% of the frame and attempt OCR again on the cropped image. Use same
      tesseract/easyocr sequence (fast full-frame attempt).
    """
    cleaned = _strip_timestamps(best)
    if not _detect_droidcam_overlay(best):
        return cleaned

    # overlay detected: crop out top banner and retry on remainder
    h, w = frame.shape[:2]
    crop_y = int(h * 0.15)  # remove top 15% where overlays usually sit
    crop = frame[crop_y:h, 0:w]
    if crop is None or crop.size == 0:
        return cleaned

    # Try a quick full-frame OCR on the cropped image
    proc = _preprocess_crop(crop)
    pil = _to_pil(cv2.cvtColor(proc, cv2.COLOR_GRAY2BGR))
    words = _tesseract_extract_words(pil, psm=6, conf_thresh=50)
    if words:
        result = ' '.join(words)
        return _strip_timestamps(re.sub(r"\s+", " ", result).strip())

    # easyocr fallback
    easy = _easyocr_read(crop)
    if easy:
        return _strip_timestamps(' '.join(easy))

    return cleaned


def read_text_from_frame(frame: np.ndarray, boxes: Optional[List[dict]] = None, debug_dir: Optional[str] = None) -> str:
    """Extract readable text from a frame.

    Order: provided boxes -> center crop -> full frame -> EasyOCR fallback.
    When debug_dir is set, crops are saved for inspection.
    """
    _ensure_tesseract_on_windows()

    def _save(img_np: np.ndarray, name: str) -> None:
        if not debug_dir:
            return
        try:
            os.makedirs(debug_dir, exist_ok=True)
            cv2.imwrite(os.path.join(debug_dir, f"{name}.png"), img_np)
        except Exception:
            pass

    candidates: List[str] = []

    # 1) try provided boxes
    if boxes:
        for i, b in enumerate(boxes):
            try:
                xy = b.get('xyxy') if isinstance(b, dict) else b
                x1, y1, x2, y2 = map(int, xy)
                crop = frame[y1:y2, x1:x2]
            except Exception:
                continue
            if crop is None or crop.size == 0:
                continue
            _save(crop, f'box_{i}')
            proc = _preprocess_crop(crop)
            pil = _to_pil(cv2.cvtColor(proc, cv2.COLOR_GRAY2BGR))
            words = _tesseract_extract_words(pil, psm=7, conf_thresh=55)
            if words:
                candidates.append(' '.join(words))

    # 2) center crop
    h, w = frame.shape[:2]
    cw, ch = int(w * 0.5), int(h * 0.25)
    x1 = max(0, (w - cw) // 2)
    y1 = max(0, (h - ch) // 2)
    center = frame[y1:y1 + ch, x1:x1 + cw]
    if center is not None and center.size:
        _save(center, 'center')
        proc = _preprocess_crop(center)
        pil = _to_pil(cv2.cvtColor(proc, cv2.COLOR_GRAY2BGR))
        words = _tesseract_extract_words(pil, psm=8, conf_thresh=50)
        if words:
            candidates.append(' '.join(words))

    # 3) full frame
    _save(frame, 'full')
    proc = _preprocess_crop(frame)
    pil = _to_pil(cv2.cvtColor(proc, cv2.COLOR_GRAY2BGR))
    words = _tesseract_extract_words(pil, psm=6, conf_thresh=50)
    if words:
        candidates.append(' '.join(words))

    # 4) easyocr fallback
    if not candidates:
        easy = _easyocr_read(frame)
        if easy:
            candidates.append(' '.join(easy))

    if not candidates:
        return ''

    best = max(candidates, key=lambda s: len(s))
    best = re.sub(r'\s+', ' ', best).strip()
    return _postprocess_text_and_maybe_rerun(best, frame)
