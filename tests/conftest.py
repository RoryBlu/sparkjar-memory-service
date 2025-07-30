# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

"""Pytest configuration for memory service tests."""

import pytest


# Basic fixtures that don't depend on sparkjar_crew
@pytest.fixture
def test_client_id():
    """Provide a test client ID."""
    return "test-client-123"

@pytest.fixture
def test_context():
    """Provide basic test context."""
    return {
        # "client_id" removed - use actor_id when actor_type="client"
        "actor_type": "test",
        "actor_id": "test-actor-123"
    }
import os
from tests.mock_services import MockEmbeddingService

@pytest.fixture(autouse=True)
def set_test_environment(monkeypatch):
    """Set minimal environment so config loads without external services."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SUPABASE_URL", "http://example.com")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test-key")
    monkeypatch.setenv("SECRET_KEY", "x" * 32)
    monkeypatch.setenv("SKIP_CONFIG_VALIDATION", "true")
    monkeypatch.setenv("EMBEDDINGS_API_URL", "http://embeddings.test")
    yield

@pytest.fixture
def mock_embedding_service():
    """Provide a mock embedding service that avoids network calls."""
    return MockEmbeddingService()

@pytest.fixture(autouse=True)
def cleanup_orphaned_data():
    """Cleanup hook that would remove test data from the database."""
    yield
    # In real tests this would delete from DB. Here we simply log for clarity.
    print("Cleaning up test data...")

