from abc import ABC, abstractmethod
from typing import List
import random

class EmbeddingProvider(ABC):
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        pass
        
    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        pass

class MockEmbeddingProvider(EmbeddingProvider):
    """Mock provider for testing without API keys. Returns random vectors."""
    async def get_embedding(self, text: str) -> List[float]:
        return [random.random() for _ in range(768)]
        
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [[random.random() for _ in range(768)] for _ in texts]

class GeminiEmbeddingProvider(EmbeddingProvider):
    """Google Gemini Embedding Provider with auto-fallback to available models."""
    def __init__(self, api_key: str):
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.candidate_models = [
            'gemini-embedding-001',
            'gemini-embedding-2',
            'text-embedding-004',
            'models/gemini-embedding-001',
            'models/gemini-embedding-2'
        ]
        self.preferred_model = 'gemini-embedding-001'
        
    async def get_embedding(self, text: str) -> List[float]:
        for model_name in [self.preferred_model] + [m for m in self.candidate_models if m != self.preferred_model]:
            try:
                response = self.client.models.embed_content(
                    model=model_name,
                    contents=text,
                )
                if response and hasattr(response, 'embeddings') and response.embeddings:
                    self.preferred_model = model_name
                    return response.embeddings[0].values
            except Exception as e:
                continue
        
        # Fallback to local vector if API models aren't supported on current key
        print("Warning: Gemini Embedding models unavailable on key, using local vector fallback.")
        return [random.random() for _ in range(768)]

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        for model_name in [self.preferred_model] + [m for m in self.candidate_models if m != self.preferred_model]:
            try:
                response = self.client.models.embed_content(
                    model=model_name,
                    contents=texts,
                )
                if response and hasattr(response, 'embeddings') and response.embeddings:
                    self.preferred_model = model_name
                    return [emb.values for emb in response.embeddings]
            except Exception as e:
                continue
        
        print("Warning: Gemini Embeddings models unavailable on key, using local vectors fallback.")
        return [[random.random() for _ in range(768)] for _ in texts]

def get_embedding_provider(api_key: str = "") -> EmbeddingProvider:
    if not api_key or api_key.strip() in ["", "your_ai_api_key_here", "your_api_key_here"]:
        print("Warning: No valid AI_API_KEY provided, using MockEmbeddingProvider")
        return MockEmbeddingProvider()
    return GeminiEmbeddingProvider(api_key)
