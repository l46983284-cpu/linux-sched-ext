import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPARE_PATH = ROOT / "tools" / "compare_benchmarks.py"

spec = importlib.util.spec_from_file_location("compare_benchmarks", COMPARE_PATH)
assert spec is not None and spec.loader is not None
compare = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = compare
spec.loader.exec_module(compare)


BASELINE = {
    "p50_us": 100.0,
    "p95_us": 200.0,
    "p99_us": 300.0,
    "mean_us": 150.0,
    "max_us": 400.0,
}


class CompareBenchmarkTests(unittest.TestCase):
    def test_compare_metrics_calculates_deltas(self):
        candidate = dict(BASELINE, p95_us=220.0)
        deltas = compare.compare_metrics(BASELINE, candidate)
        p95 = next(delta for delta in deltas if delta.metric == "p95_us")
        self.assertEqual(p95.delta, 20.0)
        self.assertEqual(p95.delta_pct, 10.0)

    def test_verdict_detects_regression(self):
        candidate = dict(BASELINE, p95_us=220.0)
        deltas = compare.compare_metrics(BASELINE, candidate)
        self.assertEqual(compare.verdict(deltas, threshold_pct=5.0), "regression")

    def test_verdict_detects_improvement(self):
        candidate = dict(BASELINE, p95_us=180.0)
        deltas = compare.compare_metrics(BASELINE, candidate)
        self.assertEqual(compare.verdict(deltas, threshold_pct=5.0), "improvement")

    def test_verdict_detects_neutral(self):
        candidate = dict(BASELINE, p95_us=204.0)
        deltas = compare.compare_metrics(BASELINE, candidate)
        self.assertEqual(compare.verdict(deltas, threshold_pct=5.0), "neutral")

    def test_load_rejects_missing_metric(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "bad.json"
            path.write_text(json.dumps({"p95_us": 1}))
            with self.assertRaises(ValueError):
                compare.load_benchmark(path)


if __name__ == "__main__":
    unittest.main()
