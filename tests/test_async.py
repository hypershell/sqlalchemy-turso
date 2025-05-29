import pytest
import pytest_asyncio
import asyncio
from sqlalchemy import Column, Integer, String, text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)


@pytest_asyncio.fixture(params=["memory", "file", "remote", "embedded"])
async def engine(request):
    import os

    match request.param:
        case "file":
            if os.path.exists("test.db"):
                os.remove("test.db")
            engine = create_async_engine(
                "sqlite+aiolibsql:///test.db",
                poolclass=AsyncAdaptedQueuePool,
            )
        case "remote" if os.getenv("TURSO_DATABASE_URL"):
            engine = create_async_engine(
                f"sqlite+aiolibsql://{os.getenv('TURSO_DATABASE_URL')}?secure=false",
                poolclass=AsyncAdaptedQueuePool,
                connect_args={
                    "auth_token": os.getenv("TURSO_AUTH_TOKEN"),
                },
            )
        case "embedded" if os.getenv("TURSO_DATABASE_URL"):
            if os.path.exists("test_embedded.db"):
                os.remove("test_embedded.db")
            engine = create_async_engine(
                "sqlite+aiolibsql:///test_embedded.db",
                poolclass=AsyncAdaptedQueuePool,
                connect_args={
                    "auth_token": os.getenv("TURSO_AUTH_TOKEN"),
                    "sync_url": f"http://{os.getenv('TURSO_DATABASE_URL')}",
                },
            )
        case "memory" | _:
            engine =  create_async_engine(
                "sqlite+aiolibsql://",
                poolclass=AsyncAdaptedQueuePool,
            )
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def session(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_connection(session: AsyncSession):
    result = await session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_create_table(session):
    result = await session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    )
    assert result.scalar() == "users"


@pytest.mark.asyncio
async def test_insert_and_query(session):
    user = User(name="Test User", email="test@example.com")
    session.add(user)
    await session.commit()

    stmt = select(User)
    result = await session.execute(stmt)
    queried_user = result.scalars().first()
    assert queried_user.name == "Test User"
    assert queried_user.email == "test@example.com"


@pytest.mark.asyncio
async def test_update(session):
    user = User(name="Test User", email="test@example.com")
    session.add(user)
    await session.commit()

    user.name = "Updated User"
    await session.commit()

    stmt = select(User)
    result = await session.execute(stmt)
    updated_user = result.scalars().first()
    assert updated_user.name == "Updated User"


@pytest.mark.asyncio
async def test_delete(session):
    user = User(name="Test User", email="test@example.com")
    session.add(user)
    await session.commit()

    await session.delete(user)
    await session.commit()

    stmt = select(User)
    result = await session.execute(stmt)
    assert result.scalars().first() is None
