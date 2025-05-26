# memory.py

from hashlib import sha256
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine, Table, Column, String, Integer, Text, DateTime, MetaData,
    select, update, insert
)
from sqlalchemy.exc import NoResultFound


class FAQCacheMemory:
    def __init__(self, db_url: str, table_name: str = "chatbot_memory"):
        self.engine = create_engine(db_url)
        self.metadata = MetaData()

        self.table = Table(
            table_name,
            self.metadata,
            Column("query_hash", String(64), primary_key=True),
            Column("original_query", Text, nullable=False),
            Column("response", Text, nullable=False),
            Column("frequency", Integer, default=1, nullable=False),
            Column("last_accessed", DateTime, default=datetime.utcnow, nullable=False),
            Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
        )
        self.metadata.create_all(self.engine)

    def _hash_query(self, query: str) -> str:
        """
        Create a SHA256 hash of the normalized query string.
        """
        normalized = query.strip().lower()
        return sha256(normalized.encode("utf-8")).hexdigest()

    def get_cached_response(self, query: str) -> Optional[str]:
        """
        Retrieve cached response for a given query if it exists.
        Also updates frequency and last_accessed timestamp.
        """
        query_hash = self._hash_query(query)
        with self.engine.connect() as conn:
            stmt = select(self.table.c.response).where(self.table.c.query_hash == query_hash)
            result = conn.execute(stmt).first()
            if result:
                # Update usage stats asynchronously (best-effort)
                try:
                    self._update_stats(query_hash)
                except Exception:
                    pass
                return result[0]
        return None

    def _update_stats(self, query_hash: str):
        """
        Increment frequency and update last_accessed timestamp for a cached query.
        """
        with self.engine.connect() as conn:
            stmt = (
                update(self.table)
                .where(self.table.c.query_hash == query_hash)
                .values(
                    frequency=self.table.c.frequency + 1,
                    last_accessed=datetime.utcnow()
                )
            )
            conn.execute(stmt)

    def cache_response(self, query: str, response: str):
        """
        Cache a new query-response pair or update existing entry stats.
        """
        query_hash = self._hash_query(query)
        now = datetime.utcnow()
        with self.engine.connect() as conn:
            # Check if already cached
            stmt = select(self.table.c.query_hash).where(self.table.c.query_hash == query_hash)
            exists = conn.execute(stmt).first()
            if exists:
                self._update_stats(query_hash)
                # Optionally, update response text here if changed:
                # update_stmt = (
                #     update(self.table)
                #     .where(self.table.c.query_hash == query_hash)
                #     .values(response=response, last_accessed=now)
                # )
                # conn.execute(update_stmt)
            else:
                ins = insert(self.table).values(
                    query_hash=query_hash,
                    original_query=query,
                    response=response,
                    frequency=1,
                    last_accessed=now,
                    created_at=now,
                )
                conn.execute(ins)
