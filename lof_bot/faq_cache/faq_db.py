from sqlalchemy import (
    create_engine, Table, Column, Integer, Text, DateTime, MetaData, String, ARRAY
)
from pgvector.sqlalchemy import Vector
from sqlalchemy.exc import OperationalError
from datetime import datetime


class FAQCacheDB:
    """
    Handles PostgreSQL connection and FAQ cache table setup.
    Requires PGVector extension enabled in your Postgres database.
    """

    def __init__(self, db_url: str, table_name: str = "faq_cache"):
        self.db_url = db_url
        self.table_name = table_name
        self.engine = create_engine(self.db_url)
        self.metadata = MetaData()

        self.table = Table(
            self.table_name,
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("query_text", Text, nullable=False),
            Column("response_text", Text, nullable=False),
            Column("embedding", VECTOR(1536), nullable=False),
            Column("context_tags", ARRAY(String), nullable=False, default=[]),
            Column("frequency", Integer, nullable=False, default=1),
            Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
            Column("last_accessed", DateTime, nullable=False, default=datetime.utcnow),
        )

        self._create_table()

    def _create_table(self):
        """
        Create the FAQ cache table if it doesn't exist.
        Ensure PGVector extension is enabled in the DB.
        """
        try:
            with self.engine.connect() as conn:
                # Enable pgvector extension if not already enabled
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                self.metadata.create_all(self.engine)
                # Create ivfflat index on embedding column for efficient similarity search
                create_index_sql = f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_embedding 
                ON {self.table_name} USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                """
                conn.execute(create_index_sql)
        except OperationalError as e:
            print("Database operational error:", e)
            raise

    def get_table(self) -> Table:
        return self.table

    def get_engine(self):
        return self.engine
