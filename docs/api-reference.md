# Memory Service API Documentation

## Overview

The Memory Service provides a sophisticated contextual memory system where every memory exists within one of four distinct realms. The system enables AI agents (synths) to function as the nexus where organizational policies, professional identity, tool knowledge, and personal learning converge. Every memory entity must have relationships, schema validation, and multiple observations to form a rich knowledge graph.

## Authentication

All endpoints require a JWT bearer token with the `sparkjar_internal` scope.

```
Authorization: Bearer <jwt_token>
```

## Base URL

- Internal (IPv6): `http://memory-internal.railway.internal:8001`
- External (IPv4): `https://memory-external.railway.app:8443`

## The Four Contextual Realms

```
CLIENT (Organization - Highest Precedence)
    ↓ provides policies & overrides
  SYNTH (Individual Agent - The Nexus) 
    ↑                        ↑
    inherits from          subscribes to
    ↓                        ↓
SYNTH_CLASS              SKILL_MODULE
(Role Identity)          (Tool Knowledge)
```

1. **CLIENT** - Organizational policies, compliance requirements, brand guidelines (highest precedence)
2. **SYNTH** - Individual agent experiences, optimizations, and personal learning (the nexus)
3. **SYNTH_CLASS** - Professional identity, core procedures, domain expertise (inherited)
4. **SKILL_MODULE** - Tool-specific knowledge, platform capabilities (subscription-based)

## API Endpoints

### 1. Create Complete Entity with Relationships

Creates a complete memory entity with relationships, observations, and validated metadata. This is the preferred method for entity creation.

**Endpoint:** `POST /memory/entities/complete`

**Request Body:**
```json
{
  "actor_type": "synth_class",
  "actor_id": "24",
  "entity": {
    "name": "blog_writing_sop_v4",
    "type": "procedure",
    "metadata": {
      "version": "4.0",
      "phases": 4,
      "approver": "Content Team Lead",
      "category": "content_creation",
      "test_coverage": 0.95
    }
  },
  "observations": [
    {
      "type": "procedure_phase",
      "value": {
        "phase": 1,
        "name": "Research & Planning",
        "duration": "30-45 minutes",
        "steps": [
          "Analyze topic relevance",
          "Research keywords",
          "Identify target audience",
          "Create outline"
        ]
      },
      "source": "Content Team",
      "confidence": 0.95
    },
    {
      "type": "procedure_update",
      "value": {
        "change_type": "enhancement",
        "description": "Added AI-assisted research tools",
        "impact": "Reduced research time by 40%"
      },
      "source": "Process Improvement Team",
      "confidence": 0.88
    }
  ],
  "relationships": [
    {
      "type": "validates",
      "direction": "incoming",
      "from_entity": "blog_qa_checklist",
      "from_realm": {"actor_type": "synth_class", "actor_id": "24"}
    },
    {
      "type": "requires",
      "direction": "outgoing",
      "to_entity": "blog_post_json_structure",
      "to_realm": {"actor_type": "synth_class", "actor_id": "24"},
      "metadata": {"critical": true}
    },
    {
      "type": "measured_by",
      "direction": "incoming",
      "from_entity": "blog_performance_metrics",
      "from_realm": {"actor_type": "synth_class", "actor_id": "24"}
    }
  ]
}
```

