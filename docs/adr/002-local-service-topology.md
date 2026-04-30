---
id: "002"
title: Local Service Topology and Port Exposure
status: Accepted
tags: [infra, docker, security, networking]
last_updated: 2026-04-30
---

# ADR-002: Local Service Topology and Port Exposure

## Context

The pipeline runs three first-party services under Docker Compose on a single EC2 host: a FastAPI backend (`api`), a Vite/React frontend (`ui`), and a PostgreSQL database (`db`). Two access patterns exist for each:

1. **In-cluster** — services on the compose network talking to each other (e.g., `api` → `db`, `ui` dev-server proxying to `api`).
2. **Host-side** — tooling running directly on the EC2 host (developer shell, MCP servers, `psql`, ad-hoc scripts) that needs to reach a containerized service.

ADR-001 already established the security posture: SSH-only public ingress, application access via VS Code SSH port forwarding. This ADR resolves the resulting question — *which container ports get published to the host, on which interface, and how do consumers address each service*?

A specific operational requirement drives the database exposure: a Postgres MCP server (run on the host, outside compose) needs read access to the telemetry database so the AI assistant can answer ad-hoc data questions during development.

## Decision

**Host-port bindings — all on `127.0.0.1` only.** The compose file publishes:

| Service | Host port | Container port | Purpose |
| :--- | :--- | :--- | :--- |
| `api`   | `127.0.0.1:8000` | 8000 | FastAPI access via SSH tunnel |
| `ui`    | `127.0.0.1:3000` | 3000 | Vite dev server via SSH tunnel |
| `db`    | `127.0.0.1:5432` | 5432 | Host-side tooling (MCP, psql, scripts) |

No service binds to `0.0.0.0` on the host. The `127.0.0.1` binding is defense-in-depth — even if the EC2 security group ever permitted a port, the kernel would not accept off-host traffic.

**In-cluster addressing — via compose service name.** Services on the `telemetry` network reach each other by service name (`db`, `api`, `ui`) on container ports. The Vite dev server proxies `/api/*` to `http://api:8000`. The API connects to Postgres at `postgresql://...@db:5432/...`.

**Two database URLs, by audience.**

- `DATABASE_URL` — `postgresql://...@db:5432/...` — for code running *inside* a compose container.
- `DATABASE_URL_LOCAL` — `postgresql://...@127.0.0.1:5432/...` — for tooling running *on the host* (MCP server, dev scripts).

## Options Considered

- **`127.0.0.1` host bindings for all three services [ACCEPTED]:** Satisfies the SSH-tunnel-only directive from ADR-001 with zero reliance on the security group, while permitting host-side MCP/dev tooling against Postgres.
- **Bind only `api` and `ui`, leave `db` compose-internal only [REJECTED]:** Would block the MCP-on-Postgres workflow that motivates this ADR. We'd have to `docker compose exec` into the API container for every ad-hoc query, which is friction during sprint iteration.
- **`0.0.0.0` host bindings (rely on security group) [REJECTED]:** Single-layer defense. One drift in the SG (e.g., a teammate widening 22 to 0.0.0.0/0 by mistake) exposes the database. `127.0.0.1` removes that failure mode entirely.
- **Single `DATABASE_URL` everywhere, switching hostname based on caller [REJECTED]:** Requires runtime detection of "am I in a container?" Two explicit env vars are clearer, type-checkable in Pydantic settings, and self-documenting.

## Consequences

- The MCP server, when configured, must use `DATABASE_URL_LOCAL` — never `DATABASE_URL`. The hostname `db` is unresolvable on the host.
- Application code running in containers must never reference `127.0.0.1` for inter-service calls — that resolves to the container itself.
- `docker compose down -v` is required to re-run `db/init/*.sql` after schema changes during early development. The volume is named (`pgdata`) so this is intentional, not a footgun.
- Adding a fourth service later means picking another `127.0.0.1:<port>` binding. The pattern is established and uniform.

## AI Coding Directives

- **DIRECTIVE:** All container host-port bindings in `docker-compose.yml` MUST use the `127.0.0.1:<host>:<container>` form. Never bind to `0.0.0.0` or omit the interface.
- **DIRECTIVE:** Inter-service calls inside the compose network MUST use the compose service name (`db`, `api`, `ui`), never `localhost` or `127.0.0.1`.
- **DIRECTIVE:** Code running inside a compose container reads `DATABASE_URL`. Code running on the EC2 host (MCP servers, scripts) reads `DATABASE_URL_LOCAL`. Do not cross these.
- **DIRECTIVE:** When adding a new compose service, follow the established pattern: `127.0.0.1` host binding, named volume for any persistent state, healthcheck if downstream services depend on it.
