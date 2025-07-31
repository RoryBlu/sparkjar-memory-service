# services/memory-service/services/embeddings.py
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

class EmbeddingService:
    """Simplified embedding service returning zero vectors."""

    def __init__(self, dimension: Optional[int] = None) -> None:
        self.dimension = dimension or int(os.getenv("EMBEDDING_DIMENSION", "768"))
        
    async def generate_embedding(self, text: str) -> List[float]:
        """Return a zero vector embedding."""
        return [0.0] * self.dimension

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Return zero vectors for each input text."""
        return [[0.0] * self.dimension for _ in texts]
    
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