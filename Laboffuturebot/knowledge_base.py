"""
Knowledge base module for Lab o Future chatbot.
Handles CSV knowledge retrieval and vector database operations.
"""
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

from agno.knowledge.csv import CSVKnowledgeBase
from agno.vectordb.pgvector import PgVector


class EnhancedCSVKnowledge:
    """Enhanced knowledge base with additional functionality for relevance checking and metadata."""

    def __init__(
        self, 
        csv_path: str,
        db_url: str,
        table_name: str = "csv_documents",
        num_documents: int = 5,
        similarity_threshold: float = 0.7,
        recreate_index: bool = False
    ):
        """
        Initialize the enhanced knowledge base.

        Args:
            csv_path: Path to the CSV file containing knowledge chunks
            db_url: PostgreSQL connection URL
            table_name: Table name for vector storage
            num_documents: Number of chunks to retrieve per query
            similarity_threshold: Minimum similarity score to consider a result relevant
            recreate_index: Whether to recreate the vector index
        """
        self.csv_path = Path(csv_path)
        self.similarity_threshold = similarity_threshold

        # Initialize underlying knowledge base
        self.knowledge_base = CSVKnowledgeBase(
            path=self.csv_path,
            vector_db=PgVector(
                table_name=table_name,
                db_url=db_url,
            ),
            num_documents=num_documents,
        )

        # Load or recreate the knowledge base index
        self.knowledge_base.load(recreate=recreate_index)

    def update_index(self, recreate: bool = True):
        """
        Update the knowledge base index.

        Args:
            recreate: Whether to recreate the index from scratch
        """
        self.knowledge_base.load(recreate=recreate)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        # This is a placeholder - implement based on your specific needs
        try:
            document_count = len(self.knowledge_base)
        except TypeError:
            document_count = None

        last_updated = getattr(self.knowledge_base, 'last_updated', None)

        return {
            "document_count": document_count,
            "last_updated": last_updated,
        }

    def query(self, query_text: str) -> Tuple[List[Dict], bool]:
        """
        Query the knowledge base and return relevant documents and relevance flag.

        Args:
            query_text: The user's query text

        Returns:
            Tuple:
                - List of documents (dict with 'content' and 'score')
                - Boolean indicating if any result passes similarity threshold
        """
        # Step 1: Embed the query using vector_db's embedder
        query_embedding = self.knowledge_base.vector_db.embedder.embed([query_text])[0]




        # Step 2: Search the vector database for top results
        results = self.knowledge_base.vector_db.search(query_embedding, top_k=self.knowledge_base.num_documents)

        documents = []
        is_relevant = False
        threshold = self.similarity_threshold

        # results is a list of lists of tuples: [[(doc_id, score), ...]]
        for doc_id, score in results[0]:
            chunk_text = self._get_chunk_text(doc_id)
            documents.append({"content": chunk_text, "score": score})

            if score >= threshold:
                is_relevant = True

        return documents, is_relevant

    def _get_chunk_text(self, doc_id: int) -> str:
        """
        Retrieve the chunk text by document ID.

        Note: Adjust this method based on how your CSVKnowledgeBase stores documents.
        The following is an example assuming an attribute or method exists to get the document.

        Args:
            doc_id: Document ID returned from vector DB search

        Returns:
            The chunk text as string or a placeholder if not found
        """
        try:
            # Example: If CSVKnowledgeBase has 'documents' list or dict attribute
            return self.knowledge_base.documents[doc_id].page_content
        except Exception:
            # Fallback placeholder text if retrieval fails
            return "[Content unavailable]"


# Utility function to create knowledge base instance
def create_knowledge_base(
    csv_path: str,
    db_url: str,
    similarity_threshold: float = 0.7,
    recreate: bool = False
) -> EnhancedCSVKnowledge:
    """
    Create and initialize the knowledge base.

    Args:
        csv_path: Path to the CSV file
        db_url: Database connection URL
        similarity_threshold: Minimum similarity score for relevance
        recreate: Whether to recreate the index

    Returns:
        Initialized EnhancedCSVKnowledge instance
    """
    return EnhancedCSVKnowledge(
        csv_path=csv_path,
        db_url=db_url,
        similarity_threshold=similarity_threshold,
        recreate_index=recreate
    )
