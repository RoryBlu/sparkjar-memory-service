# Memory Entity Structure Guide

## Overview

Memory entities in the SparkJAR system are rich, interconnected knowledge nodes that form a vast knowledge graph. This guide covers the complete lifecycle of entities from creation through validation, relationships, and observations.

## What Makes a Complete Entity

Every memory entity MUST have:

1. **Contextual Anchor** - Exists within a specific realm
2. **Schema Validation** - Metadata validates against object_schemas
3. **Relationships** - At least one connection to other entities
4. **Observations** - Multiple timestamped, sourced facts
5. **Unique Key** - Short, descriptive identifier

### Entity Anatomy

```python
{
  # 1. CONTEXTUAL ANCHOR (Required)
  "actor_type": "synth_class",              # Which realm
  "actor_id": "24",                         # Specific context
  
  # 2. IDENTIFICATION (Required)
  "entity_name": "blog_writing_sop_v4",     # Unique key within context
  "entity_type": "procedure",               # Semantic type
  
  # 3. VALIDATED METADATA (Required)
  "metadata": {
    "version": "4.0",                       # Schema-required field
    "category": "content_creation",         # Schema-required field
    "phases": 4,                           # Schema-required field
    "last_updated": "2024-01-20",          # Schema-required field
    "approver": "Content Team Lead",        # Schema-required field
    "test_coverage": 0.95                   # Schema-required field
  },
  
  # 4. RELATIONSHIPS (Required - min 1)
  "relationships": [
    {
      "type": "validates",
      "direction": "incoming",
      "from_entity": "blog_qa_checklist",
      "strength": 1.0
    },
    {
      "type": "requires", 
      "direction": "outgoing",
      "to_entity": "blog_post_json_structure",
      "metadata": {"critical": true}
    },
    {
      "type": "measured_by",
      "direction": "incoming", 
      "from_entity": "blog_performance_metrics"
    }
  ],
  
  # 5. OBSERVATIONS (Required - min 2)
  "observations": [
    {
      "id": "obs-001",
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
      "timestamp": "2024-01-15T10:00:00Z",
      "confidence": 0.95
    },
    {
      "id": "obs-002",
      "type": "procedure_update",
      "value": {
        "change_type": "enhancement",
        "description": "Added AI-assisted research tools",
        "impact": "Reduced research time by 40%"
      },
      "source": "Process Improvement Team",
      "timestamp": "2024-01-18T14:30:00Z",
      "confidence": 0.88
    }
  ],
  
  # 6. LIFECYCLE METADATA (System-managed)
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-20T09:15:00Z",
  "created_by": "system|user|synth_id",
  "validation_status": "valid",
  "validation_timestamp": "2024-01-20T09:15:00Z"
}
```

## Entity Naming Conventions

### Rules for Entity Names

Entity names are **unique keys** within their context:

1. **Maximum 30 characters**
2. **Lowercase with underscores** (snake_case)
3. **Descriptive but concise**
4. **Version suffix if needed** (_v2, _v3)
5. **No spaces or special characters**

### Good vs Bad Names

```python
# ✅ GOOD - Concise Keys
blog_writing_sop_v4
excel_pivot_tables
customer_onboarding
synth_disclosure_policy
q4_sales_metrics

# ❌ BAD - Long Descriptions
Blog Writing Standard Operating Procedure Version 4.0
Microsoft Excel Pivot Table Creation Guidelines  
Customer Onboarding Process for Enterprise Clients
This is our policy for synthetic human disclosure
Fourth Quarter Sales Performance Metrics Dashboard
```

### Naming by Entity Type

Different entity types follow patterns:

```python
# Procedures
"{domain}_{action}_sop_v{n}"     # blog_writing_sop_v4
"{process}_procedure"             # onboarding_procedure

# Policies  
"{scope}_{topic}_policy"          # company_ai_policy
"{domain}_compliance_rules"       # finance_compliance_rules

# Knowledge Bases
"{domain}_{topic}_guide"          # python_async_guide
"{tool}_reference"                # excel_formulas_reference

# Metrics
"{period}_{metric}_kpi"           # q4_revenue_kpi
"{domain}_performance_metrics"    # blog_performance_metrics

# Templates
"{output}_template"               # invoice_template
"{format}_structure"              # blog_json_structure
```

