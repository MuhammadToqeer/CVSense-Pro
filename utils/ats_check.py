# utils/ats_check.py
import os
import re
from typing import Dict, Any, List
import pdfplumber

EMAIL_RE = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", re.I)
PHONE_RE = re.compile(r"\+?\d[\d\-\s()]{6,}\d")
SECTION_HEADS = [
    "summary", "profile", "objective",
    "skills", "technical skills", "core skills",
    "experience", "work experience", "employment",
    "projects", "publications",
    "education", "certifications", "awards"
]

def _filename_hygiene(filename: str) -> Dict[str, Any]:
    issues = []
    base = os.path.basename(filename)
    if " " in base:
        issues.append("Filename contains spaces. Prefer hyphens/underscores.")
    if not base.lower().endswith(".pdf"):
        issues.append("Resume should be a PDF.")
    if len(base) > 60:
        issues.append("Filename is long; shorten for ATS friendliness.")
    return {"filename": base, "issues": issues}

def _text_sections(text: str) -> Dict[str, Any]:
    t = text.lower()
    found = []
    missing = []
    for h in SECTION_HEADS:
        if h in t:
            found.append(h)
        else:
            missing.append(h)
    return {"found": found, "missing": missing}

def _detect_columns(chars) -> bool:
    # Heuristic: if significant text appears in two dominant x-bands, likely multi‑column
    if not chars:
        return False
    xs = [c["x0"] for c in chars if "x0" in c]
    if len(xs) < 100:
        return False
    xs.sort()
    # bucket into 20px bins
    bins = {}
    for x in xs:
        key = int(x // 20)
        bins[key] = bins.get(key, 0) + 1
    # count peaks
    peaks = [v for v in bins.values() if v > max(20, len(xs) * 0.02)]
    return len(peaks) >= 2

def _font_variety(chars) -> int:
    fonts = set()
    for c in chars:
        fn = c.get("fontname")
        if fn:
            fonts.add(fn.split("+")[-1])
    return len(fonts)

def ats_audit(uploaded_pdf) -> Dict[str, Any]:
    """Run ATS‑style checks on a PDF file-like (Streamlit upload)."""
    results: Dict[str, Any] = {
        "pages": 0,
        "tables": 0,
        "images": 0,
        "multi_column": False,
        "font_families": 0,
        "contacts": {"email": False, "phone": False},
        "sections": {"found": [], "missing": []},
        "filename": {"filename": "", "issues": []},
        "warnings": []
    }

    # filename hygiene
    if hasattr(uploaded_pdf, "name"):
        results["filename"] = _filename_hygiene(uploaded_pdf.name)

    # open and scan
    try:
        with pdfplumber.open(uploaded_pdf) as pdf:
            results["pages"] = len(pdf.pages)
            all_chars = []
            for page in pdf.pages:
                # tables
                try:
                    tables = page.find_tables() or []
                    results["tables"] += len(tables)
                except Exception:
                    pass
                # images
                try:
                    results["images"] += len(page.images or [])
                except Exception:
                    pass
                try:
                    all_chars.extend(page.chars or [])
                except Exception:
                    pass

            # columns & fonts
            results["multi_column"] = _detect_columns(all_chars)
            results["font_families"] = _font_variety(all_chars)

            # text for contacts/sections
            full_text = ""
            for page in pdf.pages:
                try:
                    tt = page.extract_text() or ""
                    full_text += tt + "\n"
                except Exception:
                    pass
            if EMAIL_RE.search(full_text):
                results["contacts"]["email"] = True
            if PHONE_RE.search(full_text):
                results["contacts"]["phone"] = True
            results["sections"] = _text_sections(full_text)

    except Exception as e:
        results["warnings"].append(f"PDF read error: {e}")

    # high‑level warnings
    if results["multi_column"]:
        results["warnings"].append("Detected multi‑column layout. Some ATS parsers struggle with columns.")
    if results["font_families"] > 4:
        results["warnings"].append("Many font families detected. Keep fonts minimal (<= 3).")
    if results["tables"] > 0:
        results["warnings"].append("Tables detected. Prefer simple bullet points for ATS.")
    if results["images"] > 0:
        results["warnings"].append("Images/icons detected. ATS may ignore image text.")
    if results["pages"] > 2:
        results["warnings"].append("Resume longer than 2 pages.")
    if not results["contacts"]["email"] or not results["contacts"]["phone"]:
        results["warnings"].append("Contact info not clearly detected (email/phone).")
    # section hints
    essentials = {"summary", "skills", "experience", "education"}
    miss_essential = essentials - set(results["sections"]["found"])
    if miss_essential:
        results["warnings"].append(f"Missing key sections: {', '.join(sorted(miss_essential))}.")

    return results
