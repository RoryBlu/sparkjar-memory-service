# Sequential Thinking - Functional Requirements Specification

## 1. Overview

### 1.1 Purpose
Sequential Thinking is a capability that enables AI agents to break down complex problems into numbered thought steps, with the ability to revise previous thoughts and adjust the thinking process dynamically.

### 1.2 Core Value Proposition
- **Structured Problem Solving**: Problems are decomposed into discrete, numbered thoughts
- **Self-Correction**: Ability to revise previous thoughts when new insights emerge
- **Dynamic Planning**: Total thought count can be adjusted as understanding deepens
- **Transparent Reasoning**: Each thought step is recorded and retrievable

## 2. Database Schema

### 2.1 Tables Required

#### thinking_sessions
Stores the overall thinking session context.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique session identifier |
| client_user_id | UUID | NOT NULL, FK | The user who initiated the session |
| session_name | TEXT | NULLABLE | Human-readable name for the session |
| problem_statement | TEXT | NULLABLE | The problem being solved |
| status | TEXT | NOT NULL, DEFAULT 'active' | Session state: active, completed, abandoned |
| final_answer | TEXT | NULLABLE | The conclusion reached (when completed) |
| metadata | JSONB | NOT NULL, DEFAULT '{}' | Additional session context |
| created_at | TIMESTAMP | NOT NULL | When session started |
| completed_at | TIMESTAMP | NULLABLE | When session completed |

**Constraints**:
- status must be one of: 'active', 'completed', 'abandoned'
- completed_at must be NULL when status='active'
- final_answer must be NOT NULL when status='completed'

#### thoughts
Stores individual thought steps within a session.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique thought identifier |
| session_id | UUID | NOT NULL, FK | Parent session |
| thought_number | INTEGER | NOT NULL | Sequential position (1-based) |
| thought_content | TEXT | NOT NULL | The actual thought text |
| is_revision | BOOLEAN | DEFAULT false | Whether this revises a previous thought |
| revises_thought_number | INTEGER | NULLABLE | Which thought this revises (if any) |
| metadata | JSONB | NOT NULL, DEFAULT '{}' | Additional thought context |
| created_at | TIMESTAMP | NOT NULL | When thought was created |

**Constraints**:
- UNIQUE(session_id, thought_number) - ensures sequential ordering
- revises_thought_number must be NOT NULL when is_revision=true
- revises_thought_number must be < thought_number
- thought_number must be > 0

## 3. Functional Requirements

### 3.1 Session Management

#### FR-1: Create Session
**Description**: Initialize a new thinking session for a problem.

**Inputs**:
- client_user_id (required): The user creating the session
- session_name (optional): Descriptive name
- problem_statement (optional): The problem to solve
- metadata (optional): Additional context as JSON

**Process**:
1. Validate client_user_id exists
2. Create new session with status='active'
3. Set created_at to current timestamp
4. Return session_id

**Outputs**:
- session_id: Unique identifier for the new session
- status: 'active'
- created_at: Timestamp

**Error Conditions**:
- Invalid client_user_id → 401 Unauthorized
- Database error → 500 Internal Error

#### FR-2: Complete Session
**Description**: Mark a session as completed with a final answer.

**Inputs**:
- session_id (required): Session to complete
- final_answer (required): The conclusion reached
- client_user_id (required): For authorization

**Process**:
1. Verify session exists and belongs to client_user_id
2. Verify session status is 'active'
3. Update status to 'completed'
4. Set final_answer
5. Set completed_at to current timestamp

**Outputs**:
- Success confirmation
- completed_at timestamp

**Error Conditions**:
- Session not found → 404
- Session not owned by user → 403 Forbidden
- Session already completed → 400 Bad Request
- Missing final_answer → 400 Bad Request

#### FR-3: Abandon Session
**Description**: Mark a session as abandoned (gave up).

