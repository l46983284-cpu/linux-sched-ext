import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLASSIFIER_PATH = ROOT / "tools" / "classify_workload.py"

spec = importlib.util.spec_from_file_location("classify_workload", CLASSIFIER_PATH)
assert spec is not None and spec.loader is not None
classifier = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = classifier
spec.loader.exec_module(classifier)


class ClassifierRuleTests(unittest.TestCase):
    def test_loads_example_rules(self):
        ruleset = classifier.load_rules()
        self.assertEqual(ruleset["version"], 1)
        self.assertGreaterEqual(len(ruleset["rules"]), 1)

    def test_classifies_ml_prefix(self):
        ruleset = classifier.load_rules()
        result = classifier.classify_command("python3", ruleset)
        self.assertEqual(result.workload_class, "ml")
        self.assertEqual(result.matched_prefix, "python")
        self.assertEqual(result.slice_multiplier, 4)

    def test_classifies_default_when_no_rule_matches(self):
        ruleset = classifier.load_rules()
        result = classifier.classify_command("bash", ruleset)
        self.assertEqual(result.workload_class, "interactive")
        self.assertIsNone(result.matched_prefix)
        self.assertEqual(result.slice_multiplier, 1)

    def test_rejects_empty_command(self):
        ruleset = classifier.load_rules()
        with self.assertRaises(ValueError):
            classifier.classify_command("   ", ruleset)

    def test_rejects_invalid_rule_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "rules.json"
            path.write_text(json.dumps({"version": 1, "default_class": "x", "rules": []}))
            ruleset = classifier.load_rules(path)
            self.assertEqual(ruleset["default_class"], "x")

            path.write_text(json.dumps({"version": 2, "default_class": "x", "rules": []}))
            with self.assertRaises(ValueError):
                classifier.load_rules(path)


if __name__ == "__main__":
    unittest.main()
