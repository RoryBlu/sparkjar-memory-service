"""
Configuration for memory validation tests.

This file provides fixtures and configuration specific to memory validation
tests without requiring sys.path manipulation.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# Import from the parent conftest
from ..conftest import *  # noqa: F401,F403

@pytest.fixture
def memory_service_config():
    """Provide memory service configuration for testing."""
    return {
        "external_api_url": os.getenv("MEMORY_SERVICE_URL", "http://localhost:8002"),
        "internal_api_url": os.getenv("MEMORY_INTERNAL_URL", "http://localhost:8003"),
        "database_url": os.getenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db"),
        "test_mode": True
    }

@pytest.fixture
def mock_memory_service():
    """Provide a mock memory service for testing."""
    mock_service = MagicMock()
    mock_service.health_check.return_value = {"status": "healthy"}
    return mock_service

@pytest.fixture
def validation_test_data():
    """Provide test data for validation tests."""
    return {
        "test_entity": {
            "entity_name": "test_entity",
            "entity_type": "test_type",
            "metadata": {"test": "data"}
        },
        "test_memory": {
            "content": "Test memory content",
            "context": "test_context",
            "importance": 0.8
        }
    }