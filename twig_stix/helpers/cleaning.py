import re
import logging
from typing import Optional


def clean_phone(text: Optional[str]) -> str:
    """Normalize phone numbers to NNN-NNN-NNNN or empty string when invalid.

    Logic preserved from existing `twig_stix.py`.
    """
    if not text:
        return ""
    digits = re.sub(r"\D", "", text)
    if digits.startswith("1") and len(digits) > 10:
        digits = digits[1:]

    if len(digits) < 10:
        logging.warning(f"Phone number '{text}' has less than 10 digits. Setting to empty.")
        return ""

    if len(digits) > 10:
        # allow extensions, but default to truncation if not recognizable
        if not re.match(r'.*x\d{1,4}$', text):
            logging.warning(f"Phone number '{text}' has more than 10 digits and no valid extension. Truncating to 10 digits.")
            digits = digits[:10]
        else:
            digits = digits[:3] + '-' + digits[3:6] + '-' + digits[6:10] + 'x' + digits[10:]

    if len(digits) == 10:
        formatted = digits[:3] + '-' + digits[3:6] + '-' + digits[6:10]
        invalid_area_codes = ['163', '081']
        if formatted.startswith(tuple(invalid_area_codes)):
            logging.warning(f"Phone number '{text}' has invalid area code. Setting to empty.")
            return ""
        if formatted == '519-000-0000':
            logging.warning(f"Phone number '{text}' is all zeros. Setting to empty.")
            return ""
        return formatted

    return digits


def standardize_unit(unit: Optional[str]) -> Optional[str]:
    if not unit:
        return unit
    u = unit.strip().lower()
    if u == 'basement':
        return 'BSMT'
    if u in ('lower un', 'd lower'):
        return 'LOWR'
    if u in ('upperlev',):
        return 'UPPR'
    if u in ('main flo', 'mainfloo'):
        return 'MAIN'
    # remove parentheses
    if re.match(r'.*\(.*\).*', unit):
        return re.sub(r'[\(\)]', '', unit)
    m = re.match(r'unit\s*(\d+)', u)
    if m:
        return m.group(1)
    return unit
