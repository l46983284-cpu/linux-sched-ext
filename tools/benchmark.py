#!/usr/bin/env python3
"""Benchmark script for measuring scheduling latency."""
import subprocess
import time
import statistics
import sys

def measure_latency(n=1000):
    """Measure fork+exec latency as proxy for scheduling overhead."""
    latencies = []
    for _ in range(n):
        start = time.monotonic_ns()
        subprocess.run(["/bin/true"], capture_output=True)
        end = time.monotonic_ns()
        latencies.append(end - start)
    
    latencies.sort()
    p50 = latencies[len(latencies)//2]
    p99 = latencies[int(len(latencies)*0.99)]
    
    print(f"Scheduling latency ({n} samples):")
    print(f"  P50: {p50/1000:.1f} us")
    print(f"  P99: {p99/1000:.1f} us")
    print(f"  Min: {min(latencies)/1000:.1f} us")
    print(f"  Max: {max(latencies)/1000:.1f} us")
    print(f"  Stddev: {statistics.stdev(latencies)/1000:.1f} us")

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    measure_latency(n)
