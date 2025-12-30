# Complex Logic Application

## Current State (2025-11-27)

### Architecture
Single-workstation deployment model. Each workstation runs a complete independent stack. Raspberry Pi will act as gateway between workstations for multi-user access.

```
[Workstation 1] <---> [Raspberry Pi Gateway] <---> [Workstation 2]
     |                                                    |
Full WOLF Stack                                   Full WOLF Stack
```

### Components

| Service | Port | Description |
|---------|------|-------------|
| Wolf Dashboard | 4500 | Flask backend + LCD-style UI |
| OpenMemory API | 8765 | MCP memory API |
| OpenMemory UI | 8080 | Next.js frontend |
| Qdrant | 6333 | Vector database (2560 dims) |
| PostgreSQL | 5432 | pgvector primary store |
| Neo4j | 8474/8687 | Graph database |
| MariaDB | 32768 | Source of truth for pipeline |

### Pipeline Flow
```
API → MariaDB (source of truth) → Qdrant (vectors) + Neo4j (graph)
```

### LM Studio Configuration
- **URL**: https://ai-studio.complexsimplicityai.com/v1
- **Chat Model**: amethyst-13b-mistral
- **Embedding Model**: text-embedding-qwen3-embedding-4b
- **Embedding Dimensions**: 2560

### Key Files

| File | Purpose |
|------|---------|
| `/mnt/Wolfpack/Wolf-Logic-app/start-wolf.sh` | Main startup script |
| `/mnt/Wolfpack/Github/memory_layer/mem0/wolf_logic_app.py` | Flask backend |
| `/mnt/Wolfpack/Github/memory_layer/mem0/wolf-ui/` | Dashboard UI (HTML/CSS/JS) |
| `/mnt/Wolfpack/Github/memory_layer/mem0/openmemory/docker-stack-openmemory.yml` | Docker Swarm stack |
| `/mnt/Wolfpack/Github/memory_layer/mem0/wolf_scripts/MariaDBOutboundSync.py` | MariaDB → Qdrant/Neo4j sync |
| `/mnt/Wolfpack/Github/memory_layer/mem0/wolf_scripts/MariaDBBulkImport.py` | Bulk import to MariaDB |

### Recent Changes (This Session)
1. Migrated from Ollama to LM Studio across entire project
2. Changed embedding dimensions from 1536 → 2560
3. Updated all config files with new LM Studio URL
4. Created MariaDB pipeline scripts (OutboundSync, BulkImport)
5. Updated dashboard for MariaDB pipeline status
6. Simplified Docker Swarm config for single-workstation deployment
7. Created `start-wolf.sh` startup script

### Usage

```bash
# Start everything
./start-wolf.sh

# Check status
./start-wolf.sh --status

# Stop everything
./start-wolf.sh --stop

# Partial starts
./start-wolf.sh --no-swarm
./start-wolf.sh --no-mariadb
./start-wolf.sh --no-dashboard
```

### Next Steps / TODO
- Raspberry Pi gateway setup
- Second workstation deployment
- Memory sync between workstations (if needed)

### Credentials
- **MariaDB**: root / Lonewolf82$$$
- **PostgreSQL**: mem0 / mem0
- **Neo4j**: neo4j / mem0graph
- **OpenMemory API Key**: wolf-permanent-api-key-2024-never-expires
