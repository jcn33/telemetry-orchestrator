# telemetry-orchestrator
AI-assisted research pipeline for anomaly detection in high-frequency aerospace telemetry

## Claude Setup

| File Path | Purpose |
| :--- | :--- |
| **`CLAUDE.md`** | **Primary Context.** Put your project goals, code style, testing instructions, and "Pilot/Navigator" rules here. (Goes in the root or `.claude/CLAUDE.md`). |
| **`.claude/settings.json`** | **Project Settings.** Shared team settings, allowed Bash commands, and default model aliases. |
| **`.claude/agents/`** | **Sub-Agent Personas.** This is where you put specific files like `reliability-engineer.agent.md` if you want specialized personas. |
| **`.mcp.json`** | **Project MCP Config.** Defines which Model Context Protocol servers are available specifically for this project (e.g., your local Postgres or Qdrant MCP). |
