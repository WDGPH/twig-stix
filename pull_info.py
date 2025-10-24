#!/usr/bin/env python3

import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import xmltodict

# Logging to both console and file
DEFAULT_LOGFILE = "pull_info.log"
logger = logging.getLogger("pull_info")
logger.setLevel(logging.INFO)
fmt = logging.Formatter("%(levelname)s: %(message)s")

fh = logging.FileHandler(DEFAULT_LOGFILE, mode="w", encoding="windows-1252")
fh.setFormatter(fmt)
logger.addHandler(fh)

sh = logging.StreamHandler()
sh.setFormatter(fmt)
logger.addHandler(sh)


def _ensure_list(x: Optional[Any]) -> List[Any]:
    """Normalize xmltodict result to a list."""
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def parse_xml(path: Path) -> List[Dict[str, Any]]:
    """Parse STIX-like school XML and return a flat list of student dicts."""
    logger.info("Parsing XML: %s", path)
    text = path.read_text(encoding="windows-1252")
    data = xmltodict.parse(text)

    root = data.get("ns1:SchoolUpload", data)
    records = _ensure_list(root.get("ns1:School"))

    students_out: List[Dict[str, Any]] = []

    for rec in records:
        school_name = rec.get("ns1:Name", "") or ""
        school_number = rec.get("ns1:SchoolNumber", "") or ""
        students_node = rec.get("ns1:Students", {}) or {}
        student_nodes = _ensure_list(students_node.get("ns1:Student"))

        for student in student_nodes:
            name_node = student.get("ns1:Name", {}) or {}
            first = name_node.get("ns1:First", "") or ""
            middle = name_node.get("ns1:Middle", "") or ""
            last = name_node.get("ns1:Last", "") or ""

            alias_name_node = student.get("ns1:AliasName", {}) or {}
            address_node = student.get("ns1:Address", {}) or {}
            unit = address_node.get("ns1:Unit", "") or ""
            street_number = address_node.get("ns1:StreetNumber", "") or ""
            street_number_suffix = address_node.get("ns1:StreetNumberSuffix", "") or ""
            street_name = address_node.get("ns1:StreetName", "") or ""
            street_type = address_node.get("ns1:StreetType", "") or ""
            city = address_node.get("ns1:City", "") or ""
            province = address_node.get("ns1:Province", "") or ""
            postal_code = address_node.get("ns1:PostalCode", "") or ""

            student_dict = {
                "SchoolName": school_name,
                "SchoolNumber": school_number,
                "FirstName": first,
                "MiddleName": middle,
                "LastName": last,
                "AliasFirstName": alias_name_node.get("ns1:First"),
                "AliasMiddleName": alias_name_node.get("ns1:Middle"),
                "AliasLastName": alias_name_node.get("ns1:Last"),
                "BirthDate": student.get("ns1:BirthDate"),
                "Grade": student.get("ns1:Grade"),
                "Class": student.get("ns1:Class"),
                "OEN": student.get("ns1:OEN"),
                "Gender": student.get("ns1:Gender"),
                "Language": student.get("ns1:Language"),
                "CountryOfOrigin": student.get("ns1:CountryOfOrigin"),
                "Unit": unit,
                "StreetNumber": street_number,
                "StreetNumberSuffix": street_number_suffix,
                "StreetName": street_name,
                "StreetType": street_type,
                "City": city,
                "Province": province,
                "PostalCode": postal_code,
            }
            students_out.append(student_dict)

    logger.info("Parsed %d students", len(students_out))
    return students_out


