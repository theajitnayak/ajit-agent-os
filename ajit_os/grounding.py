"""Span grounding. A field survives only if the source literally supports it.

The model proposes, this module disposes. Every proposed field must cite a span
that appears verbatim in the source, and that span must literally contain the
claimed value. A value the source never stated cannot reach the output.

Nothing here interprets the source as an instruction. Spans are matched, never
executed. Instruction-shaped spans are withheld rather than obeyed, because a
grounded quote is not the same thing as a trustworthy one.
"""
import re
import unicodedata
from datetime import date as _date
from decimal import Decimal, InvalidOperation

NUMERIC_FIELDS = frozenset({"quantity", "unit_price"})

QUOTE_ABSENT = "quote_not_in_source"
VALUE_ABSENT = "value_not_in_quote"
UNTRUSTED_SPAN = "untrusted_span"
AMBIGUOUS_NUMBER = "ambiguous_number"
AMBIGUOUS_DATE = "ambiguous_date"
MALFORMED = "malformed_candidate"
CONTRADICTED = "contradicted_by_sibling"

#: Rejections that mean the model asserted something the source does not say.
INVENTION_REASONS = frozenset({QUOTE_ABSENT, VALUE_ABSENT})

_INSTRUCTION_PATTERNS = tuple(re.compile(pattern) for pattern in (
    r"ignore (?:all |any |the )?(?:previous|prior|above|earlier|preceding)",
    r"disregard (?:all |any |the )?(?:previous|prior|above|earlier|preceding)",
    r"forget (?:everything|all|your|the|previous)",
    r"(?:new|updated|revised|real|actual) (?:instruction|rule|system prompt|task)",
    r"system prompt",
    r"you are (?:now )?(?:a|an|the) ",
    r"act as (?:a|an|the) ",
    r"pretend (?:to be|you)",
    r"(?:respond|reply|answer|output|return|print|say|extract) (?:with|only|exactly|the following)",
    r"do not (?:mention|reveal|tell|report|flag|warn|include)",
    r"override",
    r"set (?:the )?[a-z_ ]{0,24}(?:price|amount|total|quantity|value) to",
    r"developer mode",
    r"jailbreak",
    r"</?(?:system|instruction|prompt)>",
))

_NEGATION_PATTERNS = tuple(re.compile(pattern) for pattern in (
    r"\bnot\b", r"n't\b", r"\bcannot\b", r"\bno longer\b", r"\bnever\b",
    r"\binstead of\b", r"\brather than\b", r"\bpreviously\b", r"\bused to\b",
    r"\bwithdraw", r"\bcancel", r"\bexpired\b", r"\bdeclin", r"\bretract",
))

_HEDGE_PATTERNS = tuple(re.compile(pattern) for pattern in (
    r"\bmaybe\b", r"\bperhaps\b", r"\broughly\b", r"\baround\b", r"\babout\b",
    r"\bapproximate", r"\bestimate", r"\bballpark\b", r"\btbd\b", r"~",
    r"\bup to\b", r"\bstarting (?:at|from)\b", r"\bor so\b",
))

_PLAIN = re.compile(r"\A[0-9]+(?:\.[0-9]+)?\Z")
_COMMA_GROUPED = re.compile(r"\A[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?\Z")
#: Indian grouping: a final group of three, earlier groups of two. "1,25,000" is 125000.
_INDIAN_GROUPED = re.compile(r"\A[0-9]{1,2}(?:,[0-9]{2})+,[0-9]{3}(?:\.[0-9]+)?\Z")
_DOT_GROUPED = re.compile(r"\A[0-9]{1,3}(?:\.[0-9]{3}){2,}\Z")
_DOT_AMBIGUOUS = re.compile(r"\A[0-9]{1,3}\.[0-9]{3}\Z")
_NUMBER_TOKEN = re.compile(r"[0-9][0-9,.]*[0-9]|[0-9]")


def _fold(text):
    """Collapse to a comparable form and map each output char to a source offset."""
    chars, offsets = [], []
    pending_space = False
    for offset, char in enumerate(text):
        for produced in unicodedata.normalize("NFKC", char).casefold():
            if produced.isspace():
                pending_space = True
                continue
            if pending_space and chars:
                chars.append(" ")
                offsets.append(offset)
            pending_space = False
            chars.append(produced)
            offsets.append(offset)
    return "".join(chars), offsets


