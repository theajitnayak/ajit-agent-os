# Free resources worth using

Curated, not collected. Every entry earns its place by doing a job this project
actually has. Licence status is stated honestly: "verified" means the licence was
read, "stated" means the project says so but it was not confirmed directly.

Anything you redistribute, verify yourself first. A licence claim in someone
else's README is a claim, not a fact.

## Model access

Free and open-weight models make this project reproducible by people with no
budget, which is most of the people who need it. All of the endpoints below speak
the OpenAI `/chat/completions` shape, so `ajit_os/providers.py` reaches them with
no extra code. Base URLs were checked against vendor documentation on 2026-09-19.

| Provider | Base URL | Notes |
| --- | --- | --- |
| DeepSeek | `https://api.deepseek.com/v1` | Open weights under MIT. Signup credit has been offered. |
| Alibaba Model Studio (Qwen) | `https://dashscope.aliyuncs.com/compatible-mode/v1` | Qwen ships Apache-2.0 checkpoints. Separate international regions exist. |
| Zhipu (GLM) | `https://open.bigmodel.cn/api/paas/v4` | Open weights under its own permissive licence. Flash tiers have been free. |
| SiliconFlow | `https://api.siliconflow.cn/v1` | Hosts many open-weight models behind one key. Good for cross-model comparison. |
| MiniMax | `https://api.minimax.chat/v1` | Mixed licensing, check the specific model. |
| Volcengine Ark | `https://ark.cn-beijing.volces.com/api/v3` | Model names are endpoint ids created in the console. |
| OpenRouter | `https://openrouter.ai/api/v1` | Carries free, rate-limited variants of several open models. |
| Ollama | `http://localhost:11434/v1` | Fully offline, no key, no cost. The honest default. |

Free tiers change without notice. Confirm current terms with the vendor before
depending on one. "Open weights" is not the same as "free to use commercially":
the licence on the weights decides that, and several large checkpoints use custom
licences with conditions.

## Evaluation data

The benchmark in this repository is hand written and deliberately small, because
every case has to be arguable. These larger public sets are the sensible next
step for scale.

**CUAD, Contract Understanding Atticus Dataset**
Over 500 commercial contracts with more than 13,000 expert annotations across 41
clause categories, built by lawyers. Directly relevant: contracts are exactly the
documents where an invented value is expensive.
Licence: CC BY 4.0, commercial use permitted. Verified.
<https://www.atticusprojectai.org/>

**BIPIA, Benchmarking Indirect Prompt Injection Attacks**
Microsoft's benchmark for indirect injection across web, email, table,
summarisation and code tasks. Useful for growing the `injection` category beyond
hand-written cases.
Licence: see the repository LICENSE file. Not confirmed here.
<https://github.com/microsoft/BIPIA>

**Document extraction sets: FUNSD, SROIE, CORD**
Standard key-information-extraction benchmarks for forms and receipts. Widely
used in research.
Licence: not established. Several carry research-only or non-commercial terms.
Do not assume commercial use is permitted. Check each one before touching it.

## Prior art to learn from, not to copy

**Everything Claude Code** by Affaan Mustafa, MIT.
Agent, skill and command structure for Claude Code.
<https://github.com/affaan-m/ECC>

**Claude Code Templates** by Daniel Avila, MIT.
A large component library plus a CLI installer and a browsable catalogue. Its
real value here is as a distribution channel rather than as source code: this
repository ships a `.claude-plugin/plugin.json`, so it can be installed as a
plugin rather than copied by hand.
<https://github.com/davila7/claude-code-templates>

**Reflexion** by Noah Shinn and collaborators.
Feedback stored as memory rather than as weight updates. Informs the roadmap.
<https://github.com/noahshinn024/reflexion>

## What was deliberately left out

Component libraries, prompt collections and agent bundles were considered and
not vendored. Copying them adds volume and subtracts identity, and volume is not
the scarce thing. If a component is genuinely needed, depend on it and attribute
it. Do not absorb it.

## Free infrastructure this project already uses

- GitHub Actions: unlimited minutes for public repositories.
- GitHub Pages: free hosting for the benchmark results page.
- Hugging Face Datasets: free hosting if the case set outgrows this repository.

All three are already enough to run a public benchmark at zero cost.
