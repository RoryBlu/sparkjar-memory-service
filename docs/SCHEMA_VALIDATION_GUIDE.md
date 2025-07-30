# Schema Validation Guide

## Overview

Schema validation is a **mandatory requirement** for all memory entities in the SparkJAR Memory System. Every entity's metadata must validate against schemas stored in the `object_schemas` database table. This ensures data consistency, enables intelligent validation, and maintains quality standards across all memory realms.

## Core Principle: No Unvalidated Metadata

Every memory entity MUST have its metadata validated against a registered schema:

```python
# ❌ INVALID - Entity without schema validation
{
    "entity_name": "blog_procedure",
    "entity_type": "procedure",
    "metadata": {
        "some_field": "some_value"  # Not validated!
    }
}

# ✅ VALID - Entity with validated metadata
{
    "entity_name": "blog_writing_sop_v4",
    "entity_type": "procedure",
    "metadata": {
        "version": "4.0",        # Required by procedure_metadata schema
        "phases": 4,             # Required by procedure_metadata schema
        "approver": "Team Lead", # Required by procedure_metadata schema
        "category": "content",   # Required by procedure_metadata schema
        "_validation": {
            "schema_name": "procedure_metadata",
            "validated_at": "2024-01-20T10:00:00Z",
            "passed": true
        }
    }
}
```

## Schema Storage and Lookup

### Object Schemas Table Structure

```sql
CREATE TABLE object_schemas (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,           -- Schema identifier
    object_type VARCHAR(255) NOT NULL,    -- Type of object being validated
    schema JSONB NOT NULL,               -- JSON Schema definition
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version VARCHAR(50) DEFAULT '1.0'
);

-- Unique constraint on schema name
CREATE UNIQUE INDEX idx_schema_name ON object_schemas(name);
```

### Schema Naming Convention

Schema names follow the pattern: `{entity_type}_metadata`

```python
SCHEMA_NAMING = {
    "procedure": "procedure_metadata",
    "policy": "policy_metadata", 
    "knowledge_base": "knowledge_base_metadata",
    "metric": "metric_metadata",
    "checklist": "checklist_metadata",
    "template": "template_metadata",
    "guideline": "guideline_metadata",
    "learning": "learning_metadata",
    "constraint": "constraint_metadata",
    "preference": "preference_metadata"
}
```

### Database Seeding

Run the seeding scripts once to populate the `object_schemas` table with the
default schemas:

```bash
python scripts/seed_memory_schemas.py
python scripts/seed_relationship_schemas.py
```

## Schema Definitions by Entity Type

### 1. Procedure Metadata Schema

For step-by-step processes and workflows:

```json
{
    "name": "procedure_metadata",
    "object_type": "memory_entity_metadata",
    "schema": {
        "type": "object",
        "properties": {
            "version": {
                "type": "string",
                "pattern": "^[0-9]+\\.[0-9]+$",
                "description": "Semantic version (e.g., '1.0', '2.3')"
            },
            "phases": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10,
                "description": "Number of phases in the procedure"
            },
            "approver": {
                "type": "string",
                "minLength": 3,
                "maxLength": 100,
                "description": "Person or role who approved this procedure"
            },
            "category": {
                "type": "string",
                "enum": ["content", "sales", "support", "technical", "administrative", "compliance"],
                "description": "Procedure category"
            },
            "test_coverage": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Percentage of procedure covered by tests"
            },
            "automation_level": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Percentage of procedure that can be automated"
            },
            "estimated_duration": {
                "type": "string",
                "pattern": "^[0-9]+-[0-9]+ (minutes|hours|days)$",
                "description": "Estimated time range (e.g., '30-45 minutes')"
            }
        },
        "required": ["version", "phases", "approver", "category"],
        "additionalProperties": true
    }
}
```

### 2. Policy Metadata Schema

For rules, mandates, and organizational requirements:

