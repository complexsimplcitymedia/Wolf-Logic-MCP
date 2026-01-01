# Wolf Logic MCP

**Distributed AI Memory Orchestration System with Persistent Cognitive State Layer**

[![Patent Pending](https://img.shields.io/badge/Patent-Pending-blue)](https://complexsimplicityai.com)
[![License](https://img.shields.io/badge/License-Proprietary-red)]()
[![API Status](https://img.shields.io/badge/API-Live-green)](https://api.complexsimplicityai.com)

> **First-to-market persistent AI memory infrastructure that gives any AI model long-term recall across sessions, platforms, and devices.**

---

## What Is This?

Wolf Logic MCP solves AI's amnesia problem. Every conversation you have with ChatGPT, Claude, Gemini—they forget everything the moment you close the tab. Wolf Logic doesn't.

This system provides:
- **Persistent memory** that survives across sessions
- **Cross-platform portability** — your memories work with ANY AI
- **Local-first architecture** — your data stays on YOUR device
- **Semantic search** — find memories by meaning, not just keywords

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WOLF LOGIC SYSTEM                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │   SCRIPTY   │    │  LIBRARIAN  │    │   pgai      │             │
│  │ Stenographer│───▶│  Embedding  │───▶│  PostgreSQL │             │
│  │   Agent     │    │   Engine    │    │  + Vectors  │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│        │                   │                  │                     │
│        │                   │                  │                     │
│        ▼                   ▼                  ▼                     │
│  ┌─────────────────────────────────────────────────────┐           │
│  │              PostgREST API Layer                    │           │
│  │         api.complexsimplicityai.com                 │           │
│  └─────────────────────────────────────────────────────┘           │
│                            │                                        │
│         ┌──────────────────┼──────────────────┐                    │
│         ▼                  ▼                  ▼                    │
│    ┌─────────┐       ┌─────────┐       ┌─────────┐                │
│    │ Claude  │       │ ChatGPT │       │ Gemini  │                │
│    │   MCP   │       │  Plugin │       │  Agent  │                │
│    └─────────┘       └─────────┘       └─────────┘                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## System Components

### The Librarian (qwen3-embedding:4b)
The semantic brain. Converts conversations into 2560-dimensional vectors for meaning-based retrieval. Not keyword matching—actual understanding.

### Scripty (Stenographer Agent)
Automatic conversation capture. Every 5 minutes, your AI interactions get vectorized and stored. No manual saving required.

### pgai (PostgreSQL + AI)
The intelligent database layer. PostgreSQL extended with vector similarity search, semantic queries, and namespace isolation.

### PostgREST API
RESTful access to the entire memory system. Any HTTP client can query, store, and manage memories with proper authentication.

---

## Memory Namespaces

| Namespace | Count | Purpose |
|-----------|-------|---------|
| `scripty` | 46K+ | Automatic session captures |
| `wolf_story` | 16K+ | Books, narratives, business strategy |
| `ingested` | 10K+ | Uploaded documents and files |
| `session_recovery` | 9K+ | Conversation continuity |
| `core_identity` | 9 | Immutable values and directives |

**Total: 97,000+ memories** across 26 namespaces

---

## Why This Matters

### The Problem
- ChatGPT: "I don't have access to previous conversations"
- Claude: "I don't have memory of past interactions"  
- Gemini: "I can't recall what we discussed before"

### The Solution
Wolf Logic MCP acts as a universal memory layer. Connect it to ANY AI via:
- **MCP Protocol** (Claude Desktop, Claude Code)
- **REST API** (Custom integrations)
- **Mobile Bridge** (Android/iOS apps)

Your AI remembers everything. Forever.

---

## Quick Start

### MCP Server Connection
```json
{
  "mcpServers": {
    "wolf-logic": {
      "type": "url",
      "url": "https://mcp.complexsimplicityai.com/sse",
      "name": "wolf-logic-mcp"
    }
  }
}
```

### API Query Example
```bash
curl -X GET "https://api.complexsimplicityai.com/memories?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### Semantic Search
```bash
curl -X GET "https://api.complexsimplicityai.com/rpc/semantic_search" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query": "project deadlines", "limit": 5}'
```

---

## OAuth & MCP Setup

### Prerequisites
1. Copy `.env.example` to `.env` and configure your credentials
2. Authentik OAuth provider running (see `authentik/docker-compose.yml`)
3. Node.js for npx-based MCP servers

### Claude Code MCP Configuration
The `.mcp.json` file in this repo configures Claude Code with:
- **postgres-librarian**: Direct access to memories database
- **filesystem**: Local file access
- **memory**: Knowledge graph persistence
- **fetch**: Web content retrieval
- **sequential-thinking**: Problem-solving chains

### Authentik OAuth Setup
1. Access Authentik Admin: `https://auth.complexsimplicityai.com`
2. Create OAuth Provider for MCP Gateway:
   - Client ID: `mcp-gateway`
   - Scopes: `openid profile email`
   - Redirect URIs: See `security/authentik_sso_credentials.txt`
3. Update `.env` with your client secrets

### Docker MCP (20 servers available)
```bash
# List available servers
docker mcp list

# Connect Claude to a server
docker mcp client connect claude-code
```

Available servers: postgres, filesystem, memory, fetch, grafana, prometheus, neo4j, slack, and more.

---

## Infrastructure

### Production Stack
- **Database:** PostgreSQL 16 + pgvector + pgai
- **Embeddings:** Ollama fleet (30+ models)
- **API:** PostgREST + Caddy reverse proxy
- **Auth:** JWT tokens with namespace isolation
- **Network:** Tailscale mesh VPN

### Performance
- **Vectorization:** 200,000 tokens in <10 seconds
- **Semantic search:** <100ms average latency
- **Concurrent models:** Parallel embedding processing

---

## Clients

| Platform | Status | Location |
|----------|--------|----------|
| Android | Beta | `/android-client` |
| macOS | Beta | `/macos-client` |
| Web UI | Live | [wolf-ui.complexsimplicityai.com](https://wolf-ui.complexsimplicityai.com) |
| MCP Server | Live | `/mcp-gateway` |

---

## Directory Structure

```
Wolf-Logic-MCP/
├── api/                 # PostgREST configuration
├── android-client/      # Mobile app (Kotlin)
├── macos-client/        # Desktop client (Swift)
├── mcp-gateway/         # MCP server implementation
├── mcp_servers/         # Additional MCP integrations
├── scripty/             # Stenographer agent
├── lib/                 # Shared libraries
├── deployment/          # Docker, systemd configs
├── docs/                # Documentation
├── security/            # Auth and encryption
└── tools/               # Utility scripts
```

---

## Security

- **Authentication:** JWT tokens with configurable expiration
- **Encryption:** TLS 1.3 for all API traffic
- **Isolation:** Namespace-level access control
- **Network:** Tailscale for internal services

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

---

## Business Model

**$20/month flat rate** — Unlimited vectorization, unlimited storage, unlimited queries.

Or: **$0/month** if you contribute compute resources to the network.

---

## Patent

**Utility Patent Filed:** December 17, 2024

"Distributed AI Memory Orchestration System with Persistent Cognitive State Layer"

Covers: Memory persistence architecture, cross-platform synchronization, semantic retrieval methods, and namespace isolation techniques.

---

## Links

- **Website:** [complexsimplicityai.com](https://complexsimplicityai.com)
- **API Docs:** [api.complexsimplicityai.com](https://api.complexsimplicityai.com)
- **Web UI:** [wolf-ui.complexsimplicityai.com](https://wolf-ui.complexsimplicityai.com)
- **MCP Endpoint:** [mcp.complexsimplicityai.com](https://mcp.complexsimplicityai.com)

---

## License

Proprietary. See LICENSE for terms.

---

## Contact

**Wolf** — Founder & CEO, Complex Simplicity AI

- GitHub: [@complexsimplcitymedia](https://github.com/complexsimplcitymedia)
- Email: admin@complexsimplicityai.com

---

*Built by a former Hollywood lighting programmer who got tired of AI forgetting everything.*