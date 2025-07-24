# tests/test_observation_validation.py
import pytest
import sys
import os

from services.memory_manager import MemoryManager

class TestObservationValidation:
    """Test observation validation against schemas"""
    
    def test_skill_observation_validation(self, memory_manager):
        """Test skill observation validation"""
        observations = [
            {
                "type": "skill",
                "value": "Python Programming",
                "skill_name": "Python Programming",
                "skill_category": "technical",
                "proficiency_level": "expert",
                "source": "assessment"
            }
        ]
        
        validated = memory_manager._validate_observations(observations, "person")
        
        assert len(validated) == 1
        assert validated[0]["_schema_used"] == "skill_observation"
        assert validated[0]["_validation_passed"] == True
    
    def test_invalid_skill_category(self, memory_manager):
        """Test validation fails for invalid skill category"""
        observations = [
            {
                "type": "skill",
                "value": "Python",
                "skill_name": "Python",
                "skill_category": "invalid_category",  # Not in enum
                "proficiency_level": "expert"
            }
        ]
        
        validated = memory_manager._validate_observations(observations, "person")
        
        assert len(validated) == 1
        assert validated[0]["_validation_passed"] == False
        assert "_validation_error" in validated[0]
    
    def test_database_ref_observation(self, memory_manager):
        """Test database reference observation validation"""
        observations = [
            {
                "type": "database_ref",
                "value": {
                    "table": "client_users",
                    "id": "123e4567-e89b-12d3-a456-426614174000"
                },
                "relationship_type": "created",
                "source": "system"
            }
        ]
        
        validated = memory_manager._validate_observations(observations, "person")
        
        assert len(validated) == 1
        assert validated[0]["_schema_used"] == "database_ref_observation"
        assert validated[0]["_validation_passed"] == True
    
    def test_invalid_uuid_format(self, memory_manager):
        """Test validation fails for invalid UUID format"""
        observations = [
            {
                "type": "database_ref",
                "value": {
                    "table": "client_users",
                    "id": "not-a-valid-uuid"
                },
                "relationship_type": "created"
            }
        ]
        
        validated = memory_manager._validate_observations(observations, "person")
        
        assert len(validated) == 1
        assert validated[0]["_validation_passed"] == False
    
    def test_writing_pattern_observation(self, memory_manager):
        """Test writing pattern observation validation"""
        observations = [
            {
                "type": "writing_pattern",
                "value": "Uses bullet points",
                "pattern_type": "structure",
                "content_type": "documentation",
                "frequency": "always",
                "source": "analysis"
            }
        ]
        
        validated = memory_manager._validate_observations(observations, "person")
        
        assert len(validated) == 1
        assert validated[0]["_schema_used"] == "writing_pattern_observation"
        assert validated[0]["_validation_passed"] == True
    
    def test_base_observation_fallback(self, memory_manager):
        """Test fallback to base observation schema"""
        observations = [
            {
                "type": "custom_type",
                "value": "Some custom observation",
                "source": "user",
                "confidence": 0.8
            }
        ]
        
        validated = memory_manager._validate_observations(observations, "person")
        
        assert len(validated) == 1
        assert validated[0]["_schema_used"] == "base_observation"
        assert validated[0]["_validation_passed"] == True
    
    def test_missing_required_fields(self, memory_manager):
        """Test validation fails when required fields are missing"""
        observations = [
            {
                "type": "skill",
                # Missing required fields: skill_name, skill_category
                "value": "Python"
            }
        ]
        
        validated = memory_manager._validate_observations(observations, "person")
        
        assert len(validated) == 1
        # Should still be stored but with validation error
        assert validated[0]["_validation_passed"] == False
        assert "_validation_error" in validated[0]
    
    def test_entity_metadata_validation(self, memory_manager):
        """Test entity metadata validation"""
        # Test person metadata
        person_metadata = {
            "role": "Senior Engineer",
            "organization": "TechCorp",
            "email": "john@techcorp.com",
            "relationship": "colleague"
        }
        
        validated = memory_manager._validate_entity_metadata(person_metadata, "person")
        assert validated["_validation_passed"] == True
        assert validated["_schema_used"] == "person_entity_metadata"
        
        # Test synth metadata
        synth_metadata = {
            "agent_type": "crewai_agent",
            "model_name": "gpt-4",
            "capabilities": ["search", "analysis"]
        }
        
        validated = memory_manager._validate_entity_metadata(synth_metadata, "synth")
        assert validated["_validation_passed"] == True
        assert validated["_schema_used"] == "synth_entity_metadata"
    
    def test_invalid_email_format(self, memory_manager):
        """Test validation fails for invalid email format"""
        metadata = {
            "role": "Engineer",
            "email": "not-an-email"  # Invalid format
        }
        
        validated = memory_manager._validate_entity_metadata(metadata, "person")
        assert validated["_validation_passed"] == False
        assert "_validation_error" in validated
    
    def test_batch_observation_validation(self, memory_manager):
        """Test validating multiple observations of different types"""
        observations = [
            {
                "type": "skill",
                "value": "Python",
                "skill_name": "Python",
                "skill_category": "technical",
                "proficiency_level": "expert"
            },
            {
                "type": "fact",
                "value": "Works at TechCorp",
                "source": "profile"
            },
            {
                "type": "writing_pattern",
                "value": "Prefers markdown",
                "pattern_type": "preference",
                "content_type": "documentation",
                "frequency": "always"
            }
        ]
        
        validated = memory_manager._validate_observations(observations, "person")
        
        assert len(validated) == 3
        assert validated[0]["_schema_used"] == "skill_observation"
        assert validated[1]["_schema_used"] == "base_observation"
        assert validated[2]["_schema_used"] == "writing_pattern_observation"
        
        # All should pass validation
        for obs in validated:
            assert obs["_validation_passed"] == True