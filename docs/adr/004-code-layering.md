---
id: "004"
title: Code Layering Across src/, scripts/, and api/
status: Accepted
tags: [architecture, code-layout, dependencies]
last_updated: 2026-05-01
---

# ADR-004: Code Layering Across src/, scripts/, and api/

## Context

Three categories of Python code coexist in this repo: a FastAPI service (already in `api/app/`), reusable library code (telemetry loaders, signal processing, future LangGraph nodes), and operational CLIs (data fetchers, DB indexers). With no rule for which layer owns what, dependencies flow accidentally — a script imports from the API, the API imports from a script, library code starts requiring a DB session — and the codebase becomes untestable in isolation.

A specific upcoming pressure motivates this ADR. The LangGraph agent loop, when it lands on a future branch, will import telemetry loaders. If those loaders live inside `api/app/`, the agent inherits FastAPI and psycopg as transitive dependencies for no good reason. If they live inside `scripts/`, they are not importable as a library at all. They need their own home, and the rule for that home should be encoded before the first `src/<package>/` directory is created.

## Decision

Three layers, with strictly directed imports.

| Layer | Location | May import | Side effects | Runs |
| :--- | :--- | :--- | :--- | :--- |
| Library | `src/<package>/` | numpy, scipy, pydantic | None — pure functions and data classes | Anywhere (notebook, container, host) |
| HTTP service | `api/app/` | `src.*`, FastAPI, psycopg | HTTP I/O, DB reads | Inside compose container |
| Operational CLI | `scripts/` | `src.*`, network/FS/DB clients | Network, FS writes, DB writes | EC2 host |

Permitted dependency arrows: `api → src`, `scripts → src`. Forbidden: `src → api`, `src → scripts`, `api ↔ scripts`.

`pyproject.toml` extends `pythonpath` to include `src/`, so tests and notebooks resolve `from <package> import ...` without packaging gymnastics. Test layout follows the same split: pure unit tests live under a top-level `tests/<package>/` (no Docker, no DB); integration tests against the compose stack stay under `api/tests/`.

## Options Considered

- **Three-layer split with strict import direction [ACCEPTED]:** Keeps the agent loop's dependency closure small (no FastAPI/psycopg drag), enables fast notebook iteration on library code, and makes the test pyramid mechanical.
- **Single `app/` directory holding everything [REJECTED]:** Drags FastAPI and DB drivers into every consumer of the library, including the agent graph and Jupyter notebooks. Library tests can't run without Docker.
- **Library code under `api/app/lib/` [REJECTED]:** Same dependency-drag problem, plus blurs what "the api package" means semantically. Future readers would reasonably expect everything under `api/app/` to be HTTP-shaped.
- **No directory split, rely on naming conventions [REJECTED]:** Forces every contributor (and the AI assistant) to remember the rule. ADRs exist precisely to encode such rules into directives that the assistant reads on every session.

## Consequences

- New top-level `src/` and `scripts/` directories alongside `api/`. `src/<package>/` is a Python package (has `__init__.py`); `scripts/` is flat — each file is a runnable CLI, no package init.
- `pyproject.toml` `[tool.pytest.ini_options].pythonpath` extends from `["api"]` to `["api", "src"]`.
- Pure unit tests live under a top-level `tests/<package>/` directory mirroring `src/<package>/`. Integration tests against the compose stack stay under `api/tests/`.
- The future LangGraph agent code lands in `src/agents/`, not under `api/app/`. The API will expose agent runs over HTTP by importing `src.agents`, never the other way around.
- Adding a fourth category later (e.g., a long-running worker process) means a new top-level directory and a new ADR, not a relaxation of these rules.

## AI Coding Directives

- **DIRECTIVE:** Library code goes in `src/<package>/`. It MUST NOT import FastAPI, psycopg, sqlalchemy, or any DB-session class.
- **DIRECTIVE:** FastAPI route handlers and request/response schemas go in `api/app/`. They may import from `src.*`, but `src/` MUST NOT import from `api/`.
- **DIRECTIVE:** One-shot operational CLIs (data fetchers, DB indexers) go in `scripts/`. They may import from `src.*`, but `src/` MUST NOT import from `scripts/`, and `api/app/` MUST NOT import from `scripts/`.
- **DIRECTIVE:** When adding a new module, pick the layer first and adhere to the import rules above. If a module fits no layer, raise a new ADR rather than placing it ad hoc.
