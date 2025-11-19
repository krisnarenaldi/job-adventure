"""Script to drop interview enum types if they exist"""
import os
from sqlalchemy import create_engine, text

# Get database URL from environment
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("DATABASE_URL not set")
    exit(1)

# Create engine
engine = create_engine(database_url)

# Drop the enum types
with engine.connect() as conn:
    try:
        conn.execute(text("DROP TYPE IF EXISTS interviewtype CASCADE"))
        conn.execute(text("DROP TYPE IF EXISTS interviewstatus CASCADE"))
        conn.commit()
        print("Successfully dropped interview enum types")
    except Exception as e:
        print(f"Error dropping types: {e}")
        conn.rollback()
