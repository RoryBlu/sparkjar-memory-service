# tests/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
import sys
import os
from uuid import uuid4
import jwt
from datetime import datetime, timedelta

# Import after path setup
import internal_api
import external_api
from config import settings

class TestInternalAPI:
    """Test internal API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client for internal API"""
        return TestClient(internal_api.internal_app)
    
    def test_create_entities(self, client):
        """Test entity creation endpoint"""
        request_data = {
            "client_id": str(uuid4()),
            "actor_type": "human",
            "actor_id": str(uuid4()),
            "entities": [
                {
                    "name": "Test Entity",
                    "entityType": "person",
                    "observations": [
                        {
                            "type": "fact",
                            "value": "Test observation",
                            "source": "test"
                        }
                    ]
                }
            ]
        }
        
        response = client.post("/entities", json=request_data)
        assert response.status_code == 200
        
        result = response.json()
        assert len(result) == 1
        assert result[0]["entity_name"] == "Test Entity"
    
    def test_search_entities(self, client):
        """Test search endpoint"""
        # First create an entity
        create_request = {
            "client_id": str(uuid4()),
            "actor_type": "human",
            "actor_id": str(uuid4()),
            "entities": [
                {
                    "name": "Search Test Entity",
                    "entityType": "person",
                    "observations": [
                        {
                            "type": "skill",
                            "value": "Python Programming",
                            "skill_name": "Python Programming",
                            "skill_category": "technical",
                            "proficiency_level": "expert"
                        }
                    ]
                }
            ]
        }
        
        client.post("/entities", json=create_request)
        
        # Now search
        search_request = {
            "client_id": create_request["client_id"],
            "actor_type": create_request["actor_type"],
            "actor_id": create_request["actor_id"],
            "query": "Python",
            "limit": 10,
            "threshold": 0.1
        }
        
        response = client.post("/search", json=search_request)
        assert response.status_code == 200
        
        results = response.json()
        assert isinstance(results, list)
    
    def test_add_observations(self, client):
        """Test adding observations to existing entity"""
        context = {
            "client_id": str(uuid4()),
            "actor_type": "human",
            "actor_id": str(uuid4())
        }
        
        # Create entity first
        create_request = {
            **context,
            "entities": [
                {
                    "name": "Observation Test",
                    "entityType": "person",
                    "observations": [
                        {
                            "type": "fact",
                            "value": "Initial observation"
                        }
                    ]
                }
            ]
        }
        
        client.post("/entities", json=create_request)
        
        # Add observations
        add_request = {
            **context,
            "observations": [
                {
                    "entityName": "Observation Test",
                    "contents": [
                        {
                            "type": "fact",
                            "value": "New observation"
                        }
                    ]
                }
            ]
        }
        
        response = client.post("/observations", json=add_request)
        assert response.status_code == 200
        
        result = response.json()
        assert result[0]["addedObservations"] == 1
        assert result[0]["totalObservations"] == 2

class TestExternalAPI:
    """Test external API endpoints with authentication"""
    
    @pytest.fixture
    def client(self):
        """Create test client for external API"""
        return TestClient(external_api.external_app)
    
    @pytest.fixture
    def auth_token(self):
        """Generate a valid JWT token for testing"""
        payload = {
            "client_id": str(uuid4()),
            "actor_type": "human",
            "actor_id": str(uuid4()),
            "exp": (datetime.utcnow() + timedelta(minutes=30)).timestamp()
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Create authorization headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_health_check(self, client):
        """Test health check endpoint (no auth required)"""
        response = client.get("/health")
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "healthy"
    
    def test_unauthorized_access(self, client):
        """Test that endpoints require authentication"""
        response = client.post("/memory/entities", json=[])
        assert response.status_code == 403  # Forbidden without auth
    
    def test_create_entities_with_auth(self, client, auth_headers):
        """Test authenticated entity creation"""
        # Mock the internal API call
        # In real tests, you'd use a mock or test double
        entities = [
            {
                "name": "Auth Test Entity",
                "entityType": "person",
                "observations": [
                    {
                        "type": "fact",
                        "value": "Authenticated creation"
                    }
                ]
            }
        ]
        
        # This will fail because internal API isn't running
        # In a real test, you'd mock the httpx call
        response = client.post("/memory/entities", json=entities, headers=auth_headers)
        # We expect 503 because internal service isn't available
        assert response.status_code == 503
    
    def test_token_generation(self, client):
        """Test JWT token generation endpoint"""
        request_data = {
            "client_id": str(uuid4()),
            "actor_type": "synth",
            "actor_id": str(uuid4()),
            "api_key": settings.SECRET_KEY  # In dev, using secret key
        }
        
        response = client.post("/auth/token", json=request_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "access_token" in result
        assert result["token_type"] == "bearer"
        assert result["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    def test_expired_token(self, client):
        """Test that expired tokens are rejected"""
        # Create expired token
        payload = {
            "client_id": str(uuid4()),
            "actor_type": "human",
            "actor_id": str(uuid4()),
            "exp": (datetime.utcnow() - timedelta(minutes=1)).timestamp()  # Expired
        }
        
        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.post("/memory/entities", json=[], headers=headers)
        assert response.status_code == 401  # Unauthorized
        assert "expired" in response.json()["detail"].lower()