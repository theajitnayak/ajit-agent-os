# Product requirements: v0.1

Status: implemented prototype, not production approved.

## Problem

A solo operator needs to separate buyer and seller statements without inventing missing terms or confusing offers with acceptance.

## Approach

Use a deterministic offline extractor with explicit inputs before introducing model-generated extraction. Each result carries source evidence. Only fully matching explicit acceptances receive a matching-acceptances label; no legal conclusion is drawn.

## Goals

- No transfer of terms across deals.
- Missing fields remain missing.
- Conflicting terms remain visible.
- Runnable on Windows without paid APIs.
- Repeatable tests and documented limitations.

## Non-goals

Free-form chat understanding, currency conversion, payments, messaging, legal review, model training and autonomous self-modification.

## Release criteria

Local tests and demo pass. Public repository contains only original code and fictional examples. CI checks Windows and Linux. An independent user should be able to follow README without credentials.

## Later milestones

Add a candidate-extraction adapter only after a held-out evaluation set exists. Add failure memory only after defining evidence, retention and promotion rules. Use reviewed pull requests for workflow changes.
