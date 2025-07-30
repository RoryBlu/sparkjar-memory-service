"""
Test schema validation functionality for both memory and thinking services.
Tests the unified schema validator with real database operations.
"""
import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

# Test data
TEST_CLIENT_ID = uuid4()
TEST_ACTOR_ID = uuid4()

@pytest.mark.asyncio
async def test_memory_observation_validation(db_session):
    """Test validation of memory observations against schemas"""
    # TODO: Fix import - validator should be local
# from services.schema_validator import ...
    
    validator = MemorySchemaValidator(db_session)
    
    # Test valid skill observation
    skill_obs = {
        "type": "skill",
        "value": {
            "name": "Python Programming",
            "category": "technical",
            "level": "expert"
        },
        "source": "assessment"
    }
    
    result = await validator.validate_observation(skill_obs, "person")
    assert result.valid
    assert result.schema_used == "skill_observation"
    assert len(result.errors) == 0
    
    # Test invalid skill observation (missing required field)
    invalid_skill = {
        "type": "skill",
        "value": {
            "category": "technical"  # Missing 'name'
        },
        "source": "assessment"
    }
    
    result = await validator.validate_observation(invalid_skill, "person")
    assert not result.valid
    assert len(result.errors) > 0
    assert "name" in str(result.errors)
    
    # Test database reference observation
    db_ref_obs = {
        "type": "database_ref",
        "value": {
            "table_name": "crew_jobs",
            "record_id": str(uuid4()),
            "relationship_type": "created"
        },
        "source": "system"
    }
    
    result = await validator.validate_observation(db_ref_obs, "agent")
    assert result.valid
    assert result.schema_used == "database_ref_observation"
    
    # Test fallback to base observation
    generic_obs = {
        "type": "note",
        "value": "This is a general note",
        "source": "user"
    }
    
    result = await validator.validate_observation(generic_obs, "person")
    assert result.valid
    assert result.schema_used == "base_observation"

@pytest.mark.asyncio
async def test_entity_metadata_validation(db_session):
    """Test validation of entity metadata"""
    # TODO: Fix import - validator should be local
# from services.schema_validator import ...
    
    validator = MemorySchemaValidator(db_session)
    
    # Test person entity metadata
    person_metadata = {
        "role": "Software Engineer",
        "organization": "TechCorp",
        "email": "john.doe@techcorp.com",
        "expertise": ["Python", "Docker", "PostgreSQL"]
    }
    
    result = await validator.validate_entity_metadata(person_metadata, "person")
    assert result.valid
    assert result.schema_used == "person_entity_metadata"
    
    # Test synth entity metadata
    synth_metadata = {
        "agent_type": "crewai_agent",
        "model_name": "gpt-4",
        "capabilities": ["code_generation", "analysis", "planning"],
        "version": "1.0.0"
    }
    
    result = await validator.validate_entity_metadata(synth_metadata, "synth")
    assert result.valid
    assert result.schema_used == "synth_entity_metadata"
    
    # Test invalid email format
    invalid_person = {
        "email": "not-an-email",
        "role": "Developer"
    }
    
    result = await validator.validate_entity_metadata(invalid_person, "person")
    # Should still be valid as fields are optional, but may have warnings
    assert "email" in str(result.errors) or len(result.warnings) > 0

@pytest.mark.asyncio
async def test_thinking_session_validation(db_session):
    """Test validation of thinking session metadata"""
    # TODO: Fix import - validator should be local
# from services.schema_validator import ...
    
    validator = ThinkingSchemaValidator(db_session)
    
    # Test valid session metadata
    session_metadata = {
        "context": {
            "domain": "software_architecture",
            "task_type": "problem_solving",
            "complexity": "complex"
        },
        "goals": ["Design scalable API", "Ensure security"],
        "participants": [
            {"name": "John Doe", "role": "architect"},
            {"name": "AI Assistant", "role": "advisor"}
        ]
    }
    
    result = await validator.validate_session_metadata(session_metadata)
    assert result.valid
    assert result.schema_used == "thinking_session_metadata"
    
    # Test invalid task type
    invalid_session = {
        "context": {
            "task_type": "invalid_type"
        },
        "goals": []  # Empty goals
    }
    
    result = await validator.validate_session_metadata(invalid_session)
    assert not result.valid
    assert "task_type" in str(result.errors) or "goals" in str(result.errors)

@pytest.mark.asyncio
async def test_thought_metadata_validation(db_session):
    """Test validation of thought metadata"""
    # TODO: Fix import - validator should be local
# from services.schema_validator import ...
    
    validator = ThinkingSchemaValidator(db_session)
    
    # Test regular thought metadata
    thought_metadata = {
        "thought_type": "hypothesis",
        "confidence": 0.85,
        "reasoning_method": "deductive",
        "evidence": [
            {"source": "analysis", "strength": "strong"}
        ]
    }
    
    result = await validator.validate_thought_metadata(thought_metadata, is_revision=False)
    assert result.valid
    assert result.schema_used == "thought_metadata"
    
    # Test revision metadata
    revision_metadata = {
        "revision_type": "clarification",
        "revision_reason": "Added more detail to explain the concept",
        "changes_made": [
            {
                "aspect": "explanation",
                "rationale": "Original was too brief"
            }
        ]
    }
    
    result = await validator.validate_thought_metadata(revision_metadata, is_revision=True)
    assert result.valid
    assert result.schema_used == "revision_metadata"
    
    # Test invalid confidence value
    invalid_thought = {
        "thought_type": "conclusion",
        "confidence": 1.5  # Out of range
    }
    
    result = await validator.validate_thought_metadata(invalid_thought, is_revision=False)
    assert not result.valid
    assert "confidence" in str(result.errors)

