# Sequential Thinking Feature Documentation

## Overview

The Sequential Thinking feature provides a structured way to track problem-solving processes through numbered thoughts that can be revised. It's designed to capture the iterative nature of complex problem-solving while maintaining a clear audit trail of the thinking process.

## Key Concepts

### Thinking Sessions
A thinking session represents a complete problem-solving process with:
- **Problem Statement**: The question or challenge being addressed
- **Status**: Active, Completed, or Abandoned
- **Thoughts**: Numbered sequence of thoughts
- **Final Answer**: The conclusion (required for completed sessions)

### Thoughts
Individual units of reasoning within a session:
- **Sequential Numbering**: Each thought gets the next available number
- **Immutable**: Once created, thoughts cannot be edited
- **Revisable**: Can be superseded by new thoughts that reference the original

### Revisions
A special type of thought that explicitly revises a previous thought:
- **References Original**: Points to the thought number being revised
- **Gets New Number**: Follows the same sequential numbering
- **Preserves History**: Original thought remains visible

## API Endpoints

### Session Management

#### Create Session
```http
POST /api/v1/thinking/sessions
Content-Type: application/json

{
  "client_user_id": "123e4567-e89b-12d3-a456-426614174000",
  "session_name": "API Design Review",
  "problem_statement": "How should we structure the new payment processing API?",
  "metadata": {
    "project": "payments",
    "priority": "high"
  }
}
```

Response:
```json
{
  "id": "456e7890-e89b-12d3-a456-426614174001",
  "client_user_id": "123e4567-e89b-12d3-a456-426614174000",
  "session_name": "API Design Review",
  "problem_statement": "How should we structure the new payment processing API?",
  "status": "active",
  "metadata": {"project": "payments", "priority": "high"},
  "created_at": "2024-01-15T10:00:00Z",
  "thoughts": []
}
```

#### Get Session
```http
GET /api/v1/thinking/sessions/{session_id}?include_thoughts=true
```

#### List User Sessions
```http
GET /api/v1/thinking/users/{client_user_id}/sessions?status=active&page=1&page_size=10
```

### Thought Management

#### Add Thought
```http
POST /api/v1/thinking/sessions/{session_id}/thoughts
Content-Type: application/json

{
  "thought_content": "We should use RESTful principles with clear resource endpoints",
  "metadata": {
    "category": "architecture",
    "confidence": 0.8
  }
}
```

Response:
```json
{
  "id": "789e0123-e89b-12d3-a456-426614174002",
  "session_id": "456e7890-e89b-12d3-a456-426614174001",
  "thought_number": 1,
  "thought_content": "We should use RESTful principles with clear resource endpoints",
  "is_revision": false,
  "metadata": {"category": "architecture", "confidence": 0.8},
  "created_at": "2024-01-15T10:05:00Z"
}
```

#### Revise Thought
```http
POST /api/v1/thinking/sessions/{session_id}/revise
Content-Type: application/json

{
  "thought_number": 1,
  "revised_content": "Actually, we should use GraphQL for better flexibility",
  "metadata": {
    "reason": "performance",
    "discussed_with": "team"
  }
}
```

### Session Completion

#### Complete Session
```http
POST /api/v1/thinking/sessions/{session_id}/complete
Content-Type: application/json

{
  "final_answer": "Based on the analysis, we will implement a GraphQL API with the following schema...",
  "metadata": {
    "decision_factors": ["performance", "flexibility", "team_expertise"]
  }
}
```

#### Abandon Session
```http
POST /api/v1/thinking/sessions/{session_id}/abandon
Content-Type: application/json

{
  "reason": "Requirements changed significantly",
  "metadata": {
    "new_project_id": "proj-456"
  }
}
```

### Analytics

#### Get Session Statistics
```http
GET /api/v1/thinking/sessions/{session_id}/stats
```

Response:
```json
{
  "session_id": "456e7890-e89b-12d3-a456-426614174001",
  "client_user_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "active",
  "total_thoughts": 15,
  "revision_count": 3,
  "revised_thought_numbers": [1, 5, 7],
  "average_thought_length": 127,
  "duration_seconds": 3600,
  "thoughts_per_minute": 0.25
}
```

## Usage Examples

### Complete Problem-Solving Session

