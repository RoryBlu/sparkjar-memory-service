"""
End-to-end tests for memory service operations.
Tests complete workflows with real database operations and no mocks.
"""
import pytest
import asyncio
from uuid import uuid4
from datetime import datetime
import json

from sparkjar_shared.schemas.memory_schemas import EntityCreate, Observation

# Test context
TEST_CLIENT_ID = uuid4()
TEST_ACTOR_TYPE = "human"
TEST_ACTOR_ID = uuid4()

@pytest.mark.asyncio
async def test_complete_entity_lifecycle(memory_manager, test_context):
    """Test complete entity lifecycle: create, update, search, delete"""
    
    # Step 1: Create entities with observations
    entities_data = [
        EntityCreate(
            name="Alice Johnson",
            entityType="person",
            observations=[
                Observation(
                    type="skill",
                    value={
                        "name": "Machine Learning",
                        "category": "technical",
                        "level": "expert"
                    },
                    source="resume"
                ),
                Observation(
                    type="fact",
                    value="PhD in Computer Science from MIT",
                    source="profile"
                )
            ],
            metadata={
                "role": "Lead Data Scientist",
                "organization": "AI Corp",
                "email": "alice.johnson@aicorp.com"
            }
        ),
        EntityCreate(
            name="Bob Smith",
            entityType="person",
            observations=[
                Observation(
                    type="skill",
                    value={
                        "name": "Python",
                        "category": "technical",
                        "level": "advanced"
                    },
                    source="assessment"
                )
            ],
            metadata={
                "role": "Software Engineer",
                "organization": "AI Corp"
            }
        )
    ]
    
    created = await memory_manager.create_entities(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID, entities_data
    )
    
    assert len(created) == 2
    alice = next(e for e in created if e["entity_name"] == "Alice Johnson")
    bob = next(e for e in created if e["entity_name"] == "Bob Smith")
    
    # Verify entities have required fields
    assert alice["id"]
    assert alice["entity_type"] == "person"
    assert len(alice["observations"]) == 2
    assert alice["metadata"]["role"] == "Lead Data Scientist"
    
    # Step 2: Add more observations
    new_observations = [
        ObservationAdd(
            entityName="Alice Johnson",
            contents=[
                ObservationContent(
                    type="skill",
                    value={
                        "name": "Deep Learning",
                        "category": "technical",
                        "level": "expert"
                    },
                    source="project_review"
                ),
                ObservationContent(
                    type="writing_pattern",
                    value={
                        "pattern_type": "style",
                        "content_type": "documentation",
                        "description": "Clear, concise technical writing"
                    },
                    source="peer_feedback"
                )
            ]
        )
    ]
    
    obs_results = await memory_manager.add_observations(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID, new_observations
    )
    
    assert len(obs_results) == 1
    assert obs_results[0]["addedObservations"] == 2
    assert obs_results[0]["totalObservations"] == 4  # 2 original + 2 new
    
    # Step 3: Search entities
    search_results = await memory_manager.search_nodes(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID,
        query="machine learning expert",
        limit=5
    )
    
    assert len(search_results) > 0
    # Alice should rank high for ML search
    assert any(r["entity_name"] == "Alice Johnson" for r in search_results)
    
    # Step 4: Create relationships
# from sparkjar_crew.shared.schemas.memory_schemas import ...
    
    relations = [
        RelationCreate(
            from_entity_name="Bob Smith",
            to_entity_name="Alice Johnson",
            relationType="reports_to",
            metadata={"since": "2023-01-01", "department": "AI Research"}
        )
    ]
    
    created_relations = await memory_manager.create_relations(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID, relations
    )
    
    assert len(created_relations) == 1
    relation = created_relations[0]
    assert relation["from_entity_name"] == "Bob Smith"
    assert relation["to_entity_name"] == "Alice Johnson"
    assert relation["relation_type"] == "reports_to"
    
    # Step 5: Read graph
    graph = await memory_manager.read_graph(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID
    )
    
    assert graph["total_entities"] >= 2
    assert graph["total_relations"] >= 1
    assert len(graph["entities"]) >= 2
    assert len(graph["relations"]) >= 1
    
    # Step 6: Find connections
    connections = await memory_manager.find_connections(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID,
        "Bob Smith", "Alice Johnson"
    )
    
    assert len(connections) > 0
    assert connections[0]["path_length"] == 1  # Direct connection
    
    # Step 7: Delete entities
    delete_result = await memory_manager.delete_entities(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID,
        ["Bob Smith"]
    )
    
    assert delete_result["deleted_entities"] == 1
    assert delete_result["deleted_relations"] >= 1  # Should cascade delete relations
    
    # Verify Bob is deleted
    remaining = await memory_manager.open_nodes(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID,
        ["Bob Smith", "Alice Johnson"]
    )
    
    assert len(remaining) == 1
    assert remaining[0]["entity_name"] == "Alice Johnson"

