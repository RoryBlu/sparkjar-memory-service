# Memory Access Patterns Guide for Crew Developers

## Overview

This guide explains how CrewAI crews should interact with the SparkJAR Memory System, which implements a sophisticated 4-realm contextual architecture. Crews access memories through the Synth nexus, which inherits from its class, subscribes to skill modules, and respects client precedence.

## Key Concepts

### The Four Contextual Realms

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

### Understanding Memory Flow

When a synth accesses memories:
1. **Personal experiences** from SYNTH realm
2. **Inherits professional knowledge** from SYNTH_CLASS realm
3. **Subscribes to tool knowledge** from SKILL_MODULE realm
4. **Respects organizational policies** from CLIENT realm

## Common Access Patterns

### 1. Complete Entity Creation with Relationships

Crews must create complete entities with all required components:

```python
async def store_learned_pattern(self):
    """Store a complete learned pattern with relationships"""
    
    # Create the main entity with all requirements
    entity_response = await self.memory_client.create_complete_entity(
        actor_type="synth",
        actor_id=self.synth_id,
        entity={
            "name": "tech_blog_optimization_v2",
            "type": "learned_pattern",
            "metadata": {
                "confidence": 0.92,
                "sample_size": 147,
                "domain": "technology",
                "validated": True,
                "last_updated": datetime.utcnow().isoformat()
            }
        },
        observations=[
            {
                "type": "pattern_discovery",
                "value": {
                    "pattern": "Question headlines increase engagement",
                    "impact": "+23% CTR",
                    "conditions": {
                        "audience": "technical professionals",
                        "platform": "company blog"
                    }
                },
                "source": "A/B Testing Framework",
                "confidence": 0.92
            },
            {
                "type": "implementation_result",
                "value": {
                    "before_ctr": 0.032,
                    "after_ctr": 0.041,
                    "improvement": "28.1%",
                    "statistical_significance": 0.98
                },
                "source": "Analytics Platform",
                "timestamp": datetime.utcnow().isoformat()
            }
        ],
        relationships=[
            {
                "type": "enhances",
                "to_entity": "blog_writing_sop_v4",
                "to_realm": {"actor_type": "synth_class", "actor_id": "24"},
                "metadata": {"applicable_to": "technical content"}
            },
            {
                "type": "validated_by",
                "from_entity": "content_performance_metrics",
                "from_realm": {"actor_type": "synth_class", "actor_id": "24"}
            }
        ]
    )
```

### 2. Accessing Memories Across Realms

Always search across all relevant realms:

```python
async def get_content_guidelines(self):
    """Get guidelines with full realm awareness"""
    
    # Search across all realms
    results = await self.memory_client.search_memories(
        actor_type="synth",
        actor_id=self.synth_id,
        query="content writing guidelines procedures",
        realms={
            "include_own": True,           # Personal optimizations
            "include_class": True,         # Professional procedures
            "include_skills": self.subscribed_modules,  # Tool knowledge
            "include_client": True         # Organizational policies
        },
        traverse_relationships=True,       # Follow connections
        max_depth=2                       # How deep to traverse
    )
    
    # Apply precedence (CLIENT > SYNTH > SYNTH_CLASS > SKILL_MODULE)
    guidelines = self._apply_realm_precedence(results)
    
    return guidelines
```

### 3. Checking Client Overrides

Always respect organizational policies:

```python
async def validate_content_compliance(self, content):
    """Ensure content meets client policies"""
    
    # Get client policies that might override defaults
    policies = await self.memory_client.get_realm_memories(
        actor_type="client",
        actor_id=self.client_id,
        entity_type="policy",
        include_relationships=True
    )
    
    # Check for override relationships
    for policy in policies:
        # Find what this policy overrides
        overrides = await self.memory_client.get_relationships(
            from_entity_id=policy.id,
            relationship_type="overrides"
        )
        
        for override in overrides:
            if override.to_entity in self.active_procedures:
                # Client policy takes precedence
                self.apply_policy_override(policy, override.metadata)
    
    # Validate content against all active policies
    return self.compliance_checker.validate(content, policies)
```

