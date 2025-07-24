# Contextual Realms Guide

## Introduction

The SparkJAR Memory System is built on the foundational principle that **no memory can exist without a context**. This guide provides a deep understanding of the four contextual realms, how they define boundaries for memories, and how they interact through the Synth as the central nexus.

## The Fundamental Principle: Context is Everything

### What is a Context (Realm)?

A **context** or **realm** is the foundational boundary within which ALL memory entities exist. It defines:

- **Ownership**: Who/what owns these memories
- **Access**: Who can see and use these memories  
- **Meaning**: The frame of reference for understanding the memories
- **Boundaries**: Where these memories apply and where they don't

### No Floating Memories

```python
# ❌ IMPOSSIBLE - Memory without context
{
  "entity_name": "customer_service_procedure",
  "entity_type": "procedure"
}

# ✅ REQUIRED - Memory anchored in context
{
  "entity_name": "customer_service_procedure",
  "entity_type": "procedure",
  "actor_type": "synth_class",    # THE CONTEXT
  "actor_id": "15"                 # SPECIFIC INSTANCE
}
```

## The Four Contextual Realms

### Visual Architecture

```
                    CLIENT REALM
         (Organizational Policies & Overrides)
                        |
                   [PRECEDENCE]
                        |
                        v
    SYNTH_CLASS <--- SYNTH ---> SKILL_MODULE
   (Role Identity)  (Nexus)   (Tool Knowledge)
        ^                           ^
        |                           |
    [INHERITS]                 [SUBSCRIBES]
```

### 1. CLIENT Realm - The Organization

**Purpose**: Defines company-wide policies, compliance requirements, and organizational overrides that apply to ALL synths within the organization.

**What Belongs Here**:
- Company policies and procedures
- Compliance requirements (GDPR, HIPAA, etc.)
- Brand guidelines and voice
- Business rules and constraints
- Organizational KPIs and metrics
- Legal and ethical boundaries

**Example Entities**:
```python
# Vervelyn Publishing CLIENT realm
{
  "actor_type": "client",
  "actor_id": "1d1c2154-242b-4f49-9ca8-e57129ddc823",  # Vervelyn's UUID
  "entities": [
    {
      "name": "synth_disclosure_policy",
      "type": "policy",
      "observations": [
        "Must identify as AI within 5 seconds",
        "Applies to all communication formats",
        "Legal requirement in all jurisdictions"
      ]
    },
    {
      "name": "content_compliance_rules",
      "type": "compliance",
      "observations": [
        "No medical advice permitted",
        "No financial guarantees",
        "No legal counsel"
      ]
    }
  ]
}
```

**Key Characteristics**:
- Highest precedence - overrides all other realms
- Applies to every synth in the organization
- Cannot be overridden by individual synths
- Typically managed by legal/compliance teams

### 2. SYNTH_CLASS Realm - Professional Identity

**Purpose**: Contains the core knowledge that defines WHO a synth is professionally. This is their fundamental expertise and identity.

**What Belongs Here**:
- Professional procedures and workflows
- Domain expertise and knowledge
- Role-specific best practices
- Professional standards
- Core competencies
- Identity-defining skills

**Example Entities**:
```python
# Blog Author (Class 24) SYNTH_CLASS realm
{
  "actor_type": "synth_class",
  "actor_id": "24",
  "entities": [
    {
      "name": "blog_writing_sop_v4",
      "type": "procedure",
      "observations": [
        "Phase 1: Research and topic analysis",
        "Phase 2: Content creation with hooks",
        "Phase 3: SEO optimization",
        "Phase 4: Quality assurance"
      ]
    },
    {
      "name": "content_expertise",
      "type": "knowledge_base",
      "observations": [
        "Long-form content strategies",
        "Audience engagement techniques",
        "Content marketing principles"
      ]
    }
  ]
}
```

**Key Characteristics**:
- Defines the synth's professional identity
- Shared by all synths of the same class
- Cannot be removed (core to who they are)
- Inherited automatically by synths

### 3. SKILL_MODULE Realm - Tool Capabilities

**Purpose**: Contains complete knowledge of specific tools, platforms, and systems that synths can use. These are swappable based on client needs.

