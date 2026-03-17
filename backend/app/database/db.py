from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self) -> None:
        self.engine = None
        self.SessionLocal = None

    def init(self, database_url: str) -> None:
        if self.engine is not None:
            self.engine.dispose()
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(
            database_url,
            future=True,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    def create_tables(self) -> None:
        if self.engine is None:
            raise RuntimeError("Database engine has not been initialized.")
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        if self.SessionLocal is None:
            raise RuntimeError("Database sessionmaker has not been initialized.")
        db = self.SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


database = Database()
