#!/usr/bin/env python3
"""Compare two benchmark JSON files and report latency deltas."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

METRICS = ("p50_us", "p95_us", "p99_us", "mean_us", "max_us")


@dataclass(frozen=True)
class MetricDelta:
    metric: str
    baseline: float
    candidate: float
    delta: float
    delta_pct: float


def _load_float(data: dict[str, Any], metric: str) -> float:
    value = data.get(metric)
    if not isinstance(value, (int, float)):
        raise ValueError(f"missing numeric metric: {metric}")
    return float(value)


def load_benchmark(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"benchmark file must contain a JSON object: {path}")
    for metric in METRICS:
        _load_float(data, metric)
    return data


def compare_metrics(baseline: dict[str, Any], candidate: dict[str, Any]) -> list[MetricDelta]:
    deltas: list[MetricDelta] = []
    for metric in METRICS:
        base = _load_float(baseline, metric)
        cand = _load_float(candidate, metric)
        delta = cand - base
        delta_pct = 0.0 if base == 0 else (delta / base) * 100.0
        deltas.append(MetricDelta(metric, base, cand, delta, delta_pct))
    return deltas


def verdict(deltas: Sequence[MetricDelta], threshold_pct: float) -> str:
    p95 = next(delta for delta in deltas if delta.metric == "p95_us")
    if p95.delta_pct > threshold_pct:
        return "regression"
    if p95.delta_pct < -threshold_pct:
        return "improvement"
    return "neutral"


def render_text(deltas: Sequence[MetricDelta], threshold_pct: float) -> str:
    rows = ["Benchmark comparison", f"Verdict: {verdict(deltas, threshold_pct)}"]
    for delta in deltas:
        rows.append(
            f"  {delta.metric:7s} baseline={delta.baseline:.3f}us "
            f"candidate={delta.candidate:.3f}us "
            f"delta={delta.delta:+.3f}us ({delta.delta_pct:+.2f}%)"
        )
    return "\n".join(rows)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="baseline benchmark JSON")
    parser.add_argument("candidate", type=Path, help="candidate benchmark JSON")
    parser.add_argument("--threshold-pct", type=float, default=5.0, help="p95 verdict threshold")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        deltas = compare_metrics(load_benchmark(args.baseline), load_benchmark(args.candidate))
    except ValueError as exc:
        print(f"compare error: {exc}", file=sys.stderr)
        return 2

    result = {
        "verdict": verdict(deltas, args.threshold_pct),
        "threshold_pct": args.threshold_pct,
        "metrics": [delta.__dict__ for delta in deltas],
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_text(deltas, args.threshold_pct))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
