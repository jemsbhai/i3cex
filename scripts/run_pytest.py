#!/usr/bin/env python3
"""Cross-platform pytest runner used by Hatch scripts.

Hatch passes its scripts through the platform shell. On Windows that
shell is PowerShell, which handles quoted arguments with internal
spaces (e.g. ``-m "unit or property"``) differently from POSIX shells.
Rather than fight the shell, we delegate invocation to this Python
script, which constructs argv programmatically and calls pytest via a
subprocess. Quoting is never exposed to the shell.

Usage (invoked by Hatch, not directly):

    python scripts/run_pytest.py --markers "unit or property" [extra pytest args...]
    python scripts/run_pytest.py --markers "not cosim" --cov-report=html

The first positional-style argument is the marker expression. All
remaining arguments are forwarded to pytest verbatim.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Entry point. Returns pytest's exit code."""
    parser = argparse.ArgumentParser(
        description="Invoke pytest with a marker expression and optional extra args.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--markers",
        required=True,
        help='Pytest -m marker expression, e.g. "unit or property" or "not cosim".',
    )
    # Everything after ``--`` (or unrecognised args) is forwarded to pytest.
    args, forwarded = parser.parse_known_args()

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-m",
        args.markers,
        *forwarded,
    ]

    # cwd is the package root (where pyproject.toml lives). Let pytest
    # discover its config as normal.
    cwd = Path(__file__).resolve().parent.parent
    return subprocess.call(cmd, cwd=cwd)


if __name__ == "__main__":
    raise SystemExit(main())