**Response:**
```json
{
  "entity": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "actor_type": "synth_class",
    "actor_id": "24",
    "entity_name": "blog_writing_sop_v4",
    "entity_type": "procedure",
    "metadata": {
      "version": "4.0",
      "phases": 4,
      "approver": "Content Team Lead",
      "category": "content_creation",
      "test_coverage": 0.95,
      "_validation": {
        "schema_name": "procedure_metadata",
        "validated_at": "2024-01-15T10:30:00Z",
        "validator_version": "2.0",
        "passed": true
      }
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "observations_created": 2,
  "relationships_created": 3,
  "validation_status": "valid",
  "knowledge_graph_updated": true
```

}
```

### 2. Upsert Entity with Consolidation

Creates or updates an entity with memory consolidation for statistical observations.

**Endpoint:** `POST /memory/entities/upsert`

**Request Body:**
```json
{
  "actor_type": "synth",
  "actor_id": "b9af0667-5c92-4892-a7c5-947ed0cab0db",
  "entity_name": "blog_performance_tracking",
  "entity_type": "metric",
  "metadata": {
    "tracking_since": "2024-01-01",
    "update_frequency": "daily"
  },
  "observations": [
    {
      "type": "performance_metric",
      "value": {
        "metric": "average_engagement_rate",
        "value": 0.067,
        "timestamp": "2024-01-20T10:00:00Z"
      },
      "metadata": {
        "consolidation_enabled": true,
        "consolidation_key": "average_engagement_rate"
      }
    }
  ],
  "enable_consolidation": true
}
```

**Response:**
```json
{
  "entity": {
    "id": "660e8400-e29b-41d4-a716-446655440002",
    "entity_name": "blog_performance_tracking",
    "entity_type": "metric"
  },
  "operation": "updated",
  "consolidation": {
    "performed": true,
    "observations_consolidated": 1,
    "previous_value": 0.054,
    "new_value": 0.067
  }
}

### 3. Search Memories with Realm Traversal

Search memories across all accessible realms with relationship traversal.

**Endpoint:** `POST /memory/search/realms`

**Request Body:**
```json
{
  "actor_type": "synth",
  "actor_id": "b9af0667-5c92-4892-a7c5-947ed0cab0db",
  "query": "blog writing procedures",
  "realms": {
    "include_own": true,
    "include_class": true,
    "include_skills": ["wordpress_cms", "grammarly_pro"],
    "include_client": true
  },
  "traverse_relationships": true,
  "relationship_types": ["requires", "validates", "enhances"],
  "max_depth": 2,
  "limit": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "entity": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "blog_writing_sop_v4",
        "type": "procedure",
        "realm": {"actor_type": "synth_class", "actor_id": "24"}
      },
      "access_path": "synth → synth_class (inherited)",
      "precedence_level": 3,
      "relationships": [
        {"type": "requires", "to": "blog_post_json_structure"},
        {"type": "validated_by", "from": "blog_qa_checklist"}
      ],
      "score": 0.95
    },
    {
      "entity": {
        "id": "client-001",
        "name": "vervelyn_content_policy",
        "type": "policy",
        "realm": {"actor_type": "client", "actor_id": "1d1c2154-242b-4f49-9ca8-e57129ddc823"}
      },
      "access_path": "client (organizational override)",
      "precedence_level": 1,
      "override_note": "This policy overrides synth_class procedures",
      "score": 0.88
    }
  ],
  "realms_searched": ["synth", "synth_class", "skill_module", "client"],
  "relationships_traversed": 12,
  "total_results": 2
}
```

### 4. Get Complete Knowledge Graph

Retrieve the complete knowledge graph accessible to a synth.

**Endpoint:** `GET /memory/synth/{synth_id}/knowledge-graph`