**What Belongs Here**:
- Tool-specific knowledge and procedures
- API references and integration guides
- Platform-specific workflows
- Technical specifications
- Tool best practices
- Feature documentation

**Example Entities**:
```python
# Microsoft 365 Suite SKILL_MODULE realm
{
  "actor_type": "skill_module",
  "actor_id": "microsoft_365_suite",
  "entities": [
    {
      "name": "excel_advanced_formulas",
      "type": "tool_knowledge",
      "observations": [
        "VLOOKUP and XLOOKUP patterns",
        "Pivot table best practices",
        "Power Query transformations"
      ]
    },
    {
      "name": "teams_collaboration",
      "type": "workflow",
      "observations": [
        "Channel organization strategies",
        "Meeting scheduling protocols",
        "File sharing best practices"
      ]
    }
  ]
}
```

**Key Characteristics**:
- Swappable based on client tools
- Subscription-based access
- Complete tool knowledge (not tiered)
- Can be mixed and matched

### 4. SYNTH Realm - Individual Experience

**Purpose**: Contains personal learning, optimizations, and experiences unique to an individual synth instance.

**What Belongs Here**:
- Personal performance insights
- Client-specific preferences
- Individual optimizations
- Task execution history
- Learned patterns
- Personal adjustments

**Example Entities**:
```python
# Individual Blog Author Synth realm
{
  "actor_type": "synth",
  "actor_id": "b9af0667-5c92-4892-a7c5-947ed0cab0db",
  "entities": [
    {
      "name": "tech_audience_insights",
      "type": "learned_pattern",
      "observations": [
        "Questions in titles: +23% engagement",
        "Optimal post length: 1,800 words",
        "Best posting time: Tuesday 10 AM EST"
      ]
    },
    {
      "name": "client_preferences",
      "type": "preference",
      "observations": [
        "CEO prefers bullet points",
        "Marketing wants more visuals",
        "Legal requires disclaimer placement"
      ]
    }
  ]
}
```

**Key Characteristics**:
- Unique to individual synth
- Accumulated through experience
- Can override class defaults
- Represents personal growth

## The Synth as Nexus: How Realms Connect

### The Central Integration Point

The SYNTH is not just another realm - it's the **nexus** where all contexts converge:

```python
class Synth:
    def __init__(self, synth_id, class_id, client_id):
        self.id = synth_id
        self.class_id = class_id  # Inherits from
        self.client_id = client_id  # Respects policies
        self.skill_modules = []  # Subscribes to
        self.personal_memories = []  # Accumulates
    
    def get_applicable_memories(self, query):
        memories = []
        
        # 1. Personal experiences (SYNTH realm)
        memories.extend(self.search_personal(query))
        
        # 2. Professional identity (SYNTH_CLASS realm)
        memories.extend(self.inherit_from_class(query))
        
        # 3. Tool capabilities (SKILL_MODULE realm)
        for module in self.skill_modules:
            memories.extend(self.search_module(module, query))
        
        # 4. Organizational policies (CLIENT realm)
        memories.extend(self.get_client_policies(query))
        
        # Apply precedence: CLIENT > SYNTH > SYNTH_CLASS > SKILL_MODULE
        return self.apply_precedence(memories)
```

### Inheritance vs Subscription

**Inheritance (SYNTH ← SYNTH_CLASS)**:
- Automatic and permanent
- Defines core identity
- Cannot be removed
- All synths of a class inherit

**Subscription (SYNTH → SKILL_MODULE)**:
- Optional and flexible
- Based on client needs
- Can be added/removed
- Selective access

### Precedence Through Realms

When memories conflict, precedence is applied:

```python
def apply_precedence(memories):
    """
    Precedence order:
    1. CLIENT (highest) - Organizational overrides
    2. SYNTH - Personal adjustments
    3. SYNTH_CLASS - Professional defaults
    4. SKILL_MODULE (lowest) - Tool suggestions
    """
    precedence = {
        'client': 1,
        'synth': 2,
        'synth_class': 3,
        'skill_module': 4
    }
    
    # Group by entity name
    grouped = {}
    for memory in memories:
        key = memory['entity_name']
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(memory)
    
    # Keep highest precedence version
    final = []
    for entity_name, versions in grouped.items():
        highest = min(versions, key=lambda m: precedence[m['actor_type']])
        final.append(highest)
    
    return final
```

