# Offline verification record

Run date: 2026-10-15. Platform: Windows. Source commit: 3e0b95e9093178e109b8f9443fc751248a7b4989.

The standard-library test suite passed all 96 tests. The three offline benchmark runs each completed all 16 fictional cases with no case errors. No hosted model or provider API was used.

Commands:

```
python -m unittest discover -s tests -v
python bench/run.py --stub strict --format json
python bench/run.py --stub greedy --format json
python bench/run.py --stub fabricating --format json
```

| Stub | Grounded recall | Invention rate | Refusal accuracy |
| --- | --- | --- | --- |
| strict | 7.14% | 0% | 100% |
| greedy | 21.43% | 25% | 75% |
| fabricating | 0% | 0% | 100% |

These measurements reproduce the existing README and benchmark documentation. They measure each stub combined with the verifier on a small developer-authored dataset. They are not live-model rankings or estimates of real-world performance.

The greedy result remains a known failure: a source quotation can be accurate while its interpretation is wrong. Passing the tests does not resolve that limitation.

Useful future contributions are independently reviewed fictional cases, reproducible failures and fixes with regression tests. Do not change expected benchmark answers to make a model pass. Do not commit private documents or traces.
