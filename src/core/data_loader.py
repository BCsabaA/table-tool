# src/core/data_loader.py
import csv
import polars as pl
from pathlib import Path
from typing import Dict, List, Optional, Union

class DataLoader:
    """
    Handles reading data files, extracting headers, and inferring data types.
    Supports CSV, TXT, and XLSX formats with automatic delimiter detection.
    """
    
    def __init__(self) -> None:
        self.file_path: Optional[Path] = None
        self.preview_df: Optional[pl.DataFrame] = None
        self.headers: List[str] = []
        self.dtypes: Dict[str, str] = {}

    def _detect_separator(self, file_path: Path, ext: str) -> str:
        """Attempts to guess the CSV/TXT separator using python's built-in sniffer."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read a chunk of the file to guess the dialect
                sample = f.read(4096)
                dialect = csv.Sniffer().sniff(sample)
                return dialect.delimiter
        except Exception:
            # Fallback to the v1 specification default if sniffing fails
            return ';' if ext == '.csv' else '\t'

    def load_preview(self, file_path: Union[str, Path], preview_rows: int = 200) -> pl.DataFrame:
        """
        Loads a preview of the file (up to preview_rows) and infers the schema.
        """
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        ext = self.file_path.suffix.lower()

        if ext in ['.csv', '.txt']:
            # Dynamically detect the separator
            separator = self._detect_separator(self.file_path, ext)
            
            self.preview_df = pl.read_csv(
                self.file_path,
                n_rows=preview_rows,
                infer_schema_length=10000,
                separator=separator,
                ignore_errors=True
            )
        elif ext in ['.xlsx', '.xls']:
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
            self.dtypes = {col: str(dtype) for col, dtype in zip(self.headers, self.preview_df.dtypes)}

    def get_headers(self) -> List[str]:
        return self.headers

    def get_dtypes(self) -> Dict[str, str]:
        return self.dtypes