# Hierarchical Memory System Guide

## Overview

The SparkJAR Memory System implements a sophisticated 4-realm contextual architecture where memories exist within distinct boundaries and flow through the Synth as the central nexus. This guide explains how the realms interact and how memories inherit and subscribe across contexts.

## The Four Contextual Realms

```
CLIENT (Organization Level - Highest Precedence)
    ↓ provides company-wide policies & precedence
  SYNTH (Individual Agent - The Nexus) 
    ↑                        ↑
    inherits from          subscribes to
    ↓                        ↓
SYNTH_CLASS              SKILL_MODULE
(Role Identity)          (Tool Knowledge)
```

## Understanding the Synth as Nexus

The SYNTH is not just another level in a hierarchy - it's the **central integration point** where all memories converge:

### 1. Inheritance from SYNTH_CLASS

When a synth is created, it inherits its core identity:

```python
# Synth of class 24 (Blog Author) automatically inherits:
- blog_writing_sop_v4         # Writing procedures
- blog_seo_practices          # SEO knowledge
- blog_performance_metrics    # Success criteria
- blog_style_guide           # Writing standards

# This defines WHO the synth is professionally
```

### 2. Subscription to SKILL_MODULEs

Synths subscribe to tool knowledge based on client needs:

```python
# Blog Author synth might subscribe to:
- microsoft_365_suite    # Word, Excel, PowerPoint knowledge
- grammarly_pro         # Grammar and style checking
- wordpress_cms         # Publishing platform
- google_analytics      # Traffic analysis

# These are swappable based on client tools
```

### 3. Precedence from CLIENT

Client policies take precedence over all other memories:

```python
# Vervelyn Publishing CLIENT memories override:
- AI disclosure requirements (must identify as synth)
- Content restrictions (no medical advice)
- Brand voice guidelines (formal academic tone)
- Compliance policies (GDPR, accessibility)

# These apply to ALL synths in the organization
```

### 4. Individual SYNTH Learning

Each synth accumulates personal experiences:

```python
# Individual Blog Author synth learns:
- Tech articles with questions get +23% engagement
- Morning posts perform better for this audience
- Specific client prefers shorter paragraphs
- Personal optimization patterns
```

## How Memories Flow Through Realms

### Memory Access Pattern

When a synth needs information, the system:

1. **Checks SYNTH realm** - Personal experiences and optimizations
2. **Inherits from SYNTH_CLASS** - Professional knowledge and procedures
3. **Pulls from SKILL_MODULEs** - Tool-specific knowledge (if subscribed)
4. **Applies CLIENT precedence** - Organizational policies override all

### Example: Blog Writing Task

```python
# Synth queries: "How should I write this blog introduction?"

# System returns (in precedence order):
1. CLIENT: "All content must include AI disclosure in first paragraph"
2. SYNTH_CLASS: "Use hook-based introduction pattern from blog_writing_sop_v4"
3. SKILL_MODULE: "Optimize for Yoast SEO score in WordPress"
4. SYNTH: "Questions work well for tech audience (+23% engagement)"

# Final approach combines all realms with proper precedence
```

## Implementation Details

### Actor ID Format

The system uses flexible TEXT fields for actor_id:
- **SYNTH**: UUID format `"b9af0667-5c92-4892-a7c5-947ed0cab0db"`
- **SYNTH_CLASS**: String format `"24"` (blog author class)
- **SKILL_MODULE**: Name format `"microsoft_365_suite"`
- **CLIENT**: UUID format `"1d1c2154-242b-4f49-9ca8-e57129ddc823"`

### Database Query Pattern

Hierarchical queries use OR conditions to pull from multiple realms:

