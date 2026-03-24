# tests/test_data_loader.py
import pytest
import polars as pl
from pathlib import Path
from src.core.data_loader import DataLoader

@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    """Creates a temporary CSV file for testing."""
    file_path = tmp_path / "test_data.csv"
    # Semicolon separated as per spec
    content = "id;name;age\n1;Alice;30\n2;Bob;25\n3;Charlie;40"
    file_path.write_text(content, encoding="utf-8")
    return file_path

def test_data_loader_csv_preview(sample_csv: Path) -> None:
    """Tests loading a CSV file, extracting schema, and respecting preview limit."""
    loader = DataLoader()
    
    # Test with preview_rows=2 to see if it limits correctly
    df = loader.load_preview(sample_csv, preview_rows=2)

    assert isinstance(df, pl.DataFrame)
    assert len(df) == 2  # Should only load 2 rows
    
    headers = loader.get_headers()
    assert headers == ["id", "name", "age"]
    
    dtypes = loader.get_dtypes()
    assert dtypes["id"] == "Int64"  # Polars inferred type
    assert dtypes["name"] == "String"