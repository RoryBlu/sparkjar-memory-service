class MockEmbeddingService:
    """Simple embedding service mock returning fixed vectors."""

    async def generate_embedding(self, text: str):
        return [0.0] * 768

    async def generate_embeddings_batch(self, texts):
        return [[0.0] * 768 for _ in texts]
