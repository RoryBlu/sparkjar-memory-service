# Memory Service Test Documentation

## Overview

This document describes all tests for the Memory Service, including their purpose, inputs, outputs, and database state changes.

## Test Categories

### 1. Memory Manager Tests (`test_memory_manager.py`)

#### 1.1 Entity Operations

**Test: `test_create_entities`**
- **Purpose**: Verify entity creation with embeddings and metadata
- **Input**: 
  - Entity: "John Doe", type: "person"
  - Observations: skill (Python), fact (job title)
  - Metadata: {"role": "developer"}
- **Database Operations**:
  - INSERT into memory_entities
  - INSERT into memory_observations (for each observation)
  - Generates embedding via API
- **Expected Output**: Entity with UUID, embedding, timestamps, observations
- **Cleanup**: DELETE from memory_entities (cascade deletes observations)

**Test: `test_add_observations`**
- **Purpose**: Test adding observations to entities
- **Input**: 
  - Observation: {"type": "skill", "value": "Python programming"}
- **Database Operations**:
  - INSERT into memory_observations
  - UPDATE memory_entities (updated_at)
- **Expected Output**: Observation linked to entity
- **Cleanup**: CASCADE delete via entity

**Test: `test_create_relations`**
- **Purpose**: Verify relationship creation between entities
- **Input**: 
  - Relation type: "works_with"
  - From: Entity A, To: Entity B
- **Database Operations**:
  - INSERT into memory_relations
- **Expected Output**: Relation with proper foreign keys
- **Cleanup**: DELETE from memory_relations

#### 1.2 Search Operations

**Test: `test_search_nodes`**
- **Purpose**: Test entity search functionality
- **Input**: Search query with filters
- **Database Operations**:
  - SELECT with vector similarity search
  - No data modifications
- **Expected Output**: Filtered entity list

**Test: `test_open_nodes`**
- **Purpose**: Retrieve entity details with observations
- **Input**: Entity IDs
- **Database Operations**:
  - SELECT with JOINs on observations
  - No data modifications
- **Expected Output**: Complete entity data

**Test: `test_read_graph`**
- **Purpose**: Retrieve entity relationship graph
- **Input**: Entity ID
- **Database Operations**:
  - SELECT relations and connected entities
  - No data modifications
- **Expected Output**: Graph structure with nodes and edges

#### 1.3 Advanced Operations

**Test: `test_remember_conversation`**
- **Purpose**: Test conversation memory storage
- **Input**: Conversation with participants and topics
- **Database Operations**:
  - Multiple INSERTs (entities, observations, relations)
  - Automatic embedding generation
- **Expected Output**: Complete conversation graph
- **Cleanup**: CASCADE delete all created data

**Test: `test_find_connections`**
- **Purpose**: Find paths between entities
- **Input**: Two entity names
- **Database Operations**:
  - Complex graph traversal query
  - No data modifications
- **Expected Output**: Connection paths if exist

**Test: `test_get_client_insights`**
- **Purpose**: Aggregate client memory data
- **Input**: Client context
- **Database Operations**:
  - Aggregation queries on all memory tables
  - No data modifications
- **Expected Output**: Summary statistics

### 2. API Endpoint Tests

#### 2.1 Internal API Tests (`test_api_endpoints.py`)

**Test: `test_internal_health`**
- **Endpoint**: GET /health
- **Expected**: 200 OK

**Test: `test_internal_create_entities`**
- **Endpoint**: POST /entities
- **Database**: INSERT into memory_entities
- **Cleanup**: DELETE test data

**Test: `test_internal_search`**
- **Endpoint**: POST /search
- **Database**: SELECT only
- **Cleanup**: None needed

#### 2.2 External API Tests

**Test: `test_external_health`**
- **Endpoint**: GET /health
- **Auth**: None required
- **Expected**: 200 OK

**Test: `test_external_auth`**
- **Endpoint**: POST /auth/token
- **Database**: User validation
- **Expected**: JWT token

### 3. Sequential Thinking Tests

#### 3.1 Service Tests (`test_thinking_service.py`)

**Test: `test_create_session`**
- **Purpose**: Create thinking session
- **Database**: INSERT into thinking_sessions
- **Expected**: Session with UUID and metadata

