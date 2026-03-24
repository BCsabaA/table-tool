# src/core/data_loader.py
import polars as pl
from pathlib import Path
from typing import Dict, List, Optional, Union

class DataLoader:
    """
    Handles reading data files, extracting headers, and inferring data types.
    Supports CSV, TXT, and XLSX formats.
    """
    
    def __init__(self) -> None:
        self.file_path: Optional[Path] = None
        self.preview_df: Optional[pl.DataFrame] = None
        self.headers: List[str] = []
        self.dtypes: Dict[str, str] = {}

    def load_preview(self, file_path: Union[str, Path], preview_rows: int = 200) -> pl.DataFrame:
        """
        Loads a preview of the file (up to preview_rows) and infers the schema.

        Args:
            file_path: Path to the data file.
            preview_rows: Number of rows to load for the preview grid.

        Returns:
            A Polars DataFrame containing the preview data.

        Raises:
            ValueError: If the file format is unsupported.
            FileNotFoundError: If the file does not exist.
        """
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        ext = self.file_path.suffix.lower()

        if ext in ['.csv', '.txt']:
            # Using semicolon as default separator as per v1 spec
            self.preview_df = pl.read_csv(
                self.file_path,
                n_rows=preview_rows,
                infer_schema_length=10000,
                separator=';' if ext == '.csv' else '\t',
                ignore_errors=True
            )
        elif ext in ['.xlsx', '.xls']:
            # Polars uses 'calamine' engine by default for Excel, which is extremely fast
            # We load the sheet, then slice the first N rows
            full_df = pl.read_excel(self.file_path)
            self.preview_df = full_df.head(preview_rows)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        self._extract_schema()
        return self.preview_df

    def _extract_schema(self) -> None:
        """Extracts headers and data types from the loaded preview DataFrame."""
        if self.preview_df is not None:
            self.headers = self.preview_df.columns
            # Map Polars dtypes to string representations for the GUI
            self.dtypes = {col: str(dtype) for col, dtype in zip(self.headers, self.preview_df.dtypes)}

    def get_headers(self) -> List[str]:
        """Returns the list of column headers."""
        return self.headers

    def get_dtypes(self) -> Dict[str, str]:
        """Returns a dictionary mapping column names to their inferred data types."""
        return self.dtypes