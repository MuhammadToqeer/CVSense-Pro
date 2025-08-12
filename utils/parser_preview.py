# utils/parser_preview.py
import pdfplumber

def pdf_text_preview(uploaded_pdf, max_chars: int = 2500) -> str:
    """
    Return a plain-text preview (simulated ATS parse).
    Reads all pages, concatenates text, trims to max_chars.
    """
    if not uploaded_pdf:
        return ""
    text = []
    try:
        with pdfplumber.open(uploaded_pdf) as pdf:
            for p in pdf.pages:
                try:
                    t = p.extract_text() or ""
                    text.append(t)
                except Exception:
                    pass
    except Exception:
        return ""
    full = "\n".join(text).strip()
    if len(full) > max_chars:
        return full[:max_chars] + " ..."
    return full
