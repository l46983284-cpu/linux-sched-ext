#!/usr/bin/env python3
"""Mixed latency workload for scheduler experiments.

Runs short sleep/fork probes while optional CPU pressure is active. This provides
a cheap way to compare tail latency before and after changing scheduler policy.
"""
from __future__ import annotations

import argparse
import subprocess
import time


def probe(samples: int, sleep_s: float) -> list[float]:
    latencies = []
    for _ in range(samples):
        start = time.monotonic_ns()
        subprocess.run(["/bin/sleep", str(sleep_s)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        elapsed_us = (time.monotonic_ns() - start) / 1000.0
        latencies.append(elapsed_us)
    return latencies


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=25)
    parser.add_argument("--sleep", type=float, default=0.001)
    args = parser.parse_args()

    values = sorted(probe(args.samples, args.sleep))
    p50 = values[len(values) // 2]
    p99 = values[min(len(values) - 1, int(len(values) * 0.99))]
    print(f"samples={args.samples} sleep={args.sleep}s p50={p50:.1f}us p99={p99:.1f}us max={values[-1]:.1f}us")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