## Entity Types

### Core Entity Types

1. **procedure** - Step-by-step processes
2. **policy** - Rules and mandates
3. **knowledge_base** - Reference information
4. **metric** - KPIs and measurements
5. **template** - Reusable structures
6. **checklist** - Validation criteria
7. **guideline** - Best practices
8. **preference** - Individual settings
9. **learning** - Discovered patterns
10. **constraint** - Limitations/boundaries

### Entity Type Characteristics

```python
ENTITY_TYPE_SCHEMAS = {
    "procedure": {
        "required_metadata": ["version", "phases", "approver"],
        "required_observations": ["phase_details", "prerequisites"],
        "common_relationships": ["validated_by", "requires", "supersedes"]
    },
    "policy": {
        "required_metadata": ["effective_date", "compliance_level", "authority"],
        "required_observations": ["policy_statement", "enforcement"],
        "common_relationships": ["overrides", "implements", "mandates"]
    },
    "metric": {
        "required_metadata": ["unit", "frequency", "target"],
        "required_observations": ["calculation", "threshold"],
        "common_relationships": ["measures", "triggers", "informs"]
    }
}
```

## Schema Validation

### How Validation Works

1. **Metadata Schema Lookup**
   ```sql
   SELECT schema FROM object_schemas 
   WHERE name = '{entity_type}_metadata'
   AND object_type = 'memory_entity_metadata'
   ```

2. **Validation Execution**
   ```python
   def validate_entity_metadata(entity):
       schema = get_schema(f"{entity.type}_metadata")
       
       try:
           jsonschema.validate(entity.metadata, schema)
           entity.validation_status = "valid"
       except ValidationError as e:
           entity.validation_status = "invalid"
           entity.validation_errors = str(e)
   ```

3. **Validation Recording**
   ```python
   entity.metadata["_validation"] = {
       "schema_name": f"{entity_type}_metadata",
       "validated_at": datetime.utcnow(),
       "validator_version": "2.0",
       "passed": True,
       "warnings": []
   }
   ```

### Example Schema

```json
{
  "name": "procedure_metadata",
  "schema": {
    "type": "object",
    "properties": {
      "version": {
        "type": "string",
        "pattern": "^[0-9]+\\.[0-9]+$"
      },
      "phases": {
        "type": "integer",
        "minimum": 1,
        "maximum": 10
      },
      "approver": {
        "type": "string",
        "minLength": 3
      },
      "category": {
        "type": "string",
        "enum": ["content", "sales", "support", "technical"]
      },
      "test_coverage": {
        "type": "number",
        "minimum": 0,
        "maximum": 1
      }
    },
    "required": ["version", "phases", "approver", "category"],
    "additionalProperties": true
  }
}
```

## Relationships

### Relationship Requirements

Every entity MUST have at least one relationship:

```python
# Minimum viable entity
entity = {
    "name": "new_procedure",
    "relationships": [
        {
            "type": "based_on",
            "to": "industry_standard"
        }
    ]
}

# Rich relationship network
entity = {
    "name": "customer_onboarding_v3",
    "relationships": [
        # Versioning
        {"type": "supersedes", "to": "customer_onboarding_v2"},
        
        # Dependencies
        {"type": "requires", "to": "crm_access"},
        {"type": "requires", "to": "email_templates"},
        
        # Validation
        {"type": "validated_by", "from": "onboarding_checklist"},
        
        # Measurement
        {"type": "measured_by", "from": "customer_satisfaction_kpi"},
        
        # Enhancement
        {"type": "enhanced_by", "from": "ai_automation_tools"}
    ]
}
```

### Relationship Types

**Hierarchical**:
- `implements` - Realizes an abstract concept
- `extends` - Adds to existing entity
- `supersedes` - Replaces older version
- `based_on` - Derived from source