```json
{
    "name": "policy_metadata",
    "object_type": "memory_entity_metadata",
    "schema": {
        "type": "object",
        "properties": {
            "effective_date": {
                "type": "string",
                "format": "date",
                "description": "When this policy becomes effective"
            },
            "compliance_level": {
                "type": "string",
                "enum": ["mandatory", "recommended", "optional"],
                "description": "Required compliance level"
            },
            "authority": {
                "type": "string",
                "minLength": 3,
                "description": "Authority that issued this policy"
            },
            "scope": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["all_synths", "synth_class", "specific_client", "skill_module"]
                },
                "description": "Who this policy applies to"
            },
            "enforcement_mechanism": {
                "type": "string",
                "enum": ["automatic", "manual_review", "audit", "self_enforced"],
                "description": "How policy compliance is enforced"
            },
            "violation_consequences": {
                "type": "array",
                "items": {"type": "string"},
                "description": "What happens when policy is violated"
            },
            "review_frequency": {
                "type": "string",
                "enum": ["monthly", "quarterly", "annually", "as_needed"],
                "description": "How often policy is reviewed"
            }
        },
        "required": ["effective_date", "compliance_level", "authority"],
        "additionalProperties": true
    }
}
```

### 3. Knowledge Base Metadata Schema

For reference information and documentation:

```json
{
    "name": "knowledge_base_metadata",
    "object_type": "memory_entity_metadata",
    "schema": {
        "type": "object",
        "properties": {
            "domain": {
                "type": "string",
                "minLength": 3,
                "description": "Knowledge domain (e.g., 'technology', 'finance')"
            },
            "expertise_level": {
                "type": "string",
                "enum": ["beginner", "intermediate", "advanced", "expert"],
                "description": "Required expertise level to understand"
            },
            "last_updated": {
                "type": "string",
                "format": "date",
                "description": "When knowledge was last verified/updated"
            },
            "sources": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "Sources of information"
            },
            "accuracy_confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Confidence in accuracy (0-1)"
            },
            "applicable_versions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Software/system versions this applies to"
            },
            "prerequisites": {
                "type": "array",
                "items": {"type": "string"},
                "description": "What you need to know first"
            }
        },
        "required": ["domain", "last_updated", "sources"],
        "additionalProperties": true
    }
}
```

### 4. Metric Metadata Schema

For KPIs, measurements, and performance tracking:

```json
{
    "name": "metric_metadata",
    "object_type": "memory_entity_metadata",
    "schema": {
        "type": "object",
        "properties": {
            "unit": {
                "type": "string",
                "description": "Unit of measurement (e.g., 'percentage', 'dollars', 'minutes')"
            },
            "frequency": {
                "type": "string",
                "enum": ["real-time", "hourly", "daily", "weekly", "monthly", "quarterly"],
                "description": "How often metric is measured"
            },
            "target": {
                "oneOf": [
                    {"type": "number"},
                    {"type": "string"}
                ],
                "description": "Target value for this metric"
            },
            "calculation_method": {
                "type": "string",
                "description": "How the metric is calculated"
            },
            "data_sources": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Where metric data comes from"
            },
            "threshold_critical": {
                "oneOf": [
                    {"type": "number"},
                    {"type": "string"}
                ],
                "description": "Critical threshold value"
            },
            "threshold_warning": {
                "oneOf": [
                    {"type": "number"},
                    {"type": "string"}
                ],
                "description": "Warning threshold value"
            },
            "consolidation_enabled": {
                "type": "boolean",
                "default": false,
                "description": "Whether statistical consolidation is enabled"
            }
        },
        "required": ["unit", "frequency", "target"],
        "additionalProperties": true
    }
}
```

### 5. Template Metadata Schema

For reusable structures and formats:

