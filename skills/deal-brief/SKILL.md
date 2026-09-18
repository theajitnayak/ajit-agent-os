---
name: deal-brief
description: Organize buyer and seller statements into evidence-linked records for human review.
---

Assign each conversation to an explicit deal ID. Never combine parties across deals.
Preserve the original source and message IDs. Label manually normalized or model-extracted text as a candidate until checked against the original.
Record item, quantity, unit, currency, unit price and intent only when explicit.
If a value is missing or ambiguous, leave it unknown. Never treat an offer as acceptance.
Use the offline CLI for supported normalized inputs. Review unparsed text and conflicts.
Do not send messages, accept terms or move money. Return a brief and unresolved questions.
