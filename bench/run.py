"""Run the Ghost Fields benchmark against a model, or against an offline stand-in.

Offline, no key needed:
    python bench/run.py --stub strict
    python bench/run.py --stub greedy --format json

Against a real model:
    python bench/run.py --provider ollama --model qwen2.5:7b
    python bench/run.py --provider deepseek --model deepseek-flash

Only the benchmark messages are sent. They are fictional.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from ajit_os import bench, providers  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Score a model on invented values")
    parser.add_argument("--provider", choices=sorted(providers.PROVIDERS))
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--stub", choices=("strict", "greedy", "fabricating"),
                        help="Run offline against a stand-in instead of a provider")
    parser.add_argument("--cases", type=Path, default=None)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    if bool(args.stub) == bool(args.provider):
        print("Choose exactly one of --stub or --provider", file=sys.stderr)
        return 2

    if args.stub:
        call, label = bench.stub_call(args.stub), f"stub:{args.stub}"
    else:
        label = f"{args.provider}:{args.model or 'default'}"

        def call(prompt):
            return providers.chat(prompt, provider=args.provider, model=args.model,
                                  base_url=args.base_url, timeout=args.timeout)

    try:
        cases = bench.load_cases(args.cases)
    except (ValueError, OSError) as exc:
        print(f"Cases error: {exc}", file=sys.stderr)
        return 2

    metrics, results = bench.score(cases, call)
    if args.format == "json":
        print(json.dumps({"label": label, "metrics": metrics, "results": results},
                         indent=2, ensure_ascii=True))
    else:
        print(bench.render(label, metrics, results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
