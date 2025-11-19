"""
Script to create a test user directly in the database
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import uuid
import bcrypt

# Database URL
DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_AcJK7NMl2fPn@ep-shiny-sky-adgai6a9-pooler.c-2.us-east-1.aws.neon.tech/neondb"

async def create_test_user():
    """Create a test user in the database"""
    
    # Create engine
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        connect_args={"ssl": "require"}
    )
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # Set password and ensure it's not longer than 72 bytes for bcrypt
            password = "test1234"
            # Encode to bytes and truncate to 72 bytes if needed
            password_bytes = password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            # Hash the password
            hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
            
            # Create user
            user_id = uuid.uuid4()
            
            from sqlalchemy import text
            
            query = text("""
            INSERT INTO users (id, email, hashed_password, full_name, role, created_at, updated_at)
            VALUES (:id, :email, :hashed_password, :full_name, :role, NOW(), NOW())
            """)
            
            await session.execute(
                query,
                {
                    "id": user_id,
                    "email": "test@example.com",
                    "hashed_password": hashed_password,
                    "full_name": "Test User",
                    "role": "RECRUITER",
                    "is_active": 'true'
                }
            )
            
            await session.commit()
            
            print("✅ Test user created successfully!")
            print(f"Email: test@example.com")
            print(f"Password: test1234")
            print(f"Role: recruiter")
            
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            await session.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_test_user())
