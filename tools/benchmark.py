#!/usr/bin/env python3
"""Portable scheduler-latency benchmark.

The benchmark measures subprocess start/exit latency as a portable proxy for
scheduler overhead. It intentionally does not require root or a sched_ext kernel,
so it can run in CI and produce comparable smoke-test data.
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from typing import Sequence


@dataclass(frozen=True)
class LatencyStats:
    samples: int
    command: list[str]
    p50_us: float
    p95_us: float
    p99_us: float
    min_us: float
    max_us: float
    mean_us: float
    stdev_us: float


def percentile(sorted_values: Sequence[int], pct: float) -> int:
    """Return nearest-rank percentile from sorted nanosecond values."""
    if not sorted_values:
        raise ValueError("percentile requires at least one sample")
    if pct < 0 or pct > 100:
        raise ValueError("percentile must be between 0 and 100")
    idx = round((pct / 100) * (len(sorted_values) - 1))
    return sorted_values[idx]


def run_once(command: Sequence[str]) -> int:
    start = time.monotonic_ns()
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return time.monotonic_ns() - start


def measure_latency(command: Sequence[str], samples: int = 1000, warmup: int = 10) -> LatencyStats:
    if samples <= 0:
        raise ValueError("samples must be > 0")
    if warmup < 0:
        raise ValueError("warmup must be >= 0")
    if not command:
        raise ValueError("command must not be empty")

    for _ in range(warmup):
        run_once(command)

    latencies = [run_once(command) for _ in range(samples)]
    latencies.sort()

    def us(ns: int | float) -> float:
        return round(float(ns) / 1000.0, 3)

    return LatencyStats(
        samples=samples,
        command=list(command),
        p50_us=us(percentile(latencies, 50)),
        p95_us=us(percentile(latencies, 95)),
        p99_us=us(percentile(latencies, 99)),
        min_us=us(latencies[0]),
        max_us=us(latencies[-1]),
        mean_us=us(statistics.fmean(latencies)),
        stdev_us=us(statistics.stdev(latencies) if len(latencies) > 1 else 0),
    )


def render_text(stats: LatencyStats) -> str:
    return "\n".join(
        [
            f"Scheduling latency ({stats.samples} samples)",
            f"  Command: {' '.join(stats.command)}",
            f"  P50:     {stats.p50_us:.1f} us",
            f"  P95:     {stats.p95_us:.1f} us",
            f"  P99:     {stats.p99_us:.1f} us",
            f"  Min:     {stats.min_us:.1f} us",
            f"  Max:     {stats.max_us:.1f} us",
            f"  Mean:    {stats.mean_us:.1f} us",
            f"  Stddev:  {stats.stdev_us:.1f} us",
        ]
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("legacy_samples", nargs="?", type=int, help="backward-compatible sample count")
    parser.add_argument("--samples", type=int, default=None, help="number of measured samples")
    parser.add_argument("--warmup", type=int, default=10, help="warmup iterations before measurement")
    parser.add_argument("--command", nargs="+", default=["/bin/true"], help="command to benchmark")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args(argv)
    if args.samples is None:
        args.samples = args.legacy_samples if args.legacy_samples is not None else 1000
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        stats = measure_latency(args.command, samples=args.samples, warmup=args.warmup)
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"benchmark error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(asdict(stats), indent=2, sort_keys=True))
    else:
        print(render_text(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
