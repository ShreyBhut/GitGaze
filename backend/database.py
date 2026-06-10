from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event

# Using aiosqlite for async SQLite operations
DATABASE_URL = "sqlite+aiosqlite:///./gitgaze.db"

engine = create_async_engine(DATABASE_URL, echo=False)

# Enable WAL mode and optimize synchronous settings for SQLite
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()

# Dependency to inject DB sessions into our FastAPI routes later
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session