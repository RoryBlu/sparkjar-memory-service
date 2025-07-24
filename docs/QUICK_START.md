# SparkJar Memory Service - Quick Start Guide

## Overview

The SparkJar Memory Service provides organizational memory capabilities through semantic search and relationship tracking. It stores information about people, projects, skills, and any other entities important to your organization.

## Key Features

- 🧠 **Semantic Search** - Find information using natural language
- 🔗 **Relationship Tracking** - Map connections between entities
- 📝 **Observation History** - Track changes and learnings over time
- 🔍 **Multi-tenant Isolation** - Secure data separation
- ✅ **Schema Validation** - Ensure data quality
- 🚀 **High Performance** - Optimized for agent workloads

## Quick Start Examples

### 1. Store Information About a Person

```bash
curl -X POST https://api.example.com/memory/entities \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{
    "name": "Alice Johnson",
    "entityType": "person",
    "observations": [{
      "type": "skill",
      "value": "Machine Learning",
      "skill_name": "Machine Learning",
      "skill_category": "technical",
      "proficiency_level": "expert"
    }]
  }]'
```

### 2. Search for Expertise

```bash
curl -X POST https://api.example.com/memory/search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Who knows about machine learning?",
    "limit": 5
  }'
```

### 3. Create Relationships

```bash
curl -X POST https://api.example.com/memory/relations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{
    "from_entity_name": "Alice Johnson",
    "to_entity_name": "ML Project",
    "relationType": "leads"
  }]'
```

## Python Quick Start

```python
import httpx
import asyncio

class MemoryQuickStart:
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    async def quick_example(self):
        async with httpx.AsyncClient() as client:
            # 1. Create a person
            await client.post(
                f"{self.api_url}/memory/entities",
                headers=self.headers,
                json=[{
                    "name": "Bob Smith",
                    "entityType": "person",
                    "observations": [{
                        "type": "skill",
                        "value": "Python Expert",
                        "skill_category": "technical"
                    }]
                }]
            )
            
            # 2. Search for Python developers
            response = await client.post(
                f"{self.api_url}/memory/search",
                headers=self.headers,
                json={"query": "Python developers"}
            )
            
            results = response.json()
            print(f"Found {len(results)} Python developers")

# Run it
async def main():
    memory = MemoryQuickStart("https://api.example.com", "your-token")
    await memory.quick_example()

asyncio.run(main())
```

## Common Use Cases

### 1. Team Skill Tracking
- Store team members with their skills
- Search for specific expertise
- Track skill development over time

### 2. Project Knowledge Base
- Create entities for projects
- Link people to projects
- Track project outcomes and learnings

### 3. Meeting Intelligence
- Create event entities for meetings
- Link attendees
- Store key decisions and action items

### 4. Writing Pattern Analysis
- Track writing patterns for individuals
- Optimize content creation
- Maintain consistency

## Entity Types

- **person** - Team members, contacts
- **project** - Initiatives, products
- **skill** - Capabilities, expertise
- **event** - Meetings, milestones
- **document** - Reports, artifacts
- **company** - Organizations, partners

## Observation Types

- **skill** - Technical or soft skills
- **fact** - General information
- **writing_pattern** - Communication styles
- **database_ref** - Links to other systems

## Next Steps

1. Get an API token from your administrator
2. Review the full [API Documentation](./API_DOCUMENTATION.md)
3. For Claude Desktop users, see [MCP Documentation](./MCP_DOCUMENTATION.md)
4. Check out [usage examples](./examples/)

## Support

- GitHub Issues: https://github.com/RoryBlu/sparkjar-crew/issues
- Documentation: This directory
- API Status: `GET /health`