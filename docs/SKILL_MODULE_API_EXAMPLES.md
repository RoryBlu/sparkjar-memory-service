# Skill Module Context API Examples

## Testing with cURL

### 1. Get Valid Actor Types
```bash
curl -X GET http://localhost:8443/actor-types
```

Expected response:
```json
{
  "actor_types": ["human", "synth", "synth_class", "client", "skill_module"],
  "descriptions": {
    "human": "Human users (references client_users table)",
    "synth": "AI agents/personas (references synths table)",
    "synth_class": "AI agent templates (references synth_classes table)",
    "client": "Organizations (references clients table)",
    "skill_module": "Skill modules/capabilities (references skill_modules table)"
  }
}
```

### 2. Synth Creating Memories in Skill Module Context

```bash
# Set your JWT token (must have synth actor_type)
JWT_TOKEN="your_synth_jwt_token_here"
SKILL_MODULE_ID="323e4567-e89b-12d3-a456-426614174002"

# Upsert entities in skill module context
curl -X POST "http://localhost:8443/memory/entities/upsert?skill_module_id=${SKILL_MODULE_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [
      {
        "entity_name": "odoo.sale.order",
        "entity_type": "model",
        "observations": [
          {
            "type": "field_definition",
            "content": "partner_id: many2one to res.partner",
            "metadata": {
              "field_type": "many2one",
              "relation": "res.partner",
              "required": true
            }
          },
          {
            "type": "field_definition",
            "content": "order_line: one2many to sale.order.line",
            "metadata": {
              "field_type": "one2many",
              "relation": "sale.order.line",
              "inverse_name": "order_id"
            }
          }
        ],
        "metadata": {
          "module": "sale",
          "inherits": ["mail.thread", "mail.activity.mixin"]
        }
      }
    ]
  }'
```

### 3. Skill Module Creating Its Own Memories

```bash
# Set your JWT token (must have skill_module actor_type)
SKILL_MODULE_JWT="your_skill_module_jwt_token_here"

# Create entities as skill module
curl -X POST "http://localhost:8443/memory/entities" \
  -H "Authorization: Bearer ${SKILL_MODULE_JWT}" \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [
      {
        "entity_name": "odoo.workflow.quotation_to_order",
        "entity_type": "procedure",
        "observations": [
          {
            "type": "prerequisite",
            "content": "User must have sales access rights",
            "metadata": {"importance": "high"}
          },
          {
            "type": "step",
            "content": "Navigate to Sales > Quotations",
            "metadata": {"step_number": 1, "ui_path": "Sales/Quotations"}
          },
          {
            "type": "step", 
            "content": "Click Create to start new quotation",
            "metadata": {"step_number": 2, "action": "create"}
          },
          {
            "type": "step",
            "content": "Select customer from partner dropdown",
            "metadata": {"step_number": 3, "field": "partner_id"}
          }
        ],
        "metadata": {
          "workflow_type": "sales",
          "complexity": "basic",
          "version": "16.0"
        }
      }
    ]
  }'
```

### 4. Searching with Hierarchical Access

```bash
# Search as synth (includes skill module memories)
curl -X POST "http://localhost:8443/memory/search" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how to create sales quotation in odoo",
    "entity_type": "procedure",
    "limit": 5
  }'
```

Expected response includes access_context:
```json
[
  {
    "id": "...",
    "entityName": "odoo.workflow.quotation_to_order",
    "entityType": "procedure",
    "similarity": 0.92,
    "access_context": "skill_module",
    "access_source": "skill_module",
    "observations": [...]
  }
]
```

## Postman Collection

### Collection Variables
```json
{
  "base_url": "http://localhost:8443",
  "jwt_token": "{{synth_jwt_token}}",
  "skill_module_id": "323e4567-e89b-12d3-a456-426614174002"
}
```

### Request: Upsert with Skill Module Context

**Method:** POST  
**URL:** `{{base_url}}/memory/entities/upsert?skill_module_id={{skill_module_id}}`  
**Headers:**
- Authorization: Bearer {{jwt_token}}
- Content-Type: application/json

**Body (raw JSON):**
```json
{
  "entities": [
    {
      "entity_name": "odoo.res.partner.merge",
      "entity_type": "action",
      "observations": [
        {
          "type": "description",
          "content": "Merge duplicate partner records",
          "metadata": {"module": "base"}
        },
        {
          "type": "precondition",
          "content": "Select multiple partners with similar data",
          "metadata": {"ui_element": "list_view"}
        }
      ],
      "metadata": {
        "action_type": "server_action",
        "requires_selection": true,
        "min_records": 2
      }
    }
  ]
}
```

### Request: Search Hierarchical Memories

**Method:** POST  
**URL:** `{{base_url}}/memory/search`  
**Headers:**
- Authorization: Bearer {{jwt_token}}
- Content-Type: application/json

**Body:**
```json
{
  "query": "merge duplicate partners",
  "limit": 10
}
```

## Testing Validation Errors

### 1. Non-synth Using Skill Module Context
```bash
# This should fail with error
curl -X POST "http://localhost:8443/memory/entities/upsert?skill_module_id=${SKILL_MODULE_ID}" \
  -H "Authorization: Bearer ${HUMAN_JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [{"entity_name": "test", "entity_type": "test", "observations": []}]
  }'
```

Expected error:
```json
{
  "code": "MEM-103",
  "message": "skill_module_id can only be used by synth actors"
}
```

### 2. Invalid Skill Module ID
```bash
# This should fail with validation error
curl -X POST "http://localhost:8443/memory/entities/upsert?skill_module_id=invalid-uuid" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [{"entity_name": "test", "entity_type": "test", "observations": []}]
  }'
```

### 3. Unsubscribed Skill Module
```bash
# This should fail if synth is not subscribed
curl -X POST "http://localhost:8443/memory/entities/upsert?skill_module_id=999e4567-e89b-12d3-a456-426614174999" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "entities": [{"entity_name": "test", "entity_type": "test", "observations": []}]
  }'
```

Expected error:
```json
{
  "code": "MEM-103",
  "message": "Synth {synth_id} is not subscribed to skill module {skill_module_id}"
}
```

## Environment Setup for Testing

1. **Start Memory Service:**
```bash
cd services/memory-service
python internal-api-with-validation.py  # Port 8001
python external-api-with-validation.py  # Port 8443
```

2. **Create Test Data:**
```sql
-- Insert test skill module
INSERT INTO skill_modules (id, name, module_type, vendor, metadata)
VALUES ('323e4567-e89b-12d3-a456-426614174002', 'Odoo ERP', 'erp', 'Odoo S.A.', '{}');

-- Insert test synth
INSERT INTO synths (id, name, synth_classes_id)
VALUES ('223e4567-e89b-12d3-a456-426614174001', 'Test Synth', 1);

-- Create subscription
INSERT INTO synth_skill_subscriptions (synth_id, skill_module_id, active)
VALUES ('223e4567-e89b-12d3-a456-426614174001', '323e4567-e89b-12d3-a456-426614174002', true);
```

3. **Generate JWT Tokens:**
```python
import jwt
from datetime import datetime, timedelta

# Synth token
synth_payload = {
    "client_id": "123e4567-e89b-12d3-a456-426614174000",
    "actor_type": "synth",
    "actor_id": "223e4567-e89b-12d3-a456-426614174001",
    "exp": datetime.utcnow() + timedelta(days=1)
}

synth_token = jwt.encode(synth_payload, "your_secret_key", algorithm="HS256")
print(f"Synth JWT: {synth_token}")
```