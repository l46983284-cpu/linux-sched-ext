#!/usr/bin/env python3
"""Classify workload names using a small JSON rule file.

This mirrors the scheduler prototype's current prefix-based policy in a form that
can be reviewed and tested without loading BPF. The BPF program still keeps its
hard-coded minimal classifier; this tool is the user-space contract for evolving
those rules safely before kernel-facing code consumes them.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "workload_rules.example.json"


@dataclass(frozen=True)
class Classification:
    command: str
    workload_class: str
    matched_prefix: str | None
    slice_multiplier: int
    reason: str


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def load_rules(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("rule config must be a JSON object")
    if data.get("version") != 1:
        raise ValueError("rule config version must be 1")
    _require_string(data.get("default_class"), "default_class")
    rules = data.get("rules")
    if not isinstance(rules, list):
        raise ValueError("rules must be a list")

    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise ValueError(f"rules[{index}] must be an object")
        _require_string(rule.get("class"), f"rules[{index}].class")
        prefixes = rule.get("prefixes")
        if not isinstance(prefixes, list) or not prefixes:
            raise ValueError(f"rules[{index}].prefixes must be a non-empty list")
        for prefix in prefixes:
            _require_string(prefix, f"rules[{index}].prefixes[]")
        multiplier = rule.get("slice_multiplier", 1)
        if not isinstance(multiplier, int) or multiplier < 1:
            raise ValueError(f"rules[{index}].slice_multiplier must be an integer >= 1")
        _require_string(rule.get("reason", "unspecified"), f"rules[{index}].reason")

    return data


def classify_command(command: str, ruleset: dict[str, Any]) -> Classification:
    normalized = command.strip().lower()
    if not normalized:
        raise ValueError("command must not be empty")

    for rule in ruleset["rules"]:
        for prefix in rule["prefixes"]:
            normalized_prefix = prefix.lower()
            if normalized.startswith(normalized_prefix):
                return Classification(
                    command=command,
                    workload_class=rule["class"],
                    matched_prefix=prefix,
                    slice_multiplier=rule.get("slice_multiplier", 1),
                    reason=rule["reason"],
                )

    return Classification(
        command=command,
        workload_class=ruleset["default_class"],
        matched_prefix=None,
        slice_multiplier=1,
        reason="No configured prefix matched; use the default scheduler class.",
    )


def render_text(result: Classification) -> str:
    matched = result.matched_prefix if result.matched_prefix is not None else "<default>"
    return "\n".join(
        [
            f"Command:          {result.command}",
            f"Class:            {result.workload_class}",
            f"Matched prefix:   {matched}",
            f"Slice multiplier: {result.slice_multiplier}",
            f"Reason:           {result.reason}",
        ]
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", help="process command/name to classify")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="JSON rule config")
    parser.add_argument("--json", action="store_true", help="emit JSON output")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        ruleset = load_rules(args.config)
        result = classify_command(args.command, ruleset)
    except ValueError as exc:
        print(f"classification error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
