"""Facebook Comment Auto-Reply Pipeline using RAG"""

import json
import yaml
import ollama
from datetime import datetime, timezone
from typing import Optional

from .embedder import OllamaEmbedder
from .vector_store import FAISSVectorStore
from .comment_classifier import classify_comment, IntentType

# Intents that do not need a reply
_SKIP_INTENTS = {"positive", "generic"}

# Tone instruction per intent
_TONE_MAP = {
    "complaint": (
        "Start with empathy — acknowledge their concern warmly. "
        "Then offer a helpful resolution or next step."
    ),
    "request": (
        "Acknowledge their request. Provide the relevant information "
        "or direct them to where they can find it."
    ),
    "question": (
        "Answer their question clearly and concisely using the FAQ information."
    ),
}


class FacebookReplyPipeline:
    """
    Orchestrates: classify comments → RAG retrieval → generate friendly replies.

    Uses a dedicated FAQ FAISS index (separate from the main RAG index).
    """

    def __init__(
        self,
        config_path: str = "config/config.yaml",
        faq_persist_dir: str = "data/embeddings_faq",
    ):
        """
        Initialize the pipeline.

        Args:
            config_path: Path to config.yaml
            faq_persist_dir: Directory where the FAQ FAISS index is stored
        """
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.model_name = self.config["models"]["generation"]["name"]
        self.top_k = self.config["retrieval"]["top_k"]
        # Use a slightly lower threshold so FAQ chunks are not over-filtered
        self.min_score = max(self.config["retrieval"].get("min_score", 0.4) - 0.1, 0.0)

        # Initialize embedder (shared between FAQ and comment embedding)
        print("Initializing embedder...")
        self.embedder = OllamaEmbedder(
            model_name=self.config["models"]["embedding"]["name"]
        )
        embedding_dim = self.embedder.get_embedding_dimension()

        # Initialize FAQ-specific FAISS vector store
        self.vector_store = FAISSVectorStore(
            embedding_dimension=embedding_dim,
            persist_directory=faq_persist_dir,
        )

    def load_faq_index(self, index_name: str = "faiss_index") -> bool:
        """
        Load the FAQ FAISS index from disk.

        Args:
            index_name: Name of the saved index files

        Returns:
            True if loaded successfully, False otherwise
        """
        success = self.vector_store.load(index_name)
        if success:
            print(f"FAQ index loaded: {len(self.vector_store.documents)} chunks available")
        else:
            print("No FAQ index found on disk.")
        return success

    def _build_reply_prompt(
        self,
        message: str,
        first_name: str,
        intent: IntentType,
        faq_context: str,
    ) -> str:
        """Build the Ollama prompt for a social media reply."""
        tone = _TONE_MAP.get(intent, _TONE_MAP["question"])
        return (
            "You are a friendly social media manager for a brand. "
            "Write a short, warm reply to a Facebook comment.\n\n"
            "INSTRUCTIONS:\n"
            f'- Start your reply with "Hi {first_name}!"\n'
            f"- {tone}\n"
            "- Use information from the FAQ context below where relevant.\n"
            "- Keep the reply under 80 words.\n"
            "- Do NOT include emojis unless the FAQ mentions them.\n"
            "- Do NOT cite page numbers or document references.\n"
            "- Sound natural and friendly, not robotic.\n"
            "- If the FAQ has no relevant answer, politely ask them to DM or contact support.\n\n"
            f"FAQ CONTEXT:\n{faq_context}\n\n"
            f'FACEBOOK COMMENT: "{message}"\n\n'
            "REPLY:"
        )

    def _retrieve_faq_context(self, message: str):
        """
        Retrieve relevant FAQ chunks for a comment.

        Args:
            message: The comment text used as the search query

        Returns:
            Tuple of (context_string, list of chunk dicts with score + preview)
        """
        try:
            query_embedding = self.embedder.embed_query(message)
            similar_docs = self.vector_store.similarity_search(
                query_embedding, top_k=self.top_k, min_score=self.min_score
            )
        except Exception:
            similar_docs = []

        if not similar_docs:
            return "No specific FAQ information found for this topic.", []

        parts = [doc.page_content.strip() for doc, _ in similar_docs]
        context_str = "\n\n---\n\n".join(parts)

        chunks_meta = [
            {
                "score": round(float(score), 4),
                "page": doc.metadata.get("page", "unknown"),
                "preview": doc.page_content[:120].strip(),
            }
            for doc, score in similar_docs
        ]

        return context_str, chunks_meta

    def _generate_reply(self, message: str, first_name: str, intent: IntentType) -> dict:
        """
        Generate a Facebook reply using RAG context + Ollama.

        Args:
            message: Original comment text
            first_name: Commenter's first name
            intent: Classified intent of the comment

        Returns:
            Dict with keys: reply_message, faq_chunks_used, generation_model
        """
        faq_context, chunks_meta = self._retrieve_faq_context(message)
        prompt = self._build_reply_prompt(message, first_name, intent, faq_context)
        fallback = (
            f"Hi {first_name}! Thanks for reaching out. "
            "Please DM us or contact our support team and we'll be happy to help."
        )

        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "temperature": self.config["models"]["generation"]["temperature"],
                    "num_predict": 200,
                },
            )
            reply = response.get("response", "").strip() or fallback
        except Exception as e:
            print(f"  Warning: Ollama generation failed: {e}")
            reply = fallback

        return {
            "reply_message": reply,
            "faq_chunks_used": chunks_meta,
            "generation_model": self.model_name,
        }

    def process_comments(
        self,
        comments_data: dict,
        verbose: bool = True,
    ) -> dict:
        """
        Process a batch of Facebook comments and generate replies.

        Args:
            comments_data: Parsed comments JSON (Facebook Graph API format)
            verbose: Print per-comment progress to stdout

        Returns:
            Dict with "data" (list of reply objects) and "summary"
        """
        comments = comments_data.get("data", [])
        results = []
        replied_count = 0
        skipped_count = 0
        total = len(comments)

        for i, comment in enumerate(comments, 1):
            comment_id = comment["id"]
            message = comment.get("message", "").strip()
            from_info = comment.get("from", {})
            full_name = from_info.get("name", "there")
            commenter_id = from_info.get("id", None)
            first_name = full_name.split()[0]
            created_time = comment.get("created_time", None)

            if not message:
                results.append({
                    "comment_id": comment_id,
                    "commenter_name": full_name,
                    "commenter_id": commenter_id,
                    "original_message": "",
                    "created_time": created_time,
                    "status": "skipped",
                    "reason": "empty_message",
                })
                skipped_count += 1
                continue

            if verbose:
                preview = message[:60] + ("..." if len(message) > 60 else "")
                print(f"[{i}/{total}] {preview}")

            # --- Step 1: Classify intent ---
            intent = classify_comment(message, self.model_name)

            # --- Step 2: Skip if not actionable ---
            if intent in _SKIP_INTENTS:
                if verbose:
                    print(f"  → Skipped ({intent})")
                results.append({
                    "comment_id": comment_id,
                    "commenter_name": full_name,
                    "commenter_id": commenter_id,
                    "original_message": message,
                    "created_time": created_time,
                    "intent": intent,
                    "status": "skipped",
                    "reason": intent,
                })
                skipped_count += 1
                continue

            # --- Step 3: Generate reply ---
            if verbose:
                print(f"  → Generating reply (intent: {intent})...")

            generation = self._generate_reply(message, first_name, intent)

            if verbose:
                preview_reply = generation["reply_message"][:80]
                if len(generation["reply_message"]) > 80:
                    preview_reply += "..."
                print(f"  → {preview_reply}")

            results.append({
                "comment_id": comment_id,
                "commenter_name": full_name,
                "commenter_id": commenter_id,
                "original_message": message,
                "created_time": created_time,
                "intent": intent,
                "reply_message": generation["reply_message"],
                "faq_chunks_used": generation["faq_chunks_used"],
                "generation_model": generation["generation_model"],
                "status": "pending",
            })
            replied_count += 1

        return {
            "data": results,
            "summary": {
                "total_comments": total,
                "replied": replied_count,
                "skipped": skipped_count,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        }
