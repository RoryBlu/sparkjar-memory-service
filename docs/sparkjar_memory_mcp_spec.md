# SparkJar Memory System - MCP Interface Specification

## Overview

This document defines the Model Context Protocol (MCP) interface for the SparkJar Memory System. The system is **multi-tenant with strict client isolation** - each client's data is completely walled off from others.

## MCP Components

MCP supports three types of capabilities:
- **Tools**: Functions that agents can call to perform actions
- **Resources**: Static or dynamic content that can be read
- **Prompts**: Reusable prompt templates with arguments

---

## Tools (Core Memory Operations)

### Entity Management

#### `memory:create_entities`
**Purpose**: Create new entities in the knowledge graph with initial observations.

**What it does**: 
- Creates one or more entities (people, projects, skills, concepts)
- Each entity gets a unique ID within the client's namespace
- Initial observations are validated against appropriate schemas
- Generates embeddings for semantic search
- **Client isolation**: Only creates entities for the authenticated client

**Use cases**:
- "Remember that John Doe is a senior Python developer at Acme Corp"
- "Store this new project called 'Customer Analytics Dashboard'"
- "Add this skill observation: Sarah demonstrated advanced SQL optimization"

**Parameters**:
- `entities`: Array of entity objects with name, type, and initial observations

---

#### `memory:add_observations`
**Purpose**: Add new observations to existing entities.

**What it does**:
- Finds existing entities by name within the client's data
- Appends new observations to the entity's observation list
- Re-generates embeddings to include new information
- Validates observations against schemas
- **Client isolation**: Only operates on the client's entities

**Use cases**:
- "John just completed a machine learning certification"
- "The dashboard project now includes real-time alerts"
- "Sarah showed expertise in database indexing during today's code review"

**Parameters**:
- `observations`: Array with entity names and new observation content

---

### Relationship Management

#### `memory:create_relations`
**Purpose**: Create connections between entities.

**What it does**:
- Links entities with labeled relationships (works_on, knows, uses, etc.)
- Supports many-to-many relationships
- Stores relationship metadata (strength, context, date)
- **Client isolation**: Only creates relations between entities within the same client

**Use cases**:
- "John works_on Customer Analytics Dashboard"
- "Sarah mentors John"
- "Python is_used_in machine learning projects"

**Parameters**:
- `relations`: Array of relationship objects with from/to entities and relation type

---

### Search & Discovery

#### `memory:search_nodes` ⭐ **DETAILED EXPLANATION**
**Purpose**: Semantic search across the knowledge graph using natural language.

**How semantic search works**:
1. **Query embedding**: Your search text gets converted into a 768-dimensional vector using the same embedding model that created entity embeddings
2. **Vector similarity**: The system finds entities whose embeddings are "close" to your query embedding in vector space
3. **Relevance ranking**: Results are ranked by cosine similarity scores (0-1, higher = more relevant)
4. **Context understanding**: The search understands meaning, not just keywords

**What makes it "semantic"**:
- "Python expert" will find entities about "programming", "software development", "coding"
- "Data scientist" will find people with "machine learning", "analytics", "statistics" observations
- "Writing patterns" will find entities about "content creation", "publishing workflows", "editorial processes"

**Examples**:
- Search: "machine learning" → Finds: people with ML skills, ML projects, Python/R tools, data science patterns
- Search: "communication skills" → Finds: people with presentation experience, writing abilities, team leadership
- Search: "database optimization" → Finds: SQL experts, performance tuning projects, indexing knowledge

**Client isolation**: Only searches within the authenticated client's entities

**Parameters**:
- `query`: Natural language search text
- `limit`: Maximum number of results (default: 10)
- `entity_types`: Optional filter by entity types
- `min_confidence`: Minimum similarity score threshold

---

#### `memory:open_nodes`
**Purpose**: Get complete details about specific entities by name.

**What it does**:
- Retrieves full entity data including all observations and metadata
- Shows all relationships (incoming and outgoing)
- Provides embedding similarity scores if requested
- **Client isolation**: Only returns entities owned by the client

**Use cases**:
- "Show me everything about John Doe"
- "Get full details on the Customer Analytics project"
- "What do I know about Python programming patterns?"

**Parameters**:
- `names`: Array of entity names to retrieve

---

#### `memory:read_graph`
**Purpose**: Get an overview of the entire knowledge graph structure.

