# Memory System Master Guide

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [The Four Contextual Realms](#the-four-contextual-realms)
4. [Entity Requirements](#entity-requirements)
5. [Quick Start](#quick-start)
6. [API Reference](#api-reference)
7. [Implementation Guides](#implementation-guides)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Overview

The SparkJAR Memory System is a sophisticated knowledge graph platform that implements a 4-dimensional contextual space where memories exist in distinct realms. Each memory entity is a rich, interconnected knowledge node with mandatory relationships, schema-validated metadata, and multiple observations.

### Key Principles

- **Contextual Realms**: All memories exist within one of four contexts (CLIENT, SYNTH_CLASS, SKILL_MODULE, SYNTH)
- **The Synth as Nexus**: Synths inherit from their class and subscribe to skill modules while respecting client precedence
- **Rich Entities**: Every entity requires relationships, validated metadata, and multiple observations
- **Knowledge Graphs**: Memories form interconnected webs of knowledge, not isolated records

### Current Implementation Status

- ✅ Four contextual realms fully implemented
- ✅ Synth inheritance and subscription model working
- ✅ Schema validation against object_schemas table
- ✅ Relationship requirements enforced
- ✅ Memory consolidation for statistics
- ✅ Performance: 75-80ms (remote Supabase)

## Core Concepts

### What Makes a Memory Entity

Every memory entity in the system is:

1. **Contextually Anchored** - Exists within a specific realm (actor_type + actor_id)
2. **Schema Validated** - Metadata validates against schemas in object_schemas table
3. **Relationship Connected** - Has at least one relationship to other entities
4. **Observation Rich** - Contains multiple timestamped, sourced observations
5. **Uniquely Keyed** - Uses short, descriptive keys (not long descriptions)

### Memory vs Simple Data

This is NOT a key-value store. Each memory is a node in a vast knowledge graph:

```
❌ Simple Record:
{
  "name": "synth_disclosure_policy",
  "value": "Disclose AI nature"
}

✅ Complete Memory Entity:
{
  "entity_name": "synth_disclosure_policy",
  "entity_type": "policy",
  "actor_type": "client",
  "actor_id": "1d1c2154-242b-4f49-9ca8-e57129ddc823",
  "metadata": {
    "category": "ai_transparency",
    "effective_date": "2024-01-01",
    "compliance": "mandatory",
    "review_cycle": "quarterly"
  },
  "relationships": [
    {"type": "implements", "to": "ai_ethics_framework"},
    {"type": "supersedes", "to": "synth_disclosure_v1"},
    {"type": "requires", "to": "synth_identification_badge"}
  ],
  "observations": [
    {
      "type": "policy_statement",
      "value": "All synthetic humans must identify themselves within 5 seconds",
      "source": "Legal Compliance Team",
      "timestamp": "2024-01-01T00:00:00Z"
    },
    {
      "type": "implementation_note", 
      "value": "Applied to all written, audio, and video communications",
      "source": "Technical Implementation Guide",
      "timestamp": "2024-01-15T00:00:00Z"
    }
  ]
}
```

## The Four Contextual Realms

### Understanding Contextual Realms

```
CLIENT (Organization Level - Highest Precedence)
    ↓ provides company-wide policies & overrides
  SYNTH (Individual Agent - The Nexus) 
    ↑                        ↑
    inherits from          subscribes to
    ↓                        ↓
SYNTH_CLASS              SKILL_MODULE
(Role Templates)         (Tool Capabilities)
```

### 1. CLIENT Realm (Organizational Context)

**What belongs here:**
- Company-wide policies and procedures
- Organizational overrides
- Compliance requirements
- Brand guidelines
- Business rules

**Example:** Vervelyn Publishing's AI disclosure policy that ALL synths must follow

### 2. SYNTH_CLASS Realm (Role Identity)

**What belongs here:**
- Core professional knowledge defining WHO the synth is
- Role-specific procedures and workflows
- Professional standards and best practices
- Domain expertise

**Example:** Blog Author (class 24) has writing procedures, SEO knowledge, content patterns

### 3. SKILL_MODULE Realm (Tool Knowledge)

**What belongs here:**
- Complete knowledge of specific tools/platforms
- Integration patterns and APIs
- Tool-specific workflows
- Technical specifications

**Example:** microsoft_365_suite module contains Excel formulas, Word templates, Teams workflows

### 4. SYNTH Realm (Individual Context)

**What belongs here:**
- Personal learning and experiences
- Individual optimizations
- Specific task history
- Personalized adjustments

**Example:** A specific blog author synth learns that tech articles get 23% more engagement with question headlines

### The Synth as Nexus

The SYNTH is the critical junction that:
- **Inherits** its professional identity from SYNTH_CLASS
- **Subscribes** to various SKILL_MODULEs based on client needs  
- **Respects** CLIENT realm policies and overrides
- **Accumulates** individual experiences in its own realm

## Entity Requirements

### Mandatory Entity Components

Every entity MUST have:

1. **Contextual Anchor**
   ```python
   {
     "actor_type": "synth_class",  # Which realm
     "actor_id": "24",              # Specific context instance
     "entity_name": "blog_writing_sop_v4"  # Unique within context
   }
   ```

2. **Schema-Validated Metadata**
   ```python
   {
     "metadata": {
       "version": "4.0",          # Required by schema
       "category": "procedure",    # Required by schema
       "phases": 4,               # Required by schema
       "last_updated": "2024-01-20"  # Required by schema
     }
   }
   ```

3. **At Least One Relationship**
   ```python
   {
     "relationships": [
       {"type": "validates", "from": "blog_qa_checklist"},
       {"type": "requires", "to": "blog_post_json_structure"},
       {"type": "measured_by", "to": "blog_performance_metrics"}
     ]
   }
   ```

4. **Multiple Observations**
   ```python
   {
     "observations": [
       {
         "type": "procedure_phase",
         "value": {"phase": 1, "name": "Research", "steps": [...]},
         "source": "Content Team",
         "timestamp": "2024-01-15T10:00:00Z"
       },
       {
         "type": "procedure_update",
         "value": {"change": "Added AI tool integration"},
         "source": "Tech Team",
         "timestamp": "2024-01-18T14:30:00Z"
       }
     ]
   }
   ```

### Entity Naming Conventions

Use concise, unique keys:
- ✅ `blog_writing_sop_v4`
- ✅ `synth_disclosure_policy`
- ✅ `excel_pivot_tables`
- ❌ `Blog Writing Standard Operating Procedure Version 4.0`
- ❌ `This is our policy for synthetic human disclosure`

## Quick Start

### For Crew Developers

```python
# 1. Search with realm inheritance
results = await memory_client.search_memories(
    client_id=self.client_id,
    actor_type="synth",
    actor_id=self.synth_id,
    query="blog writing procedures",
    include_synth_class=True,  # Inherit from role
    include_skill_module=True, # Include subscribed skills
    include_client=True        # Respect org policies
)

# 2. Create a complete entity with relationships
await memory_client.create_entity_with_relations(
    actor_type="synth",
    actor_id=self.synth_id,
    entity={
        "name": "tech_blog_optimization",
        "type": "learned_pattern",
        "metadata": {
            "domain": "technology",
            "confidence": 0.92,
            "sample_size": 47
        }
    },
    observations=[
        {
            "type": "performance_insight",
            "value": {"pattern": "Question headlines +23% CTR"},
            "source": "A/B Testing"
        }
    ],
    relationships=[
        {
            "type": "enhances",
            "to_entity": "blog_writing_sop_v4",
            "to_realm": "synth_class"
        }
    ]
)

# 3. Access memories by realm
class_memories = await memory_client.get_realm_memories(
    actor_type="synth_class",
    actor_id="24",
    include_relationships=True
)
```

### Available Knowledge Examples

**Blog Author Class (24):**
- `blog_writing_sop_v4` - 4-phase writing procedure
- `blog_qa_checklist` - 20-point quality checklist
- `blog_seo_practices` - SEO optimization guide
- `blog_content_types` - 7 content type templates
- `blog_performance_metrics` - KPIs and targets
- `blog_style_guide` - Writing standards
- `blog_post_json_structure` - Output format

## API Reference

### Core Endpoints

#### 1. Create Complete Entity
`POST /memory/entities/complete`

Creates entity with relationships and observations in one transaction:

```json
{
  "actor_type": "client",
  "actor_id": "1d1c2154-242b-4f49-9ca8-e57129ddc823",
  "entity": {
    "name": "content_compliance_policy",
    "type": "policy",
    "metadata": {
      "version": "2.0",
      "mandatory": true,
      "enforcement": "automatic"
    }
  },
  "observations": [
    {
      "type": "policy_rule",
      "value": {"rule": "No medical advice"},
      "source": "Legal Team"
    }
  ],
  "relationships": [
    {
      "type": "overrides",
      "to_entity": "blog_content_guidelines",
      "to_actor_type": "synth_class",
      "to_actor_id": "24"
    }
  ]
}
```

Example using `skill_module_metadata`:

```json
{
  "actor_type": "skill_module",
  "actor_id": "image_tools",
  "entity": {
    "name": "background_removal",
    "type": "integration",
    "metadata": {
      "module_name": "image_tools",
      "instruction_set": "remove_background",
      "version": "1.0"
    }
  }
}
```

#### 2. Search Across Realms
`POST /memory/search/realms`

Search with full realm awareness:

```json
{
  "synth_id": "b9af0667-5c92-4892-a7c5-947ed0cab0db",
  "query": "content guidelines",
  "realms": {
    "include_own": true,
    "include_class": true,
    "include_skills": ["microsoft_365", "grammarly"],
    "include_client": true
  },
  "traverse_relationships": true,
  "max_depth": 2
}
```

#### 3. Validate Entity Completeness
`POST /memory/entities/validate`

Check if entity meets all requirements:

```json
{
  "entity_id": "550e8400-e29b-41d4-a716-446655440000",
  "checks": {
    "schema_validation": true,
    "relationship_minimum": 1,
    "observation_minimum": 2,
    "metadata_required_fields": ["version", "category"]
  }
}
```

See [API Documentation](./api-reference.md) for complete endpoint reference.

## Implementation Guides

### 1. Creating Entities in the Right Realm

```python
# CLIENT realm - organizational policies
if memory_type in ['policy', 'compliance', 'brand_guideline']:
    actor_type = 'client'
    actor_id = client_id

# SYNTH_CLASS realm - role knowledge  
elif memory_type in ['procedure', 'expertise', 'workflow']:
    actor_type = 'synth_class'
    actor_id = synth_class_id

# SKILL_MODULE realm - tool knowledge
elif memory_type in ['integration', 'api_reference', 'tool_guide']:
    actor_type = 'skill_module'
    actor_id = skill_module_name

# SYNTH realm - individual learning
elif memory_type in ['experience', 'optimization', 'preference']:
    actor_type = 'synth'
    actor_id = synth_id
```

### 2. Building Relationship Graphs

```python
# Create a procedure with full relationship graph
procedure = await create_procedure_with_graph(
    name="customer_onboarding_v2",
    relationships=[
        # What it requires
        {"type": "requires", "to": "crm_access"},
        {"type": "requires", "to": "email_templates"},
        
        # What validates it
        {"type": "validated_by", "from": "onboarding_checklist"},
        
        # What it's measured by
        {"type": "measured_by", "from": "customer_satisfaction_kpi"},
        
        # What it supersedes
        {"type": "supersedes", "to": "customer_onboarding_v1"}
    ]
)
```

### 3. Memory Consolidation

For statistical observations, enable consolidation:

```python
# First observation
await add_observation(
    entity_id=metrics_entity_id,
    observation={
        "type": "performance_metric",
        "value": {"blog_engagement_rate": "3.2%"},
        "metadata": {"consolidation_enabled": True}
    }
)

# Later update - will consolidate, not append
await add_observation(
    entity_id=metrics_entity_id,
    observation={
        "type": "performance_metric", 
        "value": {"blog_engagement_rate": "4.1%"},  # Updates in place
        "metadata": {"consolidation_enabled": True}
    }
)
```

## Best Practices

### 1. Respect Realm Boundaries
- Don't put company policies in synth_class realm
- Don't put individual learning in client realm
- Keep tool knowledge in skill_module realm

### 2. Create Complete Entities
- Always include relationships
- Add multiple observations over time
- Validate metadata against schemas
- Use meaningful entity keys

### 3. Leverage the Synth Nexus
- Let synths inherit class knowledge automatically
- Subscribe synths to appropriate skill modules
- Apply client policies through precedence
- Store individual optimizations in synth realm

### 4. Think in Graphs, Not Records
- Design relationship patterns
- Consider traversal paths
- Build connected knowledge
- Enable discovery through relationships

## Troubleshooting

### Common Issues

1. **Missing Relationships Error**
   ```
   Error: Entity must have at least one relationship
   ```
   - Every entity needs connections
   - Add appropriate relationships based on entity type
   - Use relationship types from controlled vocabulary

2. **Schema Validation Failed**
   ```
   Error: Metadata missing required field 'version'
   ```
   - Check object_schemas table for requirements
   - Include all mandatory fields
   - Validate before submission

3. **Wrong Realm Access**
   ```
   Error: Synth cannot access skill_module memories without subscription
   ```
   - Verify synth is subscribed to skill module
   - Check realm boundaries
   - Use proper inheritance flags

4. **Entity Not Found in Search**
   - Ensure correct realm is included in search
   - Check entity exists in expected context
   - Verify relationship traversal depth

## Related Documentation

- [Contextual Realms Guide](./CONTEXTUAL_REALMS_GUIDE.md) - Deep dive into the four realms
- [Entity Relationships Guide](./ENTITY_RELATIONSHIPS_GUIDE.md) - Relationship patterns and graphs
- [Schema Validation Guide](./SCHEMA_VALIDATION_GUIDE.md) - Metadata requirements
- [Memory Consolidation Guide](./MEMORY_CONSOLIDATION_GUIDE.md) - Human-like memory updates
- [API Reference](./api-reference.md) - Complete endpoint documentation