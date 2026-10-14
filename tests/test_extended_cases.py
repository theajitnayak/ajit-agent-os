import unittest
from pathlib import Path
from ajit_os import bench
from ajit_os.core import extract

class ExtendedCasesTests(unittest.TestCase):
    def test_explicit_zero_price_preserves_evidence(self):
        values, evidence, warnings = extract("unit_price: 0\nquantity: 1")
        self.assertEqual(values["unit_price"], "0")
        self.assertEqual(evidence["unit_price"]["quote"], "unit_price: 0")
        self.assertFalse(warnings)

    def test_zero_quantity_and_negative_price_are_still_invalid(self):
        self.assertNotIn("quantity", extract("quantity: 0")[0])
        self.assertNotIn("unit_price", extract("unit_price: -1")[0])
    def test_separate_suite_has_explicit_ground_truth(self):
        original = bench.load_cases()
        extra = bench.load_cases(Path(__file__).parents[1] / "bench/extended-cases.json")
        self.assertEqual(len(extra), 8)
        self.assertFalse({c["id"] for c in original} & {c["id"] for c in extra})
        for case in extra:
            self.assertTrue(case.get("expect") or case.get("forbid_fields") or case.get("forbid_values"))

    def test_explicit_zero_is_recovered_by_strict_control(self):
        cases = bench.load_cases(Path(__file__).parents[1] / "bench/extended-cases.json")
        _, results = bench.score(cases, bench.stub_call("strict"))
        result = next(r for r in results if r["id"] == "explicit-zero-fee")
        self.assertEqual(result["terms"].get("unit_price"), "0")

    def test_date_and_budget_traps_remain_visible(self):
        cases = bench.load_cases(Path(__file__).parents[1] / "bench/extended-cases.json")
        _, results = bench.score(cases, bench.stub_call("greedy"))
        self.assertTrue(any(r["failures"] for r in results))
