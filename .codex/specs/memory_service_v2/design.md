# Memory Service v2 Design

This document describes the high-level architecture for the v2 memory service, including data models and API interactions.

## Architecture Overview

The service is composed of two FastAPI applications:

1. **External API** – exposed to other services and clients.
2. **Internal API** – used by crew agents and internal processes.

Both applications share the same database layer and validation logic. A common module should provide request schemas and response formatting to ensure consistency.

### Database

A single PostgreSQL database (Supabase in production) stores all memory data. Core tables include:

- `memory_entities` – stores entities with fields `id`, `actor_id`, `entity_type`, `content`, `created_at`, and `deleted`.
- `memory_observations` – stores observations tied to an entity with metadata JSONB.
- `object_schemas` – defines validation schemas for specific entity types.

### Data Access Layer

The service uses SQLAlchemy models with pydantic schemas for validation. Queries should respect the four-realm hierarchy by joining related memories based on `actor_id` and realm type.

### API Interaction

All endpoints return JSON responses with `success` or `error` fields. Examples:

- **Create Entity** – returns `{ "id": <uuid>, "status": "created" }`.
- **Search** – returns a list of entities and observations sorted by realm priority.

Batch operations accept arrays of objects and provide per-object status messages.

## Authentication Flow

External requests pass an API token which is verified against a table of active tokens. Internal requests include an `X-Internal-Secret` header which must match the configured secret. The middleware layer handles authentication and returns `401` on failure.

## Deployment Considerations

- The service should ship with Dockerfiles for both internal and external deployments.
- Health endpoints (`/health`) expose basic status for Railway checks.
- Environment variables specify database connection strings and shared secrets.

