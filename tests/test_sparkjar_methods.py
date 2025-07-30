# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

# tests/test_sparkjar_methods.py
import pytest
from uuid import uuid4
from datetime import datetime
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

class TestRememberConversation:
    """Test remember_conversation method"""
    
    @pytest.mark.asyncio
    async def test_remember_conversation_basic(self, memory_manager, test_context):
        """Test basic conversation memory extraction"""
        conversation_text = """
        Alice: I've been working on the machine learning pipeline for the customer analytics project.
        Bob: That's great! I know you're an expert in Python and TensorFlow.
        Alice: Thanks! I'm also using some advanced SQL optimization techniques for the data preprocessing.
        Bob: We should connect you with Sarah, she's working on a similar project for marketing.
        """
        
        participants = ["Alice", "Bob"]
        context = {
            "meeting_type": "standup",
            "date": datetime.utcnow().isoformat()
        }
        
        result = await memory_manager.remember_conversation(
            **test_context,
            conversation_text=conversation_text,
            participants=participants,
            context=context
        )
        
        # Check that participants were created
        assert len(result["entities_created"]) >= 2  # At least Alice, Bob, and event
        
        # Check that observations were added
        assert len(result["observations_added"]) > 0
        
        # Check that relations were created
        assert len(result["relations_created"]) >= 2  # Participants to event
        
        # Verify event entity was created
        event_entities = [e for e in result["entities_created"] if e["entity_type"] == "event"]
        assert len(event_entities) == 1
        assert "Conversation_" in event_entities[0]["entity_name"]
    
    @pytest.mark.asyncio
    async def test_remember_conversation_extracts_skills(self, memory_manager, test_context):
        """Test that skills are extracted from conversation"""
        conversation_text = """
        John: I have extensive experience with React and Node.js.
        Mary: That's perfect for our web project. I'm skilled in database design and PostgreSQL.
        John: I also know Docker and Kubernetes for deployment.
        """
        
        participants = ["John", "Mary"]
        context = {"meeting_type": "interview"}
        
        result = await memory_manager.remember_conversation(
            **test_context,
            conversation_text=conversation_text,
            participants=participants,
            context=context
        )
        
        # Check that skills were extracted
        assert len(result["observations_added"]) > 0
        
        # Verify John entity exists
        entities = await memory_manager.open_nodes(
            **test_context,
            names=["John"]
        )
        assert len(entities) == 1
        
        # Check John's observations contain skills
        john_observations = entities[0]["observations"]
        skill_obs = [o for o in john_observations if o.get("type") == "skill"]
        assert len(skill_obs) > 0

class TestFindConnections:
    """Test find_connections method"""
    
    @pytest.mark.asyncio
    async def test_find_direct_connection(self, memory_manager, test_context):
        """Test finding direct connections between entities"""
        # Create entities
        await memory_manager.create_entities(
            **test_context,
            entities=[
                EntityCreate(
                    name="Alice",
                    entityType="person",
                    observations=[Observation(type="fact", value="Developer")]
                ),
                EntityCreate(
                    name="Project Alpha",
                    entityType="project",
                    observations=[Observation(type="fact", value="ML Project")]
                )
            ]
        )
        
        # Create relation
        await memory_manager.create_relations(
            **test_context,
            relations=[{
                "from_entity_name": "Alice",
                "to_entity_name": "Project Alpha",
                "relationType": "works_on"
            }]
        )
        
        # Find connection
        result = await memory_manager.find_connections(
            **test_context,
            from_entity="Alice",
            to_entity="Project Alpha"
        )
        
        assert result["from_entity"] == "Alice"
        assert result["to_entity"] == "Project Alpha"
        assert len(result["paths"]) > 0
        assert result["shortest_path_length"] == 1
    
    @pytest.mark.asyncio
    async def test_find_indirect_connections(self, memory_manager, test_context):
        """Test finding indirect connections through intermediate entities"""
        # Create entities
        entities = [
            EntityCreate(name="John", entityType="person", observations=[]),
            EntityCreate(name="Python", entityType="skill", observations=[]),
            EntityCreate(name="Data Science Project", entityType="project", observations=[])
        ]
        await memory_manager.create_entities(**test_context, entities=entities)
        
        # Create relations: John -> Python -> Data Science Project
        await memory_manager.create_relations(
            **test_context,
            relations=[
                {
                    "from_entity_name": "John",
                    "to_entity_name": "Python",
                    "relationType": "knows"
                },
                {
                    "from_entity_name": "Python",
                    "to_entity_name": "Data Science Project",
                    "relationType": "used_in"
                }
            ]
        )
        
        # Find connection
        result = await memory_manager.find_connections(
            **test_context,
            from_entity="John",
            to_entity="Data Science Project",
            max_hops=2
        )
        
        assert len(result["paths"]) > 0
        assert result["shortest_path_length"] == 2
        
        # Check path includes Python
        shortest_path = result["paths"][0]
        assert "Python" in shortest_path["path"]
    
    @pytest.mark.asyncio
    async def test_find_all_connections(self, memory_manager, test_context):
        """Test finding all connections from an entity"""
        # Create a network
        entities = [
            EntityCreate(name="Sarah", entityType="person", observations=[]),
            EntityCreate(name="Team A", entityType="team", observations=[]),
            EntityCreate(name="Project X", entityType="project", observations=[]),
            EntityCreate(name="Project Y", entityType="project", observations=[])
        ]
        await memory_manager.create_entities(**test_context, entities=entities)
        
        # Create relations
        await memory_manager.create_relations(
            **test_context,
            relations=[
                {"from_entity_name": "Sarah", "to_entity_name": "Team A", "relationType": "member_of"},
                {"from_entity_name": "Team A", "to_entity_name": "Project X", "relationType": "owns"},
                {"from_entity_name": "Team A", "to_entity_name": "Project Y", "relationType": "owns"}
            ]
        )
        
        # Find all connections from Sarah
        result = await memory_manager.find_connections(
            **test_context,
            from_entity="Sarah",
            max_hops=2
        )
        
        assert "connections" in result
        assert result["total_connected_entities"] >= 3  # Team A, Project X, Project Y
        
        # Check we can reach both projects
        connections = result["connections"]
        assert "Project X" in connections
        assert "Project Y" in connections

