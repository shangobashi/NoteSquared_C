"""Database configuration and session management."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings

settings = get_settings()


def _strip_query_param(url: str, param: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if param in query:
        query.pop(param, None)
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


connect_args = {}
async_url = settings.async_database_url
if settings.database_url.startswith(("postgres://", "postgresql://")):
    if "sslmode=require" in settings.database_url:
        connect_args["ssl"] = True
        async_url = _strip_query_param(async_url, "sslmode")

engine = create_async_engine(
    async_url,
    echo=settings.debug,
    connect_args=connect_args if connect_args else None,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
