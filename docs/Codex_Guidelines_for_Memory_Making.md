# Codex Guidelines for Memory Making

## Overview

This document describes how to build the **Memory Maker Crew** for SparkJAR. The crew is responsible for extracting memories from conversation logs and events, mimicking how humans consolidate memories during sleep. The resulting memory artifacts must be immediately fetchable to provide context for other agents.

These guidelines complement the existing memory architecture. Refer to the [Memory System Master Guide](./MEMORY_SYSTEM_MASTER_GUIDE.md) and [Context Architecture](./context-architecture.md) for detailed background.

## 1. Foundations

- The SparkJAR system mirrors human memory consolidation. Important information is kept readily accessible while redundant data is merged or archived【F:docs/MEMORY_CONSOLIDATION_GUIDE.md†L5-L15】.
- Every memory entity **must** exist in a context defined by `actor_type` and `actor_id` to ensure clear ownership and boundaries【F:docs/context-architecture.md†L9-L23】【F:docs/context-architecture.md†L25-L40】.
- Sequential Thinking breaks down complex tasks into numbered thoughts and allows self‑correction over time【F:docs/sequential-thinking-functional-spec.md†L5-L12】.

## 2. Chain of Draft Prompting

Recent work on **Chain of Draft (CoD)** shows that concise intermediate reasoning can match Chain of Thought accuracy with far fewer tokens. CoD encourages drafting only the essential insights, reducing latency and cost【993661†L1-L29】.

Adopt CoD when the crew summarizes conversations or task outputs. Generate short drafts that capture the critical information needed for future recall.

## 3. Memory Maker Workflow

1. **Collect Inputs**
   - Conversation messages, system events and relevant metadata.
   - The associated `actor_type` and `actor_id` (e.g., `synth`, `synth_class`, `skill_module`, or `client`).
2. **Draft Key Points**
   - Use CoD to create a minimal set of bullet points or numbered thoughts capturing only the salient details.
   - Apply Sequential Thinking principles to break complex episodes into discrete steps if needed.
3. **Create Memory Entities**
   - Format each memory with required context fields and relationships. Follow the `create_memory_entities` pattern for internal API calls【F:docs/memory_implementation_instructions.md†L180-L198】.
   - Respect realm boundaries when choosing the `actor_type`. Example of correct and incorrect placement is shown in the Hierarchical Memory Guide【F:docs/hierarchical-memory-guide.md†L248-L259】 and in the Access Patterns Guide【F:docs/access-patterns.md†L486-L501】.
4. **Consolidate**
   - If the memory represents statistical or frequently updated information, enable consolidation so the data is merged over time instead of endlessly appending observations.
5. **Store and Index**
   - Persist the memory through the internal API. Ensure relationships are present so related knowledge is discoverable.
6. **Retrieve for Context**
   - Other crews can fetch these memories by context to reconstruct prior conversations or tasks quickly.

## 4. Best Practices

- **Keep It Simple** – Avoid unnecessary retries or over-engineering. Limit the number of reasoning loops; CoD summaries should be short and direct.
- **Accuracy First** – Validate metadata against schemas and confirm the memory accurately reflects the source conversation.
- **Leverage Hierarchy** – Use the four realms (CLIENT, SYNTH, SYNTH_CLASS, SKILL_MODULE) appropriately so that knowledge flows correctly through inheritance and subscriptions.
- **Minimal Drafts** – Prefer short bullet points or brief paragraphs generated via CoD instead of verbose narrative.

## 5. Example Outline

```python
async def memory_maker_pipeline(conversation, actor_type, actor_id):
    """Extract key points and store them as a memory"""
    # 1. Draft concise summary (CoD style)
    summary = cod_summarize(conversation)

    # 2. Build memory payload
    memory = {
        "actor_type": actor_type,
        "actor_id": actor_id,
        "entity_name": "conversation_summary",
        "observations": [{"type": "text", "value": summary}],
        "relationships": [],
    }

    # 3. Create entity via internal API
    return create_memory_entities([memory])
```

This skeleton illustrates the minimal structure. Expand it with additional fields (tags, relationships, or schema metadata) as required.

---

Adhering to these guidelines allows the Memory Maker Crew to efficiently transform raw chat data into actionable memories. By mimicking human sleep through consolidation and leveraging Chain of Draft summaries, the crew provides crisp context for downstream agents without wasting tokens or processing time.
