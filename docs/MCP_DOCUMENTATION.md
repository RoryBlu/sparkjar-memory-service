# SparkJar Memory MCP (Model Context Protocol) Documentation

## Overview

The SparkJar Memory MCP server provides memory capabilities to Claude Desktop and other MCP-compatible clients. It wraps the Memory Service API in the standard MCP protocol.

## Installation & Configuration

### For Claude Desktop

1. Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sparkjar-memory": {
      "command": "python",
      "args": ["/path/to/sparkjar-crew/services/memory-service/mcp_server.py"],
      "env": {
        "MEMORY_EXTERNAL_API_URL": "https://your-memory-api.com",
        "MEMORY_SERVICE_TOKEN": "your-jwt-token"
      }
    }
  }
}
```

2. Restart Claude Desktop

### Environment Variables

- `MEMORY_EXTERNAL_API_URL` - URL of the external memory API (required)
- `MEMORY_SERVICE_TOKEN` - JWT authentication token (required)

## Available Tools

### 1. create_memory_entities

Create one or more entities with observations in the memory system.

**Parameters:**
- `entities` (array, required) - List of entities to create

**Entity Structure:**
```json
{
  "name": "string",
  "entityType": "string",
  "observations": [
    {
      "type": "string",
      "value": "any",
      "source": "string",
      "confidence": 0.0-1.0,
      // Additional type-specific fields
    }
  ],
  "metadata": {
    // Optional metadata fields
  }
}
```

**Example Usage in Claude:**
```
I'll create a memory entity for John Doe, a Python developer:

<use_mcp_tool>
<server_name>sparkjar-memory</server_name>
<tool_name>create_memory_entities</tool_name>
<parameters>
{
  "entities": [
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
          "source": "interview"
        }
      ],
      "metadata": {
        "role": "Senior Developer",
        "organization": "TechCorp"
      }
    }
  ]
}
</parameters>
</use_mcp_tool>
```

### 2. search_memory

Search memory using semantic similarity to find relevant entities.

**Parameters:**
- `query` (string, required) - Natural language search query
- `entity_types` (array, optional) - Filter by entity types
- `limit` (integer, optional, default: 10) - Maximum results
- `min_confidence` (float, optional, default: 0.7) - Minimum similarity confidence (0-1)

**Example Usage:**
```
Let me search for Python developers in the memory:

<use_mcp_tool>
<server_name>sparkjar-memory</server_name>
<tool_name>search_memory</tool_name>
<parameters>
{
  "query": "Python developers with machine learning experience",
  "entity_types": ["person", "synth"],
  "limit": 5,
  "min_confidence": 0.7
}
</parameters>
</use_mcp_tool>
```

### 3. get_entities

Retrieve specific entities by their exact names.

**Parameters:**
- `names` (array of strings, required) - List of entity names to retrieve

**Example Usage:**
```
<use_mcp_tool>
<server_name>sparkjar-memory</server_name>
<tool_name>get_entities</tool_name>
<parameters>
{
  "names": ["John Doe", "Project Alpha"]
}
</parameters>
</use_mcp_tool>
```

### 4. add_observations

Add new observations to existing entities.

**Parameters:**
- `observations` (array, required) - List of observations to add

**Observation Structure:**
```json
{
  "entityName": "string",
  "contents": [
    {
      "type": "string",
      "value": "any",
      // Type-specific fields
    }
  ]
}
```

**Example Usage:**
```
<use_mcp_tool>
<server_name>sparkjar-memory</server_name>
<tool_name>add_observations</tool_name>
<parameters>
{
  "observations": [
    {
      "entityName": "John Doe",
      "contents": [
        {
          "type": "skill",
          "value": "Docker",
          "skill_name": "Docker",
          "skill_category": "technical",
          "proficiency_level": "advanced"
        }
      ]
    }
  ]
}
</parameters>
</use_mcp_tool>
```

### 5. create_memory_relations

Create relationships between entities.

**Parameters:**
- `relations` (array, required) - List of relationships to create

**Relation Structure:**
```json
{
  "from_entity_name": "string",
  "to_entity_name": "string",
  "relationType": "string",
  "metadata": {}
}
```

**Example Usage:**
```
<use_mcp_tool>
<server_name>sparkjar-memory</server_name>
<tool_name>create_memory_relations</tool_name>
<parameters>
{
  "relations": [
    {
      "from_entity_name": "John Doe",
      "to_entity_name": "Project Alpha",
      "relationType": "leads",
      "metadata": {
        "role": "Tech Lead",
        "since": "2024-01-01"
      }
    }
  ]
}
</parameters>
</use_mcp_tool>
```

### 6. read_memory_graph

Get all entities and relationships for the authenticated actor.

**Parameters:** None

**Example Usage:**
```
<use_mcp_tool>
<server_name>sparkjar-memory</server_name>
<tool_name>read_memory_graph</tool_name>
<parameters>{}</parameters>
</use_mcp_tool>
```

### 7. delete_entities

Delete entities and their associated relationships.

**Parameters:**
- `entity_names` (array of strings, required) - Names of entities to delete

**Example Usage:**
```
<use_mcp_tool>
<server_name>sparkjar-memory</server_name>
<tool_name>delete_entities</tool_name>
<parameters>
{
  "entity_names": ["Old Project"]
}
</parameters>
</use_mcp_tool>
```

### 8. delete_relations

Delete specific relationships between entities.

**Parameters:**
- `relations` (array, required) - List of relations to delete

**Example Usage:**
```
<use_mcp_tool>
<server_name>sparkjar-memory</server_name>
<tool_name>delete_relations</tool_name>
<parameters>
{
  "relations": [
    {
      "from_entity_name": "John Doe",
      "to_entity_name": "Old Project",
      "relation_type": "works_on"
    }
  ]
}
</parameters>
</use_mcp_tool>
```

### 9. remember_conversation (SparkJar-specific)

Extract and store knowledge from conversation transcripts.

**Parameters:**
- `conversation_text` (string, required) - Full conversation transcript
- `participants` (array of strings, required) - List of participant names/IDs
- `context` (object, required) - Meeting type, date, purpose, etc.

**Example Usage:**
```
<use_mcp_tool>
<server_name>sparkjar-memory</server_name>
<tool_name>remember_conversation</tool_name>
<parameters>
{
  "conversation_text": "Alice: I've been working on the ML pipeline for customer analytics.\nBob: Great! I know you're an expert in Python and TensorFlow.\nAlice: Thanks! I'm also using advanced SQL optimization.",
  "participants": ["Alice", "Bob"],
  "context": {
    "meeting_type": "standup",
    "date": "2024-01-01T10:00:00Z",
    "project": "Customer Analytics"
  }
}
</parameters>
</use_mcp_tool>
```

### 10. find_connections (SparkJar-specific)

Find paths between entities using graph traversal.

**Parameters:**
- `from_entity` (string, required) - Starting entity name
- `to_entity` (string, optional) - Target entity name (finds all if not specified)
- `max_hops` (integer, optional, default: 3) - Maximum relationship hops
- `relationship_types` (array, optional) - Filter by specific relationship types

**Example Usage:**
```
Finding specific connection:
<use_mcp_tool>
<server_name>sparkjar-memory</server_name>
<tool_name>find_connections</tool_name>
<parameters>
{
  "from_entity": "John Doe",
  "to_entity": "Project Alpha",
  "max_hops": 3,
  "relationship_types": ["works_on", "manages", "contributes_to"]
}
</parameters>
</use_mcp_tool>

