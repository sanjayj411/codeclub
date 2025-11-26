import pytest
from src.core.db import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize database before running tests"""
    init_db()
    yield