```python
import httpx
from uuid import uuid4

# Initialize client
client = httpx.Client(base_url="http://localhost:8000/api/v1")

# 1. Create a new session
session_response = client.post("/thinking/sessions", json={
    "client_user_id": str(uuid4()),
    "session_name": "Database Migration Strategy",
    "problem_statement": "How should we migrate from MongoDB to PostgreSQL?"
})
session = session_response.json()
session_id = session["id"]

# 2. Add initial thoughts
client.post(f"/thinking/sessions/{session_id}/thoughts", json={
    "thought_content": "We need to map MongoDB collections to PostgreSQL tables"
})

client.post(f"/thinking/sessions/{session_id}/thoughts", json={
    "thought_content": "Consider using JSONB columns for flexible schema parts"
})

client.post(f"/thinking/sessions/{session_id}/thoughts", json={
    "thought_content": "Migration should be done in phases to minimize downtime"
})

# 3. Revise a thought
client.post(f"/thinking/sessions/{session_id}/revise", json={
    "thought_number": 2,
    "revised_content": "Use JSONB only for truly dynamic data; prefer normalized tables where possible"
})

# 4. Add more thoughts
client.post(f"/thinking/sessions/{session_id}/thoughts", json={
    "thought_content": "Create a dual-write system during transition period"
})

# 5. Complete the session
client.post(f"/thinking/sessions/{session_id}/complete", json={
    "final_answer": """
    Migration Strategy:
    1. Analyze and categorize MongoDB collections
    2. Design PostgreSQL schema with appropriate use of JSONB
    3. Implement dual-write system
    4. Migrate historical data in batches
    5. Validate data integrity
    6. Switch reads to PostgreSQL
    7. Decommission MongoDB
    """
})

# 6. View the complete session
final_session = client.get(f"/thinking/sessions/{session_id}?include_thoughts=true").json()
print(f"Total thoughts: {len(final_session['thoughts'])}")
print(f"Final answer: {final_session['final_answer']}")
```

### Analyzing Thinking Patterns

```python
# Get all sessions for a user
sessions = client.get(f"/thinking/users/{user_id}/sessions").json()

# Analyze completed sessions
completed = [s for s in sessions["sessions"] if s["status"] == "completed"]
print(f"Completion rate: {len(completed) / len(sessions['sessions']) * 100:.1f}%")

# Get detailed stats for each session
for session in completed:
    stats = client.get(f"/thinking/sessions/{session['id']}/stats").json()
    print(f"Session '{session['session_name']}':")
    print(f"  - Duration: {stats['duration_seconds'] / 60:.1f} minutes")
    print(f"  - Total thoughts: {stats['total_thoughts']}")
    print(f"  - Revisions: {stats['revision_count']}")
    print(f"  - Thoughts/minute: {stats['thoughts_per_minute']:.2f}")
```

## Database Schema

### thinking_sessions
- `id`: UUID (Primary Key)
- `client_user_id`: UUID (Required)
- `session_name`: Text (Optional)
- `problem_statement`: Text (Optional)
- `status`: Text (active/completed/abandoned)
- `final_answer`: Text (Required when completed)
- `metadata`: JSONB
- `created_at`: Timestamp
- `completed_at`: Timestamp (Set when completed/abandoned)

### thoughts
- `id`: UUID (Primary Key)
- `session_id`: UUID (Foreign Key)
- `thought_number`: Integer (Sequential, unique per session)
- `thought_content`: Text (1-10000 characters)
- `is_revision`: Boolean
- `revises_thought_number`: Integer (Set when is_revision=true)
- `metadata`: JSONB
- `created_at`: Timestamp

## Best Practices

### Session Management
1. **Clear Problem Statements**: Start with well-defined problems
2. **Meaningful Names**: Use descriptive session names for easy retrieval
3. **Complete or Abandon**: Don't leave sessions in active state indefinitely

### Thought Creation
1. **Atomic Thoughts**: Each thought should represent one idea
2. **Progressive Refinement**: Build on previous thoughts
3. **Use Revisions**: Don't try to get it perfect the first time

### Metadata Usage
1. **Categorization**: Use metadata to tag thoughts by type
2. **Confidence Levels**: Track certainty in different approaches
3. **External References**: Link to relevant resources

## Error Handling

Common errors and their meanings:

- `400 Bad Request`: Invalid input (e.g., empty thought content)
- `404 Not Found`: Session doesn't exist
- `409 Conflict`: Operation not allowed (e.g., adding to completed session)
- `422 Unprocessable Entity`: Validation error in request body

## Performance Considerations

1. **Thought Limits**: Sessions with >1000 thoughts may experience slower retrieval
2. **Pagination**: Use pagination when listing many sessions
3. **Selective Loading**: Use `include_thoughts=false` when thought content not needed

## Integration with Memory Service

The Sequential Thinking feature integrates with the broader memory service:

1. **Entity Extraction**: Thoughts can be analyzed to extract entities
2. **Knowledge Graph**: Completed sessions contribute to the knowledge graph
3. **Cross-Reference**: Sessions can reference entities in memory

Example integration:
```python
# After completing a thinking session
session = client.get(f"/thinking/sessions/{session_id}?include_thoughts=true").json()

# Extract entities from the thinking process
entities_to_remember = []
for thought in session["thoughts"]:
    # Analyze thought content for entities
    if "GraphQL" in thought["thought_content"]:
        entities_to_remember.append({
            "name": "GraphQL API Design",
            "type": "technical_decision",
            "observations": [thought["thought_content"]]
        })

# Store in memory
client.post("/entities", json={
    "client_id": session["client_user_id"],
    "actor_type": "thinking_session",
    "actor_id": session["id"],
    "entities": entities_to_remember
})
```