class TestGetClientInsights:
    """Test get_client_insights method"""
    
    @pytest.mark.asyncio
    async def test_insights_skill_distribution(self, memory_manager, test_context):
        """Test insights on skill distribution"""
        # Create people with skills
        people = [
            EntityCreate(
                name="Developer1",
                entityType="person",
                observations=[
                    Observation(type="skill", value="Python", proficiency_level="expert"),
                    Observation(type="skill", value="JavaScript", proficiency_level="advanced")
                ]
            ),
            EntityCreate(
                name="Developer2",
                entityType="person",
                observations=[
                    Observation(type="skill", value="Python", proficiency_level="intermediate")
                ]
            ),
            EntityCreate(
                name="Developer3",
                entityType="person",
                observations=[
                    Observation(type="skill", value="Java", proficiency_level="expert")
                ]
            )
        ]
        await memory_manager.create_entities(**test_context, entities=people)
        
        # Get insights
        insights = await memory_manager.get_client_insights(**test_context)
        
        # Check skill distribution
        assert "skill_distribution" in insights
        assert "Python" in insights["skill_distribution"]
        assert insights["skill_distribution"]["Python"]["count"] == 2
        
        # Check knowledge gaps (skills with only 1 person)
        assert "knowledge_gaps" in insights
        gap_skills = [gap["skill"] for gap in insights["knowledge_gaps"]]
        assert "JavaScript" in gap_skills
        assert "Java" in gap_skills
    
    @pytest.mark.asyncio
    async def test_insights_underutilized_expertise(self, memory_manager, test_context):
        """Test identification of underutilized expertise"""
        # Create person with skills but no connections
        await memory_manager.create_entities(
            **test_context,
            entities=[
                EntityCreate(
                    name="Expert",
                    entityType="person",
                    observations=[
                        Observation(type="skill", value="Machine Learning"),
                        Observation(type="skill", value="Deep Learning")
                    ]
                ),
                EntityCreate(
                    name="Project1",
                    entityType="project",
                    observations=[]
                )
            ]
        )
        
        # Get insights
        insights = await memory_manager.get_client_insights(**test_context)
        
        # Check underutilized expertise
        assert "underutilized_expertise" in insights
        underutilized = insights["underutilized_expertise"]
        assert len(underutilized) > 0
        assert underutilized[0]["person"] == "Expert"
        assert len(underutilized[0]["skills"]) == 2
    
    @pytest.mark.asyncio
    async def test_insights_collaboration_opportunities(self, memory_manager, test_context):
        """Test identification of collaboration opportunities"""
        # Create people with complementary skills who aren't connected
        people = [
            EntityCreate(
                name="Frontend Dev",
                entityType="person",
                observations=[
                    Observation(type="skill", value="React"),
                    Observation(type="skill", value="CSS")
                ]
            ),
            EntityCreate(
                name="Backend Dev",
                entityType="person",
                observations=[
                    Observation(type="skill", value="Node.js"),
                    Observation(type="skill", value="PostgreSQL")
                ]
            )
        ]
        await memory_manager.create_entities(**test_context, entities=people)
        
        # Get insights
        insights = await memory_manager.get_client_insights(**test_context)
        
        # Check collaboration opportunities
        assert "collaboration_opportunities" in insights
        opportunities = insights["collaboration_opportunities"]
        assert len(opportunities) > 0
        
        # Should identify Frontend Dev and Backend Dev as having complementary skills
        opp = opportunities[0]
        people_in_opp = [opp["person1"], opp["person2"]]
        assert "Frontend Dev" in people_in_opp
        assert "Backend Dev" in people_in_opp
        assert opp["reason"] == "Complementary skills, not currently connected"
    
    @pytest.mark.asyncio
    async def test_insights_summary_statistics(self, memory_manager, test_context):
        """Test summary statistics in insights"""
        # Create a small knowledge graph
        await memory_manager.create_entities(
            **test_context,
            entities=[
                EntityCreate(name="Person1", entityType="person", observations=[]),
                EntityCreate(name="Person2", entityType="person", observations=[]),
                EntityCreate(name="Project1", entityType="project", observations=[]),
                EntityCreate(name="Skill1", entityType="skill", observations=[])
            ]
        )
        
        # Create some relations
        await memory_manager.create_relations(
            **test_context,
            relations=[
                {"from_entity_name": "Person1", "to_entity_name": "Project1", "relationType": "works_on"},
                {"from_entity_name": "Person2", "to_entity_name": "Project1", "relationType": "works_on"},
                {"from_entity_name": "Person1", "to_entity_name": "Skill1", "relationType": "has"}
            ]
        )
        
        # Get insights
        insights = await memory_manager.get_client_insights(**test_context)
        
        # Check summary
        assert "summary" in insights
        summary = insights["summary"]
        assert summary["total_people"] == 2
        assert summary["total_projects"] == 1
        assert summary["average_connections_per_entity"] > 0
        
        # Check entity statistics
        assert "entity_statistics" in insights
        assert insights["entity_statistics"]["total_entities"] == 4
        
        # Check relationship statistics
        assert "relationship_statistics" in insights
        assert insights["relationship_statistics"]["total_relationships"] == 3