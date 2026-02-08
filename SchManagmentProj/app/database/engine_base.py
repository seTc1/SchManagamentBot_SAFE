from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from datetime import datetime

engine = create_async_engine(url="sqlite+aiosqlite:///bot_data.sqlite3")
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass


async def async_main():
   async with engine.begin() as conn:
       await conn.run_sync(Base.metadata.create_all)
