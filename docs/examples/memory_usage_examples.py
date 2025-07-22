
import logging
logger = logging.getLogger(__name__)

"""
Examples of using the memory service with properly validated observations
"""

# Example 1: Creating a person entity with skill observations
person_entity = {
    "name": "John Doe",
    "entityType": "person",
    "observations": [
        {
            "type": "skill",
            "value": "Python Programming",
            "skill_name": "Python Programming",
            "skill_category": "technical",
            "proficiency_level": "expert",
            "source": "code_review",
            "confidence": 0.95,
            "tags": ["programming", "backend"]
        },
        {
            "type": "fact",
            "value": "Works at SparkJar as Senior Engineer",
            "source": "profile",
            "confidence": 1.0
        },
        {
            "type": "database_ref",
            "value": {
                "table": "client_users",
                "id": "123e4567-e89b-12d3-a456-426614174000"
            },
            "relationship_type": "referenced",
            "source": "system"
        }
    ],
    "metadata": {
        "role": "Senior Engineer",
        "organization": "SparkJar",
        "email": "john.doe@sparkjar.com",
        "relationship": "colleague",
        "expertise": ["Python", "FastAPI", "PostgreSQL"]
    }
}

# Example 2: Creating a synth entity with capabilities
synth_entity = {
    "name": "Research Assistant Bot",
    "entityType": "synth",
    "observations": [
        {
            "type": "skill",
            "value": "Web Research",
            "skill_name": "Web Research",
            "skill_category": "analytical",
            "proficiency_level": "advanced",
            "source": "performance_metrics"
        },
        {
            "type": "fact",
            "value": "Specialized in market research and competitor analysis",
            "source": "configuration"
        }
    ],
    "metadata": {
        "agent_type": "crewai_agent",
        "model_name": "gpt-4",
        "version": "1.0.0",
        "capabilities": ["web_search", "data_analysis", "report_generation"]
    }
}

# Example 3: Writing pattern observations
writing_pattern_obs = {
    "entityName": "John Doe",
    "contents": [
        {
            "type": "writing_pattern",
            "value": "Uses bullet points for technical documentation",
            "pattern_type": "structure",
            "content_type": "documentation",
            "frequency": "always",
            "source": "content_analysis",
            "confidence": 0.9
        },
        {
            "type": "writing_pattern",
            "value": "Prefers active voice in emails",
            "pattern_type": "style",
            "content_type": "email",
            "frequency": "usually",
            "description": "Tends to use active voice for clarity and directness",
            "source": "email_analysis"
        }
    ]
}

# Example 4: Creating relationships
relationships = [
    {
        "from_entity_name": "John Doe",
        "to_entity_name": "Research Assistant Bot",
        "relationType": "manages",
        "metadata": {
            "since": "2024-01-15",
            "interaction_frequency": "daily"
        }
    },
    {
        "from_entity_name": "Research Assistant Bot",
        "to_entity_name": "Market Analysis Project",
        "relationType": "works_on",
        "metadata": {
            "role": "primary_researcher",
            "hours_per_week": 20
        }
    }
]

# Example 5: Searching memory with semantic queries
search_queries = [
    {
        "query": "who knows Python programming",
        "entity_type": "person",
        "limit": 5
    },
    {
        "query": "AI agents that can do research",
        "entity_type": "synth",
        "limit": 10
    },
    {
        "query": "writing patterns for technical documentation",
        "limit": 20,
        "threshold": 0.8
    }
]

# Example API calls using httpx
import httpx
import asyncio

async def example_memory_operations():
    # For internal API (high performance, no auth)
    internal_url = "http://[::1]:8001"
    
    # For external API (with auth)
    external_url = "https://localhost:8443"
    token = "your-jwt-token-here"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(verify=False) as client:
        # Create entities
        response = await client.post(
            f"{external_url}/memory/entities",
            json=[person_entity, synth_entity],
            headers=headers
        )
        logger.info(f"Created entities: {response.status_code}")
        
        # Add observations
        response = await client.post(
            f"{external_url}/memory/observations",
            json=[writing_pattern_obs],
            headers=headers
        )
        logger.info(f"Added observations: {response.status_code}")
        
        # Create relationships
        response = await client.post(
            f"{external_url}/memory/relations",
            json=relationships,
            headers=headers
        )
        logger.info(f"Created relations: {response.status_code}")
        
        # Search memory
        response = await client.post(
            f"{external_url}/memory/search",
            json=search_queries[0],
            headers=headers
        )
        results = response.json()
        logger.info(f"Search results: {len(results)} matches")

# Run example
if __name__ == "__main__":
    asyncio.run(example_memory_operations())