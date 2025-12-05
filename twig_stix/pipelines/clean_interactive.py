"""Thin pipeline wrapper to run the existing interactive cleaner script.

This wrapper runs `twig_stix.py` as a subprocess to preserve exact CLI and interactive behavior.
"""
from pathlib import Path
import subprocess
import sys


def run_clean(input_path: Path) -> int:
    cmd = [sys.executable, str(Path(__file__).resolve().parents[2] / 'twig_stix.py'), str(input_path)]
    return subprocess.call(cmd)


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser(description='Run interactive cleaner')
    p.add_argument('input', type=Path)
    args = p.parse_args()
    if not args.input.exists():
        print('input not found', file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(run_clean(args.input))
