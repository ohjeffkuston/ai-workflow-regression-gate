"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .engine import evaluate_suite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate an AI workflow change against deterministic regression fixtures."
    )
    parser.add_argument("suite", type=Path, help="Path to a regression suite JSON file.")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = json.loads(args.suite.read_text(encoding="utf-8"))
        report = evaluate_suite(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"error: {exc}") from exc
    print(json.dumps(report, indent=None if args.compact else 2, sort_keys=True))
    return 0 if report["decision"] == "PASS" else 1

