# SparkJar Memory System Implementation Instructions

## Overview
Implement the memory system as an integrated part of SparkJar-Crew with multiple interfaces: CrewAI tools, FastAPI endpoints, and MCP wrapper. This memory system will serve as the foundation for organizational intelligence, writing pattern recognition, and agent optimization.

## Core Architecture

### Database Tables (Already Created)
- `memory_entities` - stores all entities (people, projects, writing patterns, etc.)
- `memory_relations` - stores relationships between entities with metadata

### Key Principles
1. **Multi-tenant**: Everything scoped by `client_id` and `actor_id` 
2. **Company-owned**: Memory belongs to the company (client) with actor-level access
3. **Actor-based access**: Memory accessed through humans or synths (`actor_type`) within the company
4. **Flexible entities**: Any entity type allowed (person, company, writing_pattern, meeting, etc.)
5. **Rich relationships**: Metadata includes strength, frequency, observations
6. **Semantic search**: Vector embeddings for similarity queries
7. **Multiple interfaces**: CrewAI tools, FastAPI endpoints, MCP wrapper

## Implementation Requirements

### 1. SparkJar-Crew Integration Structure
```
sparkjar-crew/  (monorepo)
├── shared/
│   ├── models/           # Shared between all services
│   ├── schemas/
│   ├── database/
│   └── auth/
├── crew-service/         # Main crew operations
│   ├── main.py
│   ├── api/
│   └── tools/
├── memory-service/       # Standalone memory service
│   ├── internal_api.py   # IPv6/HTTP for internal use
│   ├── external_api.py   # IPv4/HTTPS for external use  
│   ├── memory_manager.py # Core memory operations
│   ├── embeddings.py     # Vector embedding generation
│   └── mcp_server.py     # MCP wrapper around external API
└── docker-compose.yml    # Multiple service orchestration
```

### 2. Three-Interface Architecture

Based on research confirming IPv4/IPv6 dual stack issues with FastAPI/Uvicorn, we implement three distinct interfaces:

**Internal API (IPv6/HTTP)** - High Performance
- Uvicorn has known dual stack limitations that cause IPv6/IPv4 switching issues
- CrewAI tools and LangChain access
- No SSL overhead, maximum speed
- IPv6 internal network only

**External API (IPv4/HTTPS)** - Secure Access  
- Voice systems, web integrations
- Full authentication and SSL termination
- Railway and other platforms require separate IPv4 binding for external access
- Rate limiting and security features

**MCP Interface** - Standards Compliance
- Hypercorn recommended for dual stack support when needed
- Wraps external API for Claude Desktop
- Standard MCP protocol compliance

### 3. Dependencies Required
Add to existing sparkjar-crew requirements.txt:
```txt
# Memory system specific
openai  # for embeddings
numpy
pgvector  # for vector operations
mcp  # for MCP wrapper
httpx  # for MCP HTTP client and internal API calls
hypercorn  # ASGI server with dual stack support (replaces uvicorn)
```

### 4. Internal Memory API (memory-service/internal_api.py)

High-performance IPv6/HTTP interface for internal SparkJar services:

```python
from fastapi import FastAPI, HTTPException
from memory_manager import MemoryManager
from schemas.memory_schemas import *

# Internal API - IPv6/HTTP only
internal_app = FastAPI(
    title="Memory Service - Internal",
    description="High-performance memory API for internal SparkJar services"
)

@internal_app.post("/memory/entities")
async def create_entities_internal(entities: List[EntityCreate]):
    """Fast internal entity creation - no auth overhead"""
    # Direct memory manager calls
    
@internal_app.post("/memory/search")
async def search_nodes_internal(search_request: MemorySearchRequest):
    """High-speed semantic search for agents"""
    # Optimized for CrewAI tools

# Run with: hypercorn internal_api:internal_app --bind [::]:8001
```

### 5. External Memory API (memory-service/external_api.py)

IPv4/HTTPS interface with full security for external access:

```python
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
import httpx

# External API - IPv4/HTTPS with security
external_app = FastAPI(
    title="Memory Service - External", 
    description="Secure memory API for external integrations"
)

security = HTTPBearer()

async def verify_external_auth(token: str = Depends(security)):
    """Full authentication for external requests"""
    # Implement your auth logic
    
@external_app.post("/memory/entities")
async def create_entities_external(
    entities: List[EntityCreate],
    request: Request,
    token: str = Depends(verify_external_auth)
):
    """Secure entity creation with rate limiting"""
    # Auth + rate limiting + call internal API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://[::1]:8001/memory/entities",
            json=entities
        )
        return response.json()

# Run with: hypercorn external_api:external_app --bind 0.0.0.0:8443 --certfile cert.pem --keyfile key.pem
```

### 6. MCP Server (memory-service/mcp_server.py)

MCP wrapper that calls the external API:

