"""CLI interface for RAG module"""

import argparse
import sys
import os
from pathlib import Path

from src.rag_pipeline import RAGPipeline


def ingest_command(args, rag: RAGPipeline):
    """Handle ingest command"""
    try:
        pdf_path = args.pdf_path

        # Convert to absolute path if relative
        if not os.path.isabs(pdf_path):
            pdf_path = os.path.abspath(pdf_path)

        stats = rag.ingest_pdf(pdf_path)

        print("\n" + "=" * 60)
        print("INGESTION SUCCESSFUL")
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError during ingestion: {e}", file=sys.stderr)
        sys.exit(1)


def query_command(args, rag: RAGPipeline):
    """Handle query command"""
    try:
        # Try to load existing index first
        if not rag.vector_store.documents:
            print("Loading existing index...")
            loaded = rag.load_existing_index()
            if not loaded:
                print("\nError: No documents found. Please ingest a PDF first using:")
                print("  python main.py ingest <pdf_path>")
                sys.exit(1)

        question = args.question
        response = rag.query(question)

        # Display results
        print("\n" + "=" * 60)
        print("ANSWER")
        print("=" * 60)
        print(response['answer'])

        print("\n" + "=" * 60)
        print("SOURCES")
        print("=" * 60)
        if response['sources']:
            print(f"Pages: {', '.join(map(str, response['sources']))}")
        else:
            print("No source pages available")

        print("\n" + "=" * 60)
        print("RETRIEVED CONTEXT")
        print("=" * 60)
        for idx, chunk in enumerate(response['retrieved_chunks'], 1):
            print(f"\n[Chunk {idx} - Page {chunk['page']}, Similarity: {chunk['similarity_score']:.3f}]")
            print(chunk['preview'])

        print("\n" + "=" * 60)

    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError during query: {e}", file=sys.stderr)
        sys.exit(1)


def clear_command(args, rag: RAGPipeline):
    """Handle clear command"""
    try:
        # Confirm before clearing
        if not args.yes:
            response = input("Are you sure you want to clear all embeddings? (y/N): ")
            if response.lower() != 'y':
                print("Clear cancelled")
                return

        # Clear the index
        rag.clear_index()

        # Delete saved index files
        persist_dir = rag.config['vector_store']['persist_directory']
        if os.path.exists(persist_dir):
            for file in os.listdir(persist_dir):
                file_path = os.path.join(persist_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)

        print("All embeddings cleared successfully")

    except Exception as e:
        print(f"\nError during clear: {e}", file=sys.stderr)
        sys.exit(1)


def list_command(args, rag: RAGPipeline):
    """Handle list command"""
    try:
        # Try to load existing index
        if not rag.vector_store.documents:
            print("Loading existing index...")
            rag.load_existing_index()

        stats = rag.get_stats()

        print("\n" + "=" * 60)
        print("RAG SYSTEM STATUS")
        print("=" * 60)

        print(f"\nVector Store:")
        print(f"  - Documents: {stats['vector_store']['num_documents']}")
        print(f"  - Vectors: {stats['vector_store']['num_vectors']}")
        print(f"  - Embedding dimension: {stats['vector_store']['embedding_dimension']}")
        print(f"  - Index type: {stats['vector_store']['index_type']}")

        print(f"\nConfiguration:")
        print(f"  - Chunk size: {stats['config']['chunk_size']}")
        print(f"  - Chunk overlap: {stats['config']['chunk_overlap']}")
        print(f"  - Top-k retrieval: {stats['config']['top_k']}")
        print(f"  - Embedding model: {stats['config']['embedding_model']}")
        print(f"  - Generation model: {stats['config']['generation_model']}")

        print(f"\nIngested PDFs:")
        if stats['ingested_pdfs']:
            for pdf in stats['ingested_pdfs']:
                print(f"  - {pdf}")
        else:
            print("  None")

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\nError getting status: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="RAG Module - Retrieval-Augmented Generation with BGE-M3 and Llama3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest a PDF
  python main.py ingest data/pdfs/document.pdf

  # Query the system
  python main.py query "What are the main findings?"

  # List ingested documents
  python main.py list

  # Clear all embeddings
  python main.py clear
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest a PDF file')
    ingest_parser.add_argument('pdf_path', type=str, help='Path to PDF file')

    # Query command
    query_parser = subparsers.add_parser('query', help='Query the RAG system')
    query_parser.add_argument('question', type=str, help='Question to ask')

    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all embeddings')
    clear_parser.add_argument('-y', '--yes', action='store_true', help='Skip confirmation prompt')

    # List command
    list_parser = subparsers.add_parser('list', help='List ingested PDFs and system status')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize RAG pipeline
    try:
        print("Initializing RAG pipeline...")
        rag = RAGPipeline()
        print("RAG pipeline initialized successfully\n")
    except Exception as e:
        print(f"Error initializing RAG pipeline: {e}", file=sys.stderr)
        print("\nMake sure:")
        print("  1. Ollama is running (ollama serve)")
        print("  2. Required models are available (ollama list)")
        print("  3. config/config.yaml exists")
        sys.exit(1)

    # Execute command
    if args.command == 'ingest':
        ingest_command(args, rag)
    elif args.command == 'query':
        query_command(args, rag)
    elif args.command == 'clear':
        clear_command(args, rag)
    elif args.command == 'list':
        list_command(args, rag)


if __name__ == '__main__':
    main()