**Inputs**:
- session_id (required)
- client_user_id (required)
- reason (optional): Why abandoned

**Process**:
1. Verify session exists and belongs to client_user_id
2. Verify session status is 'active'
3. Update status to 'abandoned'
4. Store reason in metadata if provided
5. Set completed_at to current timestamp

**Outputs**:
- Success confirmation

**Error Conditions**:
- Same as FR-2, except final_answer not required

### 3.2 Thought Processing

#### FR-4: Add Thought
**Description**: Add the next sequential thought to a session.

**Inputs**:
- session_id (required): Target session
- thought_content (required): The thought text
- client_user_id (required): For authorization
- metadata (optional): Additional context

**Process**:
1. Verify session exists, belongs to user, and is active
2. Calculate next thought_number (count existing + 1)
3. Create thought record
4. Return thought details

**Outputs**:
- thought_id: Unique identifier
- thought_number: Sequential position
- created_at: Timestamp

**Error Conditions**:
- Session not active → 400 Bad Request
- Session not found → 404
- Unauthorized → 403

#### FR-5: Revise Thought
**Description**: Add a new thought that explicitly revises a previous thought.

**Inputs**:
- session_id (required)
- thought_content (required): The revision
- revises_thought_number (required): Which thought to revise
- client_user_id (required)
- metadata (optional)

**Process**:
1. Verify session exists, belongs to user, and is active
2. Verify revises_thought_number exists in session
3. Calculate next thought_number
4. Create thought with is_revision=true
5. Return thought details

**Outputs**:
- Same as FR-4, plus confirmation of which thought was revised

**Error Conditions**:
- Same as FR-4
- Invalid revises_thought_number → 400 Bad Request

### 3.3 Retrieval Operations

#### FR-6: Get Session Details
**Description**: Retrieve a complete session with all thoughts.

**Inputs**:
- session_id (required)
- client_user_id (required)

**Process**:
1. Verify session belongs to user
2. Fetch session record
3. Fetch all thoughts ordered by thought_number
4. Compile response

**Outputs**:
```json
{
  "session": {
    "id": "uuid",
    "session_name": "string",
    "problem_statement": "string",
    "status": "active|completed|abandoned",
    "final_answer": "string|null",
    "created_at": "timestamp",
    "completed_at": "timestamp|null",
    "metadata": {}
  },
  "thoughts": [
    {
      "thought_number": 1,
      "thought_content": "string",
      "is_revision": false,
      "revises_thought_number": null,
      "created_at": "timestamp",
      "metadata": {}
    }
  ],
  "statistics": {
    "total_thoughts": 10,
    "revision_count": 2,
    "duration_seconds": 3600
  }
}
```

#### FR-7: List User Sessions
**Description**: Get all sessions for a user with filtering.

**Inputs**:
- client_user_id (required)
- status (optional): Filter by status
- limit (optional): Max results (default 50)
- offset (optional): Pagination (default 0)

**Process**:
1. Query sessions for user
2. Apply status filter if provided
3. Order by created_at DESC
4. Apply pagination

**Outputs**:
- Array of session summaries (without thoughts)
- Total count for pagination

#### FR-8: Get Current Thought
**Description**: Get the latest thought in an active session.

**Inputs**:
- session_id (required)
- client_user_id (required)

**Process**:
1. Verify session exists and belongs to user
2. Get thought with highest thought_number
3. Return thought details

**Outputs**:
- Current thought details
- thought_number
- total_thoughts_so_far

### 3.4 Analysis Operations

#### FR-9: Get Revision History
**Description**: Get all revisions for a specific thought number.

**Inputs**:
- session_id (required)
- thought_number (required)
- client_user_id (required)

**Process**:
1. Verify access
2. Find all thoughts where revises_thought_number = thought_number
3. Return in chronological order

**Outputs**:
- Original thought
- Array of all revisions with timestamps

#### FR-10: Get Session Statistics
**Description**: Calculate metrics for a session.