```json
{
    "name": "template_metadata",
    "object_type": "memory_entity_metadata",
    "schema": {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "enum": ["json", "yaml", "markdown", "html", "xml", "csv", "docx"],
                "description": "Template format"
            },
            "variables": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "required": {"type": "boolean"},
                        "default": {"type": "string"}
                    },
                    "required": ["name", "type"]
                },
                "description": "Template variables"
            },
            "use_cases": {
                "type": "array",
                "items": {"type": "string"},
                "description": "When to use this template"
            },
            "output_type": {
                "type": "string",
                "description": "What the template produces"
            },
            "validation_rules": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Rules for validating template output"
            }
        },
        "required": ["format", "variables"],
        "additionalProperties": true
    }
}
```

## Validation Process

### 1. Schema Lookup

```python
async def get_validation_schema(entity_type: str) -> dict:
    """Get validation schema for entity type"""
    
    schema_name = f"{entity_type}_metadata"
    
    query = """
    SELECT schema FROM object_schemas 
    WHERE name = %s AND object_type = 'memory_entity_metadata'
    """
    
    result = await execute_query(query, [schema_name])
    
    if not result:
        raise SchemaNotFoundError(f"No schema found for {schema_name}")
    
    return result[0]['schema']
```

### 2. Validation Execution

```python
import jsonschema
from datetime import datetime

async def validate_entity_metadata(entity_type: str, metadata: dict) -> dict:
    """Validate metadata against registered schema"""
    
    # Get schema
    schema = await get_validation_schema(entity_type)
    
    # Validation result
    validation_result = {
        "schema_name": f"{entity_type}_metadata",
        "validated_at": datetime.utcnow().isoformat(),
        "validator_version": "2.0",
        "passed": False,
        "errors": [],
        "warnings": []
    }
    
    try:
        # Validate against schema
        jsonschema.validate(metadata, schema)
        validation_result["passed"] = True
        
    except jsonschema.ValidationError as e:
        validation_result["errors"].append({
            "path": list(e.path),
            "message": e.message,
            "invalid_value": e.instance
        })
        
    except jsonschema.SchemaError as e:
        validation_result["errors"].append({
            "type": "schema_error",
            "message": f"Invalid schema: {e.message}"
        })
    
    # Add warnings for missing optional fields
    if validation_result["passed"]:
        validation_result["warnings"] = check_optional_fields(schema, metadata)
    
    return validation_result
```

### 3. Validation Recording

```python
async def create_validated_entity(entity_data: dict) -> dict:
    """Create entity with validated metadata"""
    
    # Extract components
    entity_type = entity_data["entity_type"]
    metadata = entity_data["metadata"]
    
    # Validate metadata
    validation_result = await validate_entity_metadata(entity_type, metadata)
    
    if not validation_result["passed"]:
        raise ValidationError(
            f"Metadata validation failed: {validation_result['errors']}"
        )
    
    # Add validation metadata
    metadata["_validation"] = validation_result
    
    # Create entity with validated metadata
    entity = await create_entity({
        **entity_data,
        "metadata": metadata,
        "validation_status": "valid",
        "validation_timestamp": datetime.utcnow()
    })
    
    return entity
```

## Schema Management

### 1. Schema Registration

```python
async def register_schema(schema_definition: dict):
    """Register a new schema in the database"""
    
    query = """
    INSERT INTO object_schemas (name, object_type, schema, version)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (name) DO UPDATE SET
        schema = EXCLUDED.schema,
        version = EXCLUDED.version,
        updated_at = NOW()
    """
    
    await execute_query(query, [
        schema_definition["name"],
        schema_definition["object_type"],
        schema_definition["schema"],
        schema_definition.get("version", "1.0")
    ])
```

### 2. Schema Evolution

```python
async def evolve_schema(schema_name: str, new_schema: dict, migration_strategy: str):
    """Evolve an existing schema with data migration"""
    
    # Get current schema
    current_schema = await get_schema(schema_name)
    
    # Validate evolution compatibility
    compatibility = check_schema_compatibility(current_schema, new_schema)
    
    if not compatibility["backward_compatible"] and migration_strategy != "force":
        raise SchemaEvolutionError(
            f"Breaking changes detected: {compatibility['breaking_changes']}"
        )
    
    # Update schema
    await update_schema(schema_name, new_schema)
    
    # Migrate existing data if needed
    if migration_strategy == "migrate_data":
        await migrate_existing_entities(schema_name, current_schema, new_schema)
    
    # Revalidate affected entities
    await revalidate_entities_by_schema(schema_name)
```

