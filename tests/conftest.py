# Test fixtures for URL Shortener Service test suite.
# Generated from: prompts/test-generator.yaml
# Spec: specs/url-shortener.yaml (SPEC-SHORT-001)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base, get_db
from src.main import app
from src.crud import seed_blocklist

# Use an in-memory SQLite DB per test session — isolated from production DB
TEST_DATABASE_URL = "sqlite:///./test_url_shortener.db"

engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(create_test_tables):
    """Provides a transactional test DB session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    seed_blocklist(session, ["malware.example.com", "phishing.example.com"])

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient wired to the test DB session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


VALID_URL = "https://www.example.com/very/long/path?q=search&page=1"
ANOTHER_VALID_URL = "https://www.openai.com/research/gpt-4"