**Test: `test_add_thought`**
- **Purpose**: Add thoughts to session
- **Database**: 
  - INSERT into thoughts
  - Uses get_next_thought_number() function
- **Expected**: Sequential thought numbers

**Test: `test_revise_thought`**
- **Purpose**: Create thought revisions
- **Database**: INSERT revision with reference
- **Expected**: New thought marked as revision

**Test: `test_complete_session`**
- **Purpose**: Mark session complete
- **Database**: UPDATE thinking_sessions
- **Expected**: Status change and timestamp

#### 3.2 API Tests (`test_thinking_api.py`)

**Test: `test_thinking_endpoints`**
- **Endpoints**: All thinking API routes
- **Database**: Full CRUD operations
- **Cleanup**: Session-based cleanup

### 4. Integration Tests

#### 4.1 Embedding Service (`test_real_embeddings.py`)

**Test: `test_embedding_generation`**
- **Purpose**: Verify real embedding API
- **External Service**: Embedding API
- **Expected**: 768-dimension vectors

#### 4.2 Observation Validation (`test_observation_validation.py`)

**Test: `test_schema_validation`**
- **Purpose**: Validate against stored schemas
- **Database**: SELECT from object_schemas
- **Expected**: Pass/fail validation

### 5. Test Data Management

#### Cleanup Strategy

1. **Session-level cleanup** (conftest.py):
   ```python
   # Before all tests
   DELETE FROM memory_observations WHERE entity_id IN (
     SELECT id FROM memory_entities WHERE client_id = '11111111-1111-1111-1111-111111111111'
   );
   DELETE FROM memory_relations WHERE client_id = '11111111-1111-1111-1111-111111111111';
   DELETE FROM memory_entities WHERE client_id = '11111111-1111-1111-1111-111111111111';
   DELETE FROM thoughts WHERE session_id IN (
     SELECT id FROM thinking_sessions WHERE client_user_id = '11111111-1111-1111-1111-111111111111'
   );
   DELETE FROM thinking_sessions WHERE client_user_id = '11111111-1111-1111-1111-111111111111';
   ```

2. **Test isolation**: Each test uses unique UUIDs

#### Test Data Examples

**Entity Test Data**:
```json
{
  "entity_name": "John Doe",
  "entity_type": "person",
  "metadata": {"role": "developer", "team": "backend"}
}
```

**Observation Test Data**:
```json
{
  "observation_type": "skill",
  "observation_value": {"name": "Python", "level": "expert"},
  "source": "code_review"
}
```

**Relation Test Data**:
```json
{
  "relation_type": "works_with",
  "metadata": {"since": "2024-01-01", "project": "Memory Service"}
}
```

## Test Execution Guidelines

1. **Environment Setup**:
   - Ensure DATABASE_URL points to test database
   - Verify embedding service is accessible
   - Check pgvector extension is installed

2. **Running Tests**:
   ```bash
   # All tests
   pytest tests/ -v
   
   # Specific category
   pytest tests/test_memory_manager.py -v
   
   # With coverage
   pytest tests/ --cov=services --cov-report=html
   ```

3. **Performance Benchmarks**:
   - Entity creation: < 100ms (excluding embedding)
   - Search operations: < 200ms for 1000 entities
   - Graph traversal: < 500ms for 3-hop connections

## Known Issues

1. **Cleanup**: Tests using random UUIDs may leave orphaned data
2. **Concurrency**: No concurrent operation tests yet
3. **Load Testing**: No stress tests implemented
4. **External API**: Most endpoints return 503 (not implemented)

## Completed Items

The following tasks have been implemented to strengthen test coverage and
reliability:

1. **Endpoint tests** have been added in `tests/test_additional_endpoints.py`
   covering the `/debug/storage` and `/memory/search` routes.
2. **Concurrent operation tests** are provided in
   `tests/test_concurrent_operations.py` to verify that the service can handle
   multiple simultaneous requests.
3. **Load and stress tests** now live in `tests/test_load_stress.py`. These
   issue bursts of health‑check requests to ensure the API remains responsive
   under load.
4. **Cleanup steps** have been improved with a session‑level fixture in
   `tests/conftest.py` that removes test data after each run to avoid orphaned
   rows.
5. **Embedding service calls** are mocked via `MockEmbeddingService` so tests
   run without network access.
