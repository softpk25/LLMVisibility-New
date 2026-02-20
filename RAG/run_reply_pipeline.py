"""CLI for Facebook Comment Auto-Reply RAG Pipeline"""

import argparse
import json
import os
import sys

# Directory where the FAQ FAISS index is stored (separate from main RAG index)
FAQ_PERSIST_DIR = "data/embeddings_faq"


def ingest_faq_command(args):
    """Ingest a FAQ PDF into the FAQ-specific FAISS index."""
    from src.rag_pipeline import RAGPipeline
    from src.vector_store import FAISSVectorStore

    pdf_path = args.pdf_path
    if not os.path.isabs(pdf_path):
        pdf_path = os.path.abspath(pdf_path)

    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    print("Initializing RAG pipeline for FAQ ingestion...")
    rag = RAGPipeline()  # uses config/config.yaml

    # Swap the vector store to point to the FAQ-specific directory
    embedding_dim = rag.embedder.get_embedding_dimension()
    rag.vector_store = FAISSVectorStore(
        embedding_dimension=embedding_dim,
        persist_directory=FAQ_PERSIST_DIR,
    )
    rag.config["vector_store"]["persist_directory"] = FAQ_PERSIST_DIR
    rag.ingested_pdfs = []  # reset tracking for FAQ index

    # Load existing FAQ index if it exists (to allow adding multiple PDFs)
    rag.vector_store.load("faiss_index")
    rag._load_metadata()

    print(f"\nIngesting: {pdf_path}")
    stats = rag.ingest_pdf(pdf_path)

    if stats.get("skipped"):
        print(f"\n'{stats['pdf_file']}' is already in the FAQ index.")
        print("Run with --force to re-ingest it after clearing the FAQ index.")
        return

    print("\n" + "=" * 60)
    print("FAQ PDF INGESTED SUCCESSFULLY")
    print("=" * 60)
    print(f"  PDF           : {stats['pdf_file']}")
    print(f"  Chunks        : {stats['num_chunks']}")
    print(f"  Pages         : {stats['num_pages']}")
    print(f"  FAQ index at  : {FAQ_PERSIST_DIR}/")
    print("=" * 60)
    print("\nYou can now run:")
    print("  python run_reply_pipeline.py generate-replies data/comments.json")


def clear_faq_command(args):
    """Delete all FAQ index files from data/embeddings_faq/."""
    if not args.yes:
        confirm = input(f"Clear all FAQ embeddings in '{FAQ_PERSIST_DIR}'? (y/N): ")
        if confirm.lower() != "y":
            print("Clear cancelled.")
            return

    if not os.path.exists(FAQ_PERSIST_DIR):
        print("Nothing to clear — FAQ index directory does not exist.")
        return

    deleted = []
    for filename in os.listdir(FAQ_PERSIST_DIR):
        file_path = os.path.join(FAQ_PERSIST_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            deleted.append(filename)

    if deleted:
        print(f"Cleared {len(deleted)} file(s) from '{FAQ_PERSIST_DIR}':")
        for f in deleted:
            print(f"  - {f}")
        print("\nFAQ index cleared. Ingest a new PDF to rebuild:")
        print("  python run_reply_pipeline.py ingest-faq data/faq/your_faq.pdf")
    else:
        print("Nothing to clear — FAQ index directory was already empty.")


def generate_replies_command(args):
    """Generate replies for a comments JSON file."""
    from src.facebook_reply_pipeline import FacebookReplyPipeline

    comments_path = args.comments_json
    output_path = args.output

    if not os.path.exists(comments_path):
        print(f"Error: Comments file not found: {comments_path}", file=sys.stderr)
        sys.exit(1)

    with open(comments_path, "r", encoding="utf-8") as f:
        comments_data = json.load(f)

    total = len(comments_data.get("data", []))
    if total == 0:
        print("No comments found in the input file.")
        sys.exit(0)

    print("Initializing Facebook Reply Pipeline...")
    try:
        pipeline = FacebookReplyPipeline(faq_persist_dir=FAQ_PERSIST_DIR)
    except Exception as e:
        print(f"\nError initializing pipeline: {e}", file=sys.stderr)
        print("\nMake sure:")
        print("  1. Ollama is running  (ollama serve)")
        print("  2. Required models are pulled  (ollama list)")
        print("  3. config/config.yaml exists")
        sys.exit(1)

    loaded = pipeline.load_faq_index()
    if not loaded:
        print("\nError: No FAQ index found. Ingest a FAQ PDF first:", file=sys.stderr)
        print("  python run_reply_pipeline.py ingest-faq <path_to_faq.pdf>")
        sys.exit(1)

    print(f"\nProcessing {total} comments...\n")
    results = pipeline.process_comments(comments_data, verbose=not args.quiet)

    # Write output
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    summary = results["summary"]
    print("\n" + "=" * 60)
    print("REPLIES GENERATED")
    print("=" * 60)
    print(f"  Total comments  : {summary['total_comments']}")
    print(f"  Replied         : {summary['replied']}")
    print(f"  Skipped         : {summary['skipped']}")
    print(f"  Output file     : {output_path}")
    print(f"  Generated at    : {summary['generated_at']}")
    print("=" * 60)
    print(f"\nReady to post: iterate over '{output_path}' → data[*].comment_id + reply_message")
    print("  POST /{comment_id}/comments  body: {\"message\": reply_message}")


def main():
    parser = argparse.ArgumentParser(
        description="Facebook Comment Auto-Reply RAG Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Step 1 — ingest your FAQ PDF into the knowledge base (run once)
  python run_reply_pipeline.py ingest-faq data/faq/product_faq.pdf

  # Step 2 — generate replies for a batch of comments
  python run_reply_pipeline.py generate-replies data/comments.json

  # Custom output path
  python run_reply_pipeline.py generate-replies data/comments.json --output data/replies.json

  # Suppress per-comment output (only show summary)
  python run_reply_pipeline.py generate-replies data/comments.json --quiet

  # Clear the FAQ index (to re-ingest a different PDF)
  python run_reply_pipeline.py clear-faq
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- ingest-faq ---
    ingest_parser = subparsers.add_parser(
        "ingest-faq",
        help="Ingest a FAQ PDF into the knowledge base",
    )
    ingest_parser.add_argument("pdf_path", type=str, help="Path to FAQ PDF file")

    # --- clear-faq ---
    clear_parser = subparsers.add_parser(
        "clear-faq",
        help="Delete the FAQ FAISS index so you can re-ingest a fresh PDF",
    )
    clear_parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip the confirmation prompt",
    )

    # --- generate-replies ---
    replies_parser = subparsers.add_parser(
        "generate-replies",
        help="Generate replies for Facebook comments",
    )
    replies_parser.add_argument(
        "comments_json",
        type=str,
        help="Path to comments JSON file (Facebook Graph API format)",
    )
    replies_parser.add_argument(
        "--output", "-o",
        type=str,
        default="replies.json",
        help="Output path for replies JSON (default: replies.json)",
    )
    replies_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress per-comment progress output; show only the final summary",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "ingest-faq":
        try:
            ingest_faq_command(args)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "clear-faq":
        try:
            clear_faq_command(args)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "generate-replies":
        try:
            generate_replies_command(args)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