**Query Parameters:**
- `include_relationships`: Include all relationships (default: true)
- `include_observations`: Include observations (default: false)
- `depth`: Relationship traversal depth (default: 2)
```

**Response:**
```json
{
  "synth": {
    "id": "b9af0667-5c92-4892-a7c5-947ed0cab0db",
    "class_id": "24",
    "client_id": "1d1c2154-242b-4f49-9ca8-e57129ddc823",
    "subscribed_modules": ["wordpress_cms", "grammarly_pro"]
  },
  "knowledge_graph": {
    "nodes": [
      {
        "id": "e1",
        "name": "blog_writing_sop_v4",
        "type": "procedure",
        "realm": "synth_class",
        "observation_count": 4
      },
      {
        "id": "e2",
        "name": "blog_qa_checklist",
        "type": "checklist",
        "realm": "synth_class",
        "observation_count": 12
      },
      {
        "id": "e3",
        "name": "vervelyn_content_policy",
        "type": "policy",
        "realm": "client",
        "precedence": "OVERRIDE_ALL"
      }
    ],
    "edges": [
      {"from": "e2", "to": "e1", "type": "validates"},
      {"from": "e3", "to": "e1", "type": "overrides"}
    ],
    "stats": {
      "total_nodes": 3,
      "total_edges": 2,
      "realms": {"synth": 0, "synth_class": 2, "skill_module": 0, "client": 1}
    }
  }
}
```

### 5. Validate Entity Schema

Validate entity metadata against registered schemas before creation.

**Endpoint:** `POST /memory/validate/entity`

**Request Body:**
```json
{
  "entity_id": "550e8400-e29b-41d4-a716-446655440000",
  "observation_type": "writing_technique",
  "observation_value": {
    "technique": "Hook Writing",
    "description": "Engaging opening sentences",
    "examples": [
      "Ask a compelling question",
      "Start with a surprising statistic"
    ]
  },
  "source": "content_marketing_guide_2024",
  "context": {
    "applicable_to": ["blog_posts", "articles"],
    "effectiveness": "high"
  }
}
```

**Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "entity_id": "550e8400-e29b-41d4-a716-446655440000",
  "observation_type": "writing_technique",
  "observation_value": {
    "technique": "Hook Writing",
    "description": "Engaging opening sentences",
    "examples": [
      "Ask a compelling question",
      "Start with a surprising statistic"
    ]
  },
  "source": "content_marketing_guide_2024",
  "context": {
    "applicable_to": ["blog_posts", "articles"],
    "effectiveness": "high"
  },
  "created_at": "2024-01-15T10:35:00Z"
}
```

### 6. Create Entity Relationship

Create relationships between entities, including cross-realm relationships.

**Endpoint:** `POST /memory/relationships`

**Request Body:**
```json
{
  "entities": [
    {
      "actor_type": "synth_class",
      "actor_id": "24",
      "entity_name": "Blog Performance Metrics",
      "entity_type": "metrics_framework",
      "metadata": {"version": "2.0"}
    }
  ],
  "observations": [
    {
      "entity_name": "Blog Performance Metrics",
      "observation_type": "performance_target",
      "observation_key": "bounce_rate",
      "observation_value": {"target": "<35%", "critical": ">60%"}
    }
  ],
  "relations": [
    {
      "from_entity_name": "Blog Performance Metrics",
      "to_entity_name": "Blog Writing Best Practices",
      "relation_type": "measures"
    }
  ]
}
```

**Response:**
```json
{
  "entities": {
    "created": 0,
    "updated": 1,
    "failed": 0
  },
  "observations": {
    "created": 1,
    "updated": 0,
    "failed": 0
  },
  "relations": {
    "created": 1,
    "updated": 0,
    "failed": 0
  },
  "transaction_id": "txn-123456",
  "status": "completed"
}
```

## Memory Fetching Operations

### 7. Apply Realm Precedence

Get memories with proper precedence applied (CLIENT > SYNTH > SYNTH_CLASS > SKILL_MODULE).

**Endpoint:** `POST /memory/precedence/apply`

**Request Body:**
```json
{
  "client_id": "2b4ccc56-cfe9-42d0-8378-1805db211446",
  "actor_type": "synth",
  "actor_id": "b9af0667-5c92-4892-a7c5-947ed0cab0db",
  "query": "how to write blog introduction",
  "include_synth_class": true,
  "include_client": true,
  "limit": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "entity_name": "Blog Writing Best Practices",
      "entity_type": "knowledge_base",
      "actor_type": "synth_class",
      "actor_id": "24",
      "observation_type": "writing_technique",
      "observation_value": {
        "technique": "Introduction Hook Types",
        "examples": ["Question Hook", "Statistic Hook", "Story Hook"]
      },
      "score": 0.92,
      "access_context": "inherited_from_class"
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "entity_name": "SparkJar LLC Blog Policy Override",
      "entity_type": "policy_override",
      "actor_type": "client",
      "actor_id": "2b4ccc56-cfe9-42d0-8378-1805db211446",
      "observation_type": "policy_rule",
      "observation_value": {
        "rule_type": "Content Restrictions",
        "priority": "OVERRIDE_ALL",
        "restrictions": {
          "prohibited_topics": ["competitor comparisons", "financial projections"]
        }
      },
      "score": 0.85,
      "access_context": "client_override"
    }
  ],
  "total_results": 2,
  "search_time_ms": 78
}
```

