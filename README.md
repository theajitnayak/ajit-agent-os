# Ajit Agent OS

Evidence-first workflow experiments for a solo operator.

Version 0.1.0 is a working offline deal-brief organizer. It keeps buyer and seller records separate, preserves source evidence and flags missing or conflicting terms. It requires Python 3.10+ and has no third-party runtime dependencies.

## Run on Windows

From this repository folder in PowerShell:

```powershell
.\setup.ps1
```

If your PowerShell policy blocks scripts, run Python directly. No policy change is needed:

```powershell
python -m unittest discover -s tests -v
python -m ajit_os examples/fictional-deals.json
python -m ajit_os examples/fictional-deals.json --format json
```

If Python is installed under a custom path, pass it to `setup.ps1 -Python 'C:\path\python.exe'`.

## What the demo proves

- DEMO-A preserves a buyer request of INR 1500 per session and a seller offer of INR 1800. It reports a price conflict.
- DEMO-B has no quoted price. It leaves the price missing instead of copying a price from DEMO-A.
- Neither deal is marked accepted.
- JSON output includes message IDs, exact evidence lines and a digest of the input.

All examples are fictional. No external services, model calls or messages are sent.

## Input contract

Use the example JSON as the schema. Messages are ordered oldest to newest within each deal. Identify each message's speaker explicitly as buyer or seller. The parser accepts explicit lines for `item`, `quantity`, `unit`, `currency`, `unit_price` and `intent`.

Supported intents: request, offer, accept, reject. Supported currencies: INR, USD, EUR, GBP. Currency conversion is not implemented. Numbers must be positive finite decimals without commas. Each party's latest message must restate all terms; older partial terms are never silently combined. Comparison of item and unit text is case-sensitive.

Arbitrary conversation text is preserved and flagged for review. This version is deliberately a constrained extractor, not a natural-language AI agent. Manually normalize conversations into the supported format and verify them against the original before relying on results. Any future model-generated normalization must remain a reviewable candidate.

Matching explicit acceptances only describes the supplied text. It does not establish authenticity, payment, enforceability or a completed deal. Extra commercial terms require human review. Source text is untrusted data and cannot instruct the program.

## Project layout

- `ajit_os/`: executable parser and CLI
- `tests/`: offline behavioral checks
- `examples/`: fictional input
- `agents/`: optional role instructions
- `skills/`: original workflow instructions
- `docs/`: PRD, research map, evaluation process and ECC notes
- `.github/workflows/`: Windows and Linux verification

## Roadmap

1. Current: constrained extraction and executable checks.
2. Next: reviewed natural-language extraction with evidence validation and a held-out evaluation set.
3. Later: local failure memory and proposed workflow changes reviewed through pull requests.

No autonomous self-improvement, model fine-tuning, automatic negotiation or free-plan eligibility is claimed. Unit tests are not evidence of real-world accuracy.

## Inspiration

[Affaan Mustafa's ECC](https://github.com/affaan-m/ECC), [Reflexion](https://github.com/noahshinn024/reflexion) and research listed in `docs/research.md` informed the roadmap. This repository is an independent implementation. It does not vendor ECC code or install ECC automatically.

MIT licensed. See LICENSE, CONTRIBUTING.md and SECURITY.md.