```sql
-- Get all memories accessible to a synth
SELECT * FROM memory_entities
WHERE (actor_type = 'synth' AND actor_id = :synth_id)
   OR (actor_type = 'synth_class' AND actor_id = :class_id)
   OR (actor_type = 'skill_module' AND actor_id IN :subscribed_modules)
   OR (actor_type = 'client' AND actor_id = :client_id)
ORDER BY 
  CASE actor_type
    WHEN 'client' THEN 1      -- Highest precedence
    WHEN 'synth' THEN 2       -- Personal overrides
    WHEN 'synth_class' THEN 3 -- Role knowledge
    WHEN 'skill_module' THEN 4 -- Tool knowledge
  END
```

### Memory Manager Implementation

The `HierarchicalMemoryManager` handles:

```python
class HierarchicalMemoryManager:
    async def get_synth_memories(self, synth_id: str):
        # 1. Get synth's class and subscriptions
        synth = await self.get_synth(synth_id)
        
        # 2. Build realm filters
        realms = {
            "synth": (synth.actor_type, synth.actor_id),
            "synth_class": ("synth_class", synth.class_id),
            "skill_modules": [("skill_module", m) for m in synth.subscribed_modules],
            "client": ("client", synth.client_id)
        }
        
        # 3. Query all realms
        memories = await self.query_realms(realms)
        
        # 4. Apply precedence rules
        return self.apply_precedence(memories)
```

## Practical Use Cases

### 1. Role-Based Knowledge (SYNTH_CLASS)

All Blog Authors (class 24) share:
```python
{
  "actor_type": "synth_class",
  "actor_id": "24",
  "memories": [
    "blog_writing_sop_v4",      # 4-phase writing process
    "blog_seo_practices",       # SEO optimization guide
    "blog_qa_checklist",        # Quality standards
    "blog_performance_metrics"  # Success KPIs
  ]
}
```

### 2. Tool Knowledge (SKILL_MODULE)

Microsoft 365 Suite module provides:
```python
{
  "actor_type": "skill_module", 
  "actor_id": "microsoft_365_suite",
  "memories": [
    "excel_formulas_reference",
    "word_template_library",
    "powerpoint_design_guide",
    "teams_collaboration_patterns"
  ]
}
```

### 3. Company Policies (CLIENT)

Vervelyn Publishing enforces:
```python
{
  "actor_type": "client",
  "actor_id": "1d1c2154-242b-4f49-9ca8-e57129ddc823",
  "memories": [
    "synth_disclosure_policy",    # AI transparency
    "content_compliance_rules",   # Legal restrictions
    "brand_voice_guidelines",     # Company tone
    "data_privacy_requirements"   # GDPR compliance
  ]
}
```

### 4. Individual Learning (SYNTH)

Specific synth accumulates:
```python
{
  "actor_type": "synth",
  "actor_id": "b9af0667-5c92-4892-a7c5-947ed0cab0db",
  "memories": [
    "tech_audience_preferences",    # Learned patterns
    "client_specific_style",        # Individual adjustments
    "performance_optimizations",    # Personal insights
    "task_execution_history"        # Experience log
  ]
}
```

## Best Practices

### 1. Always Enable Realm Inclusion

```python
# ❌ Don't query just one realm
results = await search_memories(
    actor_type="synth",
    actor_id=synth_id,
    query="writing guidelines"
)

# ✅ Do include all relevant realms
results = await search_memories(
    actor_type="synth",
    actor_id=synth_id,
    query="writing guidelines",
    include_synth_class=True,
    include_skill_module=True,
    include_client=True
)
```

### 2. Respect Realm Boundaries

```python
# ❌ Wrong realm for content
await create_memory(
    actor_type="synth_class",  # Wrong!
    entity_name="vervelyn_compliance_policy"  # This belongs in CLIENT
)

# ✅ Correct realm placement
await create_memory(
    actor_type="client",  # Correct!
    entity_name="vervelyn_compliance_policy"
)
```

### 3. Apply Correct Precedence

