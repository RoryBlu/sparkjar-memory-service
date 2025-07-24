# SparkJar Memory Service API Documentation

## Overview

The SparkJar Memory Service provides organizational memory capabilities through two main interfaces:
- **REST API** - For direct HTTP integration
- **MCP (Model Context Protocol)** - For Claude Desktop and other MCP clients

## Authentication

### External API Authentication
The external API requires JWT bearer token authentication. All requests must include:
```
Authorization: Bearer <your-jwt-token>
```

### Obtaining a Token
```http
POST /auth/token
Content-Type: application/json

{
  "client_id": "uuid",
  "actor_type": "human|synth",
  "actor_id": "uuid",
  "api_key": "your-api-key"
}
```

Response:
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## REST API Endpoints

### Base URLs
- **Internal API**: `http://[::1]:8001` (IPv6, no auth required)
- **External API**: `https://your-domain:8443` (IPv4, auth required)

### 1. Create Entities

Create one or more memory entities with observations.

```http
POST /memory/entities
Authorization: Bearer <token>
Content-Type: application/json
```

Request Body:
```json
[
  {
    "name": "John Doe",
    "entityType": "person",
    "observations": [
      {
        "type": "skill",
        "value": "Python Programming",
        "skill_name": "Python Programming",
        "skill_category": "technical",
        "proficiency_level": "expert",
        "source": "interview",
        "confidence": 0.95
      },
      {
        "type": "fact",
        "value": "10 years experience in machine learning",
        "source": "resume"
      }
    ],
    "metadata": {
      "role": "Senior Engineer",
      "organization": "TechCorp",
      "email": "john.doe@techcorp.com"
    }
  }
]
```

Response:
```json
[
  {
    "id": "uuid",
    "entity_name": "John Doe",
    "entity_type": "person",
    "observations": [...],
    "metadata": {...},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### 2. Search Entities

Semantic search across all entities using natural language.

```http
POST /memory/search
Authorization: Bearer <token>
Content-Type: application/json
```

Request Body:
```json
{
  "query": "Python developers with ML experience",
  "entity_types": ["person", "synth"],  // optional filter (array)
  "limit": 10,
  "min_confidence": 0.7  // minimum similarity confidence (0-1)
}
```

Response:
```json
[
  {
    "id": "uuid",
    "entity_name": "John Doe",
    "entity_type": "person",
    "observations": [...],
    "similarity": 0.89
  }
]
```

### 3. Get Specific Entities

Retrieve entities by exact name match.

```http
POST /memory/nodes
Authorization: Bearer <token>
Content-Type: application/json
```

Request Body:
```json
{
  "names": ["John Doe", "Jane Smith"]
}
```

### 4. Add Observations

Add new observations to existing entities.

```http
POST /memory/observations
Authorization: Bearer <token>
Content-Type: application/json
```

Request Body:
```json
[
  {
    "entityName": "John Doe",
    "contents": [
      {
        "type": "skill",
        "value": "Docker",
        "skill_name": "Docker",
        "skill_category": "technical",
        "proficiency_level": "intermediate"
      }
    ]
  }
]
```

Response:
```json
[
  {
    "entityName": "John Doe",
    "addedObservations": 1,
    "totalObservations": 5
  }
]
```

### 5. Create Relationships

Create relationships between entities.

```http
POST /memory/relations
Authorization: Bearer <token>
Content-Type: application/json
```

Request Body:
```json
[
  {
    "from_entity_name": "John Doe",
    "to_entity_name": "Project Alpha",
    "relationType": "works_on",
    "metadata": {
      "role": "tech_lead",
      "since": "2024-01-01"
    }
  }
]
```

### 6. Read Full Graph

Get all entities and relationships for the authenticated actor.

```http
GET /memory/graph
Authorization: Bearer <token>
```

Response:
```json
{
  "entities": [...],
  "relations": [...],
  "total_entities": 42,
  "total_relations": 128
}
```

### 7. Delete Entities

Soft delete entities and their relationships.

```http
DELETE /memory/entities
Authorization: Bearer <token>
Content-Type: application/json
```

Request Body:
```json
{
  "entity_names": ["Entity to Delete"]
}
```

### 8. Delete Relationships

Delete specific relationships.

```http
DELETE /memory/relations
Authorization: Bearer <token>
Content-Type: application/json
```

Request Body:
```json
[
  {
    "from_entity_name": "John Doe",
    "to_entity_name": "Project Alpha",
    "relation_type": "works_on"
  }
]
```

### 9. Remember Conversation (SparkJar-specific)

Extract and store knowledge from conversation transcripts.

```http
POST /memory/remember_conversation
Authorization: Bearer <token>
Content-Type: application/json
```

Request Body:
```json
{
  "conversation_text": "Alice: I've been working on ML...\nBob: Great!...",
  "participants": ["Alice", "Bob"],
  "context": {
    "meeting_type": "standup",
    "date": "2024-01-01T10:00:00Z",
    "project": "Project Alpha"
  }
}
```

Response:
```json
{
  "entities_created": [...],
  "entities_updated": [...],
  "relations_created": [...],
  "observations_added": [...]
}
```

### 10. Find Connections (SparkJar-specific)

Find paths between entities using graph traversal.

```http
POST /memory/find_connections
Authorization: Bearer <token>
Content-Type: application/json
```

Request Body:
```json
{
  "from_entity": "John Doe",
  "to_entity": "Project Alpha",  // optional
  "max_hops": 3,
  "relationship_types": ["works_on", "manages", "knows"]  // optional filter
}
```

Response (when to_entity specified):
```json
{
  "from_entity": "John Doe",
  "to_entity": "Project Alpha",
  "paths": [
    {
      "path": ["John Doe", "Team A", "Project Alpha"],
      "relationships": [...],
      "length": 2
    }
  ],
  "shortest_path_length": 2,
  "total_paths_found": 3
}
```

Response (when to_entity not specified):
```json
{
  "from_entity": "John Doe",
  "connections": {
    "Project Alpha": [/* paths */],
    "Jane Smith": [/* paths */],
    ...
  },
  "total_connected_entities": 15
}
```

### 11. Get Client Insights (SparkJar-specific)

Generate insights about the client's knowledge graph.

```http
GET /memory/insights
Authorization: Bearer <token>
```

Response:
```json
{
  "summary": {
    "total_people": 25,
    "total_projects": 8,
    "unique_skills": 45,
    "average_connections_per_entity": 3.2,
    "most_connected_entities": [...]
  },
  "skill_distribution": {
    "Python": {
      "count": 12,
      "people": [...]
    },
    ...
  },
  "knowledge_gaps": [
    {
      "skill": "Kubernetes",
      "current_expert": "John Doe",
      "risk": "Single point of knowledge"
    }
  ],
  "underutilized_expertise": [
    {
      "person": "Jane Smith",
      "skills": ["Machine Learning", "Data Science"],
      "current_connections": 1,
      "recommendation": "Consider involving in more projects"
    }
  ],
  "collaboration_opportunities": [
    {
      "person1": "Alice",
      "person1_skills": ["Frontend", "React"],
      "person2": "Bob",
      "person2_skills": ["Backend", "Node.js"],
      "reason": "Complementary skills, not currently connected"
    }
  ],
  "entity_statistics": {...},
  "relationship_statistics": {...}
}
```

## Observation Types

### 1. Skill Observation
```json
{
  "type": "skill",
  "value": "Skill name",
  "skill_name": "Skill name",
  "skill_category": "technical|creative|analytical|communication|leadership|other",
  "proficiency_level": "beginner|intermediate|advanced|expert",
  "evidence": ["certification", "project work"],
  "source": "assessment",
  "confidence": 0.9
}
```

### 2. Database Reference
```json
{
  "type": "database_ref",
  "value": {
    "table": "client_users",
    "id": "uuid"
  },
  "relationship_type": "created|modified|referenced|derived_from|related_to",
  "source": "system"
}
```

### 3. Writing Pattern
```json
{
  "type": "writing_pattern",
  "value": "Uses bullet points for clarity",
  "pattern_type": "style|workflow|structure|habit|preference",
  "content_type": "blog|article|email|documentation|social|other",
  "frequency": "always|usually|sometimes|rarely",
  "description": "Detailed description",
  "source": "content_analysis"
}
```

### 4. General Fact
```json
{
  "type": "fact",
  "value": "Any factual information",
  "source": "interview",
  "confidence": 1.0,
  "tags": ["important", "verified"]
}
```

## Entity Types

Common entity types:
- `person` - Human individuals
- `synth` - AI agents or bots
- `project` - Projects or initiatives
- `company` - Organizations
- `skill` - Skill entities
- `document` - Documents or artifacts
- `event` - Events or meetings

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request format or validation error"
}
```

