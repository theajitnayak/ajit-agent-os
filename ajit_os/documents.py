"""Invoices and business documents: grounded fields, verified arithmetic, portable proof.

Span grounding stops a model inventing a number. It does not stop a model
quoting the *wrong* number accurately, and on an invoice that is the expensive
failure: the right-looking figure taken from the wrong row.

Arithmetic catches it. If the line items do not sum to the subtotal, or the
subtotal and tax do not reach the total, then something was read from the wrong
place even though every individual figure is quotable. The document has to be
internally consistent as well as individually grounded.

The output is a receipt: a hashed, portable record of which fields were proven,
which checks ran, and whether the document is safe to post without a human.
"""
import hashlib
import json
from decimal import Decimal

from . import grounding

REQUIRED_FIELDS = ("invoice_number", "invoice_date", "vendor", "total")
OPTIONAL_FIELDS = ("subtotal", "tax", "discount", "currency", "due_date",
                   "po_number", "buyer")
FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

MONEY_FIELDS = frozenset({"total", "subtotal", "tax", "discount"})
DATE_FIELDS = frozenset({"invoice_date", "due_date"})
ITEM_FIELDS = ("description", "quantity", "unit_price", "amount")
ITEM_NUMERIC = frozenset({"quantity", "unit_price", "amount"})

#: Invoices round. A cent of slack is realism, not laxity.
DEFAULT_TOLERANCE = Decimal("0.01")

PASSED = "passed"
FAILED = "failed"
SKIPPED = "skipped"


def verify_fields(source, candidates):
    """Ground every proposed document field against the source."""
    allowed = [item for item in candidates
               if isinstance(item, dict) and item.get("field") in FIELDS]
    return grounding.verify_all(source, allowed, MONEY_FIELDS, DATE_FIELDS)


def verify_line_items(source, items):
    """Ground each line item. Returns one record list per row."""
    grounded = []
    for index, item in enumerate(items if isinstance(items, list) else []):
        candidates = [entry for entry in (item or {}).get("candidates", [])
                      if isinstance(entry, dict) and entry.get("field") in ITEM_FIELDS]
        grounded.append({
            "row": index + 1,
            "records": grounding.verify_all(source, candidates, ITEM_NUMERIC),
        })
    return grounded


def _amount(terms, field):
    raw = terms.get(field)
    if raw is None:
        return None
    try:
        value = Decimal(raw)
    except Exception:
        return None
    return value if value.is_finite() else None


def _check(name, expected, found, tolerance, detail):
    if expected is None or found is None:
        return {"check": name, "status": SKIPPED, "expected": None, "found": None,
                "detail": detail}
    difference = abs(expected - found)
    return {
        "check": name,
        "status": PASSED if difference <= tolerance else FAILED,
        "expected": str(expected), "found": str(found), "difference": str(difference),
        "detail": detail,
    }


def check_arithmetic(terms, line_items, tolerance=DEFAULT_TOLERANCE):
    """Does the document agree with itself?

    Every check is skipped rather than guessed when an input is missing. A
    skipped check is not a pass, and the verdict treats it that way.
    """
    checks = []
    rows = []
    for row in line_items:
        values = grounding.accepted_terms(row["records"])
        rows.append((row["row"], values))
        quantity = _amount(values, "quantity")
        unit_price = _amount(values, "unit_price")
        amount = _amount(values, "amount")
        checks.append(_check(
            f"line_{row['row']}_extends",
            quantity * unit_price if (quantity is not None and unit_price is not None) else None,
            amount, tolerance,
            f"Row {row['row']}: quantity times unit price should equal the line amount."))

    amounts = [_amount(values, "amount") for _, values in rows]
    line_sum = sum(amounts) if amounts and all(value is not None for value in amounts) else None

    subtotal = _amount(terms, "subtotal")
    tax = _amount(terms, "tax")
    discount = _amount(terms, "discount")
    total = _amount(terms, "total")

    checks.append(_check("lines_sum_to_subtotal", line_sum, subtotal, tolerance,
                         "Line amounts should sum to the subtotal."))

    base = subtotal if subtotal is not None else line_sum
    expected_total = None
    if base is not None:
        expected_total = base + (tax or Decimal(0)) - (discount or Decimal(0))
    checks.append(_check("subtotal_plus_tax_equals_total", expected_total, total, tolerance,
                         "Subtotal plus tax minus discount should equal the total."))
    return checks


