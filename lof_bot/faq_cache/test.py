from faq_db import FAQCacheDB


def test_db():
    db_url = "postgresql+psycopg://postgres:12345@localhost:5433/ai"
    faq_db = FAQCacheDB(db_url=db_url)
    
    table = faq_db.get_table()
    print(f"Table name: {table.name}")

    engine = faq_db.get_engine()
    with engine.connect() as conn:
        result = conn.execute("SELECT 1;")
        print("DB connection test result:", result.scalar())

if __name__ == "__main__":
    test_db()