### 3. Schema Validation Cache

```python
class SchemaCache:
    def __init__(self, ttl: int = 300):  # 5 minute cache
        self.schemas = {}
        self.ttl = ttl
        self.timestamps = {}
    
    async def get_schema(self, schema_name: str) -> dict:
        """Get schema with caching"""
        
        # Check cache validity
        if (schema_name in self.schemas and 
            time.time() - self.timestamps.get(schema_name, 0) < self.ttl):
            return self.schemas[schema_name]
        
        # Load from database
        schema = await load_schema_from_db(schema_name)
        
        # Cache for future use
        self.schemas[schema_name] = schema
        self.timestamps[schema_name] = time.time()
        
        return schema
    
    def invalidate_schema(self, schema_name: str):
        """Invalidate cached schema"""
        self.schemas.pop(schema_name, None)
        self.timestamps.pop(schema_name, None)
```

## Validation Patterns

### 1. Required Field Validation

```python
# Schema with required fields
{
    "type": "object",
    "properties": {
        "version": {"type": "string"},
        "category": {"type": "string"}
    },
    "required": ["version", "category"],  # These must be present
    "additionalProperties": true          # Allow extra fields
}

# Valid metadata
{
    "version": "1.0",
    "category": "content",
    "extra_field": "allowed"  # Additional properties OK
}
```

### 2. Enumerated Values

```python
# Schema with enumerated values
{
    "type": "object",
    "properties": {
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"]
        },
        "status": {
            "type": "string", 
            "enum": ["draft", "review", "approved", "active", "deprecated"]
        }
    }
}
```

### 3. Pattern Validation

```python
# Schema with pattern validation
{
    "type": "object",
    "properties": {
        "version": {
            "type": "string",
            "pattern": "^[0-9]+\\.[0-9]+$"  # Must be X.Y format
        },
        "email": {
            "type": "string",
            "format": "email"
        },
        "duration": {
            "type": "string",
            "pattern": "^[0-9]+-[0-9]+ (minutes|hours|days)$"
        }
    }
}
```

### 4. Nested Object Validation

```python
# Schema with nested objects
{
    "type": "object",
    "properties": {
        "contact": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "role": {"type": "string"},
                "email": {"type": "string", "format": "email"}
            },
            "required": ["name", "role"]
        },
        "thresholds": {
            "type": "object",
            "properties": {
                "warning": {"type": "number"},
                "critical": {"type": "number"}
            },
            "additionalProperties": false  # No extra properties
        }
    }
}
```

## Custom Validation Rules

### 1. Cross-Field Validation

```python
def validate_cross_field_constraints(metadata: dict, schema: dict) -> list:
    """Validate constraints across multiple fields"""
    
    warnings = []
    
    # Example: If automation_level > 0.8, test_coverage should be > 0.9
    if (metadata.get("automation_level", 0) > 0.8 and 
        metadata.get("test_coverage", 0) <= 0.9):
        warnings.append({
            "type": "cross_field_warning",
            "message": "High automation should have high test coverage",
            "fields": ["automation_level", "test_coverage"]
        })
    
    # Example: Critical metrics must have thresholds
    if (metadata.get("priority") == "critical" and 
        not metadata.get("threshold_critical")):
        warnings.append({
            "type": "missing_critical_threshold",
            "message": "Critical metrics must define threshold_critical"
        })
    
    return warnings
```

### 2. Business Logic Validation

