import os
from sqlmodel import SQLModel, create_engine, Session

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./agentops.db")
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False} if "sqlite" in DB_PATH else {})


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
