# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

# tests/test_search_updates.py
import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

import sys
import os

from services.memory_manager import MemoryManager
from services.embeddings import EmbeddingService
from sparkjar_shared.schemas.memory_schemas import EntityCreate, Observation
from database import get_db
from config import settings

@pytest.fixture
def memory_manager(db_session: Session):
    """Create memory manager with real embeddings"""
    embedding_service = EmbeddingService(
        api_url=os.getenv('EMBEDDINGS_API_URL_TEST', settings.EMBEDDINGS_API_URL)
    )
    return MemoryManager(db_session, embedding_service)

@pytest.fixture
def test_context():
    """Test context for all operations"""
    return {
        # "client_id" removed - use actor_id when actor_type="client"
        "actor_type": "human",
        "actor_id": uuid4()
    }

class TestSearchUpdates:
    """Test updated search functionality"""
    
    @pytest.mark.asyncio
    async def test_search_with_multiple_entity_types(self, memory_manager, test_context):
        """Test searching with multiple entity types filter"""
        # Create entities of different types
        entities = [
            EntityCreate(
                name="John Doe",
                entityType="person",
                observations=[Observation(type="skill", value="Python programming")]
            ),
            EntityCreate(
                name="Python Project",
                entityType="project",
                observations=[Observation(type="fact", value="A project using Python")]
            ),
            EntityCreate(
                name="Python",
                entityType="skill",
                observations=[Observation(type="fact", value="Programming language")]
            ),
            EntityCreate(
                name="TechCorp",
                entityType="company",
                observations=[Observation(type="fact", value="Company using Python")]
            )
        ]
        
        await memory_manager.create_entities(**test_context, entities=entities)
        
        # Search for Python-related entities, filtering by person and project types
        results = await memory_manager.search_nodes(
            **test_context,
            query="Python",
            entity_types=["person", "project"],
            limit=10
        )
        
        # Should only return person and project entities
        entity_types_in_results = set(r["entity_type"] for r in results)
        assert entity_types_in_results.issubset({"person", "project"})
        
        # Should include John Doe and Python Project
        entity_names = [r["entity_name"] for r in results]
        assert "John Doe" in entity_names
        assert "Python Project" in entity_names
        
        # Should NOT include skill or company entities
        assert "Python" not in entity_names  # skill entity
        assert "TechCorp" not in entity_names  # company entity
    
    @pytest.mark.asyncio
    async def test_search_with_min_confidence(self, memory_manager, test_context):
        """Test search with min_confidence parameter"""
        # Create entities with varying relevance to the search term
        entities = [
            EntityCreate(
                name="Machine Learning Expert",
                entityType="person",
                observations=[
                    Observation(type="skill", value="Machine learning"),
                    Observation(type="skill", value="Deep learning"),
                    Observation(type="skill", value="Neural networks")
                ]
            ),
            EntityCreate(
                name="ML Beginner",
                entityType="person",
                observations=[
                    Observation(type="fact", value="Just started learning ML")
                ]
            ),
            EntityCreate(
                name="Unrelated Person",
                entityType="person",
                observations=[
                    Observation(type="skill", value="Cooking"),
                    Observation(type="skill", value="Gardening")
                ]
            )
        ]
        
        await memory_manager.create_entities(**test_context, entities=entities)
        
        # Search with high confidence threshold
        high_confidence_results = await memory_manager.search_nodes(
            **test_context,
            query="machine learning expert deep learning",
            min_confidence=0.8
        )
        
        # Should primarily return the ML Expert
        if high_confidence_results:
            assert high_confidence_results[0]["entity_name"] == "Machine Learning Expert"
            assert high_confidence_results[0]["similarity"] > 0.8
        
        # Search with lower confidence threshold
        low_confidence_results = await memory_manager.search_nodes(
            **test_context,
            query="machine learning",
            min_confidence=0.3
        )
        
        # Should return more results
        assert len(low_confidence_results) >= len(high_confidence_results)
        
        # Verify all results meet minimum confidence
        for result in low_confidence_results:
            assert result["similarity"] >= 0.3
    
    @pytest.mark.asyncio
    async def test_search_empty_entity_types(self, memory_manager, test_context):
        """Test search with empty entity_types array (should search all types)"""
        # Create diverse entities
        entities = [
            EntityCreate(name="Developer", entityType="person", observations=[]),
            EntityCreate(name="Development Project", entityType="project", observations=[]),
            EntityCreate(name="Development Skill", entityType="skill", observations=[])
        ]
        
        await memory_manager.create_entities(**test_context, entities=entities)
        
        # Search without entity type filter
        results = await memory_manager.search_nodes(
            **test_context,
            query="Development",
            entity_types=None  # or empty list
        )
        
        # Should return entities of all types
        entity_types_found = set(r["entity_type"] for r in results)
        assert len(entity_types_found) >= 3  # person, project, skill
    
    @pytest.mark.asyncio
    async def test_search_with_exact_confidence_boundary(self, memory_manager, test_context):
        """Test search behavior at exact confidence boundaries"""
        # Create test entity
        await memory_manager.create_entities(
            **test_context,
            entities=[
                EntityCreate(
                    name="Test Entity",
                    entityType="test",
                    observations=[Observation(type="fact", value="Test data")]
                )
            ]
        )
        
        # Search with various confidence thresholds
        # With min_confidence = 0.0, should return all remotely related results
        all_results = await memory_manager.search_nodes(
            **test_context,
            query="completely unrelated query",
            min_confidence=0.0
        )
        
        # With min_confidence = 1.0, should only return exact matches
        exact_results = await memory_manager.search_nodes(
            **test_context,
            query="Test Entity Test data",
            min_confidence=0.99  # Very high threshold
        )
        
        # Verify confidence boundaries work correctly
        if exact_results:
            assert all(r["similarity"] >= 0.99 for r in exact_results)