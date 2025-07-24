"""CRUD operations validator for memory system - Updated for actual schema."""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from .base import BaseValidator, ValidationResult, ValidationStatus
from .test_data_generator import TestDataGenerator

class CRUDValidator(BaseValidator):
    """Validate basic CRUD operations for memory system using actual schema."""
    
    def __init__(self, database_url: Optional[str] = None):
        super().__init__("CRUDValidator")
        self.database_url = database_url
        self.test_data_generator = TestDataGenerator(seed=42)
        self.test_actor_id = str(uuid.uuid4())
        self.test_actor_type = "human"  # or "synth"
    
    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        if not self.database_url:
            raise Exception("Database URL not configured")
        
        engine = create_async_engine(self.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        return async_session()
    
    async def test_entity_create(self):
        """Test entity creation using actual schema."""
        async with await self._get_session() as session:
            # Generate test entity data
            test_entity = self.test_data_generator.generate_person_entity(
                self.test_actor_id, grade="high"
            )
            
            # Insert entity using actual schema columns
            entity_id = str(uuid.uuid4())
            await session.execute(text("""
                INSERT INTO memory_entities (id, actor_type, actor_id, entity_name, entity_type, metadata, created_at)
                VALUES (:id, :actor_type, :actor_id, :entity_name, :entity_type, :metadata, :created_at)
            """), {
                "id": entity_id,
                "actor_type": self.test_actor_type,
                "actor_id": self.test_actor_id,
                "entity_name": test_entity.name,
                "entity_type": test_entity.entity_type,
                "metadata": json.dumps(test_entity.metadata),
                "created_at": datetime.utcnow()
            })
            
            await session.commit()
            
            # Verify entity was created
            result = await session.execute(text("""
                SELECT id, entity_name, entity_type FROM memory_entities WHERE id = :id
            """), {"id": entity_id})
            
            row = result.fetchone()
            assert row is not None, "Entity was not created"
            assert row.id == entity_id, "Entity ID mismatch"
            assert row.entity_name == test_entity.name, "Entity name mismatch"
            assert row.entity_type == test_entity.entity_type, "Entity type mismatch"
    
    async def test_entity_read(self):
        """Test entity reading using actual schema."""
        async with await self._get_session() as session:
            # Create test entity first
            test_entity = self.test_data_generator.generate_company_entity(
                self.test_actor_id, grade="medium"
            )
            
            entity_id = str(uuid.uuid4())
            await session.execute(text("""
                INSERT INTO memory_entities (id, actor_type, actor_id, entity_name, entity_type, metadata, created_at)
                VALUES (:id, :actor_type, :actor_id, :entity_name, :entity_type, :metadata, :created_at)
            """), {
                "id": entity_id,
                "actor_type": self.test_actor_type,
                "actor_id": self.test_actor_id,
                "entity_name": test_entity.name,
                "entity_type": test_entity.entity_type,
                "metadata": json.dumps(test_entity.metadata),
                "created_at": datetime.utcnow()
            })
            
            await session.commit()
            
            # Test reading the entity
            result = await session.execute(text("""
                SELECT id, actor_type, actor_id, entity_name, entity_type, metadata
                FROM memory_entities 
                WHERE id = :id AND actor_id = :actor_id
            """), {
                "id": entity_id,
                "actor_id": self.test_actor_id
            })
            
            row = result.fetchone()
            assert row is not None, "Entity not found"
            
            # Verify all fields
            assert row.id == entity_id
            assert row.actor_id == self.test_actor_id
            assert row.actor_type == self.test_actor_type
            assert row.entity_name == test_entity.name
            assert row.entity_type == test_entity.entity_type
            
            # Verify JSON metadata
            metadata = json.loads(row.metadata)
            assert metadata == test_entity.metadata, "Metadata mismatch"
    
    async def test_entity_update(self):
        """Test entity updating using actual schema."""
        async with await self._get_session() as session:
            # Create test entity
            test_entity = self.test_data_generator.generate_person_entity(
                self.test_actor_id, grade="low"
            )
            
            entity_id = str(uuid.uuid4())
            await session.execute(text("""
                INSERT INTO memory_entities (id, actor_type, actor_id, entity_name, entity_type, metadata, created_at)
                VALUES (:id, :actor_type, :actor_id, :entity_name, :entity_type, :metadata, :created_at)
            """), {
                "id": entity_id,
                "actor_type": self.test_actor_type,
                "actor_id": self.test_actor_id,
                "entity_name": test_entity.name,
                "entity_type": test_entity.entity_type,
                "metadata": json.dumps(test_entity.metadata),
                "created_at": datetime.utcnow()
            })
            
            await session.commit()
            
            # Update the entity
            new_name = "Updated " + test_entity.name
            updated_metadata = {**test_entity.metadata, "updated": True, "update_time": datetime.utcnow().isoformat()}
            
            await session.execute(text("""
                UPDATE memory_entities 
                SET entity_name = :entity_name, metadata = :metadata, updated_at = :updated_at
                WHERE id = :id AND actor_id = :actor_id
            """), {
                "id": entity_id,
                "actor_id": self.test_actor_id,
                "entity_name": new_name,
                "metadata": json.dumps(updated_metadata),
                "updated_at": datetime.utcnow()
            })
            
            await session.commit()
            
            # Verify update
            result = await session.execute(text("""
                SELECT entity_name, metadata FROM memory_entities WHERE id = :id
            """), {"id": entity_id})
            
            row = result.fetchone()
            assert row is not None, "Entity not found after update"
            assert row.entity_name == new_name, "Name was not updated"
            
            metadata = json.loads(row.metadata)
            assert metadata["updated"] == True, "Metadata was not updated"
    
    async def test_entity_delete(self):
        """Test entity deletion using actual schema (soft delete)."""
        async with await self._get_session() as session:
            # Create test entity
            test_entity = self.test_data_generator.generate_person_entity(
                self.test_actor_id, grade="generic"
            )
            
            entity_id = str(uuid.uuid4())
            await session.execute(text("""
                INSERT INTO memory_entities (id, actor_type, actor_id, entity_name, entity_type, metadata, created_at)
                VALUES (:id, :actor_type, :actor_id, :entity_name, :entity_type, :metadata, :created_at)
            """), {
                "id": entity_id,
                "actor_type": self.test_actor_type,
                "actor_id": self.test_actor_id,
                "entity_name": test_entity.name,
                "entity_type": test_entity.entity_type,
                "metadata": json.dumps(test_entity.metadata),
                "created_at": datetime.utcnow()
            })
            
            await session.commit()
            
            # Verify entity exists
            result = await session.execute(text("""
                SELECT COUNT(*) FROM memory_entities WHERE id = :id AND deleted_at IS NULL
            """), {"id": entity_id})
            
            count = result.scalar()
            assert count == 1, "Entity was not created"
            
            # Soft delete the entity (set deleted_at)
            await session.execute(text("""
                UPDATE memory_entities 
                SET deleted_at = :deleted_at 
                WHERE id = :id AND actor_id = :actor_id
            """), {
                "id": entity_id,
                "actor_id": self.test_actor_id,
                "deleted_at": datetime.utcnow()
            })
            
            await session.commit()
            
            # Verify entity was soft deleted
            result = await session.execute(text("""
                SELECT COUNT(*) FROM memory_entities WHERE id = :id AND deleted_at IS NULL
            """), {"id": entity_id})
            
            count = result.scalar()
            assert count == 0, "Entity was not soft deleted"
            
            # Verify entity still exists but is marked as deleted
            result = await session.execute(text("""
                SELECT COUNT(*) FROM memory_entities WHERE id = :id AND deleted_at IS NOT NULL
            """), {"id": entity_id})
            
            count = result.scalar()
            assert count == 1, "Entity was hard deleted instead of soft deleted"
    
    async def test_relationship_crud(self):
        """Test relationship CRUD operations using actual schema."""
        async with await self._get_session() as session:
            # Create two test entities first
            entities = self.test_data_generator.generate_entities(2, self.test_actor_id, ["person", "company"])
            
            entity_ids = []
            for entity in entities:
                entity_id = str(uuid.uuid4())
                entity_ids.append(entity_id)
                
                await session.execute(text("""
                    INSERT INTO memory_entities (id, actor_type, actor_id, entity_name, entity_type, metadata, created_at)
                    VALUES (:id, :actor_type, :actor_id, :entity_name, :entity_type, :metadata, :created_at)
                """), {
                    "id": entity_id,
                    "actor_type": self.test_actor_type,
                    "actor_id": self.test_actor_id,
                    "entity_name": entity.name,
                    "entity_type": entity.entity_type,
                    "metadata": json.dumps(entity.metadata),
                    "created_at": datetime.utcnow()
                })
            
            await session.commit()
            
            # Create relationship using actual schema
            relationship_id = str(uuid.uuid4())
            relation_type = "works_for"
            
            # INSERT relationship
            await session.execute(text("""
                INSERT INTO memory_relations (id, from_entity_id, to_entity_id, relation_type, metadata, created_at)
                VALUES (:id, :from_entity_id, :to_entity_id, :relation_type, :metadata, :created_at)
            """), {
                "id": relationship_id,
                "from_entity_id": entity_ids[0],
                "to_entity_id": entity_ids[1],
                "relation_type": relation_type,
                "metadata": json.dumps({"test": True, "strength": "strong"}),
                "created_at": datetime.utcnow()
            })
            
            await session.commit()
            
            # READ relationship
            result = await session.execute(text("""
                SELECT id, from_entity_id, to_entity_id, relation_type, metadata
                FROM memory_relations 
                WHERE id = :id AND deleted_at IS NULL
            """), {"id": relationship_id})
            
            row = result.fetchone()
            assert row is not None, "Relationship not found"
            assert row.from_entity_id == entity_ids[0]
            assert row.to_entity_id == entity_ids[1]
            assert row.relation_type == relation_type
            
            # UPDATE relationship
            new_metadata = {"test": True, "strength": "medium", "updated": True}
            await session.execute(text("""
                UPDATE memory_relations 
                SET metadata = :metadata, updated_at = :updated_at 
                WHERE id = :id
            """), {
                "id": relationship_id,
                "metadata": json.dumps(new_metadata),
                "updated_at": datetime.utcnow()
            })
            
            await session.commit()
            
            # Verify update
            result = await session.execute(text("""
                SELECT metadata FROM memory_relations WHERE id = :id
            """), {"id": relationship_id})
            
            updated_metadata_json = result.scalar()
            updated_metadata = json.loads(updated_metadata_json)
            assert updated_metadata["updated"] == True, "Relationship metadata was not updated"
            
            # SOFT DELETE relationship
            await session.execute(text("""
                UPDATE memory_relations 
                SET deleted_at = :deleted_at 
                WHERE id = :id
            """), {
                "id": relationship_id,
                "deleted_at": datetime.utcnow()
            })
            
            await session.commit()
            
            # Verify soft deletion
            result = await session.execute(text("""
                SELECT COUNT(*) FROM memory_relations WHERE id = :id AND deleted_at IS NULL
            """), {"id": relationship_id})
            
            count = result.scalar()
            assert count == 0, "Relationship was not soft deleted"
    
    async def test_actor_isolation(self):
        """Test that actor data is properly isolated."""
        async with await self._get_session() as session:
            # Create entities for two different actors
            actor1_id = str(uuid.uuid4())
            actor2_id = str(uuid.uuid4())
            
            entity1 = self.test_data_generator.generate_person_entity(actor1_id)
            entity2 = self.test_data_generator.generate_person_entity(actor2_id)
            
            entity1_id = str(uuid.uuid4())
            entity2_id = str(uuid.uuid4())
            
            # Insert both entities
            for entity, entity_id, actor_id in [(entity1, entity1_id, actor1_id), (entity2, entity2_id, actor2_id)]:
                await session.execute(text("""
                    INSERT INTO memory_entities (id, actor_type, actor_id, entity_name, entity_type, metadata, created_at)
                    VALUES (:id, :actor_type, :actor_id, :entity_name, :entity_type, :metadata, :created_at)
                """), {
                    "id": entity_id,
                    "actor_type": self.test_actor_type,
                    "actor_id": actor_id,
                    "entity_name": entity.name,
                    "entity_type": entity.entity_type,
                    "metadata": json.dumps(entity.metadata),
                    "created_at": datetime.utcnow()
                })
            
            await session.commit()
            
            # Test that actor1 can only see their own entity
            result = await session.execute(text("""
                SELECT COUNT(*) FROM memory_entities WHERE actor_id = :actor_id AND deleted_at IS NULL
            """), {"actor_id": actor1_id})
            
            count1 = result.scalar()
            assert count1 == 1, f"Actor1 should see exactly 1 entity, saw {count1}"
            
            # Test that actor2 can only see their own entity
            result = await session.execute(text("""
                SELECT COUNT(*) FROM memory_entities WHERE actor_id = :actor_id AND deleted_at IS NULL
            """), {"actor_id": actor2_id})
            
            count2 = result.scalar()
            assert count2 == 1, f"Actor2 should see exactly 1 entity, saw {count2}"
            
            # Test that actor1 cannot access actor2's data
            result = await session.execute(text("""
                SELECT COUNT(*) FROM memory_entities 
                WHERE actor_id = :actor1_id AND id = :entity2_id
            """), {"actor1_id": actor1_id, "entity2_id": entity2_id})
            
            cross_access_count = result.scalar()
            assert cross_access_count == 0, "Actor isolation violated - cross-actor access detected"
    
    async def cleanup_test_data(self):
        """Clean up test data after validation."""
        try:
            async with await self._get_session() as session:
                # Delete test relationships
                await session.execute(text("""
                    DELETE FROM memory_relations WHERE from_entity_id IN (
                        SELECT id FROM memory_entities WHERE actor_id = :actor_id
                    ) OR to_entity_id IN (
                        SELECT id FROM memory_entities WHERE actor_id = :actor_id
                    )
                """), {"actor_id": self.test_actor_id})
                
                # Delete test entities
                await session.execute(text("""
                    DELETE FROM memory_entities WHERE actor_id = :actor_id
                """), {"actor_id": self.test_actor_id})
                
                await session.commit()
                self.logger.info("Test data cleanup completed")
        except Exception as e:
            self.logger.warning(f"Test data cleanup failed: {e}")
    
    async def run_validation(self) -> List[ValidationResult]:
        """Run all CRUD validation tests."""
        if not self.database_url:
            return [ValidationResult(
                test_name="crud_validation_setup",
                status=ValidationStatus.FAILED,
                execution_time_ms=0.0,
                error_message="Database URL not configured"
            )]
        
        tests = [
            ("entity_create", self.test_entity_create),
            ("entity_read", self.test_entity_read),
            ("entity_update", self.test_entity_update),
            ("entity_delete", self.test_entity_delete),
            ("relationship_crud", self.test_relationship_crud),
            ("actor_isolation", self.test_actor_isolation)
        ]
        
        results = []
        
        try:
            for test_name, test_func in tests:
                result = await self.run_test(f"crud_{test_name}", test_func)
                results.append(result)
        
        finally:
            # Always try to clean up test data
            await self.cleanup_test_data()
        
        return results