@pytest.mark.asyncio
async def test_conversation_memory_extraction(memory_manager, test_context):
    """Test extracting and storing knowledge from conversations"""
    
    # Simulate a technical conversation
    conversation_text = """
    Alice: Hi everyone, I've been working with Bob on the new recommendation system.
    Bob: Yes, Alice knows Python and machine learning really well. She helped me optimize the algorithm.
    Alice: Thanks Bob. I think we should also consider using the deep learning project approach here.
    Bob: Agreed. By the way, I've been working on improving our API documentation.
    Alice: That's great! Clear documentation is essential for the team.
    """
    
    participants = ["Alice Johnson", "Bob Smith"]
    context = {
        "meeting_type": "technical_discussion",
        "date": datetime.utcnow().isoformat(),
        "topic": "recommendation_system"
    }
    
    result = await memory_manager.remember_conversation(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID,
        conversation_text, participants, context
    )
    
    # Verify entities were created/updated
    assert len(result["entities_created"]) > 0  # Event entity at minimum
    assert len(result["observations_added"]) > 0  # Skills extracted
    
    # Check that the conversation event was created
    event_entities = [e for e in result["entities_created"] if e["entity_type"] == "event"]
    assert len(event_entities) == 1
    event = event_entities[0]
    assert "Conversation" in event["entity_name"]
    assert event["metadata"]["participants"] == participants

@pytest.mark.asyncio
async def test_complex_graph_operations(memory_manager, test_context):
    """Test complex graph operations with multiple entities and relations"""
# from sparkjar_crew.shared.schemas.memory_schemas import ...
    
    # Create a network of entities
    entities = []
    for i in range(5):
        entities.append(EntityCreate(
            name=f"Entity_{i}",
            entityType="system",
            observations=[
                Observation(
                    type="fact",
                    value=f"System component {i}",
                    source="inventory"
                )
            ],
            metadata={"component_id": f"comp_{i}"}
        ))
    
    created = await memory_manager.create_entities(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID, entities
    )
    assert len(created) == 5
    
    # Create a web of relations
    relations = [
        RelationCreate(
            from_entity_name="Entity_0",
            to_entity_name="Entity_1",
            relationType="connects_to"
        ),
        RelationCreate(
            from_entity_name="Entity_1",
            to_entity_name="Entity_2",
            relationType="connects_to"
        ),
        RelationCreate(
            from_entity_name="Entity_2",
            to_entity_name="Entity_3",
            relationType="connects_to"
        ),
        RelationCreate(
            from_entity_name="Entity_3",
            to_entity_name="Entity_4",
            relationType="connects_to"
        ),
        RelationCreate(
            from_entity_name="Entity_0",
            to_entity_name="Entity_4",
            relationType="monitors"
        )
    ]
    
    created_rels = await memory_manager.create_relations(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID, relations
    )
    assert len(created_rels) == 5
    
    # Test path finding
    paths = await memory_manager.find_connections(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID,
        "Entity_0", "Entity_4"
    )
    
    # Should find at least 2 paths: direct (monitors) and through chain
    assert len(paths) >= 2
    
    # Verify path lengths
    path_lengths = [p["path_length"] for p in paths]
    assert 1 in path_lengths  # Direct path
    assert 4 in path_lengths  # Through chain

@pytest.mark.asyncio
async def test_semantic_search_accuracy(memory_manager, test_context):
    """Test semantic search with various queries"""
# from sparkjar_crew.shared.schemas.memory_schemas import ...
    
    # Create entities with diverse content
    entities = [
        EntityCreate(
            name="Python Expert",
            entityType="person",
            observations=[
                Observation(
                    type="skill",
                    value={"name": "Python", "level": "expert"},
                    source="profile"
                ),
                Observation(
                    type="fact",
                    value="10 years of Python development experience",
                    source="resume"
                )
            ]
        ),
        EntityCreate(
            name="Java Developer",
            entityType="person",
            observations=[
                Observation(
                    type="skill",
                    value={"name": "Java", "level": "advanced"},
                    source="profile"
                ),
                Observation(
                    type="fact",
                    value="Enterprise Java applications specialist",
                    source="resume"
                )
            ]
        ),
        EntityCreate(
            name="Database Admin",
            entityType="person",
            observations=[
                Observation(
                    type="skill",
                    value={"name": "PostgreSQL", "level": "expert"},
                    source="profile"
                ),
                Observation(
                    type="skill",
                    value={"name": "MySQL", "level": "advanced"},
                    source="profile"
                )
            ]
        )
    ]
    
    await memory_manager.create_entities(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID, entities
    )
    
    # Test various search queries
    test_queries = [
        ("Python programming", ["Python Expert"]),
        ("database", ["Database Admin"]),
        ("Java enterprise", ["Java Developer"]),
        ("SQL", ["Database Admin"])  # Should match PostgreSQL/MySQL
    ]
    
    for query, expected_names in test_queries:
        results = await memory_manager.search_nodes(
            TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID,
            query=query,
            limit=3
        )
        
        result_names = [r["entity_name"] for r in results]
        # Check that expected entities appear in results
        for expected in expected_names:
            assert expected in result_names, f"Expected {expected} in results for query '{query}'"

