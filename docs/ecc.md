# Optional ECC development setup

ECC is a separate third-party project: https://github.com/affaan-m/ECC

This release runs without ECC. No ECC source, hooks or MCP credentials are bundled. No settings in the user's Claude installation have been changed.

When adopting ECC, select and review a specific release or commit. Record it in this document. Start with planning and code review on fictional data. Follow that release's official installation instructions instead of combining multiple installation methods.

External integrations need their own authentication. Plugin hooks execute code and must be reviewed. Preserve the MIT notice for any ECC code copied into future versions.

Adoption status: not installed by this project. Session memory and self-improvement are future experiments, not enabled features.