### 4. Skill Module Subscription Pattern

Access tool knowledge through subscriptions:

```python
async def initialize_tool_knowledge(self):
    """Load knowledge from subscribed skill modules"""
    
    # Get synth's skill subscriptions
    subscriptions = await self.memory_client.get_skill_subscriptions(
        synth_id=self.synth_id
    )
    
    tool_knowledge = {}
    
    for skill_module in subscriptions:
        # Load each module's knowledge
        module_memories = await self.memory_client.get_realm_memories(
            actor_type="skill_module",
            actor_id=skill_module.id,
            include_relationships=True,
            include_observations=True
        )
        
        tool_knowledge[skill_module.name] = module_memories
        
        # Check for tool-specific procedures
        if skill_module.name == "microsoft_365_suite":
            self.excel_knowledge = self._extract_excel_knowledge(module_memories)
            self.word_templates = self._extract_word_templates(module_memories)
    
    return tool_knowledge
```

### 5. Creating Knowledge Graphs

Build interconnected knowledge:

```python
async def create_workflow_with_dependencies(self, workflow_def):
    """Create a complete workflow with all dependencies"""
    
    # Start transaction for atomic creation
    async with self.memory_client.transaction() as tx:
        
        # 1. Create main workflow entity
        workflow = await tx.create_entity(
            actor_type="synth_class",
            actor_id=self.synth_class_id,
            entity={
                "name": f"{workflow_def.name}_workflow_v1",
                "type": "procedure",
                "metadata": {
                    "version": "1.0",
                    "stages": len(workflow_def.stages),
                    "automation_level": workflow_def.automation_level,
                    "approved_by": "Process Team",
                    "category": workflow_def.category
                }
            }
        )
        
        # 2. Create stage entities with relationships
        stage_entities = []
        for i, stage in enumerate(workflow_def.stages):
            stage_entity = await tx.create_entity(
                actor_type="synth_class",
                actor_id=self.synth_class_id,
                entity={
                    "name": f"{workflow.name}_stage_{i+1}",
                    "type": "workflow_stage",
                    "metadata": {
                        "sequence": i + 1,
                        "duration_estimate": stage.duration,
                        "required_tools": stage.tools
                    }
                }
            )
            stage_entities.append(stage_entity)
            
            # Create relationships
            await tx.create_relationship({
                "type": "contains",
                "from": workflow.id,
                "to": stage_entity.id,
                "metadata": {"sequence": i + 1}
            })
            
            # Link to previous stage
            if i > 0:
                await tx.create_relationship({
                    "type": "follows",
                    "from": stage_entity.id,
                    "to": stage_entities[i-1].id
                })
        
        # 3. Create validation checklist
        checklist = await tx.create_entity(
            actor_type="synth_class",
            actor_id=self.synth_class_id,
            entity={
                "name": f"{workflow.name}_validation",
                "type": "checklist",
                "metadata": {
                    "check_count": len(workflow_def.validations),
                    "criticality": "required"
                }
            }
        )
        
        # Link checklist to workflow
        await tx.create_relationship({
            "type": "validates",
            "from": checklist.id,
            "to": workflow.id,
            "metadata": {"frequency": "per_execution"}
        })
        
        # 4. Create metrics
        metrics = await tx.create_entity(
            actor_type="synth_class",
            actor_id=self.synth_class_id,
            entity={
                "name": f"{workflow.name}_metrics",
                "type": "metric",
                "metadata": {
                    "kpis": workflow_def.kpis,
                    "reporting_frequency": "daily"
                }
            }
        )
        
        await tx.create_relationship({
            "type": "measures",
            "from": metrics.id,
            "to": workflow.id
        })
        
        # Commit transaction
        await tx.commit()
    
    return workflow
```

### 6. Memory Consolidation Pattern

Handle statistical observations that should update in place:

