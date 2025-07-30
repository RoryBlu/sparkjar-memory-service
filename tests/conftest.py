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