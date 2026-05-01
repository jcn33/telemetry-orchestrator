# CLAUDE.md — Telemetry Orchestrator

## Project Purpose

AI-assisted anomaly detection pipeline for high-frequency aerospace telemetry.

This is a portfolio project targeting aerospace/systems engineering roles. Code quality, commit discipline, and physics grounding are as important as functionality.

---

## Architecture

```
Remote EC2 (Docker Compose)
├── api/          FastAPI — LangGraph orchestration, HTTP endpoints
├── ui/           React (Vite) — visualization and HITL review UI
└── db/           PostgreSQL — relational telemetry storage

External Managed Services
├── Qdrant Cloud  — vector store for frequency-domain embeddings
└── Claude API    — LLM backbone (Opus 4 via Anthropic SDK)
```

All ML inference and GPU-bound work runs in an isolated container with exclusive GPU resource reservation. Orchestration is API/IO-bound and runs on CPU.

---

## Active Architectural Constraints

These directives are compiled from accepted ADRs in `docs/adr/`. When a new ADR is accepted, its directives are added here. Do not modify this section manually — update the source ADR and re-compile.

<!-- ADR-001: EC2 Instance Sizing and Security Model -->
- **DIRECTIVE:** Target environment is a remote EC2 `t3.xlarge` in `us-west-2`. Do not write code that assumes local execution for data-intensive operations.
- **DIRECTIVE:** All service access (React frontend, FastAPI) is via VS Code SSH port forwarding. Do not add public ingress rules for application ports.
- **DIRECTIVE:** Qdrant is a managed cloud service (`QDRANT_URL` env var). Never reference a localhost Qdrant endpoint.

<!-- ADR-002: Local Service Topology and Port Exposure -->
- **DIRECTIVE:** All container host-port bindings in `docker-compose.yml` MUST use the `127.0.0.1:<host>:<container>` form. Never bind to `0.0.0.0` or omit the interface.
- **DIRECTIVE:** Inter-service calls inside the compose network MUST use the compose service name (`db`, `api`, `ui`), never `localhost` or `127.0.0.1`.
- **DIRECTIVE:** Code running inside a compose container reads `DATABASE_URL`. Code running on the EC2 host (MCP servers, scripts) reads `DATABASE_URL_LOCAL`. Do not cross these.
- **DIRECTIVE:** When adding a new compose service, follow the established pattern: `127.0.0.1` host binding, named volume for any persistent state, healthcheck if downstream services depend on it.

<!-- ADR-004: Code Layering Across src/, scripts/, and api/ -->
- **DIRECTIVE:** Library code goes in `src/<package>/`. It MUST NOT import FastAPI, psycopg, sqlalchemy, or any DB-session class.
- **DIRECTIVE:** FastAPI route handlers and request/response schemas go in `api/app/`. They may import from `src.*`, but `src/` MUST NOT import from `api/`.
- **DIRECTIVE:** One-shot operational CLIs (data fetchers, DB indexers) go in `scripts/`. They may import from `src.*`, but `src/` MUST NOT import from `scripts/`, and `api/app/` MUST NOT import from `scripts/`.
- **DIRECTIVE:** When adding a new module, pick the layer first and adhere to the import rules above. If a module fits no layer, raise a new ADR rather than placing it ad hoc.

---

## Pilot / Navigator Protocol

You are the **Pilot** (implementation). I am the **Navigator** (review and approval).

Every feature follows this exact loop — no exceptions:

1. **Plan** — Break down the task. State which files will change, what math/physics is involved, and any edge cases.
2. **Implement** — Write code in small, atomic chunks. Run `ruff check` and `pytest` after each logical unit.
3. **Pause** — Stop. Output a **Technical Review Memo** (what changed, why, test results, any physics assumptions made).
4. **Wait for LIFTOFF** — Do not commit. Do not proceed to the next feature. Wait for explicit approval.
5. **Commit** — After approval, propose a Conventional Commits message. I will approve it before you run `git commit`.

If tests fail at step 2, stop and surface the failure — do not work around it silently.

---

## Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(telemetry): implement power spectral density extraction
fix(agents): correct LangGraph state routing on empty buffer
test(signal): add edge cases for NaN sensor values
refactor(retrieval): isolate Qdrant query logic from agent state
docs(readme): add system architecture and deployment guide
chore(infra): add EC2 bootstrap script and docker-compose scaffold
```

Scope options: `telemetry`, `signal`, `agents`, `retrieval`, `api`, `dashboard`, `infra`, `docs`, `adr`, `claude`

**Subject-only by default.** Add an extended body only when the diff plus any referenced ADR do not already convey the why (e.g., a subtle physics constraint, an external incident, an upstream-bug workaround). When in doubt, omit the body.

---

## Coding Conventions

- **Type hints** on all functions — no exceptions.
- **Pydantic** for all data schemas and LangGraph state.
- **numpy / scipy** for all signal processing — deterministic, verifiable.
- **No raw LLM math** — LLM agents call deterministic Python tools; they do not compute FFTs or thresholds themselves.
- **Physics rationale in docstrings** — if a function applies a domain-specific transform, one sentence explaining why belongs in the docstring.
- No magic numbers — define constants with names and units (e.g., `SAMPLE_RATE_HZ = 20_000`).

---

## Signal Processing Rationale

All transforms live in `src/signal_processing/`. They are pure functions with no side effects and 100% unit test coverage.

---

## Environment Variables

Never commit secrets. All credentials are loaded from `.env` (gitignored). See `.env.example` for required keys.

`.env` is hard-blocked via `permissions.deny` rules in `.claude/settings.json`. The harness refuses Read/Edit/Write/Bash access to the file at the tool-call layer — do not attempt to read or modify it. Edits to `.env` are the user's job. `.env.example` is unaffected.

---

## Documentation Convention

Design decisions → `docs/adr/` (AI-optimized ADRs with YAML frontmatter and AI Coding Directives).
Physics rationale → notebook markdown cells and function docstrings.
Project-level overview → `README.md`.

When an ADR is accepted: update the ADR, then compile its directives into the **Active Architectural Constraints** section above. Both files change in the same commit.

See `docs/adr/README.md` for the template.

---

## MCP Tools (configured separately in `.mcp.json`)

MCP setup is deferred to a later phase. When configured, tools will cover: sequential reasoning, human-in-the-loop approval gates, database query, and physics paper retrieval.
