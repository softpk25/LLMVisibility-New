"""FAISS vector store with Cosine similarity search"""

import os
import pickle
from typing import List, Tuple
import numpy as np
import faiss
from langchain_core.documents import Document


class FAISSVectorStore:
    """Handles vector storage and similarity search using FAISS with Cosine similarity"""

    def __init__(self, embedding_dimension: int, persist_directory: str = "data/embeddings"):
        """
        Initialize FAISS vector store

        Args:
            embedding_dimension: Dimension of embedding vectors
            persist_directory: Directory to save/load FAISS index
        """
        self.embedding_dimension = embedding_dimension
        self.persist_directory = persist_directory
        self.index = None
        self.documents = []
        self._initialize_index()

    def _initialize_index(self):
        """Initialize FAISS index with Cosine similarity (Inner Product on normalized vectors)"""
        # IndexFlatIP uses Inner Product, which equals cosine similarity for normalized vectors
        self.index = faiss.IndexFlatIP(self.embedding_dimension)

    @staticmethod
    def _normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
        """
        Normalize embeddings to unit length for cosine similarity

        Args:
            embeddings: Array of embeddings

        Returns:
            Normalized embeddings
        """
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        # Avoid division by zero
        norms = np.where(norms == 0, 1, norms)
        return embeddings / norms

    def add_documents(self, documents: List[Document], embeddings: List[List[float]]):
        """
        Add documents and their embeddings to the vector store

        Args:
            documents: List of Document objects
            embeddings: List of embedding vectors corresponding to documents

        Raises:
            ValueError: If documents and embeddings length mismatch
        """
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Number of documents ({len(documents)}) must match "
                f"number of embeddings ({len(embeddings)})"
            )

        if not documents:
            return

        # Convert embeddings to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)

        # Verify embedding dimension
        if embeddings_array.shape[1] != self.embedding_dimension:
            raise ValueError(
                f"Embedding dimension mismatch. Expected {self.embedding_dimension}, "
                f"got {embeddings_array.shape[1]}"
            )

        # Normalize embeddings for cosine similarity
        embeddings_array = self._normalize_embeddings(embeddings_array)

        # Add to FAISS index
        self.index.add(embeddings_array)

        # Store documents for retrieval
        self.documents.extend(documents)

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 3,
        min_score: float = 0.0
    ) -> List[Tuple[Document, float]]:
        """
        Search for most similar documents using Cosine similarity

        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return

        Returns:
            List of tuples (Document, similarity_score) sorted by similarity (higher score = more similar)
            Similarity scores range from -1 to 1, where 1 is identical and 0 is orthogonal

        Raises:
            ValueError: If no documents in index
        """
        if not self.documents:
            raise ValueError("No documents in vector store. Please add documents first.")

        if self.index.ntotal == 0:
            raise ValueError("FAISS index is empty. Please add documents first.")

        # Convert query to numpy array
        query_array = np.array([query_embedding], dtype=np.float32)

        # Verify query dimension
        if query_array.shape[1] != self.embedding_dimension:
            raise ValueError(
                f"Query embedding dimension mismatch. Expected {self.embedding_dimension}, "
                f"got {query_array.shape[1]}"
            )

        # Normalize query for cosine similarity
        query_array = self._normalize_embeddings(query_array)

        # Perform search - returns similarity scores and indices
        # Higher score = more similar for cosine similarity (inner product of normalized vectors)
        top_k = min(top_k, len(self.documents))
        scores, indices = self.index.search(query_array, top_k)

        # Retrieve documents with their similarity scores, filtering by min_score
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < len(self.documents) and float(score) >= min_score:
                results.append((self.documents[idx], float(score)))

        return results

    def save(self, index_name: str = "faiss_index"):
        """
        Save FAISS index and documents to disk

        Args:
            index_name: Name for the saved index files
        """
        if not os.path.exists(self.persist_directory):
            os.makedirs(self.persist_directory)

        # Save FAISS index
        index_path = os.path.join(self.persist_directory, f"{index_name}.faiss")
        faiss.write_index(self.index, index_path)

        # Save documents metadata
        docs_path = os.path.join(self.persist_directory, f"{index_name}_docs.pkl")
        with open(docs_path, 'wb') as f:
            pickle.dump(self.documents, f)

    def load(self, index_name: str = "faiss_index") -> bool:
        """
        Load FAISS index and documents from disk

        Args:
            index_name: Name of the saved index files

        Returns:
            True if loaded successfully, False otherwise
        """
        index_path = os.path.join(self.persist_directory, f"{index_name}.faiss")
        docs_path = os.path.join(self.persist_directory, f"{index_name}_docs.pkl")

        if not os.path.exists(index_path) or not os.path.exists(docs_path):
            return False

        try:
            # Load FAISS index
            self.index = faiss.read_index(index_path)

            # Load documents
            with open(docs_path, 'rb') as f:
                self.documents = pickle.load(f)

            return True
        except Exception:
            return False

    def clear(self):
        """Clear all documents and reset the index"""
        self._initialize_index()
        self.documents = []

    def get_stats(self) -> dict:
        """
        Get statistics about the vector store

        Returns:
            Dictionary with vector store statistics
        """
        return {
            "num_documents": len(self.documents),
            "num_vectors": self.index.ntotal,
            "embedding_dimension": self.embedding_dimension,
            "index_type": "FlatIP (Cosine similarity)"
        }
