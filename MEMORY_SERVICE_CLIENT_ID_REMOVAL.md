# Memory Service Architecture Change: client_id Removal

## Overview

The `client_id` field has been removed from the memory service as it was redundant. When `actor_type = "client"`, the `actor_id` already contains the client ID.

## Architecture

### Before (Redundant):
```python
{
    "client_id": "1d1c2154-242b-4f49-9ca8-e57129ddc823",
    "actor_type": "client",
    "actor_id": "1d1c2154-242b-4f49-9ca8-e57129ddc823"  # Same as client_id!
}
```

### After (Simplified):
```python
{
    "actor_type": "client",
    "actor_id": "1d1c2154-242b-4f49-9ca8-e57129ddc823"  # This IS the client ID
}
```

## Test Case

For testing memory operations at the client level:

```python
# Test case for CLIENT-level memory operations
actor_type = "client"
actor_id = "1d1c2154-242b-4f49-9ca8-e57129ddc823"  # This is the client ID

# Example API call
await memory_manager.create_entities(
    actor_type="client",
    actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823",
    entities=[...]
)
```

## Actor Type Reference

The memory service supports these actor types:
- `"client"` - When storing client-level policies/knowledge (actor_id = client UUID)
- `"synth_class"` - When storing template knowledge (actor_id = synth_class ID)
- `"synth"` - When storing individual synth memories (actor_id = synth UUID)
- `"human"` - When storing human user memories (actor_id = user UUID)

## Migration Notes

All code has been updated to:
1. Remove `client_id` parameters from function signatures
2. Use `actor_id` when `actor_type="client"` to get the client ID
3. Update JWT tokens to not include redundant `client_id` field
4. Fix all tests to use the simplified structure

## Benefits

1. **Simpler API** - One less field to worry about
2. **No Redundancy** - No duplicate IDs in requests
3. **Clearer Logic** - actor_type determines how actor_id is interpreted
4. **Consistent Pattern** - All actor types follow same pattern