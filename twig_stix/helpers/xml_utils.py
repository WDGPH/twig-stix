from pathlib import Path
from typing import Any, Dict

import xmltodict

from .encoding import read_text_with_fallbacks


def read_xml_dict(path: Path) -> Dict[str, Any]:
    """Read an XML file and return an xmltodict-parsed dictionary.

    Uses encoding helpers to respect declared encodings and fallbacks.
    """
    text = read_text_with_fallbacks(path)
    return xmltodict.parse(text)
