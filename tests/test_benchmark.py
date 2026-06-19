import importlib.util
import pathlib
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
BENCHMARK_PATH = ROOT / "tools" / "benchmark.py"

spec = importlib.util.spec_from_file_location("benchmark", BENCHMARK_PATH)
assert spec is not None and spec.loader is not None
benchmark = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = benchmark
spec.loader.exec_module(benchmark)


class BenchmarkTests(unittest.TestCase):
    def test_percentile_edges(self):
        values = [10, 20, 30, 40]
        self.assertEqual(benchmark.percentile(values, 0), 10)
        self.assertEqual(benchmark.percentile(values, 50), 30)
        self.assertEqual(benchmark.percentile(values, 100), 40)

    def test_percentile_rejects_empty(self):
        with self.assertRaises(ValueError):
            benchmark.percentile([], 50)

    def test_measure_latency_validates_inputs(self):
        with self.assertRaises(ValueError):
            benchmark.measure_latency(["/bin/true"], samples=0)
        with self.assertRaises(ValueError):
            benchmark.measure_latency([], samples=1)

    def test_measure_latency_returns_structured_stats(self):
        latencies = iter([1000, 2000, 3000, 4000, 5000])
        with mock.patch.object(benchmark, "run_once", side_effect=lambda _cmd: next(latencies)):
            stats = benchmark.measure_latency(["/bin/true"], samples=3, warmup=2)

        self.assertEqual(stats.samples, 3)
        self.assertEqual(stats.command, ["/bin/true"])
        self.assertEqual(stats.min_us, 3.0)
        self.assertEqual(stats.max_us, 5.0)
        self.assertEqual(stats.p50_us, 4.0)

    def test_parse_legacy_sample_count(self):
        args = benchmark.parse_args(["25"])
        self.assertEqual(args.samples, 25)
        self.assertEqual(args.command, ["/bin/true"])


if __name__ == "__main__":
    unittest.main()