### 8. Manage Skill Module Subscriptions

Subscribe or unsubscribe a synth to/from skill modules.

**Endpoint:** `POST /memory/synth/{synth_id}/subscriptions`

**Response:**
```json
{
  "entity": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "actor_type": "synth_class",
    "actor_id": "24",
    "entity_name": "Blog Writing Standard Operating Procedure v4.0",
    "entity_type": "procedure_template",
    "metadata": {
      "version": "4.0",
      "phases": 4
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "observations": [
    {
      "id": "obs-001",
      "observation_type": "procedure_phase",
      "observation_value": {
        "phase": 1,
        "name": "Research & Planning",
        "steps": ["Topic analysis", "Keyword research", "Outline creation"]
      },
      "source": "blog_sop_v4",
      "created_at": "2024-01-15T10:35:00Z"
    },
    {
      "id": "obs-002",
      "observation_type": "procedure_phase",
      "observation_value": {
        "phase": 2,
        "name": "Content Creation",
        "steps": ["Write introduction", "Develop main points", "Add examples"]
      },
      "source": "blog_sop_v4",
      "created_at": "2024-01-15T10:36:00Z"
    }
  ],
  "relationships": {
    "outgoing": [
      {
        "id": "rel-001",
        "relation_type": "requires",
        "to_entity": {
          "id": "entity-002",
          "name": "Blog Post JSON Structure Template"
        }
      }
    ],
    "incoming": [
      {
        "id": "rel-002",
        "relation_type": "validates",
        "from_entity": {
          "id": "entity-003",
          "name": "Blog Post Quality Assurance Checklist"
        }
      },
      {
        "id": "rel-003",
        "relation_type": "overrides",
        "from_entity": {
          "id": "client-001",
          "name": "SparkJar LLC Blog Content Policy Override"
        }
      }
    ]
  },
  "stats": {
    "observation_count": 2,
    "outgoing_relations": 1,
    "incoming_relations": 2,
    "last_accessed": "2024-01-16T10:00:00Z"
  }
}
```

### 9. Get Entity with Complete Context

Retrieve an entity with all relationships, observations, and realm context.

**Endpoint:** `GET /memory/entities/{entity_id}/complete`

**Query Parameters:**
- `entity_type`: Filter by entity type (optional)
- `include_observations`: Include observations in response (default: false)
- `include_relations`: Include relationships (default: false)
- `limit`: Maximum results (default: 100)
- `offset`: Pagination offset (default: 0)

**Example Request:**
```
GET /memory/actors/synth_class/24/memories?entity_type=knowledge_base&include_observations=true&limit=10
```

**Response:**
```json
{
  "actor": {
    "actor_type": "synth_class",
    "actor_id": "24",
    "actor_name": "blog author"
  },
  "memories": [
    {
      "id": "entity-001",
      "entity_name": "Blog SEO Best Practices Knowledge Base",
      "entity_type": "knowledge_base",
      "metadata": {"version": "2.0"},
      "observations": [
        {
          "type": "seo_technique",
          "count": 6
        }
      ],
      "created_at": "2024-01-15T09:00:00Z"
    },
    {
      "id": "entity-002",
      "entity_name": "Blog Content Type Variations Guide",
      "entity_type": "knowledge_base",
      "metadata": {"content_types": 4},
      "observations": [
        {
          "type": "content_type_spec",
          "count": 4
        }
      ],
      "created_at": "2024-01-15T09:30:00Z"
    }
  ],
  "pagination": {
    "total": 2,
    "limit": 10,
    "offset": 0,
    "has_more": false
  }
}
```

### 10. Discover Knowledge Through Relationships

Find related knowledge by traversing the relationship graph.

**Endpoint:** `POST /memory/discover`

