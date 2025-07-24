# tests/test_real_embeddings.py
import pytest
import sys
import os

from sparkjar_crew.shared.schemas.memory_schemas import EntityCreate

class TestRealEmbeddings:
    """Integration tests that verify real embedding service works"""
    
    @pytest.mark.asyncio
    async def test_embedding_service_connection(self, embedding_service):
        """Test that we can connect to the real embedding service"""
        # Simple test text
        test_text = "Python programming expert with 10 years experience"
        
        # Generate embedding
        embedding = await embedding_service.generate_embedding(test_text)
        
        # Verify we got a valid embedding
        assert isinstance(embedding, list)
        assert len(embedding) == 768  # Correct dimension
        assert all(isinstance(x, (int, float)) for x in embedding)
        assert any(x != 0 for x in embedding)  # Not all zeros
        
        print(f"\n✅ Successfully generated embedding with {len(embedding)} dimensions")
        print(f"   First 5 values: {embedding[:5]}")
    
    @pytest.mark.asyncio
    async def test_entity_creation_with_real_embeddings(self, memory_manager, test_context):
        """Test creating entity with real embeddings from Railway server"""
        entity = EntityCreate(
            name="Embedding Test User",
            entityType="person",
            observations=[
                {
                    "type": "skill",
                    "value": "Machine Learning Expert",
                    "skill_name": "Machine Learning",
                    "skill_category": "technical",
                    "proficiency_level": "expert",
                    "source": "certification"
                },
                {
                    "type": "fact",
                    "value": "Published 5 papers on neural networks",
                    "source": "publications"
                }
            ],
            metadata={
                "role": "AI Researcher",
                "organization": "Tech Institute"
            }
        )
        
        # Create entity - this will call the real embedding service
        result = await memory_manager.create_entities(
            test_context["client_id"],
            test_context["actor_type"],
            test_context["actor_id"],
            [entity]
        )
        
        assert len(result) == 1
        created = result[0]
        
        print(f"\n✅ Created entity '{created['entity_name']}' with real embeddings")
        
        # Now search for it using semantic similarity
        search_results = await memory_manager.search_nodes(
            test_context["client_id"],
            test_context["actor_type"],
            test_context["actor_id"],
            query="neural network researcher",
            limit=5,
            threshold=0.5
        )
        
        # Should find our entity
        assert len(search_results) > 0
        assert any(r["entity_name"] == "Embedding Test User" for r in search_results)
        
        best_match = search_results[0]
        print(f"✅ Semantic search found entity with similarity: {best_match['similarity']:.3f}")
    
    @pytest.mark.asyncio 
    async def test_semantic_similarity_accuracy(self, memory_manager, test_context):
        """Test that semantic search actually works with real embeddings"""
        # Create entities with different levels of similarity
        entities = [
            EntityCreate(
                name="Python Developer",
                entityType="person",
                observations=[{
                    "type": "skill",
                    "value": "Expert in Python, Django, Flask",
                    "skill_name": "Python",
                    "skill_category": "technical",
                    "proficiency_level": "expert"
                }]
            ),
            EntityCreate(
                name="JavaScript Developer", 
                entityType="person",
                observations=[{
                    "type": "skill",
                    "value": "Expert in JavaScript, React, Node.js",
                    "skill_name": "JavaScript",
                    "skill_category": "technical",
                    "proficiency_level": "expert"
                }]
            ),
            EntityCreate(
                name="Marketing Manager",
                entityType="person",
                observations=[{
                    "type": "skill",
                    "value": "Marketing strategy, brand management",
                    "skill_name": "Marketing",
                    "skill_category": "creative",
                    "proficiency_level": "expert"
                }]
            )
        ]
        
        # Create all entities
        await memory_manager.create_entities(
            test_context["client_id"],
            test_context["actor_type"],
            test_context["actor_id"],
            entities
        )
        
        # Search for Python-related
        results = await memory_manager.search_nodes(
            test_context["client_id"],
            test_context["actor_type"],
            test_context["actor_id"],
            query="Python programming and web development",
            limit=10,
            threshold=0.3
        )
        
        # Python Developer should rank highest
        assert len(results) > 0
        print(f"\n🔍 Search results for 'Python programming':")
        for i, result in enumerate(results[:3]):
            print(f"   {i+1}. {result['entity_name']} - similarity: {result['similarity']:.3f}")
        
        # Verify Python Developer has highest similarity
        python_dev = next((r for r in results if r["entity_name"] == "Python Developer"), None)
        assert python_dev is not None
        assert python_dev["similarity"] == max(r["similarity"] for r in results)