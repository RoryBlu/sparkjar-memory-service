#!/usr/bin/env python3
"""
Verify client memories using the new architecture without client_id field.

MEMORY SERVICE ARCHITECTURE:
- When actor_type = "client", the actor_id IS the client ID
- Test case: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"
"""
import asyncio
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def verify_client_memories():
    """Verify memories stored at the client level."""
    # Get database URL
    database_url = os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ No database URL found in environment")
        return
    
    # Create async engine
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Test case values
    test_actor_type = "client"
    test_actor_id = "1d1c2154-242b-4f49-9ca8-e57129ddc823"  # This IS the client ID
    
    print(f"\n🔍 Verifying memories for:")
    print(f"   actor_type: {test_actor_type}")
    print(f"   actor_id: {test_actor_id}")
    print(f"   (When actor_type='client', actor_id contains the client ID)")
    
    try:
        async with async_session() as session:
            # Query for client-level entities
            result = await session.execute(text("""
                SELECT 
                    id,
                    entity_name,
                    entity_type,
                    metadata,
                    created_at
                FROM memory_entities
                WHERE actor_type = :actor_type 
                AND actor_id = :actor_id
                ORDER BY created_at DESC
                LIMIT 10
            """), {
                "actor_type": test_actor_type,
                "actor_id": test_actor_id
            })
            
            entities = result.fetchall()
            
            if entities:
                print(f"\n✅ Found {len(entities)} client-level entities:")
                for entity in entities:
                    print(f"\n   Entity: {entity.entity_name}")
                    print(f"   Type: {entity.entity_type}")
                    print(f"   Created: {entity.created_at}")
                    if entity.metadata:
                        metadata = json.loads(entity.metadata)
                        print(f"   Metadata: {json.dumps(metadata, indent=6)}")
                    
                    # Check for observations
                    obs_result = await session.execute(text("""
                        SELECT COUNT(*) as count
                        FROM memory_observations
                        WHERE entity_id = :entity_id
                    """), {"entity_id": entity.id})
                    
                    obs_count = obs_result.scalar()
                    print(f"   Observations: {obs_count}")
            else:
                print("\n⚠️  No client-level entities found")
                print("   This could mean:")
                print("   1. No policies have been ingested yet")
                print("   2. The actor_id doesn't match any stored data")
                print("   3. The memory service hasn't been used with this client ID")
            
            # Also check for any entities using the old client_id pattern
            print("\n🔍 Checking for any legacy client_id usage...")
            
            # Check memory_entities table structure
            table_info = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'memory_entities'
                AND column_name = 'client_id'
            """))
            
            if table_info.fetchone():
                print("⚠️  WARNING: client_id column still exists in memory_entities table!")
                print("   This should have been removed in migrations")
            else:
                print("✅ Good: client_id column has been removed from memory_entities")
            
            # Show example of how to store new client-level memory
            print("\n📝 Example: How to store client-level memory with new architecture:")
            print("""
    # Python example
    await memory_client.store_memory(
        actor_type="client",
        actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823",  # This IS the client ID
        entity_name="security_policy",
        entity_type="policy",
        observations=[{
            "type": "policy_rule",
            "value": {"rule": "Require 2FA for all users"},
            "source": "company_policy"
        }]
    )
    
    # HTTP API example
    POST /entities
    {
        "actor_type": "client",
        "actor_id": "1d1c2154-242b-4f49-9ca8-e57129ddc823",
        "entities": [{
            "name": "security_policy",
            "entity_type": "policy",
            "observations": [...]
        }]
    }
            """)
            
    except Exception as e:
        print(f"\n❌ Error querying database: {e}")
    finally:
        await engine.dispose()

async def show_all_client_actors():
    """Show all unique client actors in the system."""
    database_url = os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL")
    if not database_url:
        return
    
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    print("\n📊 All client actors in the system:")
    
    try:
        async with async_session() as session:
            result = await session.execute(text("""
                SELECT DISTINCT 
                    actor_id,
                    COUNT(*) as entity_count,
                    MIN(created_at) as first_created,
                    MAX(created_at) as last_created
                FROM memory_entities
                WHERE actor_type = 'client'
                GROUP BY actor_id
                ORDER BY last_created DESC
            """))
            
            clients = result.fetchall()
            
            if clients:
                print(f"\nFound {len(clients)} unique client actors:")
                for client in clients:
                    print(f"\n   Client ID: {client.actor_id}")
                    print(f"   Entities: {client.entity_count}")
                    print(f"   First activity: {client.first_created}")
                    print(f"   Last activity: {client.last_created}")
            else:
                print("\n   No client actors found in the system")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("=" * 80)
    print("MEMORY SERVICE CLIENT VERIFICATION")
    print("=" * 80)
    print("\nArchitecture Note:")
    print("- client_id field has been REMOVED")
    print("- When actor_type='client', actor_id contains the client ID")
    print("- This simplifies the API and removes redundancy")
    
    asyncio.run(verify_client_memories())
    asyncio.run(show_all_client_actors())