**Query Parameters:**
- `relation_types`: Comma-separated list of relation types to follow
- `depth`: How many levels of relationships to traverse (default: 1, max: 3)
- `direction`: "outgoing", "incoming", or "both" (default: "both")

**Example Request:**
```
GET /memory/entities/550e8400-e29b-41d4-a716-446655440000/related?relation_types=overrides,extends&depth=2
```

**Response:**
```json
{
  "source_entity": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Blog Writing Standard Operating Procedure v4.0"
  },
  "related_memories": [
    {
      "level": 1,
      "relation": {
        "type": "overrides",
        "direction": "incoming"
      },
      "entity": {
        "id": "client-policy-001",
        "entity_name": "SparkJar LLC Blog Content Policy Override",
        "actor_type": "client",
        "actor_id": "2b4ccc56-cfe9-42d0-8378-1805db211446",
        "metadata": {"priority": "OVERRIDE_ALL"}
      }
    },
    {
      "level": 1,
      "relation": {
        "type": "extends",
        "direction": "incoming"
      },
      "entity": {
        "id": "content-guide-001",
        "entity_name": "Blog Content Type Variations Guide",
        "actor_type": "synth_class",
        "actor_id": "24"
      }
    }
  ],
  "total_related": 2,
  "traversal_stats": {
    "nodes_visited": 3,
    "max_depth_reached": 1
  }
}
```

### 11. Consolidate Statistical Observations

Consolidate statistical observations to prevent database bloat.

**Endpoint:** `POST /memory/entities/{entity_id}/consolidate`

**Response:**
```json
{
  "entity": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "actor_type": "synth_class",
    "actor_id": "24",
    "entity_name": "Blog Writing Standard Operating Procedure v4.0",
    "entity_type": "procedure_template",
    "metadata": {
      "version": "4.0",
      "phases": 4
    },
    "created_at": "2024-01-15T10:30:00Z"
  },
  "observations": [
    {
      "id": "obs-001",
      "observation_type": "procedure_phase",
      "observation_value": {
        "phase": 1,
        "name": "Research & Planning",
        "steps": ["Topic analysis", "Keyword research", "Outline creation"]
      }
    },
    {
      "id": "obs-002",
      "observation_type": "procedure_phase",
      "observation_value": {
        "phase": 2,
        "name": "Content Creation",
        "steps": ["Write introduction", "Develop main points", "Add examples"]
      }
    }
  ],
  "observation_count": 2
}
```

### 12. Entity Naming Guidelines

**Entity names must be:**
- Maximum 30 characters
- Lowercase with underscores (snake_case)
- Descriptive keys, not sentences
- Version suffixed if needed (_v2, _v3)

**Examples:**
```
✅ GOOD: blog_writing_sop_v4
❌ BAD: Blog Writing Standard Operating Procedure Version 4.0
```

**Request Body:**
```json
{
  "from_entity_id": "client-policy-001",
  "to_entity_id": "class-sop-001",
  "relation_type": "overrides",
  "metadata": {
    "override_level": "complete",
    "precedence": "client > synth_class",
    "reason": "Company-specific compliance requirements"
  }
}
```

**Response:**
```json
{
  "id": "rel-001",
  "from_entity_id": "client-policy-001",
  "to_entity_id": "class-sop-001",
  "relation_type": "overrides",
  "metadata": {
    "override_level": "complete",
    "precedence": "client > synth_class",
    "reason": "Company-specific compliance requirements"
  },
  "created_at": "2024-01-15T11:00:00Z"
}
```

### 13. Schema Validation Requirements

All entity metadata must validate against schemas in the `object_schemas` table:

```json
{
  "procedure_metadata": {
    "required": ["version", "phases", "approver", "category"],
    "properties": {
      "version": {"pattern": "^[0-9]+\\.[0-9]+$"},
      "phases": {"minimum": 1, "maximum": 10}
    }
  },
  "policy_metadata": {
    "required": ["effective_date", "compliance_level", "authority"]
  },
  "metric_metadata": {
    "required": ["unit", "frequency", "target"]
  }
}
```