```python
async def update_performance_metrics(self, metric_name, new_value):
    """Update metrics with consolidation"""
    
    # Find existing metric entity
    metric_entity = await self.memory_client.get_entity_by_name(
        actor_type="synth",
        actor_id=self.synth_id,
        entity_name=f"{metric_name}_metrics"
    )
    
    if not metric_entity:
        # Create new metric entity
        metric_entity = await self.create_metric_entity(metric_name)
    
    # Add observation with consolidation flag
    await self.memory_client.add_observation(
        entity_id=metric_entity.id,
        observation={
            "type": "performance_metric",
            "value": {
                "metric": metric_name,
                "value": new_value,
                "timestamp": datetime.utcnow().isoformat()
            },
            "source": "Performance Monitor",
            "metadata": {
                "consolidation_enabled": True,  # Will update, not append
                "consolidation_key": metric_name
            }
        }
    )
```

### 7. Hierarchical Knowledge Initialization

Load all accessible knowledge at startup:

```python
async def initialize_crew_knowledge(self):
    """Load complete knowledge graph for crew"""
    
    # 1. Get synth's realm memberships
    realm_info = await self.memory_client.get_synth_realms(self.synth_id)
    
    self.knowledge_graph = {
        "client": {},
        "class": {},
        "modules": {},
        "personal": {}
    }
    
    # 2. Load CLIENT realm (highest precedence)
    if realm_info.client_id:
        client_memories = await self.memory_client.get_realm_memories(
            actor_type="client",
            actor_id=realm_info.client_id,
            include_relationships=True
        )
        self.knowledge_graph["client"] = self._index_by_type(client_memories)
    
    # 3. Load SYNTH_CLASS realm (inherited)
    if realm_info.class_id:
        class_memories = await self.memory_client.get_realm_memories(
            actor_type="synth_class",
            actor_id=realm_info.class_id,
            include_relationships=True
        )
        self.knowledge_graph["class"] = self._index_by_type(class_memories)
    
    # 4. Load SKILL_MODULE realms (subscribed)
    for module_id in realm_info.subscribed_modules:
        module_memories = await self.memory_client.get_realm_memories(
            actor_type="skill_module",
            actor_id=module_id,
            include_relationships=True
        )
        self.knowledge_graph["modules"][module_id] = module_memories
    
    # 5. Load SYNTH realm (personal)
    personal_memories = await self.memory_client.get_realm_memories(
        actor_type="synth",
        actor_id=self.synth_id,
        include_relationships=True
    )
    self.knowledge_graph["personal"] = self._index_by_type(personal_memories)
    
    # 6. Build relationship index for fast traversal
    self.relationship_index = await self._build_relationship_index()
    
    logger.info(
        f"Initialized knowledge graph: "
        f"{len(self.knowledge_graph['client'])} client policies, "
        f"{len(self.knowledge_graph['class'])} class procedures, "
        f"{len(self.knowledge_graph['modules'])} skill modules, "
        f"{len(self.knowledge_graph['personal'])} personal memories"
    )
```

### 8. Relationship-Based Discovery

Find knowledge through relationships:

```python
async def discover_related_procedures(self, task_type):
    """Find all procedures related to a task type"""
    
    # Start with direct matches
    seed_procedures = await self.memory_client.search_memories(
        actor_type="synth",
        actor_id=self.synth_id,
        query=f"{task_type} procedure workflow",
        entity_type="procedure",
        include_all_realms=True
    )
    
    discovered = {}
    
    for procedure in seed_procedures:
        # Find what this procedure requires
        requirements = await self.memory_client.get_relationships(
            from_entity_id=procedure.id,
            relationship_type="requires"
        )
        
        # Find what validates this procedure
        validators = await self.memory_client.get_relationships(
            to_entity_id=procedure.id,
            relationship_type="validates"
        )
        
        # Find what this procedure enables
        enables = await self.memory_client.get_relationships(
            from_entity_id=procedure.id,
            relationship_type="enables"
        )
        
        discovered[procedure.name] = {
            "procedure": procedure,
            "requirements": [self._load_entity(r.to_entity_id) for r in requirements],
            "validators": [self._load_entity(v.from_entity_id) for v in validators],
            "enables": [self._load_entity(e.to_entity_id) for e in enables]
        }
    
    return discovered
```

