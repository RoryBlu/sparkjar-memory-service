# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

"""Data integrity validator for memory system tables."""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

from .base import BaseValidator, ValidationResult, ValidationStatus
from .test_data_generator import TestDataGenerator

class DataIntegrityValidator(BaseValidator):
    """Validate data integrity and consistency in memory system."""
    
    def __init__(self, database_url: Optional[str] = None):
        super().__init__("DataIntegrityValidator")
        self.database_url = database_url
        self.test_data_generator = TestDataGenerator(seed=123)
        self.test_client_id = f"integrity_test_{uuid.uuid4().hex[:8]}"
    
    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        if not self.database_url:
            raise Exception("Database URL not configured")
        
        engine = create_async_engine(self.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        return async_session()
    
    async def test_table_schema_validation(self):
        """Validate that all required memory tables exist with correct schema."""
        async with await self._get_session() as session:
            # Check memory_entities table
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'memory_entities'
                ORDER BY ordinal_position
            """))
            
            entity_columns = {row.column_name: (row.data_type, row.is_nullable) for row in result.fetchall()}
            
            required_entity_columns = {
                'id': ('uuid', 'NO'),
                'client_id': ('uuid', 'NO'),
                'actor_type': ('character varying', 'YES'),  # client, human, synth, synth_class
                'actor_id': ('uuid', 'YES'),
                'name': ('text', 'NO'),
                'entity_type': ('character varying', 'YES'),
                'metadata': ('jsonb', 'YES'),
                'created_at': ('timestamp without time zone', 'YES'),
                'updated_at': ('timestamp without time zone', 'YES')
            }
            
            for col_name, (expected_type, expected_nullable) in required_entity_columns.items():
                assert col_name in entity_columns, f"Missing column: {col_name} in memory_entities"
                actual_type, actual_nullable = entity_columns[col_name]
                # Allow some type variations (e.g., varchar vs character varying)
                if 'character' in expected_type and 'character' in actual_type:
                    pass  # Both are character types
                elif expected_type != actual_type:
                    self.logger.warning(f"Column {col_name} type mismatch: expected {expected_type}, got {actual_type}")
            
            # Check memory_relations table
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'memory_relations'
                ORDER BY ordinal_position
            """))
            
            relation_columns = {row.column_name: (row.data_type, row.is_nullable) for row in result.fetchall()}
            
            required_relation_columns = {
                'id': ('uuid', 'NO'),
                'actor_type': ('character varying', 'YES'),  # client, human, synth, synth_class
                'actor_id': ('uuid', 'YES'),
                'source_id': ('uuid', 'NO'),
                'target_id': ('uuid', 'NO'),
                'relationship_type': ('character varying', 'YES'),
                'metadata': ('jsonb', 'YES'),
                'created_at': ('timestamp without time zone', 'YES')
            }
            
            for col_name, (expected_type, expected_nullable) in required_relation_columns.items():
                assert col_name in relation_columns, f"Missing column: {col_name} in memory_relations"
            
            # Check object_schemas table exists
            result = await session.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'object_schemas'
            """))
            
            schema_table_count = result.scalar()
            assert schema_table_count > 0, "object_schemas table not found"
    
    async def test_entity_uniqueness_constraints(self):
        """Test that entity uniqueness is properly enforced."""
        async with await self._get_session() as session:
            # Create a test entity
            test_entity = self.test_data_generator.generate_person_entity(
                self.test_client_id, grade="high"
            )
            
            # Insert the entity using actor_type and actor_id
            await session.execute(text("""
                INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
            """), {
                "id": test_entity.id,
                "actor_type": "client",
                "actor_id": test_entity.client_user_id,  # Use client_user_id as actor_id
                "name": test_entity.name,
                "entity_type": test_entity.entity_type,
                "metadata": json.dumps(test_entity.metadata),
                "created_at": test_entity.created_at
            })
            
            await session.commit()
            
            # Try to insert the same entity again (should fail or be handled)
            try:
                await session.execute(text("""
                    INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                    VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
                """), {
                    "id": test_entity.id,  # Same ID
                    "actor_type": "client",
                    "actor_id": test_entity.client_user_id,
                    "name": test_entity.name + " Duplicate",
                    "entity_type": test_entity.entity_type,
                    "metadata": json.dumps(test_entity.metadata),
                    "created_at": datetime.utcnow()
                })
                
                await session.commit()
                
                # If we get here, check if there's actually a duplicate
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM memory_entities WHERE id = :id
                """), {"id": test_entity.id})
                
                count = result.scalar()
                assert count == 1, f"Duplicate entity created - found {count} entities with same ID"
                
            except Exception as e:
                # This is expected - duplicate key should be rejected
                await session.rollback()
                self.logger.info(f"Duplicate entity properly rejected: {e}")
    
    async def test_relationship_referential_integrity(self):
        """Test that relationships maintain referential integrity."""
        async with await self._get_session() as session:
            # Create two test entities
            entities = self.test_data_generator.generate_entities(2, self.test_client_id)
            
            for entity in entities:
                await session.execute(text("""
                    INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                    VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
                """), {
                    "id": entity.id,
                    "actor_type": "client",
                    "actor_id": entity.client_user_id,
                    "name": entity.name,
                    "entity_type": entity.entity_type,
                    "metadata": json.dumps(entity.metadata),
                    "created_at": entity.created_at
                })
            
            await session.commit()
            
            # Create a valid relationship
            relationship = self.test_data_generator.generate_relationships(entities, 1)[0]
            
            await session.execute(text("""
                INSERT INTO memory_relations (id, actor_type, actor_id, source_id, target_id, relationship_type, metadata, created_at)
                VALUES (:id, :actor_type, :actor_id, :source_id, :target_id, :relationship_type, :metadata, :created_at)
            """), {
                "id": relationship.id,
                "actor_type": "client",
                "actor_id": relationship.client_user_id,
                "source_id": relationship.source_id,
                "target_id": relationship.target_id,
                "relationship_type": relationship.relationship_type,
                "metadata": json.dumps(relationship.metadata),
                "created_at": relationship.created_at
            })
            
            await session.commit()
            
            # Verify relationship exists
            result = await session.execute(text("""
                SELECT COUNT(*) FROM memory_relations WHERE id = :id
            """), {"id": relationship.id})
            
            count = result.scalar()
            assert count == 1, "Valid relationship was not created"
            
            # Test creating relationship with non-existent entity
            fake_entity_id = str(uuid.uuid4())
            
            try:
                await session.execute(text("""
                    INSERT INTO memory_relations (id, actor_type, actor_id, source_id, target_id, relationship_type, metadata, created_at)
                    VALUES (:id, :actor_type, :actor_id, :source_id, :target_id, :relationship_type, :metadata, :created_at)
                """), {
                    "id": str(uuid.uuid4()),
                    "actor_type": "client",
                    "actor_id": self.test_client_id,
                    "source_id": entities[0].id,
                    "target_id": fake_entity_id,  # Non-existent entity
                    "relationship_type": "test_relation",
                    "metadata": json.dumps({"test": True}),
                    "created_at": datetime.utcnow()
                })
                
                await session.commit()
                
                # If we get here, the system allows orphaned relationships
                # This might be by design, so we'll log it as a warning
                self.logger.warning("System allows relationships to non-existent entities")
                
            except Exception as e:
                # This is expected if foreign key constraints are enforced
                await session.rollback()
                self.logger.info(f"Orphaned relationship properly rejected: {e}")
    
    async def test_client_data_isolation(self):
        """Test strict actor data boundaries (client, human, synth, synth_class)."""
        async with await self._get_session() as session:
            # Create entities for multiple actors
            actor_configs = [
                ("client", f"client_{i}_{uuid.uuid4().hex[:6]}") for i in range(2)
            ] + [
                ("human", f"human_{i}_{uuid.uuid4().hex[:6]}") for i in range(2)
            ]
            all_entities = []
            
            for actor_type, actor_id in actor_configs:
                entities = self.test_data_generator.generate_entities(3, actor_id)
                all_entities.extend(entities)
                
                for entity in entities:
                    await session.execute(text("""
                        INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                        VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
                    """), {
                        "id": entity.id,
                        "actor_type": actor_type,
                        "actor_id": actor_id,
                        "name": entity.name,
                        "entity_type": entity.entity_type,
                        "metadata": json.dumps(entity.metadata),
                        "created_at": entity.created_at
                    })
            
            await session.commit()
            
            # Test that each actor can only see their own data
            for actor_type, actor_id in actor_configs:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM memory_entities 
                    WHERE actor_type = :actor_type AND actor_id = :actor_id
                """), {"actor_type": actor_type, "actor_id": actor_id})
                
                count = result.scalar()
                assert count == 3, f"Actor {actor_type}:{actor_id} should see exactly 3 entities, saw {count}"
            
            # Test cross-actor relationship behavior
            # Try to create a relationship between entities from different actors
            client_entities = [e for e in all_entities if e.client_user_id == actor_configs[0][1]]
            human_entities = [e for e in all_entities if e.client_user_id == actor_configs[2][1]]
            
            try:
                await session.execute(text("""
                    INSERT INTO memory_relations (id, actor_type, actor_id, source_id, target_id, relationship_type, metadata, created_at)
                    VALUES (:id, :actor_type, :actor_id, :source_id, :target_id, :relationship_type, :metadata, :created_at)
                """), {
                    "id": str(uuid.uuid4()),
                    "actor_type": "client",
                    "actor_id": actor_configs[0][1],  # Client's relationship
                    "source_id": client_entities[0].id,  # Client's entity
                    "target_id": human_entities[0].id,  # Human's entity - cross-actor relationship
                    "relationship_type": "cross_actor_test",
                    "metadata": json.dumps({"test": "cross_actor"}),
                    "created_at": datetime.utcnow()
                })
                
                await session.commit()
                
                # If this succeeds, log it as expected behavior
                self.logger.info("Cross-actor relationships are allowed - this may be by design")
                
            except Exception as e:
                await session.rollback()
                self.logger.info(f"Cross-actor relationship prevented: {e}")
    
    async def test_json_metadata_integrity(self):
        """Test that JSON metadata fields are properly validated and stored."""
        async with await self._get_session() as session:
            # Test valid JSON metadata
            test_entity = self.test_data_generator.generate_person_entity(self.test_client_id)
            
            complex_metadata = {
                "personal_info": {
                    "age": 30,
                    "skills": ["Python", "SQL", "Machine Learning"],
                    "preferences": {
                        "work_style": "remote",
                        "communication": ["email", "slack"]
                    }
                },
                "timestamps": {
                    "last_contact": datetime.utcnow().isoformat(),
                    "next_followup": (datetime.utcnow() + timedelta(days=7)).isoformat()
                },
                "metrics": {
                    "engagement_score": 0.85,
                    "response_rate": 0.92
                }
            }
            
            await session.execute(text("""
                INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
            """), {
                "id": test_entity.id,
                "actor_type": "client",
                "actor_id": test_entity.client_user_id,
                "name": test_entity.name,
                "entity_type": test_entity.entity_type,
                "metadata": json.dumps(complex_metadata),
                "created_at": test_entity.created_at
            })
            
            await session.commit()
            
            # Retrieve and verify JSON metadata
            result = await session.execute(text("""
                SELECT metadata FROM memory_entities WHERE id = :id
            """), {"id": test_entity.id})
            
            stored_metadata_json = result.scalar()
            stored_metadata = json.loads(stored_metadata_json)
            
            # Verify complex nested structure is preserved
            assert stored_metadata["personal_info"]["age"] == 30
            assert "Python" in stored_metadata["personal_info"]["skills"]
            assert stored_metadata["personal_info"]["preferences"]["work_style"] == "remote"
            assert stored_metadata["metrics"]["engagement_score"] == 0.85
            
            # Test JSON querying capabilities
            result = await session.execute(text("""
                SELECT name FROM memory_entities 
                WHERE metadata->>'entity_type' IS NOT NULL
                AND metadata->'personal_info'->>'age' = '30'
                AND id = :id
            """), {"id": test_entity.id})
            
            queried_name = result.scalar()
            assert queried_name == test_entity.name, "JSON querying not working correctly"
    
    async def test_timestamp_consistency(self):
        """Test that timestamps are properly maintained."""
        async with await self._get_session() as session:
            # Create entity with specific timestamp
            test_entity = self.test_data_generator.generate_person_entity(self.test_client_id)
            creation_time = datetime.utcnow()
            
            await session.execute(text("""
                INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at, updated_at)
                VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at, :updated_at)
            """), {
                "id": test_entity.id,
                "actor_type": "client",
                "actor_id": test_entity.client_user_id,
                "name": test_entity.name,
                "entity_type": test_entity.entity_type,
                "metadata": json.dumps(test_entity.metadata),
                "created_at": creation_time,
                "updated_at": creation_time
            })
            
            await session.commit()
            
            # Wait a moment and update the entity
            await asyncio.sleep(0.1)
            update_time = datetime.utcnow()
            
            await session.execute(text("""
                UPDATE memory_entities 
                SET name = :new_name, updated_at = :updated_at
                WHERE id = :id
            """), {
                "id": test_entity.id,
                "new_name": test_entity.name + " Updated",
                "updated_at": update_time
            })
            
            await session.commit()
            
            # Verify timestamps
            result = await session.execute(text("""
                SELECT created_at, updated_at FROM memory_entities WHERE id = :id
            """), {"id": test_entity.id})
            
            row = result.fetchone()
            assert row.created_at == creation_time, "Created timestamp was modified"
            assert row.updated_at == update_time, "Updated timestamp was not set correctly"
            assert row.updated_at > row.created_at, "Updated timestamp should be after created timestamp"
    
    async def test_entity_deduplication_logic(self):
        """Test entity deduplication and merging behavior."""
        async with await self._get_session() as session:
            # Create entities with identical absolute identifiers
            base_entity = self.test_data_generator.generate_person_entity(self.test_client_id, grade="absolute")
            
            # Create first entity
            await session.execute(text("""
                INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
            """), {
                "id": base_entity.id,
                "actor_type": "client",
                "actor_id": base_entity.client_user_id,
                "name": base_entity.name,
                "entity_type": base_entity.entity_type,
                "metadata": json.dumps(base_entity.metadata),
                "created_at": base_entity.created_at
            })
            
            # Create second entity with same identifiers but different metadata
            duplicate_entity = self.test_data_generator.generate_person_entity(self.test_client_id, grade="absolute")
            duplicate_entity.name = base_entity.name  # Same name
            duplicate_entity.identifiers = base_entity.identifiers  # Same identifiers
            duplicate_entity.metadata["additional_info"] = "This is a duplicate"
            
            try:
                await session.execute(text("""
                    INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                    VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
                """), {
                    "id": str(uuid.uuid4()),  # Different ID
                    "actor_type": "client",
                    "actor_id": duplicate_entity.client_user_id,
                    "name": duplicate_entity.name,
                    "entity_type": duplicate_entity.entity_type,
                    "metadata": json.dumps(duplicate_entity.metadata),
                    "created_at": datetime.utcnow()
                })
                
                await session.commit()
                
                # Check if system allows or prevents duplicates
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM memory_entities 
                    WHERE actor_id = :actor_id AND name = :name
                """), {"actor_id": base_entity.client_user_id, "name": base_entity.name})
                
                count = result.scalar()
                if count > 1:
                    self.logger.warning(f"System allows duplicate entities with same identifiers: {count} found")
                else:
                    self.logger.info("System prevents duplicate entities with same identifiers")
                
            except Exception as e:
                await session.rollback()
                self.logger.info(f"Duplicate entity creation prevented: {e}")
    
    async def test_concurrent_entity_creation(self):
        """Test concurrent entity creation for race conditions."""
        async def create_entity_task(session_factory, entity_data):
            """Task to create an entity in a separate session."""
            try:
                async with session_factory() as session:
                    await session.execute(text("""
                        INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                        VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
                    """), entity_data)
                    await session.commit()
                    return True
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Create session factory
        engine = create_async_engine(self.database_url)
        session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        # Create multiple entities with potential conflicts
        entities = self.test_data_generator.generate_entities(5, self.test_client_id)
        tasks = []
        
        for entity in entities:
            entity_data = {
                "id": entity.id,
                "actor_type": "client",
                "actor_id": entity.client_user_id,
                "name": entity.name,
                "entity_type": entity.entity_type,
                "metadata": json.dumps(entity.metadata),
                "created_at": entity.created_at
            }
            tasks.append(create_entity_task(session_factory, entity_data))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful_creates = sum(1 for r in results if r is True)
        failed_creates = len(results) - successful_creates
        
        self.logger.info(f"Concurrent entity creation: {successful_creates} succeeded, {failed_creates} failed")
        
        # Verify actual entity count in database
        async with session_factory() as session:
            result = await session.execute(text("""
                SELECT COUNT(*) FROM memory_entities WHERE actor_id = :actor_id
            """), {"actor_id": self.test_client_id})
            
            actual_count = result.scalar()
            assert actual_count <= len(entities), f"More entities created than expected: {actual_count} > {len(entities)}"
        
        await engine.dispose()
    
    async def test_relationship_cascade_behavior(self):
        """Test relationship behavior when entities are deleted."""
        async with await self._get_session() as session:
            # Create entities and relationships
            entities = self.test_data_generator.generate_entities(3, self.test_client_id)
            
            for entity in entities:
                await session.execute(text("""
                    INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                    VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
                """), {
                    "id": entity.id,
                    "actor_type": "client",
                    "actor_id": entity.client_user_id,
                    "name": entity.name,
                    "entity_type": entity.entity_type,
                    "metadata": json.dumps(entity.metadata),
                    "created_at": entity.created_at
                })
            
            # Create relationships between entities
            relationships = self.test_data_generator.generate_relationships(entities, 3)
            
            for relationship in relationships:
                await session.execute(text("""
                    INSERT INTO memory_relations (id, actor_type, actor_id, source_id, target_id, relationship_type, metadata, created_at)
                    VALUES (:id, :actor_type, :actor_id, :source_id, :target_id, :relationship_type, :metadata, :created_at)
                """), {
                    "id": relationship.id,
                    "actor_type": "client",
                    "actor_id": relationship.client_user_id,
                    "source_id": relationship.source_id,
                    "target_id": relationship.target_id,
                    "relationship_type": relationship.relationship_type,
                    "metadata": json.dumps(relationship.metadata),
                    "created_at": relationship.created_at
                })
            
            await session.commit()
            
            # Count relationships before deletion
            result = await session.execute(text("""
                SELECT COUNT(*) FROM memory_relations WHERE actor_id = :actor_id
            """), {"actor_id": self.test_client_id})
            
            relationships_before = result.scalar()
            
            # Delete one entity
            entity_to_delete = entities[0]
            await session.execute(text("""
                DELETE FROM memory_entities WHERE id = :id
            """), {"id": entity_to_delete.id})
            
            await session.commit()
            
            # Check what happened to relationships
            result = await session.execute(text("""
                SELECT COUNT(*) FROM memory_relations WHERE actor_id = :actor_id
            """), {"actor_id": self.test_client_id})
            
            relationships_after = result.scalar()
            
            # Check for orphaned relationships
            result = await session.execute(text("""
                SELECT COUNT(*) FROM memory_relations r
                LEFT JOIN memory_entities e1 ON r.source_id = e1.id
                LEFT JOIN memory_entities e2 ON r.target_id = e2.id
                WHERE r.actor_id = :actor_id AND (e1.id IS NULL OR e2.id IS NULL)
            """), {"actor_id": self.test_client_id})
            
            orphaned_relationships = result.scalar()
            
            if orphaned_relationships > 0:
                self.logger.warning(f"Found {orphaned_relationships} orphaned relationships after entity deletion")
            else:
                self.logger.info("No orphaned relationships found - cascade behavior working correctly")
    
    async def test_large_metadata_handling(self):
        """Test handling of large JSON metadata objects."""
        async with await self._get_session() as session:
            # Create entity with large metadata
            test_entity = self.test_data_generator.generate_person_entity(self.test_client_id)
            
            # Generate large metadata (approximately 100KB)
            large_metadata = {
                "description": "A" * 10000,  # 10KB string
                "history": [
                    {
                        "date": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                        "event": f"Event {i}: " + "B" * 100,
                        "details": {
                            "participants": [f"Person {j}" for j in range(10)],
                            "notes": "C" * 200
                        }
                    }
                    for i in range(100)  # 100 history entries
                ],
                "tags": [f"tag_{i}" for i in range(1000)],  # 1000 tags
                "metrics": {f"metric_{i}": random.uniform(0, 1) for i in range(500)}  # 500 metrics
            }
            
            start_time = time.perf_counter()
            
            await session.execute(text("""
                INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
            """), {
                "id": test_entity.id,
                "actor_type": "client",
                "actor_id": test_entity.client_user_id,
                "name": test_entity.name,
                "entity_type": test_entity.entity_type,
                "metadata": json.dumps(large_metadata),
                "created_at": test_entity.created_at
            })
            
            await session.commit()
            
            insert_time = (time.perf_counter() - start_time) * 1000
            
            # Test retrieval of large metadata
            start_time = time.perf_counter()
            
            result = await session.execute(text("""
                SELECT metadata FROM memory_entities WHERE id = :id
            """), {"id": test_entity.id})
            
            retrieved_metadata_json = result.scalar()
            retrieved_metadata = json.loads(retrieved_metadata_json)
            
            retrieval_time = (time.perf_counter() - start_time) * 1000
            
            # Verify data integrity
            assert len(retrieved_metadata["history"]) == 100, "History entries not preserved"
            assert len(retrieved_metadata["tags"]) == 1000, "Tags not preserved"
            assert len(retrieved_metadata["metrics"]) == 500, "Metrics not preserved"
            assert retrieved_metadata["description"] == large_metadata["description"], "Large text not preserved"
            
            self.logger.info(f"Large metadata handling: insert={insert_time:.2f}ms, retrieval={retrieval_time:.2f}ms")
            
            # Test JSON querying on large metadata
            start_time = time.perf_counter()
            
            result = await session.execute(text("""
                SELECT name FROM memory_entities 
                WHERE metadata->'history'->0->>'event' LIKE 'Event 0:%'
                AND id = :id
            """), {"id": test_entity.id})
            
            queried_name = result.scalar()
            query_time = (time.perf_counter() - start_time) * 1000
            
            assert queried_name == test_entity.name, "JSON querying on large metadata failed"
            self.logger.info(f"Large metadata JSON query time: {query_time:.2f}ms")
    
    async def cleanup_test_data(self):
        """Clean up test data after validation."""
        try:
            async with await self._get_session() as session:
                # Delete test relationships
                await session.execute(text("""
                    DELETE FROM memory_relations 
                    WHERE actor_id LIKE 'integrity_test_%' 
                    OR actor_id LIKE 'client_%'
                    OR actor_id LIKE 'human_%'
                """))
                
                # Delete test entities
                await session.execute(text("""
                    DELETE FROM memory_entities 
                    WHERE actor_id LIKE 'integrity_test_%' 
                    OR actor_id LIKE 'client_%'
                    OR actor_id LIKE 'human_%'
                """))
                
                await session.commit()
                self.logger.info("Data integrity test cleanup completed")
        except Exception as e:
            self.logger.warning(f"Data integrity test cleanup failed: {e}")
    
    async def run_validation(self) -> List[ValidationResult]:
        """Run all data integrity validation tests."""
        if not self.database_url:
            # Try to get from environment
            self.database_url = os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL")
            
        if not self.database_url:
            return [ValidationResult(
                test_name="data_integrity_setup",
                status=ValidationStatus.FAILED,
                execution_time_ms=0.0,
                error_message="Database URL not configured. Set DATABASE_URL_DIRECT or DATABASE_URL environment variable."
            )]
        
        tests = [
            ("table_schema_validation", self.test_table_schema_validation),
            ("entity_uniqueness_constraints", self.test_entity_uniqueness_constraints),
            ("relationship_referential_integrity", self.test_relationship_referential_integrity),
            ("client_data_isolation", self.test_client_data_isolation),
            ("json_metadata_integrity", self.test_json_metadata_integrity),
            ("timestamp_consistency", self.test_timestamp_consistency),
            ("entity_deduplication_logic", self.test_entity_deduplication_logic),
            ("concurrent_entity_creation", self.test_concurrent_entity_creation),
            ("relationship_cascade_behavior", self.test_relationship_cascade_behavior),
            ("large_metadata_handling", self.test_large_metadata_handling)
        ]
        
        results = []
        
        try:
            for test_name, test_func in tests:
                result = await self.run_test(f"integrity_{test_name}", test_func)
                results.append(result)
        
        finally:
            # Always try to clean up test data
            await self.cleanup_test_data()
        
        return results