# Evaluation and improvement protocol

Current evidence: behavioral unit tests against fictional inputs. No model benchmark has been run.

For a later model adapter, freeze separate development and held-out sets before tuning. Include missing prices, contradictory updates, ambiguous parties, malicious source instructions and superficially similar deals.

Measure cross-deal leakage, unsupported extracted values, missing-field detection, false acceptance labels, latency and model usage. Report denominators and failures, not just percentages. Run baseline and candidate on the same inputs and model settings. Keep multiple runs when results are nondeterministic.

Store private runs locally under `runs/` and lessons under `memory/`; both are ignored. Proposed lesson records need task ID, failure evidence, suggested change, evaluation result and review status. This storage pipeline is planned, not implemented.

Reject any candidate with new cross-deal leakage or false acceptance. Preserve the old version. A reviewer decides whether a tested change becomes a pull request and is merged. A second AI opinion is not an independent ground-truth test.