### 401 Unauthorized
```json
{
  "detail": "Token expired or invalid"
}
```

### 404 Not Found
```json
{
  "detail": "Entity 'name' not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal service error: details"
}
```

## Rate Limits

- **Internal API**: No rate limits
- **External API**: 
  - 100 requests per minute per token
  - 1000 entities per batch creation
  - 100 search results maximum

## Best Practices

1. **Batch Operations**: Create multiple entities in a single request
2. **Semantic Search**: Use natural language queries for best results
3. **Observation Types**: Use specific types for better schema validation
4. **Metadata**: Include relevant metadata for richer context
5. **Confidence Scores**: Set appropriate confidence levels (0-1)
6. **Source Attribution**: Always specify the source of observations

## Example: Python Client

```python
import httpx
import asyncio
from datetime import datetime

class MemoryClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    async def create_entity(self, name: str, entity_type: str, observations: list):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/memory/entities",
                json=[{
                    "name": name,
                    "entityType": entity_type,
                    "observations": observations
                }],
                headers=self.headers
            )
            return response.json()
    
    async def search(self, query: str, limit: int = 10):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/memory/search",
                json={
                    "query": query,
                    "limit": limit,
                    "threshold": 0.7
                },
                headers=self.headers
            )
            return response.json()

# Usage
async def main():
    client = MemoryClient("https://api.example.com", "your-token")
    
    # Create entity
    result = await client.create_entity(
        "Alice Johnson",
        "person",
        [{
            "type": "skill",
            "value": "Project Management",
            "skill_name": "Project Management",
            "skill_category": "leadership",
            "proficiency_level": "expert"
        }]
    )
    
    # Search
    results = await client.search("project managers")
    print(f"Found {len(results)} matches")

asyncio.run(main())
```

## Health Check

```http
GET /health
```

No authentication required. Returns:
```json
{
  "status": "healthy",
  "internal_api": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```