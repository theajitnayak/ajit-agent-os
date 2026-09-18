# Ghost Fields

**How often does a model report a value the document never contained?**

That is the only question this benchmark asks. It is a narrow question on
purpose, because it is the one that decides whether extracted data can be
trusted without a human re-reading the source.

## Run it

Offline, no key, no cost:

```bash
python bench/run.py --stub strict
```

Against a local model:

```bash
ollama serve
python bench/run.py --provider ollama --model qwen2.5:7b
```

Against a hosted model:

```bash
export DEEPSEEK_API_KEY=...
python bench/run.py --provider deepseek --model deepseek-flash
```

`--format json` gives the full per-case record for analysis.

## What is measured

| Metric | Meaning |
| --- | --- |
| Grounded recall | Values that were present and were found |
| **Invention rate** | Values that were absent and were asserted anyway |
| Refusal accuracy | Fields correctly left empty |
| Injection resistance | Planted commands that were not obeyed |

**Invention rate is the headline.** Recall is easy to buy by guessing, so a
recall number on its own tells you almost nothing. A model that answers
everything scores well on recall and is useless.

## The cases

Sixteen hand-written business messages, all fictional, grouped by what makes
them hard:

- `grounded` the value is plainly stated, including Indian lakh grouping
- `absent` no value exists and the correct answer is silence
- `trap` something that looks like an answer but is not: an ambiguous decimal,
  a currency symbol rather than a code, a dropped zero, another party's rate,
  enthusiasm mistaken for acceptance
- `injection` a planted instruction sitting inside the document
- `superseded` a figure that was refused or revised in the same message
- `hedged` an indicative number that must arrive labelled as indicative

Each case states what must be extracted and what must not. A case that asserts
nothing is rejected by the loader, so no case can be quietly toothless.

## Reading the stub results

Three offline stand-ins ship with the benchmark. They are controls, not
contenders, and their low recall is the point.

| Stub | Recall | Invention rate | What it demonstrates |
| --- | --- | --- | --- |
| `fabricating` | 0% | 0% | Asserts a price on every case with a fabricated quote. **Not one value survives verification.** |
| `greedy` | 21.4% | 25.0% | Grabs the first number it sees and cites it accurately. Its quotes are real, so grounding cannot stop it. |
| `strict` | 7.1% | 0% | Reads only explicit `key: value` lines. Never wrong, rarely useful. |

Measured on 2026-09-19, reproducible with `python bench/run.py --stub <name>`.

The `fabricating` and `greedy` rows are the whole argument for this project.
Verification reduces a fabricating model to harmless. It does nothing at all
about a model that cites real text and draws the wrong conclusion from it. Those
two failure modes need different defences, and conflating them is how extraction
pipelines end up trusted more than they deserve.

## What a score does not mean

A result describes **a model plus this verifier**, never a model alone. Nobody
should quote these numbers as a property of a model.

Sixteen hand-written cases is a small sample. It is enough to expose a failure
mode and not enough to rank models confidently. Growing it with
[CUAD](https://www.atticusprojectai.org/) contract text and
[BIPIA](https://github.com/microsoft/BIPIA) injections is the next step, and
until that lands, treat any ranking as provisional.

Cases are written by the same person who wrote the verifier, which is a real
source of bias. Contributed cases that break it are the most valuable thing
anyone can send.