```python
def validate_business_logic(entity_type: str, metadata: dict) -> list:
    """Validate business-specific rules"""
    
    errors = []
    
    if entity_type == "procedure":
        # Procedures with >5 phases should have test coverage
        if metadata.get("phases", 0) > 5 and not metadata.get("test_coverage"):
            errors.append({
                "type": "business_rule_violation",
                "message": "Complex procedures (>5 phases) require test coverage"
            })
    
    elif entity_type == "policy":
        # Mandatory policies must have enforcement mechanism
        if (metadata.get("compliance_level") == "mandatory" and 
            not metadata.get("enforcement_mechanism")):
            errors.append({
                "type": "enforcement_required",
                "message": "Mandatory policies must specify enforcement mechanism"
            })
    
    return errors
```

## Error Handling

### 1. Validation Error Types

```python
class ValidationError(Exception):
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class SchemaNotFoundError(ValidationError):
    pass

class SchemaEvolutionError(ValidationError):
    pass

class ValidationTimeoutError(ValidationError):
    pass
```

### 2. Error Response Format

```json
{
    "error": {
        "type": "validation_error",
        "message": "Entity metadata validation failed",
        "details": {
            "entity_type": "procedure",
            "schema_name": "procedure_metadata",
            "validation_errors": [
                {
                    "path": ["phases"],
                    "message": "11 is greater than the maximum of 10",
                    "invalid_value": 11
                },
                {
                    "path": ["category"],
                    "message": "'invalid_category' is not one of ['content', 'sales', 'support', 'technical', 'administrative', 'compliance']",
                    "invalid_value": "invalid_category"
                }
            ],
            "validation_warnings": [
                {
                    "type": "missing_optional",
                    "message": "Consider adding 'test_coverage' for better quality tracking"
                }
            ]
        }
    },
    "status": 400
}
```

## Best Practices

### 1. Schema Design Principles

```python
# ✅ Good schema design
{
    "type": "object",
    "properties": {
        # Clear, descriptive names
        "estimated_duration": {
            "type": "string",
            "pattern": "^[0-9]+-[0-9]+ (minutes|hours|days)$",
            "description": "Time range for completion"
        },
        # Reasonable constraints
        "confidence_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Confidence in accuracy (0-1)"
        },
        # Extensible enums
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"],
            "description": "Task priority level"
        }
    },
    "required": ["estimated_duration"],  # Only truly required fields
    "additionalProperties": true         # Allow future extension
}
```

### 2. Schema Evolution Strategy

```python
# Version 1.0 - Initial schema
{
    "version": "1.0",
    "properties": {
        "name": {"type": "string"},
        "category": {"type": "string"}
    },
    "required": ["name"]
}

# Version 1.1 - Add optional field (backward compatible)
{
    "version": "1.1", 
    "properties": {
        "name": {"type": "string"},
        "category": {"type": "string"},
        "priority": {              # New optional field
            "type": "string",
            "enum": ["low", "medium", "high"],
            "default": "medium"
        }
    },
    "required": ["name"]  # Same required fields
}

# Version 2.0 - Breaking change (requires migration)
{
    "version": "2.0",
    "properties": {
        "name": {"type": "string"},
        "category": {"type": "string"}, 
        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
        "created_by": {"type": "string"}  # New required field
    },
    "required": ["name", "created_by"]  # Added required field
}
```

### 3. Validation Performance

```python
# Performance optimization strategies
class OptimizedValidator:
    def __init__(self):
        # Pre-compile schemas for faster validation
        self.compiled_schemas = {}
        
    def get_compiled_schema(self, schema_name: str):
        if schema_name not in self.compiled_schemas:
            schema = load_schema(schema_name)
            self.compiled_schemas[schema_name] = jsonschema.Draft7Validator(schema)
        return self.compiled_schemas[schema_name]
    
    async def validate_batch(self, entities: list) -> list:
        """Validate multiple entities efficiently"""
        
        results = []
        
        # Group by entity type for schema reuse
        by_type = {}
        for entity in entities:
            entity_type = entity["entity_type"]
            if entity_type not in by_type:
                by_type[entity_type] = []
            by_type[entity_type].append(entity)
        
        # Validate each type batch
        for entity_type, type_entities in by_type.items():
            validator = self.get_compiled_schema(f"{entity_type}_metadata")
            
            for entity in type_entities:
                validation_result = self.validate_single(validator, entity)
                results.append(validation_result)
        
        return results
```

