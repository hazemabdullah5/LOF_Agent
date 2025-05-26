from typing import List
import os

# Example using OpenAI embeddings API; replace with your actual model or API
import openai

# Load your OpenAI API key from environment variables or config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable")

openai.api_key = OPENAI_API_KEY


def embed_query(text: str) -> List[float]:
    """
    Generate an embedding vector for the given text using OpenAI's embedding model.
    Returns a list of floats representing the embedding.
    """
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-3-large"  # or whichever embedding model you prefer
    )
    embedding = response["data"][0]["embedding"]
    return embedding
