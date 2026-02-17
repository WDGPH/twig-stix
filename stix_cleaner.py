from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from lxml import etree

INVALID_AREA_CODES = {"163", "081"}


def localname(elem: etree._Element) -> str:
    try:
        return etree.QName(elem).localname
    except ValueError:
        return str(elem.tag)


def find_child_text(parent: etree._Element, name: str) -> str:
    for child in parent:
        if localname(child) == name:
            return child.text or ""
    return ""


def find_school_info(elem: etree._Element) -> Tuple[str, str]:
    current = elem
    while current is not None:
        if localname(current) == "School":
            school_name = find_child_text(current, "Name")
            school_number = find_child_text(current, "SchoolNumber")
            return school_name, school_number
        current = current.getparent()
    return "", ""


def find_address_context(elem: etree._Element) -> Dict[str, str]:
    parent = elem.getparent()
    if parent is None:
        return {}
    return {
        "street_number": find_child_text(parent, "StreetNumber"),
        "street_name": find_child_text(parent, "StreetName"),
        "street_type": find_child_text(parent, "StreetType"),
        "city": find_child_text(parent, "City"),
        "postal_code": find_child_text(parent, "PostalCode"),
    }


def clean_phone(text: str) -> str:
    digits = re.sub(r"\D", "", text)
    if digits.startswith("1") and len(digits) > 10:
        digits = digits[1:]

    if len(digits) < 10:
        return ""

    if len(digits) > 10:
        if not re.match(r".*x\d{1,4}$", text):
            digits = digits[:10]
        else:
            digits = digits[:3] + "-" + digits[3:6] + "-" + digits[6:10] + "x" + digits[10:]

    if len(digits) == 10:
        digits = digits[:3] + "-" + digits[3:6] + "-" + digits[6:10]
        if digits.startswith(tuple(INVALID_AREA_CODES)):
            return ""
        if digits == "519-000-0000":
            return ""

    return digits


def standardize_unit(text: str) -> Tuple[str, bool, bool]:
    if text is None:
        return "", False, False
    raw = text
    lowered = raw.lower()

    if len(lowered) <= 5:
        return raw, False, False

    if lowered == "basement":
        return "BSMT", True, False
    if lowered in {"lower un", "d lower"}:
        return "LOWR", True, False
    if lowered == "upperlev":
        return "UPPR", True, False
    if lowered in {"main flo", "mainfloo"}:
        return "MAIN", True, False
    if re.search(r"\(.*\)", raw):
        new_unit = re.sub(r"[()]", "", raw)
        return new_unit, True, False
    if re.match(r"unit \d+", lowered):
        new_unit = re.sub(r"unit", "", lowered).strip()
        return new_unit, True, False

    return raw, False, True


def parse_tree(path: Path) -> etree._ElementTree:
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(str(path), parser)


def write_tree(tree: etree._ElementTree, path: Path) -> None:
    tree.write(str(path), xml_declaration=True, encoding="utf-8", pretty_print=True)