**What it does**:
- Returns high-level statistics (entity counts by type, relationship counts)
- Shows recent activity and most connected entities
- Provides graph health metrics
- **Client isolation**: Only shows the client's graph data

**Use cases**:
- Understanding the scope of stored knowledge
- Finding highly connected entities (key people, important projects)
- Debugging memory system health

---

### SparkJar-Specific Methods

#### `memory:remember_conversation`
**Purpose**: Extract and store knowledge from conversation transcripts.

**What it does**:
- Analyzes conversation text to identify entities and relationships
- Extracts skills, insights, and patterns mentioned
- Creates or updates entities automatically
- Links conversation participants and topics
- **Client isolation**: Only stores in the client's namespace

**Use cases**:
- "Process this client meeting transcript"
- "Remember insights from this team standup"
- "Extract action items and responsibilities from this call"

**Parameters**:
- `conversation_text`: Full conversation transcript
- `participants`: Array of participant names/IDs
- `context`: Meeting type, date, purpose

---

#### `memory:find_connections`
**Purpose**: Graph traversal to find relationships between entities.

**What it does**:
- Finds paths between two entities (shortest path, all paths)
- Discovers indirect connections (John → Python → Data Science → Sarah)
- Maps relationship strength and frequency
- **Client isolation**: Only traverses within client's graph

**Use cases**:
- "How is John connected to the Analytics project?"
- "Find common connections between Sarah and Mike"
- "Show the path from Python skills to current projects"

**Parameters**:
- `from_entity`: Starting entity name
- `to_entity`: Target entity name (optional - finds all connections if not specified)
- `max_hops`: Maximum relationship hops to traverse
- `relationship_types`: Filter by specific relationship types

---

#### `memory:get_client_insights`
**Purpose**: Generate insights and analytics about the client's knowledge graph.

**What it does**:
- Identifies knowledge gaps and clusters
- Shows skill distribution across people
- Highlights underutilized expertise
- Suggests relationship opportunities
- **Client isolation**: Only analyzes the client's data

**Use cases**:
- "What skills are missing from our team?"
- "Which projects need more technical support?"
- "Who should be connected for knowledge sharing?"

---

## Resources (Knowledge Access)

### `memory://entities/{type}`
**Purpose**: Browse entities by type (person, project, skill, pattern).

**What it provides**:
- Structured list of all entities of a specific type
- Summary information and key observations
- Last updated timestamps and activity levels

### `memory://relationships/{type}`
**Purpose**: Browse relationships by type (works_on, knows, uses).

**What it provides**:
- All relationships of a specific type within the client
- Relationship strength and frequency data
- Network analysis insights

### `memory://recent-activity`
**Purpose**: Show recent memory system activity.

**What it provides**:
- Recently created or updated entities
- New relationships formed
- Search query patterns and results

---

## Prompts (Memory-Aware Templates)

### `extract-entities`
**Purpose**: Prompt template for extracting entities from text.

**Arguments**:
- `text`: Source text to analyze
- `focus_areas`: Specific types of entities to look for

### `relationship-analysis`
**Purpose**: Prompt template for analyzing relationships between entities.

**Arguments**:
- `entity1`: First entity name
- `entity2`: Second entity name
- `context`: Additional context for analysis

### `skill-assessment`
**Purpose**: Prompt template for evaluating skill levels from observations.

**Arguments**:
- `person`: Person entity name
- `skill_area`: Skill category to assess

---

## Client Isolation & Security

**Multi-tenant enforcement**:
- All operations include `client_id` from authentication
- Database queries use Row Level Security (RLS)
- No cross-client data access possible
- Separate embedding spaces per client

**Authentication flow**:
1. MCP client authenticates with JWT or API key
2. Token contains `client_id` and `actor_id`
3. All memory operations scoped to that client
4. Actor-level permissions within client (optional)

---

## Implementation Notes

**For developers**:
- Each MCP tool maps to internal API endpoints
- Resource URIs map to filtered data queries
- Prompt templates can access client-specific examples
- All operations must validate client isolation
- Embedding generation happens asynchronously
- Schema validation occurs before storage

**Performance considerations**:
- Semantic search uses vector indexes (pgvector)
- Relationship queries use graph traversal optimization
- Large result sets use pagination
- Embedding caching for frequently accessed entities