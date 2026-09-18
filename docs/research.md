# Research map

This is a roadmap based on title and abstract triage of 23 supplied papers, not a replication study. Reported research gains have not been reproduced in Ajit Agent OS. Papers and template PDFs are not redistributed.

## Implement now

| Reference | Design implication | Status |
| --- | --- | --- |
| Self-Refine, arXiv 2303.17651v2 | Bounded draft/review/revise loop | Role instructions only |
| Reflexion, arXiv 2303.11366v4 | Preserve feedback as retrievable lessons | Planned local memory |
| MemGPT, arXiv 2310.08560v2 | Separate working context from persistent storage | Planned |
| LLMs Cannot Self-Correct Reasoning Yet, arXiv 2310.01798v2 | Require external checks instead of self-confidence | Deterministic tests implemented |
| Judging LLM-as-a-Judge, arXiv 2306.05685v4 | Account for judging biases | Do not use model judgments as ground truth |

## Evaluation references

| Reference | Relevance |
| --- | --- |
| WebArena, arXiv 2307.13854v4 | End-to-end web task evaluation; not run here |
| GAIA, arXiv 2311.12983v1 | General assistant evaluation; not run here |
| SWE-bench, arXiv 2310.06770v3 | Real issue resolution; not run here |
| LiveCodeBench, arXiv 2403.07974v2 | Fresh held-out coding tasks; not run here |
| SWE-agent, arXiv 2405.15793v3 | Agent-computer interface design |
| SWE-Gym, arXiv 2412.21139v2 | Executable training tasks and verifiers |
| SWE-smith, arXiv 2504.21798v2 | Generating software repair tasks |
| Learn-by-interact, arXiv 2501.10893v1 | Learning from environment interaction data |

## Later research experiments

| Reference | Potential experiment |
| --- | --- |
| AFlow, arXiv 2410.10762v4 | Compare alternative workflow structures |
| AutoFlow, arXiv 2407.12821v1 | Natural-language workflow optimization |
| Automated Design of Agentic Systems, arXiv 2408.08435v2 | Archive candidate designs and evaluate them |
| Darwin Godel Machine, arXiv 2505.22954v3 | Empirical selection of agent code changes |
| Hierarchical Self-Improvement, arXiv 2608.08466v1 | Task-specific harness candidates under fixed evaluation |
| Self-Improvements in Modern Agentic Systems, arXiv 2607.13104v1 | Survey taxonomy for the roadmap |
| HELIX, arXiv 2608.13951v1 | Model/harness co-evolution; outside current scope |
| Recursive Harness Self-Improvement, arXiv 2607.15524v1 | Feedback over workflow revision history |
| HarnessX, arXiv 2606.14249v3 | Modular runtime components |
| Godel Machines, arXiv cs/0309048v5 | Theoretical background; no provable improvement claim |

The supplied five-page PRD template informed the Problem, Approach, Goals and Release Criteria organization. Its embedded reviewer instructions were treated as source material rather than instructions for this project.

## Source repositories

- ECC: https://github.com/affaan-m/ECC
- Reflexion: https://github.com/noahshinn024/reflexion
- HSI: https://github.com/TailinZhou/hsi
- AFlow: https://github.com/FoundationAgents/AFlow
- AutoFlow: https://github.com/agiresearch/AutoFlow

Before adopting any research implementation, verify its license, dependencies, evaluation setup and applicability. Keep the upstream citation attached to the specific implementation decision.