### 4. Schema Testing

```python
import pytest

def test_procedure_schema_validation():
    """Test procedure metadata schema"""
    
    # Valid metadata
    valid_metadata = {
        "version": "1.0",
        "phases": 3,
        "approver": "Team Lead",
        "category": "content",
        "test_coverage": 0.85
    }
    
    result = validate_entity_metadata("procedure", valid_metadata)
    assert result["passed"] == True
    
    # Invalid metadata
    invalid_metadata = {
        "version": "1.0",
        "phases": 15,  # Exceeds maximum
        # Missing required 'approver'
        "category": "invalid_category"  # Not in enum
    }
    
    result = validate_entity_metadata("procedure", invalid_metadata)
    assert result["passed"] == False
    assert len(result["errors"]) == 3

def test_schema_backward_compatibility():
    """Test schema evolution doesn't break existing data"""
    
    old_data = {"name": "test", "category": "content"}
    new_schema = load_schema("procedure_metadata_v2")
    
    # Old data should still validate against new schema
    result = jsonschema.validate(old_data, new_schema)
    assert result is None  # No validation errors
```

## Integration with Memory Services

### 1. Memory Creation with Validation

```python
# Services integration
async def create_memory_with_validation(memory_data: dict):
    """Create memory entity with full validation"""
    
    # 1. Validate metadata schema
    validation_result = await validate_entity_metadata(
        memory_data["entity_type"], 
        memory_data["metadata"]
    )
    
    if not validation_result["passed"]:
        raise ValidationError("Schema validation failed", validation_result)
    
    # 2. Validate relationships
    if "relationships" in memory_data:
        await validate_relationships(memory_data["relationships"])
    
    # 3. Validate observations
    if "observations" in memory_data:
        await validate_observations(memory_data["observations"])
    
    # 4. Create entity with validation metadata
    return await create_entity({
        **memory_data,
        "metadata": {
            **memory_data["metadata"],
            "_validation": validation_result
        }
    })
```

### 2. Batch Validation for Performance

```python
async def validate_batch_memories(memories: list) -> dict:
    """Validate multiple memories efficiently"""
    
    validation_results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }
    
    # Group by entity type for schema caching
    by_type = defaultdict(list)
    for memory in memories:
        by_type[memory["entity_type"]].append(memory)
    
    # Validate each type group
    for entity_type, type_memories in by_type.items():
        schema = await get_validation_schema(entity_type)
        
        for memory in type_memories:
            try:
                result = await validate_entity_metadata(entity_type, memory["metadata"])
                
                if result["passed"]:
                    validation_results["passed"].append({
                        "memory": memory,
                        "validation": result
                    })
                else:
                    validation_results["failed"].append({
                        "memory": memory,
                        "validation": result
                    })
                
                if result["warnings"]:
                    validation_results["warnings"].extend(result["warnings"])
                    
            except Exception as e:
                validation_results["failed"].append({
                    "memory": memory,
                    "error": str(e)
                })
    
    return validation_results
```

## Summary

Schema validation in the SparkJAR Memory System:

1. **Mandatory Requirement** - All entity metadata must validate against registered schemas
2. **Type-Specific Schemas** - Each entity type has its own metadata schema requirements
3. **Flexible Evolution** - Schemas can evolve with backward compatibility considerations
4. **Performance Optimization** - Validation is cached and batched for efficiency
5. **Quality Assurance** - Ensures consistent, high-quality memory entities
6. **Business Logic Integration** - Supports custom validation rules beyond schema structure

By enforcing schema validation, the memory system maintains data integrity while enabling intelligent quality assurance and automated validation of complex knowledge structures.