# Memory Service API - Skill Module Context Support

## Overview

The Memory Service has been extended to support skill module context, allowing synths to create and manage memories within skill module contexts they are subscribed to. This enables skill modules to maintain their own memory spaces while still being accessible to subscribed synths through the hierarchical memory system.

## New Actor Type: skill_module

The `skill_module` actor type has been added to the system, joining the existing actor types:
- `human` - Human users (references client_users table)
- `synth` - AI agents/personas (references synths table)  
- `synth_class` - AI agent templates (references synth_classes table)
- `client` - Organizations (references clients table)
- **`skill_module`** - Skill modules/capabilities (references skill_modules table)

## Memory Hierarchy

The enhanced memory hierarchy now supports:
```
synth → skill_module → synth_class → client
```

This allows synths to:
1. Access their own memories
2. Access memories from skill modules they're subscribed to
3. Inherit procedural knowledge from their class templates
4. Access shared organizational knowledge

## API Endpoints

### 1. Upsert Entities with Skill Module Context

**Endpoint:** `POST /memory/entities/upsert`

**Description:** Creates new entities or updates existing ones based on entity_name. Supports optional skill module context for synth actors.

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Request Body:**
```json
{
  "entities": [
    {
      "entity_name": "odoo.res.partner",
      "entity_type": "model",
      "observations": [
        {
          "type": "field_definition",
          "content": "name: char(required=True)",
          "metadata": {"field_type": "char", "required": true}
        }
      ],
      "metadata": {
        "module": "base",
        "inherits": ["mail.thread"]
      }
    }
  ]
}
```

**Query Parameters:**
- `skill_module_id` (optional, UUID): The skill module context to use for creating/updating entities

**Response:** `200 OK`
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "entityName": "odoo.res.partner",
    "entityType": "model",
    "observations": [...],
    "metadata": {...},
    "createdAt": "2024-01-10T10:00:00Z",
    "updatedAt": "2024-01-10T10:00:00Z"
  }
]
```

**Error Responses:**

- `400 Bad Request` - Invalid request
  ```json
  {
    "code": "MEM-103",
    "message": "skill_module_id can only be used by synth actors"
  }
  ```

- `400 Bad Request` - Not subscribed
  ```json
  {
    "code": "MEM-103", 
    "message": "Synth {synth_id} is not subscribed to skill module {skill_module_id}"
  }
  ```

### 2. Search with Hierarchical Access

The existing search endpoint automatically includes skill module memories for synth actors:

**Endpoint:** `POST /memory/search`

**Response includes `access_context` and `access_source` fields:**
```json
[
  {
    "id": "...",
    "entityName": "odoo.res.partner",
    "similarity": 0.95,
    "access_context": "skill_module",
    "access_source": "skill_module",
    ...
  }
]
```

Access sources:
- `own` - Actor's own memories
- `skill_module` - From a subscribed skill module
- `inherited_template` - From synth_class template
- `organizational` - From client-level memories

## Usage Examples

### 1. Synth Creating Memories in Skill Module Context

```bash
# Synth creating memories in Odoo skill module context
curl -X POST https://api.sparkjar.com/memory/entities/upsert?skill_module_id=odoo-skill-module-uuid \
  -H "Authorization: Bearer synth_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [{
      "entity_name": "sale.order.workflow",
      "entity_type": "procedure",
      "observations": [{
        "type": "step",
        "content": "Create quotation with customer and products"
      }]
    }]
  }'
```

### 2. Skill Module Creating Its Own Memories

```bash
# Skill module directly creating memories (e.g., during initialization)
curl -X POST https://api.sparkjar.com/memory/entities \
  -H "Authorization: Bearer skill_module_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [{
      "entity_name": "odoo.api.version",
      "entity_type": "configuration",
      "observations": [{
        "type": "version_info",
        "content": "Odoo 16.0"
      }]
    }]
  }'
```

### 3. Synth Searching Across All Contexts

```bash
# Search includes synth's own memories + skill modules + synth_class + client
curl -X POST https://api.sparkjar.com/memory/search \
  -H "Authorization: Bearer synth_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how to create sales order",
    "limit": 10
  }'
```

## Validation Rules

1. **Actor Validation**: All actor_id values must exist in their corresponding tables
2. **Skill Module Context**: Only synth actors can use skill_module_id parameter
3. **Subscription Check**: Synths must be subscribed to a skill module to create memories in its context
4. **Hierarchical Access**: Read access follows the hierarchy, write access requires explicit context

## Database Changes

1. **New Table**: `skill_modules` table stores skill module definitions
2. **New Table**: `synth_skill_subscriptions` links synths to skill modules
3. **Updated Constraints**: `memory_entities` and `memory_relations` tables now accept 'skill_module' as valid actor_type
4. **Migration Required**: Run `update_actor_type_constraints.sql` to update existing CHECK constraints

## Best Practices

1. **Use Upsert for Idempotency**: The upsert endpoint ensures memories can be safely re-created without duplication
2. **Skill Module Context**: Use skill_module_id when creating memories that belong to a specific skill/capability domain
3. **Access Patterns**: Design your memory queries to leverage the hierarchical access pattern
4. **Validation**: Always validate actor references before attempting to create memories

## Error Codes

- `MEM-101`: Invalid actor_type
- `MEM-102`: Actor validation failed (actor_id doesn't exist)
- `MEM-103`: Skill module context validation failed
- `MEM-104`: Subscription validation failed