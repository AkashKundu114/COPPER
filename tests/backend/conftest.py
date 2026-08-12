import pytest

@pytest.fixture(scope='session')
def db_session():
    return None