Finding all connections:
<use_mcp_tool>
<server_name>sparkjar-memory</server_name>
<tool_name>find_connections</tool_name>
<parameters>
{
  "from_entity": "Sarah Chen",
  "max_hops": 2
}
</parameters>
</use_mcp_tool>
```

### 11. get_client_insights (SparkJar-specific)

Generate insights and analytics about the client's knowledge graph.

**Parameters:** None

**Example Usage:**
```
<use_mcp_tool>
<server_name>sparkjar-memory</server_name>
<tool_name>get_client_insights</tool_name>
<parameters>{}</parameters>
</use_mcp_tool>
```

Returns comprehensive insights including:
- Knowledge gaps (skills with single expert)
- Skill distribution across team
- Underutilized expertise
- Collaboration opportunities
- Entity and relationship statistics

## MCP Resources

The memory system provides browsable resources:

### memory://entities/{type}
Browse all entities of a specific type (person, project, skill, etc.)

### memory://relationships/{type}
Browse all relationships of a specific type (works_on, knows, manages, etc.)

### memory://recent-activity
View recent memory system activity (last 20 entities and relationships)

## MCP Prompts

Pre-configured prompts for common memory operations:

### extract-entities
Extract entities from text with optional focus areas.

**Arguments:**
- `text` - Source text to analyze
- `focus_areas` (optional) - Specific types to focus on

### relationship-analysis
Analyze relationships between two entities.

**Arguments:**
- `entity1` - First entity name
- `entity2` - Second entity name
- `context` (optional) - Additional context

### skill-assessment
Evaluate skill levels from observations.

**Arguments:**
- `person` - Person entity name
- `skill_area` - Skill category to assess

## Observation Types Reference

### Skill Observation
```json
{
  "type": "skill",
  "value": "Skill description",
  "skill_name": "Exact skill name",
  "skill_category": "technical|creative|analytical|communication|leadership|other",
  "proficiency_level": "beginner|intermediate|advanced|expert",
  "evidence": ["list", "of", "evidence"],
  "source": "where this came from",
  "confidence": 0.95
}
```

### Database Reference
```json
{
  "type": "database_ref",
  "value": {
    "table": "table_name",
    "id": "record_uuid"
  },
  "relationship_type": "created|modified|referenced|derived_from|related_to",
  "source": "system"
}
```

### Writing Pattern
```json
{
  "type": "writing_pattern",
  "value": "Pattern description",
  "pattern_type": "style|workflow|structure|habit|preference",
  "content_type": "blog|article|email|documentation|social|other",
  "frequency": "always|usually|sometimes|rarely",
  "description": "Detailed description",
  "source": "analysis"
}
```

### General Fact
```json
{
  "type": "fact",
  "value": "Any factual information",
  "source": "source of information",
  "confidence": 1.0,
  "tags": ["optional", "tags"]
}
```

## Entity Types

Common entity types you can use:
- `person` - Human individuals
- `synth` - AI agents or assistants
- `project` - Projects or initiatives
- `company` - Organizations or companies
- `skill` - Skills as entities
- `document` - Documents or artifacts
- `event` - Events or meetings
- `concept` - Abstract concepts
- `tool` - Software tools or systems

## Common Workflows

### 1. Building a Knowledge Graph

```
1. Create person entities with their skills
2. Create project entities
3. Create relationships between people and projects
4. Add observations as you learn more
5. Search for expertise when needed
```

### 2. Tracking Interactions

```
1. Create entity for each person you interact with
2. Add observations about their preferences, skills, context
3. Create "interacted_with" relationships
4. Update with new observations after each interaction
```

### 3. Skill Mapping

```
1. Create person entities
2. Add skill observations with proficiency levels
3. Search by skill when forming teams
4. Track skill development over time
```

## Error Handling

All tools return a response object:

**Success:**
```json
{
  "success": true,
  "result": { /* actual response data */ }
}
```

**Error:**
```json
{
  "success": false,
  "result": {
    "error": "Error message"
  }
}
```

## Best Practices

1. **Entity Names**: Use consistent, unique names for entities
2. **Observation Types**: Use specific types for better validation
3. **Metadata**: Include relevant metadata for context
4. **Relationships**: Keep relationship types consistent
5. **Search Queries**: Use natural language for better semantic matching
6. **Batch Operations**: Create multiple entities/relations in one call

## Troubleshooting

### Tool Not Available
- Ensure MCP server is properly configured in Claude Desktop
- Check that environment variables are set correctly
- Verify the API server is accessible

### Authentication Errors
- Token may be expired - generate a new one
- Ensure token has correct permissions

### No Search Results
- Try broader search terms
- Lower the similarity threshold
- Check if entities exist with `get_entities`

## Example Conversation

```
User: Can you help me track information about my team members?

Claude: I'll help you track information about your team members using the memory system. Let me create entries for them.

<use_mcp_tool>
<server_name>sparkjar-memory</server_name>
<tool_name>create_memory_entities</tool_name>
<parameters>
{
  "entities": [
    {
      "name": "Sarah Chen",
      "entityType": "person",
      "observations": [
        {
          "type": "skill",
          "value": "Frontend Development",
          "skill_name": "React",
          "skill_category": "technical",
          "proficiency_level": "expert"
        },
        {
          "type": "fact",
          "value": "Leads the UI/UX initiatives",
          "source": "team_structure"
        }
      ],
      "metadata": {
        "role": "Frontend Lead",
        "team": "Product Development"
      }
    }
  ]
}
</parameters>
</use_mcp_tool>

I've created an entry for Sarah Chen. Would you like me to add more team members or search for specific expertise?
```