## Best Practices

### 1. Always Create Complete Entities

```python
# ❌ Don't create incomplete entities
await create_entity({
    "name": "new_process",
    "type": "procedure"
})

# ✅ Do create complete entities with all requirements
await create_complete_entity({
    "name": "invoice_processing_v2",
    "type": "procedure",
    "metadata": {
        "version": "2.0",
        "phases": 3,
        "approver": "Finance Lead",
        "category": "financial"
    },
    "observations": [
        {"type": "phase_detail", "value": {...}},
        {"type": "performance_baseline", "value": {...}}
    ],
    "relationships": [
        {"type": "supersedes", "to": "invoice_processing_v1"},
        {"type": "requires", "to": "erp_access"},
        {"type": "validated_by", "from": "audit_checklist"}
    ]
})
```

### 2. Respect Realm Boundaries

```python
# ❌ Don't put memories in wrong realms
await create_memory(
    actor_type="synth_class",  # Wrong!
    entity_name="john_prefers_morning_calls"  # This is personal
)

# ✅ Do place memories in appropriate realms
await create_memory(
    actor_type="synth",  # Correct - personal preference
    entity_name="client_communication_preference"
)
```

### 3. Use Relationship Traversal

```python
# ❌ Don't search in isolation
results = await search_memories(query="blog writing")

# ✅ Do traverse relationships for complete knowledge
results = await search_memories(
    query="blog writing",
    traverse_relationships=True,
    relationship_types=["requires", "validates", "enhances"],
    max_depth=2
)
```

### 4. Apply Proper Precedence

```python
def apply_realm_precedence(self, memories):
    """Apply correct precedence: CLIENT > SYNTH > SYNTH_CLASS > SKILL_MODULE"""
    
    precedence_order = {
        'client': 1,
        'synth': 2, 
        'synth_class': 3,
        'skill_module': 4
    }
    
    # Group by entity name
    by_name = {}
    for memory in memories:
        name = memory['entity_name']
        if name not in by_name:
            by_name[name] = []
        by_name[name].append(memory)
    
    # Keep highest precedence version
    final_memories = []
    for name, versions in by_name.items():
        highest = min(versions, key=lambda m: precedence_order[m['actor_type']])
        final_memories.append(highest)
    
    return final_memories
```

### 5. Cache Frequently Used Knowledge

```python
class MemoryCachedCrew:
    def __init__(self):
        self._procedure_cache = {}
        self._policy_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_timestamps = {}
    
    async def get_procedure(self, procedure_name):
        cache_key = f"{self.synth_class_id}:{procedure_name}"
        
        # Check cache validity
        if (cache_key in self._procedure_cache and 
            time.time() - self._cache_timestamps.get(cache_key, 0) < self._cache_ttl):
            return self._procedure_cache[cache_key]
        
        # Load from memory service
        procedure = await self.memory_client.get_entity_by_name(
            actor_type="synth_class",
            actor_id=self.synth_class_id,
            entity_name=procedure_name,
            include_relationships=True,
            include_observations=True
        )
        
        # Cache for future use
        self._procedure_cache[cache_key] = procedure
        self._cache_timestamps[cache_key] = time.time()
        
        return procedure
```

### 6. Handle Missing Memories Gracefully

```python
async def get_writing_knowledge(self, topic):
    """Get knowledge with fallback strategy"""
    
    try:
        # Try to get from memory service
        memories = await self.memory_client.search_memories(
            actor_type="synth",
            actor_id=self.synth_id,
            query=topic,
            include_all_realms=True
        )
        
        if memories:
            return self.apply_realm_precedence(memories)
            
    except MemoryServiceError as e:
        logger.warning(f"Memory service error: {e}")
    
    # Fallback to embedded defaults
    return self.get_default_knowledge(topic)
```

