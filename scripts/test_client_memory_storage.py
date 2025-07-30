#!/usr/bin/env python3
"""
Test storing client-level memories with the new architecture.

MEMORY SERVICE ARCHITECTURE:
- When actor_type = "client", the actor_id IS the client ID
- Test case: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"
"""
import asyncio
import os
import json
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_client_memory_storage():
    """Test storing memories at the client level."""
    database_url = os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ No database URL found in environment")
        return
    
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Test case values
    test_actor_type = "client"
    test_actor_id = "1d1c2154-242b-4f49-9ca8-e57129ddc823"  # This IS the client ID
    
    print(f"\n🧪 Testing client memory storage with new architecture:")
    print(f"   actor_type: {test_actor_type}")
    print(f"   actor_id: {test_actor_id}")
    
    try:
        async with async_session() as session:
            # Create a test entity
            entity_id = str(uuid4())
            entity_name = f"test_policy_{int(datetime.now().timestamp())}"
            
            print(f"\n📝 Creating test entity: {entity_name}")
            
            # Insert entity
            await session.execute(text("""
                INSERT INTO memory_entities (
                    id, 
                    actor_type, 
                    actor_id, 
                    entity_name, 
                    entity_type, 
                    metadata, 
                    created_at
                )
                VALUES (
                    :id,
                    :actor_type,
                    :actor_id,
                    :entity_name,
                    :entity_type,
                    :metadata,
                    :created_at
                )
            """), {
                "id": entity_id,
                "actor_type": test_actor_type,
                "actor_id": test_actor_id,  # This is the client ID when actor_type="client"
                "entity_name": entity_name,
                "entity_type": "policy",
                "metadata": json.dumps({
                    "description": "Test policy for new architecture",
                    "version": "1.0",
                    "test": True
                }),
                "created_at": datetime.utcnow()
            })
            
            # Create a test observation
            observation_id = str(uuid4())
            
            await session.execute(text("""
                INSERT INTO memory_observations (
                    id,
                    entity_id,
                    observation_type,
                    observation_value,
                    source,
                    context,
                    created_at
                )
                VALUES (
                    :id,
                    :entity_id,
                    :observation_type,
                    :observation_value,
                    :source,
                    :context,
                    :created_at
                )
            """), {
                "id": observation_id,
                "entity_id": entity_id,
                "observation_type": "policy_rule",
                "observation_value": json.dumps({
                    "rule": "Test rule for client-level policy",
                    "description": "This tests the new architecture without client_id"
                }),
                "source": "test_script",
                "context": json.dumps({
                    "test": True,
                    "architecture": "new"
                }),
                "created_at": datetime.utcnow()
            })
            
            await session.commit()
            print("✅ Successfully created entity and observation!")
            
            # Verify the data was stored
            result = await session.execute(text("""
                SELECT 
                    e.entity_name,
                    e.entity_type,
                    e.metadata as entity_metadata,
                    COUNT(o.id) as observation_count
                FROM memory_entities e
                LEFT JOIN memory_observations o ON e.id = o.entity_id
                WHERE e.actor_type = :actor_type
                AND e.actor_id = :actor_id
                AND e.entity_name = :entity_name
                GROUP BY e.id, e.entity_name, e.entity_type, e.metadata
            """), {
                "actor_type": test_actor_type,
                "actor_id": test_actor_id,
                "entity_name": entity_name
            })
            
            verification = result.fetchone()
            if verification:
                print(f"\n✅ Verification successful:")
                print(f"   Entity: {verification.entity_name}")
                print(f"   Type: {verification.entity_type}")
                print(f"   Observations: {verification.observation_count}")
                if verification.entity_metadata:
                    # Check if it's already a dict (from JSONB) or needs parsing
                    if isinstance(verification.entity_metadata, dict):
                        metadata = verification.entity_metadata
                    else:
                        metadata = json.loads(verification.entity_metadata)
                    print(f"   Metadata: {json.dumps(metadata, indent=6)}")
            else:
                print("\n❌ Verification failed - data not found!")
            
            # Clean up test data
            print("\n🧹 Cleaning up test data...")
            await session.execute(text("""
                DELETE FROM memory_observations WHERE entity_id = :entity_id
            """), {"entity_id": entity_id})
            
            await session.execute(text("""
                DELETE FROM memory_entities WHERE id = :entity_id
            """), {"entity_id": entity_id})
            
            await session.commit()
            print("✅ Test data cleaned up")
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

async def test_hierarchical_query():
    """Test querying with hierarchical memory architecture."""
    database_url = os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL")
    if not database_url:
        return
    
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    print("\n\n🔍 Testing hierarchical memory query:")
    print("   This simulates how a synth would access memories from:")
    print("   1. Its own memories (synth level)")
    print("   2. Its template memories (synth_class level)")
    print("   3. Client policies (client level)")
    
    # Example synth querying memories
    synth_id = str(uuid4())
    synth_class_id = "24"  # Example synth class
    client_id = "1d1c2154-242b-4f49-9ca8-e57129ddc823"
    
    try:
        async with async_session() as session:
            # Query that would include all hierarchical levels
            result = await session.execute(text("""
                SELECT 
                    actor_type,
                    actor_id,
                    COUNT(*) as entity_count
                FROM memory_entities
                WHERE (
                    (actor_type = 'synth' AND actor_id = :synth_id) OR
                    (actor_type = 'synth_class' AND actor_id = :synth_class_id) OR
                    (actor_type = 'client' AND actor_id = :client_id)
                )
                GROUP BY actor_type, actor_id
                ORDER BY 
                    CASE actor_type
                        WHEN 'client' THEN 1
                        WHEN 'synth_class' THEN 2
                        WHEN 'synth' THEN 3
                    END
            """), {
                "synth_id": synth_id,
                "synth_class_id": synth_class_id,
                "client_id": client_id
            })
            
            levels = result.fetchall()
            
            if levels:
                print("\n📊 Memory hierarchy results:")
                for level in levels:
                    print(f"   {level.actor_type}: {level.entity_count} entities (actor_id: {level.actor_id})")
            else:
                print("\n   No memories found at any level")
                print("   This is expected if no data has been ingested yet")
                
    except Exception as e:
        print(f"\n❌ Error during hierarchical query: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("=" * 80)
    print("CLIENT MEMORY STORAGE TEST")
    print("=" * 80)
    print("\nTesting the new architecture without client_id field")
    
    asyncio.run(test_client_memory_storage())
    asyncio.run(test_hierarchical_query())