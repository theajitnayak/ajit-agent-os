import argparse
import json
import sys
from pathlib import Path
from .core import brief, render


def main():
    parser = argparse.ArgumentParser(description="Create evidence-linked deal briefs offline")
    parser.add_argument("input", type=Path)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args()
    try:
        result = brief(json.loads(args.input.read_text(encoding="utf-8-sig")))
        print(json.dumps(result, indent=2, ensure_ascii=True) if args.format == "json" else render(result))
    except (ValueError, OSError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
