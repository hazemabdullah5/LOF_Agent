
from typing import List, Set
import re

# Define keywords or patterns relevant to your domain for context extraction
KEYWORDS = {
    "india",
    "online",
    "data science",
    "python",
    "beginner",
    "advanced",
    "machine learning",
    "ai",
    "artificial intelligence",
    "web development",
    "java",
    "cloud",
    "full stack",
    "part time",
    "full time",
    "weekend",
    "certification",
    "short course",
    "diploma",
    "degree",
}

def extract_context_tags(text: str) -> List[str]:
    """
    Extract context tags from the input text based on keyword matching.
    This can be replaced or extended with an NLP library like spaCy for entity recognition.
    """
    text_lower = text.lower()
    found_tags: Set[str] = set()

    # Simple keyword matching
    for keyword in KEYWORDS:
        # Using word boundaries to avoid partial matches
        if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
            found_tags.add(keyword)

    return list(found_tags)