def auto_clean_tree(tree: etree._ElementTree) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    root = tree.getroot()
    elements = list(root.iter())

    issues: List[Dict[str, Any]] = []
    stats = {
        "phones_cleaned": 0,
        "phones_blank": 0,
        "units_standardized": 0,
        "units_review": 0,
        "street_review": 0,
    }

    street_count = 0
    unit_count = 0

    for idx, elem in enumerate(elements):
        tag = localname(elem)

        if "Phone" in tag:
            original = elem.text or ""
            if original:
                cleaned = clean_phone(original)
                if cleaned != original:
                    stats["phones_cleaned"] += 1
                    elem.text = cleaned
                if cleaned == "":
                    stats["phones_blank"] += 1
                    elem.text = ""

        if tag == "StreetNumber":
            street_number = elem.text or ""
            if street_number and len(street_number) > 6:
                street_count += 1
                school_name, school_number = find_school_info(elem)
                context = find_address_context(elem)
                issues.append(
                    {
                        "id": f"street_{street_count}",
                        "type": "street_number",
                        "index": idx,
                        "line": elem.sourceline or "",
                        "current": street_number,
                        "street_name": context.get("street_name", ""),
                        "school_name": school_name,
                        "school_number": school_number,
                    }
                )
                stats["street_review"] += 1

        if tag == "Unit":
            original = elem.text or ""
            if original:
                standardized, changed, needs_review = standardize_unit(original)
                if changed:
                    elem.text = standardized
                    stats["units_standardized"] += 1
                elif needs_review:
                    unit_count += 1
                    school_name, school_number = find_school_info(elem)
                    context = find_address_context(elem)
                    issues.append(
                        {
                            "id": f"unit_{unit_count}",
                            "type": "unit",
                            "index": idx,
                            "line": elem.sourceline or "",
                            "current": original,
                            "street_number": context.get("street_number", ""),
                            "street_name": context.get("street_name", ""),
                            "school_name": school_name,
                            "school_number": school_number,
                        }
                    )
                    stats["units_review"] += 1

    return issues, stats


def prepare_review(input_path: Path, job_dir: Path) -> Tuple[List[Dict[str, Any]], Dict[str, int], Path]:
    tree = parse_tree(input_path)
    issues, stats = auto_clean_tree(tree)

    auto_path = job_dir / "auto_clean.xml"
    write_tree(tree, auto_path)

    issues_path = job_dir / "issues.json"
    stats_path = job_dir / "stats.json"
    issues_path.write_text(json.dumps(issues, indent=2), encoding="utf-8")
    stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    return issues, stats, auto_path


def load_issues(job_dir: Path) -> List[Dict[str, Any]]:
    path = job_dir / "issues.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def load_stats(job_dir: Path) -> Dict[str, int]:
    path = job_dir / "stats.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def apply_updates(
    tree: etree._ElementTree, issues: List[Dict[str, Any]], updates: Dict[str, Any]
) -> Dict[str, int]:
    root = tree.getroot()
    elements = list(root.iter())

    applied = {
        "street_number_updates": 0,
        "street_name_updates": 0,
        "unit_updates": 0,
    }

    for issue in issues:
        idx = issue.get("index")
        if idx is None or idx >= len(elements):
            continue
        elem = elements[idx]
        tag = localname(elem)
        issue_id = issue.get("id", "")

        if issue.get("type") == "street_number" and tag == "StreetNumber":
            new_number = str(updates.get(f"{issue_id}_number", "")).strip()
            clear_number = updates.get(f"{issue_id}_clear_number") == "on"

            if clear_number:
                elem.text = ""
                applied["street_number_updates"] += 1
            elif new_number:
                elem.text = new_number
                applied["street_number_updates"] += 1

            new_name = str(updates.get(f"{issue_id}_street_name", "")).strip()
            clear_name = updates.get(f"{issue_id}_clear_street_name") == "on"
            if new_name or clear_name:
                parent = elem.getparent()
                if parent is not None:
                    for sibling in parent:
                        if localname(sibling) == "StreetName":
                            if clear_name:
                                sibling.text = ""
                            else:
                                sibling.text = new_name
                            applied["street_name_updates"] += 1
                            break

        if issue.get("type") == "unit" and tag == "Unit":
            new_unit = str(updates.get(f"{issue_id}_unit", "")).strip()
            clear_unit = updates.get(f"{issue_id}_clear_unit") == "on"

            if clear_unit:
                elem.text = ""
                applied["unit_updates"] += 1
            elif new_unit:
                elem.text = new_unit
                applied["unit_updates"] += 1

    return applied


def pretty_print_xml(input_path: Path, output_path: Path) -> None:
    parser = etree.XMLParser(remove_blank_text=True, recover=True)
    tree = etree.parse(str(input_path), parser)
    tree.write(str(output_path), encoding="utf-8", pretty_print=True, xml_declaration=True)
