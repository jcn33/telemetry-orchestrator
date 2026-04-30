# Architecture Decision Records

Significant design decisions are captured here as permanent, numbered records. ADRs are never edited after acceptance — if a decision is reversed, a new ADR supersedes it.

Each ADR also contains an **AI Coding Directives** section. When an ADR is accepted, its directives are compiled into the `Active Architectural Constraints` section of `CLAUDE.md` so they are available to the AI assistant on every session without requiring a filesystem traversal.

## Index

| ID | Title | Status | Tags |
| :--- | :--- | :--- | :--- |
| [ADR-001](001-ec2-instance-sizing.md) | EC2 Instance Sizing and Security Model | Accepted | `infra`, `security`, `ec2` |

---

## AI-Optimized Template

```markdown
---
id: NNN
title: Short Title
status: Proposed | Accepted | Deprecated | Superseded by ADR-NNN
tags: [tag1, tag2]
last_updated: YYYY-MM-DD
---

# ADR-NNN: Title

## Context
What situation forced this decision? What constraints, requirements, or tradeoffs were in play?

## Decision
What was chosen and why.

## Options Considered
- **Chosen Option [ACCEPTED]:** Brief reason.
- **Alternative [REJECTED]:** Brief reason it was not chosen. (Explicit rejection prevents AI from treating this as part of the active stack.)

## Consequences
What becomes easier? What becomes harder? What assumptions does this lock in?

## AI Coding Directives
Explicit rules for the AI assistant derived from this decision. These are compiled into CLAUDE.md when the ADR is accepted.

- **DIRECTIVE:** Always use `X`. Never use `Y`.
- **DIRECTIVE:** When writing Z, adhere to the schema in `path/to/file.py`.
```