def assess(field_records, line_items, checks):
    """Can this document be posted without a human reading it?

    The bar is deliberately high. Anything unproven, inconsistent or merely
    unchecked sends the document to review.
    """
    terms = grounding.accepted_terms(field_records)
    reasons = []

    missing = [field for field in REQUIRED_FIELDS if field not in terms]
    if missing:
        reasons.append("Required fields not proven: " + ", ".join(missing))

    rejected = [record for record in field_records if record["status"] == "rejected"]
    for record in rejected:
        reasons.append(f"{record['field']}: {record['reason']}")

    for row in line_items:
        for record in row["records"]:
            if record["status"] == "rejected":
                reasons.append(f"row {row['row']} {record['field']}: {record['reason']}")

    failed = [check for check in checks if check["status"] == FAILED]
    for check in failed:
        reasons.append(f"{check['check']}: expected {check['expected']}, document says {check['found']}")

    ran = [check for check in checks if check["status"] != SKIPPED]
    if not ran:
        reasons.append("No arithmetic check could run, so internal consistency is unverified.")

    cautions = [note for record in field_records for note in record["cautions"]]
    if cautions:
        reasons.append(f"{len(cautions)} field(s) carry a caution.")

    return {"auto_post": not reasons, "reasons": reasons,
            "checks_run": len(ran), "checks_failed": len(failed)}


def receipt(source, field_records, line_items, checks, verdict, issued_at=None):
    """A portable record of what was proven. Hash the source so it cannot be swapped."""
    def public(record):
        return {"field": record["field"], "value": record["value"],
                "status": record["status"], "reason": record["reason"],
                "line": record["line"], "quote": record["span"],
                "cautions": record["cautions"]}

    return {
        "schema_version": 1,
        "document_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "issued_at": issued_at,
        "fields": [public(record) for record in field_records],
        "line_items": [{"row": row["row"], "fields": [public(r) for r in row["records"]]}
                       for row in line_items],
        "arithmetic": checks,
        "verdict": verdict,
        "note": "Proves each value appears in this document and that the document agrees "
                "with itself. Does not prove the document is genuine, authorised or owed.",
    }


def process(source, proposal, tolerance=DEFAULT_TOLERANCE, issued_at=None):
    """Full pass: ground the fields, check the arithmetic, issue the receipt."""
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a nonempty string")
    if not isinstance(proposal, dict):
        raise ValueError("proposal must be a dict with candidates and line_items")
    field_records = verify_fields(source, proposal.get("candidates", []))
    line_items = verify_line_items(source, proposal.get("line_items", []))
    terms = grounding.accepted_terms(field_records)
    checks = check_arithmetic(terms, line_items, tolerance)
    verdict = assess(field_records, line_items, checks)
    return receipt(source, field_records, line_items, checks, verdict, issued_at)


def render(issued):
    """Short human summary of a receipt."""
    verdict = issued["verdict"]
    lines = ["# Document receipt", "",
             f"SHA-256: `{issued['document_sha256'][:16]}...`",
             "",
             f"## {'SAFE TO POST' if verdict['auto_post'] else 'NEEDS REVIEW'}", ""]
    if verdict["reasons"]:
        lines += [f"- {reason}" for reason in verdict["reasons"]] + [""]
    proven = [record for record in issued["fields"] if record["status"] == "accepted"]
    if proven:
        lines += ["| Field | Value | Line |", "| --- | --- | --- |"]
        lines += [f"| {record['field']} | {record['value']} | {record['line']} |"
                  for record in proven]
        lines.append("")
    lines += [f"Arithmetic: {verdict['checks_run']} checks ran, "
              f"{verdict['checks_failed']} failed.", ""]
    for check in issued["arithmetic"]:
        if check["status"] == FAILED:
            lines.append(f"- FAILED `{check['check']}`: expected {check['expected']}, "
                         f"document says {check['found']}")
    return "\n".join(lines)


def as_json(issued):
    return json.dumps(issued, indent=2, ensure_ascii=True)


def _cli(argv=None):
    import argparse
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(
        prog="python -m ajit_os.documents",
        description="Prove every field against the document and check that it adds up.")
    parser.add_argument("document", type=Path, help="The source text")
    parser.add_argument("proposal", type=Path, help="What a model proposed, as JSON")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--tolerance", default=str(DEFAULT_TOLERANCE))
    args = parser.parse_args(argv)
    try:
        source = args.document.read_text(encoding="utf-8-sig")
        proposal = json.loads(args.proposal.read_text(encoding="utf-8-sig"))
        issued = process(source, proposal, Decimal(args.tolerance))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    print(as_json(issued) if args.format == "json" else render(issued))
    return 0 if issued["verdict"]["auto_post"] else 1


if __name__ == "__main__":
    import sys

    sys.exit(_cli())
