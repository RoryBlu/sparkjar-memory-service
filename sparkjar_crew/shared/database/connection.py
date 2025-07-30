import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

DATABASE_URL_DIRECT = os.getenv('DATABASE_URL_DIRECT', 'sqlite+aiosqlite:///./test.db')

async_engine = create_async_engine(DATABASE_URL_DIRECT, echo=False)
async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

def get_direct_session():
    return async_session()

def get_pooled_session():
    return async_session()

def create_direct_engine():
    return create_engine(DATABASE_URL_DIRECT.replace('+aiosqlite', ''))