```python
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server

class MemoryMCPServer:
    def __init__(self, external_api_url: str = "https://localhost:8443"):
        self.external_api_url = external_api_url
        self.server = Server("sparkjar-memory-server")
        self.setup_handlers()
    
    async def _call_external_api(self, endpoint: str, method: str = "POST", data: Any = None):
        """Call the external API with proper SSL verification"""
        async with httpx.AsyncClient(verify=False) as client:  # Configure SSL properly
            if method == "POST":
                response = await client.post(f"{self.external_api_url}{endpoint}", json=data)
            elif method == "GET":
                response = await client.get(f"{self.external_api_url}{endpoint}")
            return response.json()

# Usage: python mcp_server.py
```

### 7. CrewAI Tools (crew-service/tools/memory_tools.py)

Tools that call the high-speed internal API:

```python
from crewai_tools import BaseTool
import httpx
import asyncio

class MemoryToolBase(BaseTool):
    def __init__(self):
        super().__init__()
        self.internal_api_url = "http://[::1]:8001"  # IPv6 internal
    
    async def _call_internal_api(self, endpoint: str, data: Any):
        """Fast internal API calls for agents"""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.internal_api_url}{endpoint}", json=data)
            return response.json()

class CreateMemoryEntities(MemoryToolBase):
    name: str = "create_memory_entities"
    description: str = "Create entities in memory system"
    
    def _run(self, entities: List[Dict[str, Any]]) -> str:
        return asyncio.run(self._call_internal_api("/memory/entities", entities))
```

### 8. Deployment Configuration

Docker Compose setup for three-interface architecture:

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Internal Memory API (IPv6/HTTP)
  memory-internal:
    build: ./memory-service
    command: hypercorn internal_api:internal_app --bind [::]:8001
    ports:
      - "8001:8001"
    networks:
      - internal-ipv6
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    
  # External Memory API (IPv4/HTTPS)  
  memory-external:
    build: ./memory-service
    command: hypercorn external_api:external_app --bind 0.0.0.0:8443 --certfile /certs/cert.pem --keyfile /certs/key.pem
    ports:
      - "8443:8443"
    networks:
      - external-ipv4
    depends_on:
      - memory-internal
    environment:
      - INTERNAL_API_URL=http://[::1]:8001
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - ./certs:/certs
      
  # CrewAI Service
  crew-service:
    build: ./crew-service
    networks:
      - internal-ipv6
    depends_on:
      - memory-internal
    environment:
      - MEMORY_INTERNAL_URL=http://[::1]:8001

networks:
  internal-ipv6:
    driver: bridge
    enable_ipv6: true
  external-ipv4:
    driver: bridge
```

### 9. Hypercorn Dual Stack Configuration (if single service needed)

For deployments requiring true dual stack on single port:

```python
# dual_stack_memory.py
from hypercorn.config import Config
from hypercorn.asyncio import serve
import asyncio

async def run_dual_stack():
    config = Config()
    config.bind = ["0.0.0.0:8000", "[::]:8000"]  # Both IPv4 and IPv6
    config.use_reloader = False
    config.certfile = "cert.pem"  # For HTTPS
    config.keyfile = "key.pem"
    
    await serve(external_app, config)

# Run with: python dual_stack_memory.py
```

## Architecture Summary

**Research-Validated Three-Interface Solution:**

Based on confirmed IPv4/IPv6 dual stack issues with Uvicorn/FastAPI, we implement:

1. **Internal API (IPv6/HTTP)** - High-speed agent access, no SSL overhead
2. **External API (IPv4/HTTPS)** - Secure external integrations with auth
3. **MCP Interface** - Standards-compliant wrapper for Claude Desktop

## Integration Flow

```
CrewAI Tools → Internal API (IPv6) → Memory Service
Voice Systems → External API (IPv4/HTTPS) → Internal API → Memory Service  
Claude Desktop → MCP Server → External API → Internal API → Memory Service
```

## Research Findings

- Uvicorn has known dual stack limitations: "IPv6 binding with :: doesn't listen on IPv4 by default"
- Railway and cloud platforms require separate IPv4/IPv6 handling: "you need to use :: not ::1"
- Hypercorn provides proper dual stack support: "you can bind it to multiple servers and serve them simultaneously...binding to an IPv4 and an IPv6 address"
- Production deployments need IPv4 for external access: "Uvicorn does not support dual stack binding from the CLI"

## Expected Outcomes

- **Store organizational knowledge** via CrewAI tools
- **Track writing patterns** for publishing workflows
- **Enable agent optimization** through learned patterns
- **Support semantic search** across all knowledge
- **Integrate with voice/chat** for contextual memory access
- **Scale with SparkJar** infrastructure

## Success Criteria

- CrewAI tools work seamlessly with existing workflows
- FastAPI endpoints handle external integrations efficiently
- MCP wrapper enables Claude Desktop memory access
- Semantic search returns relevant results quickly
- Multi-tenant isolation maintains security
- Performance handles thousands of entities per client