## Realm Boundaries and Interactions

### What Can Cross Boundaries

1. **References** - Entities can reference across realms
2. **Inheritance** - Synths inherit from their class
3. **Subscriptions** - Synths subscribe to modules
4. **Precedence** - Higher realms override lower

### What Cannot Cross Boundaries

1. **Direct Access** - Synth A cannot access Synth B's memories
2. **Class Mixing** - Blog Author cannot access CFO procedures
3. **Unauthorized Modules** - Must subscribe to access
4. **Client Isolation** - Company A cannot see Company B

### Example: Cross-Realm Interaction

```python
# Blog post creation showing realm interaction

# 1. CLIENT realm provides constraint
client_policy = {
    "realm": "CLIENT",
    "rule": "All content must include AI disclosure"
}

# 2. SYNTH_CLASS provides procedure
class_procedure = {
    "realm": "SYNTH_CLASS",
    "procedure": "Use 4-phase blog writing process"
}

# 3. SKILL_MODULE provides tool knowledge
wordpress_knowledge = {
    "realm": "SKILL_MODULE",
    "tool": "Use Yoast SEO plugin for optimization"
}

# 4. SYNTH applies personal learning
personal_insight = {
    "realm": "SYNTH",
    "learning": "Tech audience prefers question headlines"
}

# Final blog post incorporates all realms
blog_post = create_blog(
    must_include=client_policy,      # Mandatory
    follow_process=class_procedure,  # Professional standard
    use_tools=wordpress_knowledge,   # If subscribed
    optimize_with=personal_insight   # Personal touch
)
```

## Design Patterns for Realm-Aware Systems

### 1. Context-First Design

Always determine context before creating entities:

```python
def create_memory_entity(entity_data):
    # First question: Which realm?
    realm = determine_realm(entity_data)
    
    if realm == "CLIENT":
        # Company-wide impact
        validate_authority(user, "compliance_team")
        actor_type = "client"
        actor_id = company_id
        
    elif realm == "SYNTH_CLASS":
        # Role definition
        validate_authority(user, "class_designer")
        actor_type = "synth_class"
        actor_id = class_id
        
    elif realm == "SKILL_MODULE":
        # Tool knowledge
        validate_authority(user, "tool_expert")
        actor_type = "skill_module"
        actor_id = module_name
        
    elif realm == "SYNTH":
        # Individual learning
        actor_type = "synth"
        actor_id = synth_id
    
    return create_entity(actor_type, actor_id, entity_data)
```

### 2. Realm-Appropriate Validation

Different realms have different requirements:

```python
def validate_entity_for_realm(entity, realm):
    if realm == "CLIENT":
        # Strict validation for policies
        required = ["effective_date", "compliance_review", "legal_approval"]
        validate_fields(entity, required)
        
    elif realm == "SYNTH_CLASS":
        # Professional standards
        required = ["version", "peer_review", "test_coverage"]
        validate_fields(entity, required)
        
    elif realm == "SKILL_MODULE":
        # Technical accuracy
        required = ["tool_version", "api_compatibility", "documentation"]
        validate_fields(entity, required)
        
    elif realm == "SYNTH":
        # Learning validation
        required = ["confidence_score", "sample_size", "timestamp"]
        validate_fields(entity, required)
```

### 3. Realm Traversal Patterns

Common patterns for accessing memories across realms:

```python
class RealmTraverser:
    def get_complete_context(self, synth_id, topic):
        """Get all relevant memories across realms"""
        
        # Start with synth's personal context
        synth_context = self.get_synth_memories(synth_id, topic)
        
        # Expand to inherited class knowledge
        class_context = self.get_class_memories(
            synth_context.class_id, topic
        )
        
        # Include subscribed modules
        module_contexts = []
        for module_id in synth_context.subscribed_modules:
            module_contexts.append(
                self.get_module_memories(module_id, topic)
            )
        
        # Apply client overrides
        client_context = self.get_client_policies(
            synth_context.client_id, topic
        )
        
        # Merge with precedence
        return self.merge_contexts(
            client_context,    # Highest
            synth_context,     # Personal
            class_context,     # Professional
            module_contexts    # Tools
        )
```

