"""PDF text extraction and chunking using LangChain"""

import re
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class PDFProcessor:
    """Handles PDF text extraction and chunking"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        """
        Initialize PDF processor

        Args:
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            # Prioritize splitting at natural boundaries (paragraphs, sentences, words)
            separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean extracted PDF text before chunking.

        Removes duplicate consecutive lines, collapses excessive whitespace,
        and strips common web/PDF extraction noise.
        """
        # Collapse 3+ newlines into a paragraph break
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Collapse multiple spaces into one
        text = re.sub(r' {2,}', ' ', text)
        # Remove lines that are just punctuation / symbols with no words
        text = re.sub(r'(?m)^[^\w\n]{0,5}$', '', text)

        # Deduplicate consecutive identical lines (handles repeated nav/UI text)
        lines = text.split('\n')
        cleaned = []
        prev = None
        for line in lines:
            stripped = line.strip()
            if stripped != prev:
                cleaned.append(line)
            prev = stripped

        return '\n'.join(cleaned).strip()

    def load_and_split_pdf(self, pdf_path: str) -> List[Document]:
        """
        Load PDF and split into chunks

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of Document objects with text chunks and metadata

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If PDF loading or processing fails
        """
        try:
            # Load PDF using LangChain's PyPDFLoader
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()

            if not pages:
                raise ValueError(f"No content extracted from PDF: {pdf_path}")

            # Clean each page's text before chunking
            for page in pages:
                page.page_content = self._clean_text(page.page_content)

            # Remove pages that became empty after cleaning
            pages = [p for p in pages if p.page_content.strip()]

            # Split pages into chunks
            chunks = self.text_splitter.split_documents(pages)

            # Enhance metadata with source file info
            for chunk in chunks:
                chunk.metadata['source_file'] = pdf_path

            return chunks

        except FileNotFoundError:
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        except Exception as e:
            raise Exception(f"Failed to process PDF {pdf_path}: {str(e)}")

    def get_chunk_info(self, chunks: List[Document]) -> dict:
        """
        Get information about chunks

        Args:
            chunks: List of Document chunks

        Returns:
            Dictionary with chunk statistics
        """
        if not chunks:
            return {"num_chunks": 0, "avg_chunk_length": 0, "pages": set()}

        total_length = sum(len(chunk.page_content) for chunk in chunks)
        pages = set(chunk.metadata.get('page', 'unknown') for chunk in chunks)

        return {
            "num_chunks": len(chunks),
            "avg_chunk_length": total_length // len(chunks),
            "total_length": total_length,
            "pages": sorted(pages) if all(isinstance(p, int) for p in pages) else pages
        }