def _decimal(text):
    try:
        number = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def read_number(token):
    """Return (possible values, ambiguous). Ambiguous digits are never accepted silently."""
    token = token.strip(".,")
    if not token:
        return [], True
    if _DOT_AMBIGUOUS.match(token):
        # "1.500" is 1.5 in one convention and 1500 in another. Refuse to pick.
        both = [_decimal(token), _decimal(token.replace(".", ""))]
        return [value for value in both if value is not None], True
    if _DOT_GROUPED.match(token):
        value = _decimal(token.replace(".", ""))
        return ([value] if value is not None else []), False
    if _COMMA_GROUPED.match(token) or _INDIAN_GROUPED.match(token):
        value = _decimal(token.replace(",", ""))
        return ([value] if value is not None else []), False
    if _PLAIN.match(token):
        value = _decimal(token)
        return ([value] if value is not None else []), False
    return [], True


_MONTHS = {name: number for number, names in enumerate((
    ("jan", "january"), ("feb", "february"), ("mar", "march"), ("apr", "april"),
    ("may",), ("jun", "june"), ("jul", "july"), ("aug", "august"),
    ("sep", "sept", "september"), ("oct", "october"), ("nov", "november"),
    ("dec", "december")), start=1) for name in names}

_ISO_DATE = re.compile(r"\A([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})\Z")
_SLASHED_DATE = re.compile(r"\A([0-9]{1,4})[/.-]([0-9]{1,2})[/.-]([0-9]{1,4})\Z")
_DAY_FIRST_TEXT = re.compile(r"\A([0-9]{1,2})\s+([a-z]{3,9})\.?,?\s+([0-9]{4})\Z", re.IGNORECASE)
_MONTH_FIRST_TEXT = re.compile(r"\A([a-z]{3,9})\.?\s+([0-9]{1,2})(?:st|nd|rd|th)?,?\s+([0-9]{4})\Z", re.IGNORECASE)

_DATE_TOKEN = re.compile(
    r"[0-9]{4}[/.-][0-9]{1,2}[/.-][0-9]{1,2}"
    r"|[0-9]{1,2}[/.-][0-9]{1,2}[/.-][0-9]{2,4}"
    r"|[0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]{3,9}\.?,?\s+[0-9]{4}"
    r"|[A-Za-z]{3,9}\.?\s+[0-9]{1,2}(?:st|nd|rd|th)?,?\s+[0-9]{4}",
    re.IGNORECASE)


def _iso(year, month, day):
    try:
        return _date(int(year), int(month), int(day)).isoformat()
    except ValueError:
        return None


def read_date(token):
    """Return (possible ISO dates, ambiguous).

    `03/04/2026` is 3 April or 4 March depending on where you live. There is no
    safe default, so both readings are returned and the caller refuses to pick.
    Two-digit years are ambiguous in the century and are never resolved.
    """
    token = token.strip().rstrip(".,")
    if not token:
        return [], True

    match = _ISO_DATE.match(token)
    if match:
        value = _iso(*match.groups())
        return ([value] if value else []), False

    for pattern, order in ((_DAY_FIRST_TEXT, "dmy"), (_MONTH_FIRST_TEXT, "mdy")):
        match = pattern.match(token)
        if match:
            day, name, year = match.groups() if order == "dmy" else (
                match.group(2), match.group(1), match.group(3))
            month = _MONTHS.get(name.lower())
            value = _iso(year, month, day) if month else None
            return ([value] if value else []), False

    match = _SLASHED_DATE.match(token)
    if match:
        first, second, third = match.groups()
        if len(first) == 4:                       # year first, unambiguous
            value = _iso(first, second, third)
            return ([value] if value else []), False
        if len(third) != 4:                       # two-digit year, century unknown
            return [], True
        day_first = _iso(third, second, first)    # DD/MM/YYYY
        month_first = _iso(third, first, second)  # MM/DD/YYYY
        readings = [value for value in (day_first, month_first) if value]
        if not readings:
            return [], True
        if day_first and month_first and day_first != month_first:
            return readings, True                 # both plausible, refuse to choose
        return readings[:1], False
    return [], True


def _date_support(value, span):
    """A date field is supported only when the span names that exact day, unambiguously."""
    if not _ISO_DATE.match(value) or _iso(*_ISO_DATE.match(value).groups()) != value:
        return MALFORMED
    ambiguous_hit = False
    for token in _DATE_TOKEN.findall(span):
        readings, ambiguous = read_date(token)
        if value in readings:
            if ambiguous:
                ambiguous_hit = True
                continue
            return None
    return AMBIGUOUS_DATE if ambiguous_hit else VALUE_ABSENT


def instruction_shaped(folded_span):
    """True when the span reads as a command to the reader rather than as deal text."""
    return any(pattern.search(folded_span) for pattern in _INSTRUCTION_PATTERNS)


def _cautions(folded_span):
    notes = []
    if any(pattern.search(folded_span) for pattern in _NEGATION_PATTERNS):
        notes.append("span contains negation or withdrawal language; confirm the value still stands")
    if any(pattern.search(folded_span) for pattern in _HEDGE_PATTERNS):
        notes.append("span contains hedging language; the value may be indicative only")
    return notes