```python
def apply_memory_precedence(memories):
    """CLIENT > SYNTH > SYNTH_CLASS > SKILL_MODULE"""
    
    precedence_map = {}
    
    for memory in memories:
        key = memory['entity_name']
        realm = memory['actor_type']
        
        # Only keep highest precedence version
        if key not in precedence_map:
            precedence_map[key] = memory
        elif realm_precedence(realm) < realm_precedence(precedence_map[key]['actor_type']):
            precedence_map[key] = memory
    
    return list(precedence_map.values())
```

### 4. Manage Skill Module Subscriptions

```python
# Subscribe synth to new skill module
await subscribe_to_skill_module(
    synth_id=synth_id,
    skill_module="adobe_creative_suite",
    reason="Client requires Photoshop work"
)

# Unsubscribe when no longer needed
await unsubscribe_from_skill_module(
    synth_id=synth_id,
    skill_module="microsoft_365_suite",
    reason="Client migrated to Google Workspace"
)
```

## Performance Optimization

### 1. Cache Realm Mappings

```python
class RealmCache:
    def __init__(self, ttl=300):  # 5 minute cache
        self.synth_mappings = {}  # synth -> class, modules, client
        self.ttl = ttl
    
    async def get_synth_realms(self, synth_id):
        if synth_id in self.synth_mappings:
            return self.synth_mappings[synth_id]
        
        # Load and cache
        realms = await self.load_synth_realms(synth_id)
        self.synth_mappings[synth_id] = realms
        return realms
```

### 2. Batch Realm Queries

```python
# ❌ Multiple queries
class_memories = await get_memories("synth_class", class_id)
module_memories = await get_memories("skill_module", module_id)
client_memories = await get_memories("client", client_id)

# ✅ Single batched query
all_memories = await get_realm_memories({
    "synth_class": class_id,
    "skill_module": module_ids,
    "client": client_id
})
```

### 3. Index Optimization

Ensure indexes on:
- `(actor_type, actor_id)` - Primary realm lookup
- `(actor_type, actor_id, entity_name)` - Unique constraint
- `(client_id, deleted_at)` - Soft delete queries

## Troubleshooting

### Common Issues

1. **Missing Inherited Memories**
   ```python
   # Check synth-class association
   SELECT synth_classes_id FROM synths WHERE id = :synth_id
   
   # Verify class has memories
   SELECT COUNT(*) FROM memory_entities 
   WHERE actor_type = 'synth_class' AND actor_id = :class_id
   ```

2. **Skill Module Not Accessible**
   ```python
   # Verify subscription exists
   SELECT * FROM synth_skill_subscriptions
   WHERE synth_id = :synth_id AND skill_module_id = :module_id
   AND active = true
   ```

3. **Client Override Not Applied**
   ```python
   # Check precedence logic
   # CLIENT memories should always win
   # Verify client_id is correct in query
   ```

4. **Performance Degradation**
   - Enable caching for realm mappings
   - Use batch queries for multiple realms
   - Consider read replicas for heavy loads

## Future Enhancement: Dynamic Skill Modules

The architecture supports future dynamic skill module marketplace:

```python
# Future: Skill module subscription
{
  "skill_modules": [
    {
      "id": "salesforce_crm",
      "name": "Salesforce CRM Suite",
      "capabilities": ["lead_management", "opportunity_tracking"],
      "subscription_type": "per_synth",
      "cost": "$50/month"
    }
  ]
}

# Synths can swap modules based on client needs
await swap_skill_module(
    synth_id=synth_id,
    remove="hubspot_crm",
    add="salesforce_crm",
    reason="Client migrated CRM platforms"
)
```

## Summary

The hierarchical memory system enables:

1. **Clear Separation of Concerns** - Each realm has its purpose
2. **Flexible Knowledge Composition** - Synths combine multiple sources
3. **Organizational Control** - Client policies enforce compliance
4. **Individual Growth** - Synths learn and optimize personally
5. **Tool Flexibility** - Skill modules can be swapped as needed

By understanding the Synth as the nexus where all realms converge, you can build sophisticated agents that combine professional expertise, tool knowledge, organizational policies, and personal learning into coherent, effective behaviors.