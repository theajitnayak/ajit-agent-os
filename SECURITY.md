# Security and privacy

This prototype runs locally without network access. It prints source excerpts to stdout.
Keep real inputs and outputs in an access-controlled local location outside the repository.
The gitignore excludes common private folders but is not a privacy boundary.
Never publish private traces, credentials or customer conversations in issues.
The Markdown report escapes source-derived HTML and Markdown control characters. JSON retains the original evidence text and must be treated as data by downstream consumers.
Review code and dependencies before running third-party hooks or plugins.
For a vulnerability, use GitHub private vulnerability reporting if enabled. Otherwise contact the maintainer privately before disclosing sensitive details.