## Common Patterns and Anti-Patterns

### ✅ Good Patterns

1. **Realm-Appropriate Storage**
   ```python
   # Company policy in CLIENT realm
   create_memory("ai_ethics_policy", realm="CLIENT")
   
   # Professional knowledge in SYNTH_CLASS
   create_memory("accounting_principles", realm="SYNTH_CLASS")
   
   # Tool guide in SKILL_MODULE  
   create_memory("excel_macros", realm="SKILL_MODULE")
   
   # Personal insight in SYNTH
   create_memory("client_meeting_notes", realm="SYNTH")
   ```

2. **Respecting Boundaries**
   ```python
   # Synth can reference but not modify class memories
   reference = create_reference(
       from_realm="SYNTH",
       to_realm="SYNTH_CLASS",
       relationship="enhances"
   )
   ```

3. **Proper Inheritance**
   ```python
   # All blog authors get base knowledge
   class BlogAuthorSynth(Synth):
       def __init__(self):
           super().__init__(class_id="24")
           # Automatically inherits all class 24 memories
   ```

### ❌ Anti-Patterns

1. **Wrong Realm Storage**
   ```python
   # Individual preference in SYNTH_CLASS (wrong!)
   create_memory(
       "john_prefers_morning_meetings",
       realm="SYNTH_CLASS"  # Should be SYNTH
   )
   ```

2. **Bypassing Precedence**
   ```python
   # Trying to override client policy at synth level
   # This won't work - client always wins
   synth.override_policy("no_medical_advice", "allow_general_health")
   ```

3. **Cross-Contamination**
   ```python
   # Mixing realms in one entity (wrong!)
   entity = {
       "name": "mixed_memory",
       "synth_data": {...},      # Personal
       "class_procedure": {...},  # Professional
       "client_policy": {...}     # Organizational
   }
   ```

## Advanced Realm Concepts

### Realm Evolution

Memories can influence realm evolution:

1. **Bottom-Up Learning**
   - SYNTH discovers pattern
   - Pattern validated across multiple synths
   - Promoted to SYNTH_CLASS best practice
   - May become CLIENT standard

2. **Top-Down Mandates**
   - CLIENT sets new policy
   - SYNTH_CLASS updates procedures
   - SKILL_MODULE adds compliance features
   - SYNTH adjusts behavior

### Realm Conflicts and Resolution

When realms conflict:

```python
class ConflictResolver:
    def resolve(self, conflicts):
        # 1. CLIENT always wins
        if has_client_mandate(conflicts):
            return apply_client_override(conflicts)
        
        # 2. Personal experience can override class defaults
        if has_strong_personal_evidence(conflicts):
            return apply_personal_override(conflicts)
        
        # 3. Class knowledge overrides module suggestions
        if has_class_standard(conflicts):
            return apply_class_standard(conflicts)
        
        # 4. Module provides baseline
        return apply_module_default(conflicts)
```

### Realm Migrations

Moving memories between realms:

```python
async def promote_to_class_knowledge(synth_memory):
    """Promote successful pattern to class level"""
    
    # Validate pattern success
    if synth_memory.success_rate < 0.90:
        raise ValueError("Pattern not successful enough")
    
    # Check pattern applies broadly
    if synth_memory.sample_size < 100:
        raise ValueError("Insufficient evidence")
    
    # Create class-level version
    class_memory = transform_to_class_pattern(synth_memory)
    
    # Store in SYNTH_CLASS realm
    await create_memory(
        realm="SYNTH_CLASS",
        entity=class_memory,
        source=f"Promoted from synth {synth_memory.synth_id}"
    )
```

## Summary

The four contextual realms provide:

1. **Clear Boundaries** - Every memory knows where it belongs
2. **Proper Precedence** - CLIENT > SYNTH > SYNTH_CLASS > SKILL_MODULE
3. **Flexible Composition** - Synths combine all realms effectively
4. **Controlled Evolution** - Memories can influence realm development
5. **Isolated Security** - Realms enforce access boundaries

By understanding that every memory MUST exist within a context, and that the Synth serves as the nexus where all contexts converge, you can build sophisticated knowledge systems that respect organizational boundaries while enabling individual growth and flexibility.