def _numeric_support(value, span, allow_zero=False):
    target = _decimal(value) if _PLAIN.match(value) else None
    if target is None or target < 0 or (target == 0 and not allow_zero):
        return MALFORMED, []
    ambiguous_hit = False
    for token in _NUMBER_TOKEN.findall(span):
        values, ambiguous = read_number(token)
        if target in values:
            if ambiguous:
                ambiguous_hit = True
                continue
            return None, []
    return (AMBIGUOUS_NUMBER if ambiguous_hit else VALUE_ABSENT), []


def verify(source, candidate, numeric_fields=NUMERIC_FIELDS, date_fields=frozenset()):
    """Check one proposed field against the source. Returns a decision record."""
    field = candidate.get("field") if isinstance(candidate, dict) else None
    value = candidate.get("value") if isinstance(candidate, dict) else None
    quote = candidate.get("quote") if isinstance(candidate, dict) else None
    record = {"field": field, "value": value, "quote": quote, "status": "rejected",
              "reason": None, "line": None, "span": None, "cautions": []}

    if not all(isinstance(part, str) and part.strip() for part in (field, value, quote)):
        record["reason"] = MALFORMED
        return record

    folded_source, offsets = _fold(source)
    folded_quote, _ = _fold(quote)
    if not folded_quote:
        record["reason"] = MALFORMED
        return record

    position = folded_source.find(folded_quote)
    if position < 0:
        record["reason"] = QUOTE_ABSENT
        return record

    start = offsets[position]
    end = offsets[position + len(folded_quote) - 1]
    span = source[start:end + 1]
    record["span"] = span
    record["line"] = source.count("\n", 0, start) + 1

    # Judge the source text itself, not the model's transcription of it.
    folded_span, _ = _fold(span)
    if instruction_shaped(folded_span):
        record["reason"] = UNTRUSTED_SPAN
        return record

    if field in date_fields:
        reason = _date_support(value, span)
        if reason:
            record["reason"] = reason
            return record
    elif field in numeric_fields:
        reason, _ = _numeric_support(value, span, allow_zero=field == "unit_price")
        if reason:
            record["reason"] = reason
            return record
    else:
        folded_value, _ = _fold(value)
        if not folded_value or folded_value not in folded_span:
            record["reason"] = VALUE_ABSENT
            return record

    record["status"] = "accepted"
    record["cautions"] = _cautions(folded_span)
    return record


def verify_all(source, candidates, numeric_fields=NUMERIC_FIELDS, date_fields=frozenset()):
    """Verify every candidate, then withhold fields claimed twice with different values."""
    if not isinstance(candidates, list):
        return []
    records = [verify(source, candidate, numeric_fields, date_fields) for candidate in candidates]
    claimed = {}
    for record in records:
        if record["status"] == "accepted":
            claimed.setdefault(record["field"], set()).add(record["value"])
    for record in records:
        if record["status"] == "accepted" and len(claimed.get(record["field"], ())) > 1:
            record["status"] = "rejected"
            record["reason"] = CONTRADICTED
    return records


def accepted_terms(records):
    """Field to value for everything that survived verification."""
    return {record["field"]: record["value"] for record in records if record["status"] == "accepted"}


def canonical_text(records, fields):
    """Render survivors as the strict `key: value` lines that core.extract accepts."""
    terms = accepted_terms(records)
    return "\n".join(f"{field}: {terms[field]}" for field in fields if field in terms)


def _cli(argv=None):
    import argparse
    import json
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(
        prog="python -m ajit_os.grounding",
        description="Check proposed fields against the source that is supposed to support them.")
    parser.add_argument("source", type=Path, help="File holding the original text")
    parser.add_argument("candidates", type=Path,
                        help='JSON list of {"field","value","quote"} objects')
    args = parser.parse_args(argv)
    try:
        source = args.source.read_text(encoding="utf-8-sig")
        proposed = json.loads(args.candidates.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    records = verify_all(source, proposed)
    print(json.dumps({"summary": summary(records), "records": records},
                     indent=2, ensure_ascii=True))
    return 1 if summary(records)["inventions"] else 0


def summary(records):
    """Counts for reporting and benchmarking."""
    reasons = {}
    for record in records:
        if record["status"] == "rejected":
            reasons[record["reason"]] = reasons.get(record["reason"], 0) + 1
    return {
        "proposed": len(records),
        "accepted": sum(1 for record in records if record["status"] == "accepted"),
        "rejected": sum(1 for record in records if record["status"] == "rejected"),
        "inventions": sum(1 for record in records if record["reason"] in INVENTION_REASONS),
        "cautions": sum(len(record["cautions"]) for record in records),
        "reasons": reasons,
    }


if __name__ == "__main__":
    import sys

    sys.exit(_cli())
