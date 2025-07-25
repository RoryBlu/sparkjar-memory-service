# sparkjar-memory-service

SparkJAR Memory Service - Hierarchical memory management for AI agents.

## Overview

This service provides:
- Hierarchical memory storage (client → synth_class → skill_module → synth)
- Entity and observation management
- Schema validation
- Vector embeddings for semantic search
- RESTful API with JWT authentication

## Quick Start

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the service
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8001
```

## API Endpoints

### Entity Management
- `POST /entities` - Create or update entity
- `GET /entities/{entity_id}` - Get entity by ID
- `GET /entities/by-name/{name}` - Get entity by name
- `DELETE /entities/{entity_id}` - Delete entity

### Observation Management
- `POST /observations` - Create observation
- `GET /observations/{observation_id}` - Get observation
- `GET /observations/by-entity/{entity_id}` - List observations for entity
- `DELETE /observations/{observation_id}` - Delete observation

### Memory Queries
- `POST /query` - Query memories with hierarchy traversal
- `GET /hierarchy/{entity_id}` - Get entity hierarchy
- `POST /search` - Semantic search across memories

### Health & Admin
- `GET /health` - Service health check
- `GET /metrics` - Service metrics

## Memory Hierarchy

```
client (organization)
  └── synth_class (character type)
      └── skill_module (capabilities)
          └── synth (individual instance)
              └── human (user)
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://...

# Authentication
API_SECRET_KEY=your-secret-key

# OpenAI
OPENAI_API_KEY=your-openai-key

# Embeddings
EMBEDDING_PROVIDER=custom
EMBEDDINGS_API_URL=http://embeddings.railway.internal:8000
```

## Development

```bash
# Run tests
pytest tests/

# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/
```

## Docker

```bash
# Build image
docker build -t sparkjar-memory-service .

# Run container
docker run -p 8001:8001 --env-file .env sparkjar-memory-service
```

## Notes

- Extracted from sparkjar-crew monorepo
- Uses PostgreSQL with pgvector for embeddings
- Supports multiple actor types: client, synth_class, skill_module, synth, human, system
- Schema validation for all observation types