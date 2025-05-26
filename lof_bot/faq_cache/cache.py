# cache.py

from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update, insert, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
import numpy as np
from db import FAQCacheDB
from embedding import embed_query
from context import extract_context_tags
from scipy.spatial.distance import cosine


class FAQCache:
    def __init__(self, db_url: str, similarity_threshold: float = 0.85):
        self.db = FAQCacheDB(db_url)
        self.table = self.db.get_table()
        self.engine = self.db.get_engine()
        self.similarity_threshold = similarity_threshold

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        # Handle zero vectors safely
        if not vec1.any() or not vec2.any():
            return 0.0
        return 1 - cosine(vec1, vec2)

    def _vector_search(self, query_embedding: List[float]) -> List[dict]:
        """
        Search cached queries whose embeddings have cosine similarity above threshold.
        Returns a list of candidate rows as dicts with keys matching table columns.
        """
        with self.engine.connect() as conn:
            # Use raw SQL to perform vector similarity search with PGVector cosine operator
            sql = f"""
            SELECT id, query_text, response_text, embedding, context_tags, frequency, last_accessed
            FROM {self.table.name}
            ORDER BY embedding <-> :query_embedding
            LIMIT 20;
            """
            result = conn.execute(sql, {"query_embedding": query_embedding}).fetchall()
            candidates = []
            for row in result:
                candidates.append({
                    "id": row[0],
                    "query_text": row[1],
                    "response_text": row[2],
                    "embedding": row[3],
                    "context_tags": row[4],
                    "frequency": row[5],
                    "last_accessed": row[6],
                })
            return candidates

    def _filter_by_context(self, query_tags: List[str], candidates: List[dict]) -> List[dict]:
        """
        Filter cached query candidates by matching context tags.
        Returns candidates that have at least one overlapping tag.
        """
        if not query_tags:
            return candidates  # No tags to filter, return all

        filtered = []
        query_tag_set = set(query_tags)
        for c in candidates:
            candidate_tags = set(c["context_tags"] or [])
            if query_tag_set.intersection(candidate_tags):
                filtered.append(c)
        return filtered

    def get_cached_response(self, query_text: str) -> Optional[str]:
        """
        Try to get a cached response for the query_text.
        Returns response text if a good match is found, else None.
        """
        query_embedding = np.array(embed_query(query_text))
        query_tags = extract_context_tags(query_text)

        # 1. Search nearest neighbors by embedding distance
        candidates = self._vector_search(query_embedding)

        # 2. Filter candidates by context tag overlap
        candidates = self._filter_by_context(query_tags, candidates)

        # 3. Find best candidate above similarity threshold
        best_match = None
        best_score = 0.0
        for c in candidates:
            candidate_embedding = np.array(c["embedding"])
            similarity = 1 - cosine(query_embedding, candidate_embedding)
            if similarity > self.similarity_threshold and similarity > best_score:
                best_score = similarity
                best_match = c

        if best_match:
            # Update frequency and last_accessed asynchronously
            self._update_usage(best_match["id"])
            return best_match["response_text"]

        return None

    def _update_usage(self, entry_id: int):
        """
        Increment frequency and update last_accessed timestamp.
        """
        with self.engine.connect() as conn:
            stmt = (
                update(self.table)
                .where(self.table.c.id == entry_id)
                .values(
                    frequency=self.table.c.frequency + 1,
                    last_accessed=datetime.utcnow()
                )
            )
            conn.execute(stmt)

    def cache_response(self, query_text: str, response_text: str):
        """
        Cache the query and response in the DB with embedding and context tags.
        If the query already exists (exact text match), update usage stats.
        """
        query_embedding = embed_query(query_text)
        context_tags = extract_context_tags(query_text)
        now = datetime.utcnow()

        with self.engine.begin() as conn:  # Transactional block
            # Check if exact query already cached
            stmt = select(self.table.c.id).where(self.table.c.query_text == query_text)
            existing = conn.execute(stmt).first()

            if existing:
                entry_id = existing[0]
                self._update_usage(entry_id)
                # Optionally update response text here if changed
                # update_stmt = (
                #     update(self.table)
                #     .where(self.table.c.id == entry_id)
                #     .values(response_text=response_text, last_accessed=now)
                # )
                # conn.execute(update_stmt)
            else:
                # Insert new cache entry
                ins = insert(self.table).values(
                    query_text=query_text,
                    response_text=response_text,
                    embedding=query_embedding,
                    context_tags=context_tags,
                    frequency=1,
                    created_at=now,
                    last_accessed=now,
                )
                conn.execute(ins)
