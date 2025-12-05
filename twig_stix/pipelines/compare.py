"""Thin pipeline wrapper for comparing two STIX XML files.

Uses functions from `compare_files.py` when available.
"""
from pathlib import Path
import sys
import subprocess
import argparse

try:
    from compare_files import parse_xml, build_dataframe, compare_dataframes, compare_client_info
except Exception:
    parse_xml = None
    build_dataframe = None
    compare_dataframes = None


def run_compare(old_path: Path, new_path: Path, out_dir: Path) -> int:
    # prefer Python-level functions if available
    if parse_xml and build_dataframe and compare_dataframes:
        old = parse_xml(old_path)
        new = parse_xml(new_path)
        df_old = build_dataframe(old)
        df_new = build_dataframe(new)
        diffs = compare_dataframes(df_old, df_new)
        # Write outputs to CSV in out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        diffs['added'].to_csv(out_dir / 'added.csv', index=False, encoding='utf-8-sig')
        diffs['removed'].to_csv(out_dir / 'removed.csv', index=False, encoding='utf-8-sig')
    
        # Compare client info if possible
        if compare_client_info:
            client_diffs = compare_client_info(old, new)

        return 0
    # fallback: run existing script as subprocess
    cmd = [sys.executable, str(Path(__file__).resolve().parents[2] / 'compare_files.py'), str(old_path), str(new_path), '--out', str(out_dir)]
    return subprocess.call(cmd)


if __name__ == '__main__':

    p = argparse.ArgumentParser(description='Run compare pipeline')
    p.add_argument('old', type=Path)
    p.add_argument('new', type=Path)
    p.add_argument('--out', '-o', type=Path, default=Path('output/compare'))
    args = p.parse_args()
    if not args.old.exists() or not args.new.exists():
        print('input(s) not found', file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(run_compare(args.old, args.new, args.out))
