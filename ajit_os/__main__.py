import argparse
import json
import sys
from pathlib import Path
from . import nl, providers
from .core import brief, render


def main():
    parser = argparse.ArgumentParser(description="Create evidence-linked deal briefs offline")
    parser.add_argument("input", type=Path)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--normalize", action="store_true",
                        help="Read messages as ordinary text and verify every field a model proposes")
    parser.add_argument("--provider", choices=sorted(providers.PROVIDERS), default="ollama")
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--audit", type=Path,
                        help="Write the accept and reject record for every proposed field")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8-sig"))
        if args.normalize:
            def call(prompt):
                return providers.chat(prompt, provider=args.provider, model=args.model,
                                      base_url=args.base_url)

            payload, audit = nl.normalize_payload(payload, call)
            if args.audit:
                args.audit.write_text(json.dumps(audit, indent=2, ensure_ascii=True), encoding="utf-8")
        result = brief(payload)
        print(json.dumps(result, indent=2, ensure_ascii=True) if args.format == "json" else render(result))
    except (ValueError, OSError, providers.ProviderError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