## Integration with CrewAI Tools

### Custom Memory Tool for Crews

```python
from crewai_tools import BaseTool
from typing import Type, Dict, Any, List
from pydantic import BaseModel, Field

class MemorySearchInput(BaseModel):
    query: str = Field(description="What to search for")
    include_relationships: bool = Field(
        default=True, 
        description="Follow entity relationships"
    )
    max_results: int = Field(
        default=10,
        description="Maximum results to return"
    )

class HierarchicalMemoryTool(BaseTool):
    name: str = "search_knowledge"
    description: str = "Search across all memory realms with proper inheritance"
    args_schema: Type[BaseModel] = MemorySearchInput
    
    def __init__(self, memory_client, synth_id, **kwargs):
        super().__init__(**kwargs)
        self.memory_client = memory_client
        self.synth_id = synth_id
    
    def _run(self, query: str, include_relationships: bool = True, 
             max_results: int = 10) -> str:
        """Search memories with realm awareness"""
        
        # Search across all realms
        results = self.memory_client.search_memories(
            actor_type="synth",
            actor_id=self.synth_id,
            query=query,
            include_all_realms=True,
            traverse_relationships=include_relationships,
            limit=max_results
        )
        
        # Format for agent consumption
        return self._format_memory_results(results)
    
    def _format_memory_results(self, results: List[Dict[str, Any]]) -> str:
        """Format memories for agent understanding"""
        
        if not results:
            return "No relevant memories found."
        
        formatted = []
        for memory in results:
            realm = memory['actor_type'].upper()
            name = memory['entity_name']
            
            # Show key observations
            obs_summary = []
            for obs in memory.get('observations', [])[:3]:
                obs_summary.append(f"- {obs['type']}: {obs['value']}")
            
            formatted.append(
                f"[{realm}] {name}:\n" + 
                "\n".join(obs_summary)
            )
        
        return "\n\n".join(formatted)
```

### Memory-Aware Agent Configuration

```python
from crewai import Agent

# Create agent with memory access
knowledge_worker = Agent(
    role='Knowledge Worker',
    goal='Complete tasks using organizational knowledge',
    backstory="""You are an AI agent with access to rich organizational 
    knowledge including procedures, policies, and learned patterns.""",
    tools=[
        HierarchicalMemoryTool(
            memory_client=memory_client,
            synth_id=synth_id
        ),
        CreateMemoryTool(
            memory_client=memory_client,
            synth_id=synth_id
        )
    ],
    callbacks={
        'on_task_start': load_relevant_memories,
        'on_task_complete': save_task_learnings,
        'on_error': log_and_learn_from_error
    }
)
```

## Troubleshooting

### Common Issues

1. **Missing Inherited Memories**
   - Verify synth is properly associated with synth_class
   - Check that include_class=True in searches
   - Ensure synth_class has memories stored

2. **Client Override Not Applied**
   - Verify include_client=True in searches
   - Check precedence logic implementation
   - Ensure client memories exist for the organization

3. **Skill Module Not Accessible**
   - Verify synth is subscribed to the module
   - Check subscription is active
   - Ensure module memories exist

4. **Incomplete Entities**
   - Always include relationships (minimum 1)
   - Include observations (minimum 2)
   - Validate metadata against schema

5. **Performance Issues**
   - Implement caching for frequently accessed memories
   - Use batch operations when possible
   - Limit relationship traversal depth

## Summary

Effective memory access patterns:

1. **Create Complete Entities** - With relationships, observations, validated metadata
2. **Search Across Realms** - Always include relevant contexts
3. **Respect Precedence** - CLIENT > SYNTH > SYNTH_CLASS > SKILL_MODULE
4. **Traverse Relationships** - Discover knowledge through connections
5. **Cache Strategically** - Reduce redundant queries
6. **Handle Failures Gracefully** - Always have fallback strategies

By following these patterns, your crews will have access to the full power of the hierarchical memory system, combining organizational policies, professional knowledge, tool capabilities, and personal learning into intelligent behavior.