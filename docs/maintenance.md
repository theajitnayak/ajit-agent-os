# Actual maintenance evidence

Run the offline check on Windows:

```
python scripts/maintenance.py --date YYYY-MM-DD --output maintenance
```

Use the actual date in India. The runner refuses other dates. It runs the unit suite, the original fictional benchmark and a separate extended suite. It writes commands, exit codes, metrics, fixture hashes, log hashes and source commit to the dated folder.

No provider API is called. The benchmark results remain offline controls rather than live-model performance claims. The record includes local modifications so the commit ID does not imply uncommitted fixtures are already in that commit.

The extended suite adds dates mistaken for quantities, validity periods mistaken for orders, buyer budgets mistaken for seller quotes, acceptance requests mistaken for acceptance, price ranges and a literal zero fee. The old suite is unchanged.

Do not fill missing days with invented activity. A dated test run is maintenance evidence, not evidence of external users or funding eligibility.