**Query Parameters:**
- `client_id`: Client UUID
- `actor_type`: Actor type (synth, synth_class, client)
- `actor_id`: Actor ID

**Example Request:**
```
GET /memory/hierarchy?client_id=2b4ccc56-cfe9-42d0-8378-1805db211446&actor_type=synth&actor_id=b9af0667-5c92-4892-a7c5-947ed0cab0db
```

**Response:**
```json
{
  "hierarchy": {
    "synth": {
      "actor_id": "b9af0667-5c92-4892-a7c5-947ed0cab0db",
      "memory_count": 0,
      "entity_types": []
    },
    "synth_class": {
      "class_id": "24",
      "class_name": "blog author",
      "memory_count": 9,
      "entity_types": ["procedure_template", "knowledge_base", "style_guide", "metrics_framework"]
    },
    "client": {
      "client_id": "2b4ccc56-cfe9-42d0-8378-1805db211446",
      "client_name": "SparkJar LLC",
      "memory_count": 1,
      "entity_types": ["policy_override"],
      "overrides": ["Blog Writing Standard Operating Procedure v4.0"]
    }
  },
  "total_accessible_memories": 10,
  "access_pattern": "synth → synth_class → client"
}
```

### 14. Relationship Requirements

Every entity MUST have at least one relationship. Common patterns:

**Hierarchical**: implements, extends, supersedes, based_on
**Dependency**: requires, uses, triggers, enables
**Validation**: validates, validated_by, measures, measured_by
**Modification**: overrides, enhances, conflicts_with, replaces

**Request Body:**
```json
{
  "client_id": "2b4ccc56-cfe9-42d0-8378-1805db211446",
  "actor_type": "synth",
  "actor_id": "b9af0667-5c92-4892-a7c5-947ed0cab0db",
  "target_memory_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "has_access": true,
  "access_reason": "inherited_from_synth_class",
  "access_path": "synth(b9af0667) → synth_class(24) → memory(550e8400)",
  "override_status": {
    "has_override": true,
    "override_source": "client",
    "override_id": "client-policy-001"
  }
}
```

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": {
    "code": "INVALID_ACTOR_TYPE",
    "message": "Actor type must be one of: human, synth, synth_class, client",
    "details": {
      "provided_value": "invalid_type",
      "valid_values": ["human", "synth", "synth_class", "client"]
    }
  },
  "status": 400
}
```

Common error codes:
- `UNAUTHORIZED` (401) - Invalid or missing JWT token
- `FORBIDDEN` (403) - Token lacks required scope
- `NOT_FOUND` (404) - Entity or observation not found
- `VALIDATION_ERROR` (400) - Request validation failed
- `INTERNAL_ERROR` (500) - Server error

## Usage Examples

### Example 1: Creating a Complete Entity with Knowledge Graph

```python
import requests

# Create a complete procedure with all requirements
response = requests.post(
    "http://memory-internal.railway.internal:8001/memory/entities/complete",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "actor_type": "synth_class",
        "actor_id": "24",
        "entity": {
            "name": "content_optimization_v2",
            "type": "procedure",
            "metadata": {
                "version": "2.0",
                "phases": 3,
                "approver": "Content Lead",
                "category": "optimization",
                "effectiveness": 0.89
            }
        },
        "observations": [
            {
                "type": "optimization_technique",
                "value": {
                    "technique": "Headline A/B Testing",
                    "impact": "+23% CTR",
                    "sample_size": 1200
                },
                "source": "Analytics Platform",
                "confidence": 0.92
            },
            {
                "type": "implementation_guide",
                "value": {
                    "steps": [
                        "Create 3-5 headline variants",
                        "Test with 10% of audience",
                        "Measure CTR over 48 hours",
                        "Deploy winner to remaining 90%"
                    ]
                },
                "source": "Marketing Team"
            }
        ],
        "relationships": [
            {
                "type": "enhances",
                "to_entity": "blog_writing_sop_v4",
                "to_realm": {"actor_type": "synth_class", "actor_id": "24"},
                "metadata": {"applicable_to": "all_content_types"}
            },
            {
                "type": "measured_by",
                "from_entity": "content_performance_kpi",
                "from_realm": {"actor_type": "synth_class", "actor_id": "24"}
            },
            {
                "type": "validated_by",
                "from_entity": "ab_test_checklist",
                "from_realm": {"actor_type": "synth_class", "actor_id": "24"}
            }
        ]
    }
)