@pytest.mark.asyncio
async def test_schema_caching(db_session):
    """Test that schema caching works correctly"""
    # TODO: Fix import - validator should be local
# from services.schema_validator import ...
    
    validator = MemorySchemaValidator(db_session)
    
    # Enable caching
    validator.enable_cache(True)
    
    # First call - should query database
    obs1 = {"type": "skill", "value": {"name": "Test"}, "source": "test"}
    result1 = await validator.validate_observation(obs1, "person")
    assert result1.valid
    
    # Check cache
    stats = validator.get_validation_stats()
    assert stats["cache_enabled"]
    assert stats["schemas_cached"] > 0
    
    # Second call - should use cache
    obs2 = {"type": "skill", "value": {"name": "Test2"}, "source": "test"}
    result2 = await validator.validate_observation(obs2, "person")
    assert result2.valid
    
    # Clear cache
    validator.clear_cache()
    stats = validator.get_validation_stats()
    assert stats["schemas_cached"] == 0

@pytest.mark.asyncio
async def test_batch_validation(db_session):
    """Test batch validation of multiple items"""
    # TODO: Fix import - validator should be local
# from services.schema_validator import ...
    
    validator = MemorySchemaValidator(db_session)
    
    # Create batch of observations with different schemas
    items = [
        ({"type": "skill", "value": {"name": "Python"}, "source": "test"}, "skill_observation"),
        ({"type": "fact", "value": "Works at TechCorp", "source": "profile"}, "base_observation"),
        ({"type": "database_ref", "value": {"table_name": "users", "record_id": str(uuid4()), "relationship_type": "created"}, "source": "system"}, "database_ref_observation")
    ]
    
    results = await validator.validate_batch(items, "memory_observation")
    
    assert len(results) == 3
    assert all(r.valid for r in results)
    assert results[0].schema_used == "skill_observation"
    assert results[1].schema_used == "base_observation"
    assert results[2].schema_used == "database_ref_observation"

@pytest.mark.asyncio
async def test_validation_metadata_storage(db_session):
    """Test that validation metadata is stored correctly"""
    # TODO: Fix import - validator should be local
# from services.schema_validator import ...
    
    validator = MemorySchemaValidator(db_session)
    
    obs = {
        "type": "skill",
        "value": {"name": "Testing", "category": "technical"},
        "source": "test"
    }
    
    result = await validator.validate_observation(obs, "person")
    metadata = result.to_dict()
    
    # Check required metadata fields
    assert "_schema_used" in metadata
    assert "_validated_at" in metadata
    assert "_validation_passed" in metadata
    assert metadata["_validation_passed"] == True
    assert metadata["_schema_used"] == "skill_observation"
    
    # Validate timestamp format
    timestamp = datetime.fromisoformat(metadata["_validated_at"])
    assert isinstance(timestamp, datetime)

@pytest.mark.asyncio
async def test_schema_not_found_handling(db_session):
    """Test handling when schema is not found"""
    # TODO: Fix import - validator should be local
# from services.schema_validator import ...
    
    validator = MemorySchemaValidator(db_session)
    
    # Use a type that doesn't have a schema
    unknown_obs = {
        "type": "unknown_type_xyz",
        "value": "Some value",
        "source": "test"
    }
    
    # Should fall back to base_observation
    result = await validator.validate_observation(unknown_obs, "person")
    assert result.valid  # Should still validate against base schema
    assert result.schema_used == "base_observation"

@pytest.mark.asyncio  
async def test_crew_request_validation(db_session):
    """Test validation of crew API requests"""
    # TODO: Fix import - validator should be local
# from services.schema_validator import ...
    
    validator = CrewSchemaValidator(db_session)
    
    # Test valid crew request with all core fields
    valid_request = {
        "job_key": "gen_crew",
        "client_user_id": str(uuid4()),
        "actor_type": "agent",
        "actor_id": str(uuid4()),
        "context": {
            "task": "Generate report"
        }
    }
    
    result = await validator.validate_crew_request(valid_request)
    # May not be valid if gen_crew schema doesn't exist, but core fields should pass
    assert len([e for e in result.errors if "core field" in e]) == 0
    
    # Test missing core field
    invalid_request = {
        "job_key": "test_crew",
        "client_user_id": str(uuid4())
        # Missing actor_type and actor_id
    }
    
    result = await validator.validate_crew_request(invalid_request)
    assert not result.valid
    assert "actor_type" in str(result.errors)
    assert "actor_id" in str(result.errors)
    
    # Test null core field
    null_request = {
        "job_key": "test_crew",
        "client_user_id": None,
        "actor_type": "agent",
        "actor_id": str(uuid4())
    }
    
    result = await validator.validate_crew_request(null_request)
    assert not result.valid
    assert "client_user_id" in str(result.errors)
    assert "cannot be null" in str(result.errors)