**Dependency**:
- `requires` - Needs to function
- `uses` - Optionally leverages
- `triggers` - Causes activation
- `enables` - Makes possible

**Validation**:
- `validates` - Checks correctness
- `validated_by` - Is checked by
- `measures` - Tracks performance
- `measured_by` - Performance tracked by

**Modification**:
- `overrides` - Takes precedence
- `enhances` - Improves upon
- `conflicts_with` - Incompatible
- `replaces` - Direct substitution

## Observations

### Observation Structure

```python
{
    "id": "obs-{uuid}",
    "type": "observation_type",
    "value": {
        # Structured data specific to type
    },
    "source": "System|Human|Synth|External",
    "timestamp": "2024-01-20T10:00:00Z",
    "confidence": 0.95,
    "metadata": {
        "method": "direct_observation|inference|calculation",
        "sample_size": 100,
        "conditions": {}
    }
}
```

### Observation Types by Entity

**Procedure Observations**:
```python
observations = [
    {
        "type": "phase_detail",
        "value": {
            "phase_number": 1,
            "name": "Initialization",
            "steps": [...],
            "duration_estimate": "10-15 minutes"
        }
    },
    {
        "type": "success_metric",
        "value": {
            "metric": "completion_rate",
            "target": 0.95,
            "current": 0.97
        }
    }
]
```

**Policy Observations**:
```python
observations = [
    {
        "type": "policy_statement",
        "value": {
            "statement": "All data must be encrypted at rest",
            "requirement_level": "mandatory",
            "exceptions": []
        }
    },
    {
        "type": "compliance_check",
        "value": {
            "last_audit": "2024-01-15",
            "compliance_rate": 1.0,
            "findings": []
        }
    }
]
```

### Observation Evolution

Observations accumulate over time:

```python
# Initial observation
{
    "type": "performance_metric",
    "value": {"engagement_rate": 0.032},
    "timestamp": "2024-01-01T00:00:00Z"
}

# Learning observation
{
    "type": "pattern_discovered",
    "value": {
        "pattern": "Question headlines increase engagement",
        "impact": "+23%",
        "confidence": 0.89
    },
    "timestamp": "2024-01-15T00:00:00Z"
}

# Optimization observation
{
    "type": "optimization_applied",
    "value": {
        "change": "All titles now use questions",
        "result": {"engagement_rate": 0.041}
    },
    "timestamp": "2024-01-20T00:00:00Z"
}
```

## Entity Lifecycle

### 1. Creation

```python
async def create_complete_entity(realm_context, entity_def):
    # 1. Validate realm placement
    validate_realm_appropriateness(realm_context, entity_def)
    
    # 2. Generate unique key
    entity_name = generate_entity_key(entity_def)
    
    # 3. Validate metadata schema
    metadata = validate_against_schema(
        entity_def.metadata,
        f"{entity_def.type}_metadata"
    )
    
    # 4. Ensure relationships
    if not entity_def.relationships:
        raise ValueError("Entity must have at least one relationship")
    
    # 5. Validate observations
    if len(entity_def.observations) < 2:
        raise ValueError("Entity must have at least two observations")
    
    # 6. Create with transaction
    entity = await create_entity_transaction(
        realm_context,
        entity_name,
        entity_def
    )
    
    return entity
```

### 2. Evolution

```python
async def evolve_entity(entity_id, evolution_type, data):
    entity = await get_entity(entity_id)
    
    if evolution_type == "add_observation":
        # Validate observation matches entity type
        validate_observation_for_entity(data, entity.type)
        await add_observation(entity_id, data)
        
    elif evolution_type == "add_relationship":
        # Ensure relationship makes sense
        validate_relationship_logic(entity, data)
        await add_relationship(entity_id, data)
        
    elif evolution_type == "update_metadata":
        # Re-validate against schema
        new_metadata = {**entity.metadata, **data}
        validate_against_schema(new_metadata, f"{entity.type}_metadata")
        await update_metadata(entity_id, new_metadata)
        
    # Update timestamp
    await update_entity_timestamp(entity_id)
```

### 3. Consolidation

For statistical entities:

```python
async def consolidate_statistical_entity(entity_id):
    entity = await get_entity(entity_id)
    
    if entity.type != "metric":
        return
    
    observations = await get_observations(entity_id)
    
    # Group by metric key
    metrics = {}
    for obs in observations:
        if obs.type == "performance_metric":
            key = obs.value.get("metric_name")
            metrics[key] = obs
    
    # Keep only latest value per metric
    for metric_name, observations in metrics.items():
        latest = max(observations, key=lambda o: o.timestamp)
        # Archive others
        for obs in observations:
            if obs.id != latest.id:
                await archive_observation(obs.id)
```

## Entity Discovery

### Through Relationships

```python
async def discover_related_entities(entity_id, depth=2):
    """Discover entities through relationship traversal"""
    
    discovered = set()
    to_explore = [(entity_id, 0)]
    
    while to_explore:
        current_id, current_depth = to_explore.pop(0)
        
        if current_depth >= depth:
            continue
            
        # Get all relationships
        relationships = await get_entity_relationships(current_id)
        
        for rel in relationships:
            related_id = rel.to_entity_id or rel.from_entity_id
            
            if related_id not in discovered:
                discovered.add(related_id)
                to_explore.append((related_id, current_depth + 1))
    
    return discovered
```

### Through Observations

```python
async def discover_by_observation_pattern(pattern):
    """Find entities with similar observations"""
    
    query = """
    SELECT DISTINCT e.*
    FROM memory_entities e
    JOIN memory_observations o ON e.id = o.entity_id
    WHERE o.observation_value @> %s
    AND e.deleted_at IS NULL
    """
    
    return await execute_query(query, pattern)
```

## Best Practices

### 1. Entity Completeness

Always create complete entities:

```python
# ❌ Incomplete entity
entity = {
    "name": "new_process",
    "type": "procedure"
}

# ✅ Complete entity
entity = {
    "name": "invoice_processing_v2",
    "type": "procedure",
    "metadata": {
        "version": "2.0",
        "phases": 3,
        "approver": "Finance Lead",
        "category": "financial",
        "automation_level": 0.7
    },
    "relationships": [
        {"type": "supersedes", "to": "invoice_processing_v1"},
        {"type": "requires", "to": "accounting_system_access"},
        {"type": "validated_by", "from": "invoice_audit_checklist"}
    ],
    "observations": [
        {
            "type": "phase_detail",
            "value": {"phase": 1, "name": "Receipt & Validation"},
            "source": "Process Team"
        },
        {
            "type": "performance_metric",
            "value": {"processing_time": "4.5 minutes"},
            "source": "System Analytics"
        }
    ]
}
```

### 2. Meaningful Relationships

Create relationships that add value:

```python
# ❌ Weak relationship
{"type": "related_to", "to": "some_entity"}

# ✅ Strong relationships
[
    {"type": "implements", "to": "iso_9001_standard"},
    {"type": "validated_by", "from": "quality_audit_checklist"},
    {"type": "triggers", "to": "payment_workflow"},
    {"type": "measured_by", "from": "processing_time_kpi"}
]
```

### 3. Rich Observations

Observations should tell a story:

```python
# ❌ Poor observation
{
    "type": "note",
    "value": "Works well"
}

# ✅ Rich observation
{
    "type": "performance_analysis",
    "value": {
        "metric": "customer_satisfaction",
        "baseline": 3.2,
        "current": 4.7,
        "improvement": "47%",
        "factors": [
            "Reduced wait time",
            "Clearer communication",
            "Proactive updates"
        ]
    },
    "source": "Q4 Customer Survey",
    "timestamp": "2024-01-20T15:00:00Z",
    "confidence": 0.92,
    "sample_size": 1847
}
```

## Summary

Memory entities are:
- **Contextually Anchored** - Exist within realms
- **Schema Validated** - Conform to standards
- **Relationship Rich** - Connected in graphs
- **Observation Dense** - Multiple perspectives
- **Uniquely Keyed** - Concise identifiers

By following these patterns, you create a rich, discoverable, validated knowledge graph that powers intelligent agent behavior.