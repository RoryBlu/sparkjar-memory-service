# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

#!/usr/bin/env python3
"""
Test script for skill module context functionality in Memory Service.

This script demonstrates:
1. Creating memories as a skill module
2. Synth creating memories in skill module context
3. Hierarchical memory search including skill modules
"""

import asyncio
import httpx
import json
from uuid import UUID
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"  # Internal API for testing
CLIENT_ID = "123e4567-e89b-12d3-a456-426614174000"  # Example client ID
SYNTH_ID = "223e4567-e89b-12d3-a456-426614174001"  # Example synth ID
SKILL_MODULE_ID = "323e4567-e89b-12d3-a456-426614174002"  # Example skill module ID

async def test_create_skill_module_memories():
    """Test creating memories directly as a skill module."""
    print("\n1. Testing skill module creating its own memories...")
    
    async with httpx.AsyncClient() as client:
        # Create memories as skill module
        request_data = {
            # "client_id" removed - use actor_id when actor_type="client"
            "actor_type": "skill_module",
            "actor_id": SKILL_MODULE_ID,
            "entities": [
                {
                    "entity_name": "odoo.res.partner",
                    "entity_type": "model",
                    "observations": [
                        {
                            "type": "field_definition",
                            "content": "name: required char field",
                            "metadata": {"field_type": "char", "required": True}
                        },
                        {
                            "type": "field_definition", 
                            "content": "email: optional char field",
                            "metadata": {"field_type": "char", "required": False}
                        }
                    ],
                    "metadata": {
                        "module": "base",
                        "model_type": "transient"
                    }
                }
            ]
        }
        
        response = await client.post(f"{BASE_URL}/entities", json=request_data)
        
        if response.status_code == 200:
            print("✓ Successfully created skill module memories")
            print(f"  Created entities: {len(response.json())}")
        else:
            print(f"✗ Failed to create skill module memories: {response.status_code}")
            print(f"  Error: {response.text}")

async def test_synth_upsert_with_skill_module_context():
    """Test synth creating/updating memories in skill module context."""
    print("\n2. Testing synth upserting memories in skill module context...")
    
    async with httpx.AsyncClient() as client:
        # Upsert memories with skill module context
        request_data = {
            # "client_id" removed - use actor_id when actor_type="client"
            "actor_type": "synth",
            "actor_id": SYNTH_ID,
            "entities": [
                {
                    "entity_name": "sale.order.workflow",
                    "entity_type": "procedure",
                    "observations": [
                        {
                            "type": "step",
                            "content": "1. Create quotation with customer",
                            "metadata": {"step_number": 1}
                        },
                        {
                            "type": "step",
                            "content": "2. Add products to order lines",
                            "metadata": {"step_number": 2}
                        },
                        {
                            "type": "step",
                            "content": "3. Confirm order to generate invoice",
                            "metadata": {"step_number": 3}
                        }
                    ],
                    "metadata": {
                        "workflow_type": "sales",
                        "module": "sale"
                    }
                }
            ]
        }
        
        # Add skill_module_id as query parameter
        url = f"{BASE_URL}/entities/upsert?skill_module_id={SKILL_MODULE_ID}"
        response = await client.post(url, json=request_data)
        
        if response.status_code == 200:
            print("✓ Successfully upserted memories in skill module context")
            entities = response.json()
            for entity in entities:
                print(f"  - {entity['entityName']} ({entity['entityType']})")
        else:
            print(f"✗ Failed to upsert with skill module context: {response.status_code}")
            print(f"  Error: {response.text}")

async def test_hierarchical_search():
    """Test searching memories across hierarchical contexts."""
    print("\n3. Testing hierarchical memory search...")
    
    async with httpx.AsyncClient() as client:
        # Search as synth (should include skill module memories)
        request_data = {
            # "client_id" removed - use actor_id when actor_type="client"
            "actor_type": "synth", 
            "actor_id": SYNTH_ID,
            "query": "odoo partner model fields",
            "limit": 10
        }
        
        response = await client.post(f"{BASE_URL}/search", json=request_data)
        
        if response.status_code == 200:
            results = response.json()
            print(f"✓ Search returned {len(results)} results")
            
            # Group results by access context
            by_context = {}
            for result in results:
                context = result.get('access_context', 'unknown')
                if context not in by_context:
                    by_context[context] = []
                by_context[context].append(result)
            
            # Display results grouped by context
            for context, items in by_context.items():
                print(f"\n  From {context}:")
                for item in items[:2]:  # Show first 2 from each context
                    print(f"    - {item['entityName']} (similarity: {item.get('similarity', 0):.3f})")
        else:
            print(f"✗ Search failed: {response.status_code}")
            print(f"  Error: {response.text}")

async def test_validation_errors():
    """Test validation error cases."""
    print("\n4. Testing validation error cases...")
    
    async with httpx.AsyncClient() as client:
        # Test 1: Non-synth trying to use skill_module_id
        print("\n  a) Testing non-synth using skill_module_id...")
        request_data = {
            # "client_id" removed - use actor_id when actor_type="client"
            "actor_type": "human",
            "actor_id": "423e4567-e89b-12d3-a456-426614174003",
            "entities": [{"entity_name": "test", "entity_type": "test", "observations": []}]
        }
        
        url = f"{BASE_URL}/entities/upsert?skill_module_id={SKILL_MODULE_ID}"
        response = await client.post(url, json=request_data)
        
        if response.status_code == 400:
            error = response.json()
            print(f"    ✓ Correctly rejected: {error.get('detail', {}).get('message', 'Unknown error')}")
        else:
            print(f"    ✗ Should have failed but got: {response.status_code}")
        
        # Test 2: Invalid skill_module_id
        print("\n  b) Testing invalid skill_module_id...")
        request_data["actor_type"] = "synth"
        request_data["actor_id"] = SYNTH_ID
        
        url = f"{BASE_URL}/entities/upsert?skill_module_id=999e4567-e89b-12d3-a456-426614174999"
        response = await client.post(url, json=request_data)
        
        if response.status_code == 400:
            error = response.json()
            print(f"    ✓ Correctly rejected: {error.get('detail', {}).get('message', 'Unknown error')}")
        else:
            print(f"    ✗ Should have failed but got: {response.status_code}")

async def main():
    """Run all tests."""
    print("=" * 60)
    print("Memory Service Skill Module Context Tests")
    print("=" * 60)
    
    try:
        # Test each feature
        await test_create_skill_module_memories()
        await test_synth_upsert_with_skill_module_context()
        await test_hierarchical_search()
        await test_validation_errors()
        
        print("\n" + "=" * 60)
        print("Tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())