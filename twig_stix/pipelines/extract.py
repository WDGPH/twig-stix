"""Thin pipeline wrapper for extraction tasks.

This module provides a small programmatic wrapper around `pull_info.py` functions.
"""
from pathlib import Path
from typing import Optional

from pull_info import parse_xml, build_dataframe, export_outputs, summarize, filter_students


def run_extract(input_path: Path, output_path: Optional[Path] = None, excel: bool = False) -> int:
    students = parse_xml(input_path)
    df = build_dataframe(students)
    summaries = summarize(df)
    df_filtered = filter_students(df)
    export_outputs(df, df_filtered, summaries, output_path, excel=excel)
    return 0


if __name__ == '__main__':
    import argparse
    import sys

    p = argparse.ArgumentParser(description="Run extraction pipeline")
    p.add_argument('input', type=Path)
    p.add_argument('--output', '-o', type=Path)
    p.add_argument('--excel', action='store_true')
    args = p.parse_args()
    if not args.input.exists():
        print('input not found', file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(run_extract(args.input, args.output, excel=args.excel))
