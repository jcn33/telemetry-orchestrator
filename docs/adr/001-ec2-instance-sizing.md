---
id: "001"
title: EC2 Instance Sizing and Security Model
status: Accepted
tags: [infra, security, ec2]
last_updated: 2026-04-30
---

# ADR-001: EC2 Instance Sizing and Security Model

## Context

The pipeline requires a remote compute environment capable of running concurrent Docker Compose services (FastAPI, React frontend, PostgreSQL), in-memory signal processing of NASA C-MAPSS data, and LangGraph orchestration — all while maintaining a development experience tight enough for a fast iteration cycle (no git push/pull loop between local and remote).

The instance must support a secure, minimal-exposure access model consistent with aerospace-grade security posture.

## Decision

**Instance:** `t3.xlarge` (4 vCPU, 16 GB RAM, 30 GB gp3 EBS) in `us-west-2`.

**Security:** SSH on port 22 restricted to the developer's current IP. No other public ingress. All application access (React 3000, FastAPI 8000) tunneled via VS Code SSH port forwarding — no firewall rules for application ports.

**Development workflow:** VS Code Remote SSH directly into the instance. The local machine is a thin client. All execution happens on EC2.

**Qdrant:** External managed service (Qdrant Cloud). Not self-hosted on this instance.

## Options Considered

- **`t3.xlarge` [ACCEPTED]:** 16 GB RAM comfortably handles concurrent Docker services + NumPy/Pandas data expansion (5–10x raw CSV footprint). 4 vCPUs prevent UI blocking during CPU-bound signal processing.
- **`t3.large` [REJECTED]:** 8 GB RAM creates memory pressure when running all services concurrently with in-memory FFT transforms on the full C-MAPSS dataset.
- **`g4dn.xlarge` (GPU) [REJECTED]:** Unnecessary for this workload. LangGraph orchestration is IO-bound (API calls), not GPU-bound. Signal processing uses CPU-optimized numpy/scipy. Adding a GPU instance wastes cost and introduces CUDA overhead with no benefit.
- **Self-hosted Qdrant on EC2 [REJECTED]:** Consumes RAM needed for signal processing, adds operational overhead (backups, patching, failover) with no benefit over the free managed tier during a sprint.

## Consequences

- All code must be written assuming remote execution — no local file path assumptions for data ingestion or output.
- SSH IP restriction means the developer must re-run the security group update command if their IP changes (dynamic IPs). See `infra/update_ssh_ip.sh` (future).
- `us-west-2` is the canonical region for all AWS resources in this project.

## AI Coding Directives

- **DIRECTIVE:** Target environment is a remote EC2 `t3.xlarge` in `us-west-2`. Do not write code that assumes local execution for data-intensive operations.
- **DIRECTIVE:** All application port access (React 3000, FastAPI 8000) is via VS Code SSH port forwarding. Do not add public ingress rules or hardcode public IP addresses.
- **DIRECTIVE:** Qdrant is a managed cloud service accessed via `QDRANT_URL` env var. Never reference a `localhost` Qdrant endpoint.