**Inputs**:
- session_id (required)
- client_user_id (required)

**Process**:
1. Verify access
2. Calculate metrics

**Outputs**:
```json
{
  "total_thoughts": 15,
  "revision_count": 3,
  "revised_thought_numbers": [3, 7],
  "average_thought_length": 150,
  "duration_seconds": 3600,
  "thoughts_per_minute": 0.25
}
```

## 4. Business Rules

### 4.1 Sequential Integrity
- Thought numbers must be sequential without gaps
- A thought cannot be added to a completed/abandoned session
- Revisions cannot revise thoughts that don't exist
- Revisions cannot revise future thoughts (revises_thought_number < current thought_number)

### 4.2 Access Control
- Users can only access their own sessions
- All operations require client_user_id verification
- No cross-user session sharing

### 4.3 Session Lifecycle
- Sessions start as 'active'
- Active → Completed (requires final_answer)
- Active → Abandoned (optional reason)
- Completed/Abandoned sessions are immutable

### 4.4 Data Constraints
- thought_content minimum length: 1 character
- thought_content maximum length: 10,000 characters
- session_name maximum length: 255 characters
- Maximum thoughts per session: 1,000 (configurable)

## 5. Non-Functional Requirements

### 5.1 Performance
- Session creation: < 100ms
- Thought addition: < 100ms  
- Full session retrieval (100 thoughts): < 500ms
- Session list retrieval: < 200ms

### 5.2 Scalability
- Support 10,000 concurrent active sessions
- Support sessions with up to 1,000 thoughts
- Efficient pagination for session lists

### 5.3 Data Retention
- Active sessions: No expiration
- Completed sessions: Retain indefinitely
- Abandoned sessions: Retain for 30 days (configurable)

## 6. Integration Points

### 6.1 With CrewAI
- Sessions can be created by crew jobs
- Thoughts can be generated by AI agents
- Final answers can trigger downstream crew tasks

### 6.2 With Existing Auth
- Use existing JWT/auth system
- client_user_id comes from authenticated context

### 6.3 With Job System
- Sessions can be linked to crew_jobs (stored in metadata)
- Job completion can trigger session completion

## 7. Future Considerations (NOT MVP)

These are documented for awareness but should NOT be implemented initially:

- Branching (multiple thought paths)
- Collaborative sessions (multiple users)
- Thought templates
- Confidence scoring
- Semantic search across thoughts
- Export formats (PDF, Markdown)
- Real-time collaboration
- Thought version control

## 8. Example Scenarios

### Scenario 1: Simple Problem Solving
```
1. Create session: "How to optimize database queries"
2. Add thought 1: "First, I need to identify slow queries"
3. Add thought 2: "I should look at query execution plans"
4. Add thought 3: "Check for missing indexes"
5. Complete session: "Add indexes on foreign keys and commonly filtered columns"
```

### Scenario 2: With Revision
```
1. Create session: "Design user authentication"
2. Add thought 1: "Use simple password authentication"
3. Add thought 2: "Store passwords in database"
4. Add thought 3: "Wait, passwords should be hashed"
5. Revise thought 2: "Store hashed passwords using bcrypt"
6. Add thought 4: "Add password reset functionality"
7. Complete session: "Implement bcrypt password hashing with secure reset flow"
```

## 9. Acceptance Criteria

### For MVP Release:
- [ ] Can create sessions
- [ ] Can add sequential thoughts
- [ ] Can revise previous thoughts  
- [ ] Can complete sessions with final answer
- [ ] Can retrieve full session history
- [ ] Can list user's sessions
- [ ] Enforces sequential numbering
- [ ] Enforces access control
- [ ] Handles concurrent thought addition correctly

### Quality Gates:
- All operations authorize against client_user_id
- No data leakage between users
- Thought numbers are always sequential
- Completed sessions cannot be modified
- All endpoints handle errors gracefully