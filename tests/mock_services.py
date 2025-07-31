import os


class MockEmbeddingService:
    """Simple embedding service mock returning zero vectors."""

    def __init__(self, dimension: int | None = None) -> None:
        self.dimension = dimension or int(os.getenv("EMBEDDING_DIMENSION", "768"))

    async def generate_embedding(self, text: str):
        return [0.0] * self.dimension

    async def generate_embeddings_batch(self, texts):
        return [[0.0] * self.dimension for _ in texts]

    def prepare_entity_text_from_data(
        self,
        entity_name: str,
        entity_type: str,
        observations: list[dict],
    ) -> str:
        text_parts = [f"Entity: {entity_name}", f"Type: {entity_type}"]
        for obs in observations:
            if isinstance(obs, dict):
                obs_type = obs.get("type", "general")
                obs_value = obs.get("value", "")
                obs_source = obs.get("source", "")
                text_parts.append(f"{obs_type}: {obs_value}")
                if obs_source and obs_source != "api":
                    text_parts.append(f"Source: {obs_source}")
                if "context" in obs and obs["context"]:
                    for key, value in obs["context"].items():
                        text_parts.append(f"{key}: {value}")
        return " | ".join(text_parts)