@pytest.mark.asyncio
async def test_observation_validation_integration(memory_manager, test_context):
    """Test that observation validation works correctly in practice"""
# from sparkjar_crew.shared.schemas.memory_schemas import ...
    
    # Create entity with various observation types
    entity = EntityCreate(
        name="Test Entity",
        entityType="person",
        observations=[
            # Valid skill observation
            Observation(
                type="skill",
                value={
                    "name": "Testing",
                    "category": "technical",
                    "level": "expert"
                },
                source="test"
            ),
            # Valid database ref
            Observation(
                type="database_ref",
                value={
                    "table_name": "test_table",
                    "record_id": str(uuid4()),
                    "relationship_type": "created"
                },
                source="system"
            ),
            # Generic observation (falls back to base)
            Observation(
                type="note",
                value="This is a general note",
                source="user"
            )
        ]
    )
    
    created = await memory_manager.create_entities(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID, [entity]
    )
    
    assert len(created) == 1
    entity_data = created[0]
    
    # Check that all observations were stored with validation metadata
    for obs in entity_data["observations"]:
        # Validation metadata should be present
        assert "_schema_used" in obs
        assert "_validated_at" in obs
        assert "_validation_passed" in obs
        
        # Check correct schema was used
        if obs["type"] == "skill":
            assert obs["_schema_used"] == "skill_observation"
        elif obs["type"] == "database_ref":
            assert obs["_schema_used"] == "database_ref_observation"
        else:
            assert obs["_schema_used"] == "base_observation"

@pytest.mark.asyncio
async def test_client_insights_aggregation(memory_manager, test_context):
    """Test client insights aggregation functionality"""
    # Create diverse data
# from sparkjar_crew.shared.schemas.memory_schemas import ...
    
    # Create multiple entities
    entities = []
    for i in range(10):
        entity_type = "person" if i < 7 else "system"
        entities.append(EntityCreate(
            name=f"Entity_{i}",
            entityType=entity_type,
            observations=[
                Observation(
                    type="fact",
                    value=f"Description of entity {i}",
                    source="test"
                )
            ]
        ))
    
    await memory_manager.create_entities(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID, entities
    )
    
    # Create some relations
    relations = []
    for i in range(5):
        relations.append(RelationCreate(
            from_entity_name=f"Entity_{i}",
            to_entity_name=f"Entity_{i+1}",
            relationType="connected_to"
        ))
    
    await memory_manager.create_relations(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID, relations
    )
    
    # Get insights
    insights = await memory_manager.get_client_insights(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID
    )
    
    # Verify insights structure
    assert insights["summary"]["total_entities"] == 10
    assert insights["summary"]["total_relations"] == 5
    assert insights["summary"]["total_observations"] >= 10
    
    # Check entity breakdown
    assert insights["entities_by_type"]["person"] == 7
    assert insights["entities_by_type"]["system"] == 3
    
    # Check recent activity
    assert len(insights["recent_entities"]) <= 5
    assert insights["recent_entities"][0]["entity_name"]  # Should have entity info

@pytest.mark.asyncio
async def test_duplicate_entity_handling(memory_manager, test_context):
    """Test that duplicate entities are handled correctly"""
# from sparkjar_crew.shared.schemas.memory_schemas import ...
    
    # Create initial entity
    entity = EntityCreate(
        name="Unique Entity",
        entityType="person",
        observations=[
            Observation(
                type="fact",
                value="Initial observation",
                source="test"
            )
        ]
    )
    
    created1 = await memory_manager.create_entities(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID, [entity]
    )
    assert len(created1) == 1
    initial_obs_count = len(created1[0]["observations"])
    
    # Try to create same entity again
    entity2 = EntityCreate(
        name="Unique Entity",  # Same name
        entityType="person",   # Same type
        observations=[
            Observation(
                type="fact",
                value="New observation",
                source="test"
            )
        ]
    )
    
    created2 = await memory_manager.create_entities(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID, [entity2]
    )
    
    # Should update existing entity, not create new one
    assert len(created2) == 1
    assert created2[0]["id"] == created1[0]["id"]  # Same entity ID
    assert len(created2[0]["observations"]) == initial_obs_count + 1  # Added observation

@pytest.mark.asyncio
async def test_error_handling_and_recovery(memory_manager, test_context, db_session):
    """Test error handling and transaction rollback"""
# from sparkjar_crew.shared.schemas.memory_schemas import ...
    
    # Test invalid relation (non-existent entities)
    with pytest.raises(Exception):
        await memory_manager.create_relations(
            TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID,
            [RelationCreate(
                from_entity_name="NonExistent1",
                to_entity_name="NonExistent2",
                relationType="invalid"
            )]
        )
    
    # Verify database is still functional after error
    test_entity = EntityCreate(
        name="Recovery Test",
        entityType="test",
        observations=[Observation(type="fact", value="Testing recovery", source="test")]
    )
    
    created = await memory_manager.create_entities(
        TEST_CLIENT_ID, TEST_ACTOR_TYPE, TEST_ACTOR_ID, [test_entity]
    )
    assert len(created) == 1  # Should work fine after previous error