def summarize(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Produce summary tables used by original script."""
    school_counts = df.groupby(["SchoolName", "BirthYear"]).size().reset_index(name="StudentCount")
    grade_counts = df.groupby(["SchoolName", "Grade"]).size().reset_index(name="GradeCount")
    return {"school_counts": school_counts, "grade_counts": grade_counts}


def filter_students(df: pd.DataFrame) -> pd.DataFrame:
    """Apply birth year and grade filters (2012/2013 & GR7/GR8)."""
    df_filtered = df[df["BirthYear"].isin([2012, 2013])]
    df_filtered = df_filtered[df_filtered["Grade"].isin(["GR7", "GR8"])]
    return df_filtered

def build_dataframe(student_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """Return DataFrame with parsed dates and derived columns."""
    df = pd.DataFrame(student_list)
    if "BirthDate" in df.columns:
        df["BirthDate"] = pd.to_datetime(df["BirthDate"], errors="coerce")
        df["BirthYear"] = df["BirthDate"].dt.year
    else:
        df["BirthDate"] = pd.NaT
        df["BirthYear"] = pd.NA
    return df

def export_outputs(
    df_all: pd.DataFrame,
    df_filtered: pd.DataFrame,
    summaries: Dict[str, pd.DataFrame],
    out: Optional[Path],
    excel: bool = False,
) -> None:
    """Export results to CSVs or a single Excel workbook."""
    if out is None:
        logger.info("No output path provided; skipping export.")
        return

    out = out.expanduser()
    out_parent = out.parent
    if not out_parent.exists():
        out_parent.mkdir(parents=True, exist_ok=True)

    if excel:
        out_file = out if out.suffix.lower() == ".xlsx" else out.with_suffix(".xlsx")
        logger.info("Writing Excel output: %s", out_file)
        with pd.ExcelWriter(out_file, engine="openpyxl") as writer:
            df_all.to_excel(writer, sheet_name="All_Students", index=False)
            df_filtered.to_excel(writer, sheet_name="Filtered_Students", index=False)
            summaries["school_counts"].to_excel(writer, sheet_name="School_Counts", index=False)
            summaries["grade_counts"].to_excel(writer, sheet_name="Grade_Counts", index=False)
    else:
        base = out.with_suffix("") if out.suffix else out
        students_csv = base.with_name(base.name + "_all_students.csv")
        filtered_csv = base.with_name(base.name + "_filtered_students.csv")
        school_csv = base.with_name(base.name + "_school_counts.csv")
        grade_csv = base.with_name(base.name + "_grade_counts.csv")

        logger.info("Writing CSV outputs to: %s*", base)
        df_all.to_csv(students_csv, index=False, encoding="utf-8-sig")
        df_filtered.to_csv(filtered_csv, index=False, encoding="utf-8-sig")
        summaries["school_counts"].to_csv(school_csv, index=False, encoding="utf-8-sig")
        summaries["grade_counts"].to_csv(grade_csv, index=False, encoding="utf-8-sig")


def main() -> int:
    p = argparse.ArgumentParser(description="Extract student info from school XML.")
    p.add_argument("input", type=Path, help="Path to the XML file")
    p.add_argument("--output", "-o", type=Path, help="Output path (file). If --excel passed produces .xlsx")
    p.add_argument("--excel", action="store_true", help="Export results as a single Excel workbook (.xlsx)")
    args = p.parse_args()

    if not args.input.exists():
        logger.error("Input file not found: %s", args.input)
        return 2

    try:
        students = parse_xml(args.input)
        df = build_dataframe(students)
        summaries = summarize(df)
        df_filtered = filter_students(df)

        logger.info("Total schools processed: %d", df["SchoolName"].nunique() if "SchoolName" in df else 0)
        logger.info("Total students extracted: %d", len(df))
        logger.info("Birth year distribution:\n%s", df["BirthYear"].value_counts(dropna=True).to_string())
        logger.info("Grade distribution:\n%s", summaries["grade_counts"].to_string(index=False))
        logger.info("Total students born in 2012 and 2013: %d", len(df_filtered))
        logger.info("Grade distribution for filtered students:\n%s", df_filtered["Grade"].value_counts(dropna=True).to_string())
        logger.info("Schools with filtered students:\n%s", df_filtered["SchoolName"].unique())

        export_outputs(df, df_filtered, summaries, args.output, excel=args.excel)
    except Exception as exc:
        logger.exception("Processing failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

