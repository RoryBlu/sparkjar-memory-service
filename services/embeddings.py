# services/memory-service/services/embeddings.py
from typing import List, Dict, Any, Optional
import httpx
import asyncio
from datetime import datetime
import os
from enum import Enum

class EmbeddingProvider(Enum):
    """Enum for embedding providers"""
    CUSTOM = "custom"
    OPENAI = "openai"

class EmbeddingService:
    """Service for generating embeddings using custom or OpenAI embedding servers"""
    
    def __init__(
        self, 
        api_url: Optional[str] = None, 
        model: Optional[str] = None, 
        dimension: Optional[int] = None,
        provider: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ):
        # Determine provider from environment or parameter
        self.provider = EmbeddingProvider(provider or os.getenv("EMBEDDING_PROVIDER", "custom"))
        
        if self.provider == EmbeddingProvider.OPENAI:
            self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            self.model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            self.dimension = int(os.getenv("OPENAI_EMBEDDING_DIMENSION", "1536"))
            self.api_url = "https://api.openai.com/v1/embeddings"
            if not self.api_key:
                raise ValueError("OpenAI API key required when using OpenAI provider")
        else:
            # Custom provider (default)
            self.api_url = api_url or os.getenv("EMBEDDINGS_API_URL", "http://embeddings.railway.internal")
            self.model = model or os.getenv("EMBEDDING_MODEL", "Alibaba-NLP/gte-multilingual-base")
            self.dimension = dimension or int(os.getenv("EMBEDDING_DIMENSION", "768"))
            self.api_key = None
        
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text using configured provider"""
        if self.provider == EmbeddingProvider.OPENAI:
            return await self._generate_openai_embedding(text)
        else:
            return await self._generate_custom_embedding(text)
    
    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "input": text,
                        "encoding_format": "float"
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                if "data" in result and len(result["data"]) > 0:
                    return result["data"][0]["embedding"]
                else:
                    raise ValueError(f"Unexpected OpenAI embedding response format: {result}")
                    
            except httpx.RequestError as e:
                # OpenAI API request failed
                return [0.0] * self.dimension
            except Exception as e:
                # OpenAI embedding generation error
                return [0.0] * self.dimension
    
    async def _generate_custom_embedding(self, text: str) -> List[float]:
        """Generate embedding using custom embedding server"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/embeddings",
                    json={
                        "model": self.model,
                        "input": text
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                # Handle different response formats
                if "data" in result and len(result["data"]) > 0:
                    return result["data"][0]["embedding"]
                elif "embedding" in result:
                    return result["embedding"]
                else:
                    raise ValueError(f"Unexpected custom embedding response format: {result}")
                    
            except httpx.RequestError as e:
                # Custom embedding service request failed
                return [0.0] * self.dimension
            except Exception as e:
                # Custom embedding generation error
                return [0.0] * self.dimension
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        tasks = [self.generate_embedding(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    def prepare_entity_text(self, entity: Any) -> str:
        """Prepare entity text for embedding generation"""
        text_parts = [
            f"Entity: {entity.entity_name}",
            f"Type: {entity.entity_type}"
        ]
        
        # Add observations
        if entity.observations:
            for obs in entity.observations:
                if isinstance(obs, dict):
                    obs_type = obs.get('type', 'general')
                    obs_value = obs.get('value', '')
                    obs_source = obs.get('source', '')
                    
                    text_parts.append(f"{obs_type}: {obs_value}")
                    if obs_source:
                        text_parts.append(f"Source: {obs_source}")
        
        # Add metadata if relevant
        if hasattr(entity, 'metadata_json') and entity.metadata_json:
            for key, value in entity.metadata_json.items():
                if not key.startswith('_'):  # Skip internal keys
                    text_parts.append(f"{key}: {value}")
        
        return " | ".join(text_parts)
    
    def prepare_entity_text_from_data(
        self, 
        entity_name: str, 
        entity_type: str, 
        observations: List[Dict[str, Any]]
    ) -> str:
        """Prepare entity text from raw data for embedding generation"""
        text_parts = [
            f"Entity: {entity_name}",
            f"Type: {entity_type}"
        ]
        
        # Add observations
        for obs in observations:
            if isinstance(obs, dict):
                obs_type = obs.get('type', 'general')
                obs_value = obs.get('value', '')
                obs_source = obs.get('source', '')
                
                text_parts.append(f"{obs_type}: {obs_value}")
                if obs_source and obs_source != 'api':
                    text_parts.append(f"Source: {obs_source}")
                    
                # Add context if available
                if 'context' in obs and obs['context']:
                    for key, value in obs['context'].items():
                        text_parts.append(f"{key}: {value}")
        
        return " | ".join(text_parts)