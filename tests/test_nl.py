import json
import unittest

from ajit_os import bench, core, nl


def replay(reply):
    """A model that always says the same thing."""
    return lambda prompt: reply


class PromptTests(unittest.TestCase):
    def test_source_is_fenced_and_recoverable(self):
        prompt = nl.build_prompt("hello 1500")
        self.assertIn("untrusted data", prompt)
        self.assertEqual(bench.source_from_prompt(prompt), "hello 1500")

    def test_source_with_fence_characters_does_not_break_recovery(self):
        prompt = nl.build_prompt("line\n---\nmore")
        self.assertIn("line", prompt)


class ParseTests(unittest.TestCase):
    def test_json_surrounded_by_chat_is_parsed(self):
        reply = 'Sure! Here you go:\n{"candidates": [{"field": "item", "value": "a", "quote": "a"}]}\nHope that helps.'
        self.assertEqual(len(nl.parse_candidates(reply)), 1)

    def test_unparseable_reply_yields_nothing(self):
        for reply in ("no json here", "", None, "{not json}", '{"candidates": "nope"}', "[]"):
            self.assertEqual(nl.parse_candidates(reply), [])

    def test_non_dict_entries_dropped(self):
        reply = '{"candidates": ["x", {"field": "item", "value": "a", "quote": "a"}]}'
        self.assertEqual(len(nl.parse_candidates(reply)), 1)


class NormalizeTests(unittest.TestCase):
    def test_grounded_field_survives(self):
        reply = json.dumps({"candidates": [
            {"field": "unit_price", "value": "1500", "quote": "INR 1500 per session"}]})
        result = nl.normalize("We can do INR 1500 per session.", replay(reply))
        self.assertEqual(result["terms"], {"unit_price": "1500"})
        self.assertEqual(result["text"], "unit_price: 1500")

    def test_invented_field_never_reaches_output(self):
        reply = json.dumps({"candidates": [
            {"field": "unit_price", "value": "99999", "quote": "the price is 99999"}]})
        result = nl.normalize("No price has been discussed.", replay(reply))
        self.assertEqual(result["terms"], {})
        self.assertEqual(result["text"], "")
        self.assertEqual(result["summary"]["inventions"], 1)

    def test_unknown_field_names_dropped_before_verification(self):
        reply = json.dumps({"candidates": [
            {"field": "secret_discount", "value": "50", "quote": "50"}]})
        result = nl.normalize("50", replay(reply))
        self.assertEqual(result["records"], [])

    def test_silent_model_yields_empty_not_error(self):
        result = nl.normalize("Some message.", replay("I cannot help with that."))
        self.assertEqual(result["terms"], {})

    def test_empty_source_rejected(self):
        with self.assertRaises(ValueError):
            nl.normalize("   ", replay("{}"))

    def test_output_feeds_the_deterministic_engine_unchanged(self):
        reply = json.dumps({"candidates": [
            {"field": "item", "value": "design review", "quote": "design review"},
            {"field": "quantity", "value": "2", "quote": "2 sessions"},
            {"field": "unit", "value": "session", "quote": "2 sessions"},
            {"field": "currency", "value": "INR", "quote": "INR 1500"},
            {"field": "unit_price", "value": "1500", "quote": "INR 1500"},
        ]})
        source = "Quote for design review, 2 sessions at INR 1500 each."
        result = nl.normalize(source, replay(reply))
        values, evidence, warnings = core.extract(result["text"])
        self.assertEqual(values["unit_price"], "1500")
        self.assertEqual(values["item"], "design review")
        self.assertEqual(warnings, [])
        self.assertTrue(evidence)


class PayloadTests(unittest.TestCase):
    def setUp(self):
        self.payload = {"schema_version": 1, "deals": [{
            "deal_id": "D1", "buyer": "Buyer One", "seller": "Seller One",
            "messages": [{"message_id": "m1", "speaker": "buyer",
                          "text": "We can pay INR 1500 per session for 2 sessions of design review."}],
        }]}
        self.reply = json.dumps({"candidates": [
            {"field": "unit_price", "value": "1500", "quote": "INR 1500 per session"},
            {"field": "currency", "value": "INR", "quote": "INR 1500 per session"},
        ]})

    def test_strict_payload_is_accepted_by_core(self):
        strict, audit = nl.normalize_payload(self.payload, replay(self.reply))
        result = core.brief(strict)
        terms = result["deals"][0]["messages"][0]["terms"]
        self.assertEqual(terms["unit_price"], "1500")
        self.assertEqual(audit["deals"][0]["messages"][0]["message_id"], "m1")

    def test_audit_keeps_the_original_text(self):
        _, audit = nl.normalize_payload(self.payload, replay(self.reply))
        self.assertIn("design review", audit["deals"][0]["messages"][0]["original_text"])

    def test_bad_payload_rejected(self):
        with self.assertRaises(ValueError):
            nl.normalize_payload({"deals_missing": True}, replay(self.reply))


if __name__ == "__main__":
    unittest.main()
