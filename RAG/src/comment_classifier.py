"""Intent classification for Facebook comments"""

import re
import ollama
from typing import Literal

IntentType = Literal["question", "complaint", "request", "positive", "generic"]

# Words that typically start a question
_QUESTION_START_WORDS = {
    "how", "what", "when", "where", "why", "which", "who",
    "is", "are", "can", "could", "do", "does", "did",
    "will", "would", "should", "has", "have",
}

# Keywords that strongly signal a complaint
_COMPLAINT_KEYWORDS = [
    "complaint", "complain", "issue", "problem", "not received",
    "didn't receive", "didnt receive", "havent received", "haven't received",
    "wrong", "poor", "disappointed", "frustrat", "refund",
    "overpriced", "too expensive", "scam", "fake", "not working",
    "broken", "damaged", "delay", "late delivery", "bad experience",
]

# Keywords that strongly signal a request for action/info
_REQUEST_KEYWORDS = [
    "please share", "please send", "please call", "please provide",
    "please clarify", "please check", "can you send", "can you share",
    "can you call", "send me", "check dm", "check dms",
    "brochure", "contact me", "support number", "more info",
    "pricing details", "customer support", "whatsapp", "phone number",
    "interested in bulk", "bulk order", "partnership",
]

# Words that signal clear positive/praise (no follow-up needed)
_POSITIVE_KEYWORDS = [
    "amazing", "great", "fantastic", "brilliant", "excellent",
    "wonderful", "awesome", "loved it", "loved", "helpful",
    "super excited", "excited", "looks promising", "fantastic offer",
    "brilliant campaign", "great initiative", "amazing work",
    "thanks for clarifying",
]


def classify_comment(message: str, model_name: str = "phi3:mini") -> IntentType:
    """
    Classify a Facebook comment's intent.

    Applies fast heuristics first. Falls back to Ollama for ambiguous cases.

    Args:
        message: The comment text to classify
        model_name: Ollama model name for fallback LLM classification

    Returns:
        One of: "question", "complaint", "request", "positive", "generic"
    """
    msg_lower = message.lower().strip()

    # --- Complaint check (highest priority) ---
    for kw in _COMPLAINT_KEYWORDS:
        if kw in msg_lower:
            return "complaint"

    # --- Question check ---
    if "?" in message:
        return "question"

    words = msg_lower.split()
    if words and words[0] in _QUESTION_START_WORDS:
        return "question"

    # --- Request check ---
    for kw in _REQUEST_KEYWORDS:
        if kw in msg_lower:
            return "request"

    # --- Positive check (short praise with no action needed) ---
    # Only mark as positive if it's a clearly positive, brief comment
    if len(message) <= 80:
        for kw in _POSITIVE_KEYWORDS:
            if kw in msg_lower:
                return "positive"

    # --- LLM fallback for ambiguous cases ---
    return _llm_classify(message, model_name)


def _llm_classify(message: str, model_name: str) -> IntentType:
    """
    Use Ollama to classify ambiguous comments.

    Args:
        message: Comment text
        model_name: Ollama model to use

    Returns:
        Classified intent, defaults to "generic" on failure
    """
    prompt = (
        "Classify this Facebook comment into exactly one category.\n"
        "Reply with ONLY ONE WORD. Choose from: question, complaint, request, positive, generic\n\n"
        f'Comment: "{message}"\n\n'
        "Category:"
    )

    try:
        response = ollama.generate(
            model=model_name,
            prompt=prompt,
            options={"temperature": 0, "num_predict": 5}
        )
        raw = response.get("response", "").strip().lower()
        first_word = raw.split()[0] if raw.split() else "generic"
        if first_word in ("question", "complaint", "request", "positive", "generic"):
            return first_word
    except Exception:
        pass

    return "generic"