# Entity created with full knowledge graph connections
```

### Example 2: Synth Accessing Memories Across All Realms

```python
# Synth searches across all realms with relationship traversal
response = requests.post(
    "http://memory-internal.railway.internal:8001/memory/search/realms",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "actor_type": "synth",
        "actor_id": "b9af0667-5c92-4892-a7c5-947ed0cab0db",
        "query": "how to optimize blog content",
        "realms": {
            "include_own": True,           # Personal optimizations
            "include_class": True,         # Professional procedures
            "include_skills": ["wordpress_cms", "grammarly_pro"],
            "include_client": True         # Organizational policies
        },
        "traverse_relationships": True,
        "relationship_types": ["enhances", "requires", "validates"],
        "max_depth": 2
    }
)

results = response.json()

# Apply precedence to get final guidance
precedence_response = requests.post(
    "http://memory-internal.railway.internal:8001/memory/precedence/apply",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "memories": results["results"],
        "actor_type": "synth",
        "actor_id": "b9af0667-5c92-4892-a7c5-947ed0cab0db"
    }
)

final_guidance = precedence_response.json()
# CLIENT policies override all, then SYNTH personal, then CLASS, then MODULES
```

### Example 3: Memory Consolidation for Performance Metrics

```python
# Update performance metric with consolidation
response = requests.post(
    "http://memory-internal.railway.internal:8001/memory/entities/upsert",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "actor_type": "synth",
        "actor_id": "b9af0667-5c92-4892-a7c5-947ed0cab0db",
        "entity_name": "blog_performance_tracker",
        "entity_type": "metric",
        "observations": [
            {
                "type": "performance_metric",
                "value": {
                    "metric": "average_read_time",
                    "value": "4:32",
                    "timestamp": "2024-01-20T15:00:00Z"
                },
                "metadata": {
                    "consolidation_enabled": true,
                    "consolidation_key": "average_read_time"
                }
            }
        ],
        "enable_consolidation": true
    }
)

# Previous observation with same key is updated, not appended
# Prevents database bloat for frequently updated metrics
```

## Performance Considerations

1. **Realm Caching**: Cache synth realm memberships (class, modules, client) for 5 minutes
2. **Response Times**: 
   - Simple queries: ~75-80ms (remote Supabase)
   - Realm traversal queries: ~85-95ms
   - Relationship graph traversal: ~100-120ms
   - With local database: <50ms achievable
3. **Batch Operations**: Always use batch endpoints when creating entities with relationships
4. **Indexing**: Required indexes:
   - `(actor_type, actor_id)` - Primary realm lookup
   - `(actor_type, actor_id, entity_name)` - Unique constraint
   - `(entity_id, deleted_at)` - Soft delete queries
   - Relationship indexes for graph traversal
5. **Consolidation**: Run consolidation on metric entities regularly to prevent observation bloat

## Key Design Principles

1. **No Floating Memories**: Every memory MUST exist within a contextual realm
2. **Complete Entities**: Every entity MUST have relationships, validated metadata, and observations
3. **Synth as Nexus**: Synths are the integration point where all realms converge
4. **Realm Precedence**: CLIENT > SYNTH > SYNTH_CLASS > SKILL_MODULE
5. **Knowledge Graphs**: Memories form interconnected webs through relationships
6. **Schema Validation**: All metadata validates against registered schemas
7. **Consolidation**: Statistical observations update in place like human memory

## Migration Notes

As of January 2024:
- `actor_id` field is TEXT type, supporting UUIDs and string IDs
- Entity names must be short keys (max 30 chars), not descriptions
- All entities require at least one relationship
- Schema validation is mandatory for all entity metadata
- Consolidation is available for metric-type entities