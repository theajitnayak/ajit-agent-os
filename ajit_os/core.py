"""Strict, offline deal briefs. Source documents are data, never instructions."""
import hashlib
import html
import json
import re
from decimal import Decimal, InvalidOperation

FIELDS = ("item", "quantity", "unit", "currency", "unit_price")
KEYS = set(FIELDS) | {"intent"}
INTENTS = {"request", "offer", "accept", "reject"}


def positive(value):
    if not re.fullmatch(r"[0-9]{1,18}(?:\.[0-9]{1,8})?", value):
        raise ValueError("Expected decimal digits (at most 18 integer and 8 fractional digits)")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError("Expected a positive decimal") from None
    if not number.is_finite() or number <= 0:
        raise ValueError("Expected a finite positive decimal")
    return format(number.normalize(), "f")


def extract(text):
    """Only accept explicit key: value lines; never guess terms from prose."""
    values, evidence, warnings = {}, {}, []
    duplicates = set()
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"\s*([a-z_]+)\s*:\s*(.*?)\s*", line)
        if not match or match[1] not in KEYS:
            warnings.append(f"Line {line_no}: unparsed text requires human review")
            continue
        key, value = match[1], match[2]
        if key in values or key in duplicates:
            duplicates.add(key)
            warnings.append(f"Line {line_no}: duplicate {key}; field withheld")
            values.pop(key, None)
            evidence.pop(key, None)
            continue
        if not value:
            warnings.append(f"Line {line_no}: empty {key}")
            continue
        try:
            if key in {"quantity", "unit_price"}:
                value = positive(value)
            elif key == "currency":
                if value not in {"INR", "USD", "EUR", "GBP"}:
                    raise ValueError("Unsupported or ambiguous currency")
            elif key == "intent" and value not in INTENTS:
                raise ValueError("Unsupported intent")
        except ValueError as exc:
            warnings.append(f"Line {line_no}: {exc}")
            continue
        values[key] = value
        evidence[key] = {"line": line_no, "quote": line}
    return values, evidence, warnings


def brief(payload):
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "deals"}:
        raise ValueError("Expected schema_version and deals")
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        raise ValueError("Unsupported schema_version")
    if not isinstance(payload["deals"], list) or not payload["deals"]:
        raise ValueError("deals must be a nonempty list")
    ids, output = set(), []
    for deal in payload["deals"]:
        if not isinstance(deal, dict) or set(deal) != {"deal_id", "buyer", "seller", "messages"}:
            raise ValueError("Each deal needs deal_id, buyer, seller and messages")
        for key in ("deal_id", "buyer", "seller"):
            if not isinstance(deal[key], str) or not deal[key].strip():
                raise ValueError(f"Missing {key}")
        if deal["deal_id"] in ids:
            raise ValueError("Duplicate deal_id")
        ids.add(deal["deal_id"])
        if deal["buyer"] == deal["seller"]:
            raise ValueError("Buyer and seller must differ")
        if not isinstance(deal["messages"], list) or not deal["messages"]:
            raise ValueError("messages must be a nonempty ordered list")
        records, seen, latest = [], set(), {}
        for msg in deal["messages"]:
            if not isinstance(msg, dict) or set(msg) != {"message_id", "speaker", "text"}:
                raise ValueError("Each message needs message_id, speaker and text")
            if not isinstance(msg["message_id"], str) or not msg["message_id"].strip():
                raise ValueError("Invalid message_id")
            if msg["message_id"] in seen:
                raise ValueError("Duplicate message_id within deal")
            seen.add(msg["message_id"])
            if not isinstance(msg["speaker"], str) or msg["speaker"] not in {"buyer", "seller"}:
                raise ValueError("speaker must be buyer or seller")
            if not isinstance(msg["text"], str):
                raise ValueError("text must be a string")
            values, evidence, warnings = extract(msg["text"])
            record = {**msg, "terms": values, "evidence": evidence, "warnings": warnings}
            records.append(record)
            latest[msg["speaker"]] = record
        missing, conflicts = [], []
        for role in ("buyer", "seller"):
            terms = latest.get(role, {}).get("terms", {})
            missing.extend(f"{role}.{key}" for key in FIELDS if key not in terms)
        if all(role in latest for role in ("buyer", "seller")):
            a, b = latest["buyer"]["terms"], latest["seller"]["terms"]
            conflicts = [key for key in FIELDS if key in a and key in b and a[key] != b[key]]
        clean = not any(record["warnings"] for record in records)
        matches = not missing and not conflicts and clean
        accepted = matches and all(latest[role]["terms"].get("intent") == "accept" for role in ("buyer", "seller"))
        status = "matching_explicit_acceptances" if accepted else "needs_review"
        output.append({"deal_id": deal["deal_id"], "buyer": deal["buyer"], "seller": deal["seller"],
                       "status": status, "missing": missing, "conflicts": conflicts,
                       "messages": records,
                       "note": "Extraction only. Verify source authenticity and all commercial terms manually."})
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode()
    return {"schema_version": 1, "input_sha256": hashlib.sha256(canonical).hexdigest(), "deals": output}


def safe_text(value):
    value = html.escape(value, quote=True).replace("\n", " ").replace("\r", " ")
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", value)


def render(result):
    lines = ["# Deal briefs", "", "Offline extraction. No legal or commercial approval is implied.", ""]
    for deal in result["deals"]:
        lines += [f"## {safe_text(deal['deal_id'])}", "", f"Buyer: {safe_text(deal['buyer'])} | Seller: {safe_text(deal['seller'])}",
                  f"Status: {deal['status']}", ""]
        for msg in deal["messages"]:
            terms = "; ".join(f"{key}={safe_text(value)}" for key, value in msg["terms"].items()) or "No supported terms"
            lines += [f"- {msg['speaker']} [{safe_text(msg['message_id'])}]: {terms}"]
            lines += [f"  - REVIEW: {warning}" for warning in msg["warnings"]]
        lines += ["", "Missing: " + (", ".join(deal["missing"]) or "none"),
                  "Conflicts: " + (", ".join(deal["conflicts"]) or "none"), ""]
    return "\n".join(lines)
