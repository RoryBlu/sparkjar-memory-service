"""
Integration tests for Sequential Thinking API endpoints.
Tests the full API layer including request/response validation.
"""
import pytest
import httpx
from uuid import uuid4
import sys
import os

from fastapi.testclient import TestClient
from internal_api import internal_app
from external_api import external_app

@pytest.fixture
def internal_client():
    """Create test client for internal API."""
    return TestClient(internal_app)

@pytest.fixture
def external_client():
    """Create test client for external API."""
    return TestClient(external_app)

@pytest.fixture
def test_user_id():
    """Generate a test user ID."""
    return str(uuid4())

@pytest.fixture
def auth_headers(external_client):
    """Get authentication headers for external API."""
    # In a real test, you'd use proper auth
    # For now, we'll skip auth for testing
    return {}

class TestThinkingAPIInternal:
    """Test internal API endpoints for Sequential Thinking."""
    
    def test_create_session(self, internal_client, test_user_id):
        """Test creating a session via API."""
        response = internal_client.post(
            "/api/v1/thinking/sessions",
            json={
                "client_user_id": test_user_id,
                "session_name": "API Test Session",
                "problem_statement": "Testing the API integration",
                "metadata": {"test": True}
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["client_user_id"] == test_user_id
        assert data["session_name"] == "API Test Session"
        assert data["status"] == "active"
        assert "id" in data
        
        return data["id"]
    
    def test_add_thought(self, internal_client, test_user_id):
        """Test adding thoughts via API."""
        # Create session
        session_response = internal_client.post(
            "/api/v1/thinking/sessions",
            json={"client_user_id": test_user_id}
        )
        session_id = session_response.json()["id"]
        
        # Add thought
        response = internal_client.post(
            f"/api/v1/thinking/sessions/{session_id}/thoughts",
            json={
                "thought_content": "This is my first thought",
                "metadata": {"confidence": 0.8}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["thought_number"] == 1
        assert data["thought_content"] == "This is my first thought"
        assert data["is_revision"] == False
    
    def test_revise_thought(self, internal_client, test_user_id):
        """Test revising thoughts via API."""
        # Create session and add thought
        session_response = internal_client.post(
            "/api/v1/thinking/sessions",
            json={"client_user_id": test_user_id}
        )
        session_id = session_response.json()["id"]
        
        internal_client.post(
            f"/api/v1/thinking/sessions/{session_id}/thoughts",
            json={"thought_content": "Original thought"}
        )
        
        # Revise thought
        response = internal_client.post(
            f"/api/v1/thinking/sessions/{session_id}/revise",
            json={
                "thought_number": 1,
                "revised_content": "Better version of the thought",
                "metadata": {"reason": "clarity"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["thought_number"] == 2
        assert data["is_revision"] == True
        assert data["revises_thought_number"] == 1
    
    def test_complete_session(self, internal_client, test_user_id):
        """Test completing a session via API."""
        # Create session
        session_response = internal_client.post(
            "/api/v1/thinking/sessions",
            json={"client_user_id": test_user_id}
        )
        session_id = session_response.json()["id"]
        
        # Complete session
        response = internal_client.post(
            f"/api/v1/thinking/sessions/{session_id}/complete",
            json={
                "final_answer": "The solution is to implement caching",
                "metadata": {"confidence": 0.9}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["final_answer"] == "The solution is to implement caching"
        assert "completed_at" in data
    
    def test_abandon_session(self, internal_client, test_user_id):
        """Test abandoning a session via API."""
        # Create session
        session_response = internal_client.post(
            "/api/v1/thinking/sessions",
            json={"client_user_id": test_user_id}
        )
        session_id = session_response.json()["id"]
        
        # Abandon session
        response = internal_client.post(
            f"/api/v1/thinking/sessions/{session_id}/abandon",
            json={
                "reason": "No longer relevant",
                "metadata": {"replaced_by": "new-project"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "abandoned"
        assert "completed_at" in data
    
    def test_get_session(self, internal_client, test_user_id):
        """Test retrieving a session via API."""
        # Create session with thoughts
        session_response = internal_client.post(
            "/api/v1/thinking/sessions",
            json={"client_user_id": test_user_id}
        )
        session_id = session_response.json()["id"]
        
        # Add thoughts
        for i in range(3):
            internal_client.post(
                f"/api/v1/thinking/sessions/{session_id}/thoughts",
                json={"thought_content": f"Thought {i+1}"}
            )
        
        # Get session
        response = internal_client.get(
            f"/api/v1/thinking/sessions/{session_id}?include_thoughts=true"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert len(data["thoughts"]) == 3
        assert data["thoughts"][0]["thought_content"] == "Thought 1"
    
    def test_list_sessions(self, internal_client, test_user_id):
        """Test listing sessions via API."""
        # Create multiple sessions
        for i in range(5):
            internal_client.post(
                "/api/v1/thinking/sessions",
                json={
                    "client_user_id": test_user_id,
                    "session_name": f"Session {i+1}"
                }
            )
        
        # List sessions
        response = internal_client.get(
            f"/api/v1/thinking/users/{test_user_id}/sessions?page=1&page_size=3"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 5
        assert len(data["sessions"]) == 3
        assert data["page"] == 1
        assert data["page_size"] == 3
    
    def test_get_session_stats(self, internal_client, test_user_id):
        """Test getting session statistics via API."""
        # Create session with activity
        session_response = internal_client.post(
            "/api/v1/thinking/sessions",
            json={"client_user_id": test_user_id}
        )
        session_id = session_response.json()["id"]
        
        # Add thoughts and revision
        internal_client.post(
            f"/api/v1/thinking/sessions/{session_id}/thoughts",
            json={"thought_content": "First thought"}
        )
        internal_client.post(
            f"/api/v1/thinking/sessions/{session_id}/thoughts",
            json={"thought_content": "Second thought"}
        )
        internal_client.post(
            f"/api/v1/thinking/sessions/{session_id}/revise",
            json={
                "thought_number": 1,
                "revised_content": "Revised first thought"
            }
        )
        
        # Get stats
        response = internal_client.get(
            f"/api/v1/thinking/sessions/{session_id}/stats"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_thoughts"] == 3
        assert data["revision_count"] == 1
        assert data["revised_thought_numbers"] == [1]
    
    def test_error_handling(self, internal_client, test_user_id):
        """Test API error handling."""
        # Test 404 - session not found
        response = internal_client.get(
            f"/api/v1/thinking/sessions/{uuid4()}"
        )
        assert response.status_code == 404
        
        # Test 400 - invalid request
        response = internal_client.post(
            "/api/v1/thinking/sessions",
            json={"invalid": "data"}
        )
        assert response.status_code == 422  # FastAPI validation error
        
        # Test adding thought to non-existent session
        response = internal_client.post(
            f"/api/v1/thinking/sessions/{uuid4()}/thoughts",
            json={"thought_content": "Test"}
        )
        assert response.status_code == 400
        
        # Test invalid pagination
        response = internal_client.get(
            f"/api/v1/thinking/users/{test_user_id}/sessions?page=0"
        )
        assert response.status_code == 400
    
    def test_health_check(self, internal_client):
        """Test health check endpoint."""
        response = internal_client.get("/api/v1/thinking/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "sequential-thinking"

class TestThinkingAPIExternal:
    """Test external API endpoints (with auth)."""
    
    def test_external_api_requires_auth(self, external_client):
        """Test that external API requires authentication."""
        # Without auth, should fail
        response = external_client.post(
            "/api/v1/thinking/sessions",
            json={"client_user_id": str(uuid4())}
        )
        
        # FastAPI might return 422 for missing dependencies
        # or the actual auth middleware might return 401/403
        # This depends on the auth implementation
        assert response.status_code in [401, 403, 422]
    
    def test_health_check_no_auth(self, external_client):
        """Test that health check doesn't require auth."""
        response = external_client.get("/api/v1/thinking/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"