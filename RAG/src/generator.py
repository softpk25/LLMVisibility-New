"""Llama3 response generation via Ollama"""

from typing import List, Tuple
import ollama
from langchain_core.documents import Document


class OllamaGenerator:
    """Handles response generation using Llama3 via Ollama"""

    def __init__(
        self,
        model_name: str = "llama3:latest",
        temperature: float = 0.7,
        max_tokens: int = 512
    ):
        """
        Initialize Ollama generator

        Args:
            model_name: Name of the Ollama generation model
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
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

    def _create_prompt(self, question: str, context_docs: List[Tuple[Document, float]]) -> str:
        """
        Create RAG prompt with context and question

        Args:
            question: User's question
            context_docs: List of (Document, similarity_score) tuples from retrieval

        Returns:
            Formatted prompt string
        """
        # Extract and format context from documents
        context_parts = []
        for idx, (doc, score) in enumerate(context_docs, 1):
            page = doc.metadata.get('page', 'unknown')
            content = doc.page_content.strip()
            context_parts.append(f"[Excerpt {idx} | Page {page} | Relevance: {score:.2f}]:\n{content}")

        context = "\n\n---\n\n".join(context_parts)

        prompt = f"""You are a precise document assistant. Your job is to answer questions using ONLY the excerpts provided below.

INSTRUCTIONS:
- Read all excerpts carefully before answering.
- Extract specific facts, numbers, and values directly from the text — do not paraphrase vaguely.
- If an excerpt contains a partial answer, use it and note which page it came from.
- If the excerpts genuinely do not contain relevant information, say: "The document does not cover this."
- Do NOT say information is missing if it appears anywhere in the excerpts, even partially.
- Cite page numbers inline, e.g. (Page 3).

EXCERPTS FROM DOCUMENT:
{context}

QUESTION: {question}

ANSWER:"""

        return prompt

    def generate(
        self,
        question: str,
        context_docs: List[Tuple[Document, float]]
    ) -> dict:
        """
        Generate response using Llama3 with RAG context

        Args:
            question: User's question
            context_docs: List of (Document, distance) tuples from retrieval

        Returns:
            Dictionary with response and metadata

        Raises:
            ValueError: If question is empty or no context provided
            Exception: If generation fails
        """
        if not question:
            raise ValueError("Question cannot be empty")

        if not context_docs:
            raise ValueError("No context documents provided for generation")

        try:
            # Create RAG prompt
            prompt = self._create_prompt(question, context_docs)

            # Generate response using Ollama
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens
                }
            )

            # Extract relevant information
            answer = response.get('response', '').strip()

            # Extract source pages
            source_pages = sorted(set(
                doc.metadata.get('page', 'unknown')
                for doc, _ in context_docs
            ))

            return {
                'answer': answer,
                'sources': source_pages,
                'num_context_docs': len(context_docs),
                'model': self.model_name
            }

        except Exception as e:
            raise Exception(f"Failed to generate response: {str(e)}")

    def generate_stream(
        self,
        question: str,
        context_docs: List[Tuple[Document, float]]
    ):
        """
        Generate response with streaming (for real-time output)

        Args:
            question: User's question
            context_docs: List of (Document, distance) tuples from retrieval

        Yields:
            Response chunks as they are generated

        Raises:
            ValueError: If question is empty or no context provided
            Exception: If generation fails
        """
        if not question:
            raise ValueError("Question cannot be empty")

        if not context_docs:
            raise ValueError("No context documents provided for generation")

        try:
            # Create RAG prompt
            prompt = self._create_prompt(question, context_docs)

            # Generate response with streaming
            stream = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                stream=True,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens
                }
            )

            for chunk in stream:
                yield chunk.get('response', '')

        except Exception as e:
            raise Exception(f"Failed to generate streaming response: {str(e)}")
