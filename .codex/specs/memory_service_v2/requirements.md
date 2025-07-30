# Memory Service v2 Requirements

This document outlines the functional requirements for the next version of the SparkJAR memory service.

## Four-Realm Memory Hierarchy

The system must organize memories across four realms:

1. **Client** – highest priority overrides for specific clients.
2. **Synth Class** – shared knowledge for a class of synths.
3. **Synth** – memories unique to a single synth actor.
4. **Skill Module** – reusable knowledge modules that any synth can adopt.

Queries must resolve memories by priority in the order above, ensuring that client overrides take precedence over class and individual synth memories.

## Entity Validation

All API inputs must be validated before persistence:

- **Entities** require a valid `actor_id`, `entity_type`, and `content` field.
- **Observations** require an existing entity reference and structured metadata.
- Incoming requests with invalid types or missing fields must return `400` errors with descriptive messages.

## API Endpoints

The service exposes both internal and external APIs. Key endpoints include:

- `POST /entities` – upsert memory entities.
- `POST /observations` – attach observations to an entity.
- `GET /entities/{id}` – fetch a single entity including observations.
- `GET /search` – query memories across realms.
- `DELETE /entities/{id}` – soft delete an entity.

Both interfaces should maintain consistent request/response formats.

## Authentication

- External requests require an API token provided via the `Authorization` header.
- Internal service-to-service calls use a shared secret configured via environment variables.
- Unauthorized requests must receive a `401` response.

## Performance Targets

- Individual queries should return within **100ms** when using a remote database.
- Batch upserts must handle at least **50** entities per request.

