#!/usr/bin/env python3
"""Synthetic ML-like CPU workload for scheduler experiments.

The script creates worker processes with Python process names and predictable CPU
pressure. It is useful for testing workload classification and mixed latency
benchmarks without requiring GPU dependencies.
"""
from __future__ import annotations

import argparse
import math
import multiprocessing as mp
import os
import time


def burn_cpu(seconds: float, worker_id: int) -> None:
    deadline = time.monotonic() + seconds
    value = 0.0
    iterations = 0
    while time.monotonic() < deadline:
        # Keep the loop deterministic and CPU-heavy enough for scheduler traces.
        value += math.sin(iterations % 1024) * math.cos(worker_id + iterations % 2048)
        iterations += 1
    print(f"worker={worker_id} pid={os.getpid()} iterations={iterations} checksum={value:.3f}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    parser.add_argument("--seconds", type=float, default=10.0)
    args = parser.parse_args()

    if args.workers <= 0:
        parser.error("--workers must be > 0")
    if args.seconds <= 0:
        parser.error("--seconds must be > 0")

    print(f"starting {args.workers} synthetic ML workers for {args.seconds:.1f}s")
    processes = [mp.Process(target=burn_cpu, args=(args.seconds, i), name=f"python-ml-{i}") for i in range(args.workers)]
    for proc in processes:
        proc.start()
    for proc in processes:
        proc.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
