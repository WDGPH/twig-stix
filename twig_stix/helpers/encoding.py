import re
from pathlib import Path
from typing import List, Optional


XML_ENCODING_RE = re.compile(rb'<\?xml[^>]*encoding=[\"\']([^\"\']+)[\"\']', re.IGNORECASE)


def detect_xml_encoding(path: Path) -> Optional[str]:
    """Peek at the XML declaration to detect the encoding, if present."""
    try:
        with path.open("rb") as fh:
            head = fh.read(2048)
    except Exception:
        return None
    m = XML_ENCODING_RE.search(head)
    if m:
        try:
            return m.group(1).decode("ascii", errors="ignore")
        except Exception:
            return None
    return None


def read_text_with_fallbacks(path: Path, fallbacks: Optional[List[str]] = None) -> str:
    """Read a text file trying detected encoding first, then fallbacks.

    Do not silently change file encoding: detected encoding (XML declaration) is used when available.
    """
    if fallbacks is None:
        fallbacks = ["utf-8", "utf-8-sig", "windows-1252", "latin-1"]
    detected = detect_xml_encoding(path)
    encodings = [detected] if detected else []
    encodings += [e for e in fallbacks if e not in encodings]
    last_exc = None
    for enc in encodings:
        try:
            return path.read_text(encoding=enc)
        except Exception as exc:
            last_exc = exc
    # final attempt without specifying encoding
    try:
        return path.read_text()
    except Exception as exc:
        raise last_exc or exc
