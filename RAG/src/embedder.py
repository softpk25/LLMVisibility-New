"""BGE-M3 embedding generation via Ollama"""

from typing import List
from langchain_ollama import OllamaEmbeddings
import ollama


class OllamaEmbedder:
    """Handles text embedding using BGE-M3 via Ollama"""

    def __init__(self, model_name: str = "bge-m3:latest"):
        """
        Initialize Ollama embedder

        Args:
            model_name: Name of the Ollama embedding model
        """
        self.model_name = model_name
        self.embeddings = OllamaEmbeddings(model=model_name)
        self._verify_ollama_connection()

    def _verify_ollama_connection(self):
        """
        Verify that Ollama is running and model is available

        Raises:
            ConnectionError: If Ollama is not accessible
            ValueError: If the specified model is not available
        """
        try:
            # List available models
            response = ollama.list()

            # Extract model names from response
            model_names = []
            if hasattr(response, 'models'):
                # ListResponse object with models attribute
                for model in response.models:
                    if hasattr(model, 'model'):
                        model_names.append(model.model)
            elif isinstance(response, dict) and 'models' in response:
                # Dict response (older version)
                for model in response['models']:
                    if isinstance(model, dict) and 'name' in model:
                        model_names.append(model['name'])

            if not model_names:
                raise ValueError("No models found in Ollama. Please pull models first.")

            if self.model_name not in model_names:
                raise ValueError(
                    f"Model '{self.model_name}' not found in Ollama. "
                    f"Available models: {', '.join(model_names)}"
                )

        except ValueError:
            raise
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Ollama. Make sure Ollama is running. Error: {str(e)}"
            )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (each vector is a list of floats)

        Raises:
            Exception: If embedding generation fails
        """
        if not texts:
            return []

        try:
            embeddings = self.embeddings.embed_documents(texts)
            return embeddings
        except Exception as e:
            raise Exception(f"Failed to generate embeddings: {str(e)}")

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query

        Args:
            text: Query text to embed

        Returns:
            Embedding vector as a list of floats

        Raises:
            Exception: If embedding generation fails
        """
        if not text:
            raise ValueError("Query text cannot be empty")

        try:
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            raise Exception(f"Failed to generate query embedding: {str(e)}")

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by the model

        Returns:
            Dimension of embedding vectors
        """
        try:
            # Generate a test embedding to determine dimension
            test_embedding = self.embed_query("test")
            return len(test_embedding)
        except Exception:
            # BGE-M3 default dimension
            return 768
