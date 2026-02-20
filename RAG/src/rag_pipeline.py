"""Main RAG pipeline orchestration"""

import os
import json
import yaml
from typing import List, Optional

from .pdf_processor import PDFProcessor
from .embedder import OllamaEmbedder
from .vector_store import FAISSVectorStore
from .generator import OllamaGenerator


class RAGPipeline:
    """Orchestrates the complete RAG workflow"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize RAG pipeline

        Args:
            config_path: Path to configuration YAML file. If None, uses default config.
        """
        self.config = self._load_config(config_path)
        self._initialize_components()

    def _load_config(self, config_path: Optional[str] = None) -> dict:
        """
        Load configuration from YAML file

        Args:
            config_path: Path to config file

        Returns:
            Configuration dictionary
        """
        if config_path is None:
            # Use default config path
            config_path = os.path.join("config", "config.yaml")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        return config

    def _initialize_components(self):
        """Initialize all RAG components"""
        # Initialize PDF processor
        self.pdf_processor = PDFProcessor(
            chunk_size=self.config['chunking']['chunk_size'],
            chunk_overlap=self.config['chunking']['chunk_overlap']
        )

        # Initialize embedder
        self.embedder = OllamaEmbedder(
            model_name=self.config['models']['embedding']['name']
        )

        # Get embedding dimension
        embedding_dim = self.embedder.get_embedding_dimension()

        # Initialize vector store
        self.vector_store = FAISSVectorStore(
            embedding_dimension=embedding_dim,
            persist_directory=self.config['vector_store']['persist_directory']
        )

        # Initialize generator
        self.generator = OllamaGenerator(
            model_name=self.config['models']['generation']['name'],
            temperature=self.config['models']['generation']['temperature'],
            max_tokens=self.config['models']['generation']['max_tokens']
        )

        # State tracking — loaded from disk on index load
        self.ingested_pdfs = []

    def _metadata_path(self) -> str:
        return os.path.join(
            self.config['vector_store']['persist_directory'],
            "metadata.json"
        )

    def _save_metadata(self):
        os.makedirs(self.config['vector_store']['persist_directory'], exist_ok=True)
        with open(self._metadata_path(), 'w') as f:
            json.dump({'ingested_pdfs': self.ingested_pdfs}, f, indent=2)

    def _load_metadata(self):
        path = self._metadata_path()
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                self.ingested_pdfs = data.get('ingested_pdfs', [])

    def ingest_pdf(self, pdf_path: str, save_index: bool = True) -> dict:
        """
        Ingest a PDF file into the RAG system

        Args:
            pdf_path: Path to PDF file
            save_index: Whether to save the FAISS index after ingestion

        Returns:
            Dictionary with ingestion statistics

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If ingestion fails
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        pdf_name = os.path.basename(pdf_path)

        # Block duplicate ingestion
        if pdf_name in self.ingested_pdfs:
            print(f"'{pdf_name}' is already ingested. Skipping.")
            print(f"  Run 'python main.py clear -y' first if you want to re-ingest it.")
            return {
                'pdf_file': pdf_name,
                'skipped': True,
                'reason': 'already_ingested'
            }

        print(f"Loading PDF: {pdf_path}")

        # Step 1: Load and chunk PDF
        chunks = self.pdf_processor.load_and_split_pdf(pdf_path)
        chunk_info = self.pdf_processor.get_chunk_info(chunks)

        print(f"Extracted {chunk_info['num_chunks']} chunks from {len(chunk_info['pages'])} pages")

        # Step 2: Generate embeddings
        print("Generating embeddings...")
        texts = [chunk.page_content for chunk in chunks]
        embeddings = self.embedder.embed_documents(texts)

        # Step 3: Add to vector store
        print("Adding to vector store...")
        self.vector_store.add_documents(chunks, embeddings)

        # Step 4: Save index and metadata if requested
        if save_index:
            print("Saving index...")
            self.vector_store.save()
            self.ingested_pdfs.append(pdf_name)
            self._save_metadata()

        # Return statistics
        stats = {
            'pdf_file': pdf_name,
            'skipped': False,
            'num_chunks': chunk_info['num_chunks'],
            'num_pages': len(chunk_info['pages']),
            'embedding_dimension': len(embeddings[0]) if embeddings else 0,
            'total_documents': len(self.vector_store.documents)
        }

        print(f"\nSuccessfully ingested {pdf_name}:")
        print(f"  - {stats['num_chunks']} chunks")
        print(f"  - {stats['num_pages']} pages")
        print(f"  - {stats['embedding_dimension']}-dimensional embeddings")

        return stats

    def query(self, question: str, top_k: Optional[int] = None) -> dict:
        """
        Query the RAG system

        Args:
            question: User's question
            top_k: Number of top documents to retrieve. If None, uses config value.

        Returns:
            Dictionary with answer and metadata

        Raises:
            ValueError: If no documents in vector store or question is empty
            Exception: If query fails
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        if not self.vector_store.documents:
            raise ValueError(
                "No documents in vector store. Please ingest a PDF first using ingest_pdf()."
            )

        if top_k is None:
            top_k = self.config['retrieval']['top_k']

        print(f"Processing query: {question}")

        # Step 1: Embed the query
        print("Generating query embedding...")
        query_embedding = self.embedder.embed_query(question)

        # Step 2: Retrieve similar documents
        min_score = self.config['retrieval'].get('min_score', 0.4)
        print(f"Searching for top {top_k} relevant chunks (min score: {min_score})...")
        similar_docs = self.vector_store.similarity_search(
            query_embedding, top_k=top_k, min_score=min_score
        )

        print(f"Retrieved {len(similar_docs)} chunks (similarity scores: {[f'{d:.3f}' for _, d in similar_docs]})")

        if not similar_docs:
            return {
                'answer': "I could not find any sufficiently relevant content in the document to answer this question.",
                'sources': [],
                'retrieved_chunks': [],
                'num_context_docs': 0,
                'model': self.config['models']['generation']['name']
            }

        # Step 3: Generate response
        print("Generating response...")
        response = self.generator.generate(question, similar_docs)

        # Add retrieval info to response
        response['retrieved_chunks'] = [
            {
                'page': doc.metadata.get('page', 'unknown'),
                'similarity_score': float(score),
                'preview': doc.page_content[:100] + '...' if len(doc.page_content) > 100 else doc.page_content
            }
            for doc, score in similar_docs
        ]

        return response

    def load_existing_index(self, index_name: str = "faiss_index") -> bool:
        """
        Load an existing FAISS index from disk

        Args:
            index_name: Name of the index to load

        Returns:
            True if loaded successfully, False otherwise
        """
        success = self.vector_store.load(index_name)

        if success:
            self._load_metadata()
            stats = self.vector_store.get_stats()
            print(f"Loaded existing index: {stats['num_documents']} documents")
            if self.ingested_pdfs:
                print(f"  Ingested PDFs: {', '.join(self.ingested_pdfs)}")
            return True
        else:
            print("No existing index found")
            return False

    def clear_index(self):
        """Clear all documents from the vector store"""
        self.vector_store.clear()
        self.ingested_pdfs = []
        # Remove saved metadata file
        meta_path = self._metadata_path()
        if os.path.exists(meta_path):
            os.remove(meta_path)
        print("Vector store cleared")

    def get_stats(self) -> dict:
        """
        Get statistics about the RAG system

        Returns:
            Dictionary with system statistics
        """
        vector_stats = self.vector_store.get_stats()

        return {
            'vector_store': vector_stats,
            'ingested_pdfs': self.ingested_pdfs,
            'config': {
                'chunk_size': self.config['chunking']['chunk_size'],
                'chunk_overlap': self.config['chunking']['chunk_overlap'],
                'top_k': self.config['retrieval']['top_k'],
                'embedding_model': self.config['models']['embedding']['name'],
                'generation_model': self.config['models']['generation']['name']
            }
        }

    def list_ingested_pdfs(self) -> List[str]:
        """
        Get list of ingested PDF files

        Returns:
            List of PDF filenames
        """
        return self.ingested_pdfs
