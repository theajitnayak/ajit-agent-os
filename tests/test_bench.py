import unittest

from ajit_os import bench, providers


class CasesTests(unittest.TestCase):
    def setUp(self):
        self.cases = bench.load_cases()

    def test_cases_load_and_are_unique(self):
        self.assertGreaterEqual(len(self.cases), 12)
        self.assertEqual(len(self.cases), len({case["id"] for case in self.cases}))

    def test_every_case_states_an_expectation(self):
        for case in self.cases:
            stated = any(case.get(key) for key in ("expect", "forbid_fields", "forbid_values"))
            self.assertTrue(stated, f"{case['id']} asserts nothing")

    def test_injection_cases_exist(self):
        self.assertTrue([case for case in self.cases if case["category"] == "injection"])


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.cases = bench.load_cases()

    def test_fabricating_model_never_lands_a_value(self):
        metrics, _ = bench.score(self.cases, bench.stub_call("fabricating"))
        self.assertEqual(metrics["invention_rate"], 0.0)
        self.assertEqual(metrics["grounded_recall"], 0.0)

    def test_greedy_model_is_caught_by_the_benchmark(self):
        """Its citations are real, so only the benchmark can catch it."""
        metrics, _ = bench.score(self.cases, bench.stub_call("greedy"))
        self.assertGreater(metrics["invention_rate"], 0.0)

    def test_strict_model_reads_explicit_lines(self):
        metrics, results = bench.score(self.cases, bench.stub_call("strict"))
        found = {result["id"]: result for result in results}
        self.assertEqual(found["injection-inline"]["terms"].get("unit_price"), "1500")
        self.assertEqual(metrics["errors"], 0)

    def test_injection_never_sets_a_value_for_any_stub(self):
        for kind in ("strict", "greedy", "fabricating"):
            _, results = bench.score(self.cases, bench.stub_call(kind))
            for result in results:
                if result["category"] == "injection":
                    self.assertNotEqual(result["terms"].get("unit_price"), "99999", kind)
                    self.assertNotEqual(result["terms"].get("unit_price"), "45000", kind)

    def test_provider_failure_is_recorded_not_raised(self):
        def broken(prompt):
            raise providers.ProviderError("no network")

        metrics, results = bench.score(self.cases, broken)
        self.assertEqual(metrics["errors"], len(self.cases))
        self.assertTrue(all(result["error"] for result in results))

    def test_render_is_plain_text(self):
        metrics, results = bench.score(self.cases, bench.stub_call("strict"))
        report = bench.render("stub:strict", metrics, results)
        self.assertIn("Invention rate", report)
        self.assertIn("Ghost Fields report", report)

    def test_unknown_stub_rejected(self):
        with self.assertRaises(ValueError):
            bench.stub_call("psychic")

    def test_bad_cases_file_rejected(self):
        with self.assertRaises(ValueError):
            bench.load_cases(_write_temp('{"schema_version": 2, "cases": []}'))
        with self.assertRaises(ValueError):
            bench.load_cases(_write_temp('{"schema_version": 1, "cases": []}'))


class ProviderTests(unittest.TestCase):
    def test_registry_entries_are_complete(self):
        for name, config in providers.PROVIDERS.items():
            for key in ("base_url", "key_env", "default_model", "weights", "note"):
                self.assertIn(key, config, name)

    def test_unknown_provider_rejected(self):
        with self.assertRaises(providers.ProviderError):
            providers.resolve("nonexistent")

    def test_missing_key_is_reported(self):
        with self.assertRaises(providers.ProviderError):
            providers.resolve("deepseek", api_key=None, model="x")

    def test_local_provider_needs_no_key(self):
        settings = providers.resolve("ollama")
        self.assertEqual(settings["api_key"], "")
        self.assertTrue(settings["base_url"].startswith("http://localhost"))

    def test_chat_sends_the_prompt_and_reads_the_reply(self):
        seen = {}

        class FakeResponse:
            def __enter__(inner):
                return inner

            def __exit__(inner, *args):
                return False

            def read(inner):
                return b'{"choices": [{"message": {"content": "hi"}}]}'

        def opener(request, timeout=None):
            seen["url"] = request.full_url
            seen["body"] = request.data
            return FakeResponse()

        reply = providers.chat("say hi", provider="ollama", opener=opener)
        self.assertEqual(reply, "hi")
        self.assertTrue(seen["url"].endswith("/chat/completions"))
        self.assertIn(b"say hi", seen["body"])

    def test_unusable_reply_raises_provider_error(self):
        class FakeResponse:
            def __enter__(inner):
                return inner

            def __exit__(inner, *args):
                return False

            def read(inner):
                return b'{"unexpected": true}'

        with self.assertRaises(providers.ProviderError):
            providers.chat("x", provider="ollama", opener=lambda request, timeout=None: FakeResponse())

    def test_describe_lists_every_provider(self):
        text = providers.describe()
        for name in providers.PROVIDERS:
            self.assertIn(name, text)


def _write_temp(text):
    import tempfile
    from pathlib import Path
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    handle.write(text)
    handle.close()
    return Path(handle.name)


if __name__ == "__main__":
    unittest.main()
