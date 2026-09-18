# Changelog

## 0.2.0 - 2026-09-19

Natural-language input, with verification standing between the model and the output.

- Added span grounding: every proposed field must cite text that exists in the
  source and that literally contains the value. Unsupported claims are dropped,
  never silently accepted.
- Added instruction-shaped span detection, so a planted command inside a document
  is withheld rather than obeyed even when the quote is technically grounded.
- Added number reading that handles Indian lakh grouping and refuses ambiguous
  forms such as `1.500` instead of guessing a convention.
- Added cautions for negated, withdrawn and hedged figures.
- Added an OpenAI-compatible client covering DeepSeek, Qwen, GLM, MiniMax,
  SiliconFlow, OpenRouter and local Ollama, standard library only.
- Added the Ghost Fields benchmark: 16 adversarial cases, four metrics and three
  offline stand-in models, so it runs in CI with no key and no network.
- Added `--normalize` and `--audit` to the CLI, and a grounding CLI that exits
  non-zero on unsupported claims for use as a pipeline gate.
- Added a Claude Code plugin manifest and the `ghost-fields` skill.
- Documented the known limits, including the case verification cannot catch:
  a true quotation of the wrong sentence.

The deterministic engine from 0.1.0 is unchanged. It gained a way to be fed.

## 0.1.0 - 2026-09-18

- Added offline evidence-linked deal briefs with separate counterparty records.
- Added conservative missing-field and conflict handling.
- Added Windows setup, fictional examples and behavioral regression tests.
- Added original role instructions, workflow skill and research roadmap.
- Added CI for Windows and Linux on Python 3.10 and 3.12.

No ECC components were copied. No external AI or self-improvement loop is enabled.
