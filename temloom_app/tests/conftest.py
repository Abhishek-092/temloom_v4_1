import os
import sys
import tempfile
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from temloom.core.database import TemloomDatabase

@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_temloom.db")
        yield TemloomDatabase(db_path=db_path)
