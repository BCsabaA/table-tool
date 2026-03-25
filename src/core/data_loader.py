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
    
    # Map string representations from the UI to actual Polars Data Types
    TYPE_MAPPING = {
        "String": pl.String,
        "Int64": pl.Int64,
        "Float64": pl.Float64,
        "Boolean": pl.Boolean,
        "Date": pl.Date,
        "Datetime": pl.Datetime
    }
    
    def __init__(self) -> None:
        self.file_path: Optional[Path] = None
        self.preview_df: Optional[pl.DataFrame] = None
        self.headers: List[str] = []
        self.dtypes: Dict[str, str] = {}

    def _detect_separator(self, file_path: Path, ext: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sample = f.read(4096)
                dialect = csv.Sniffer().sniff(sample)
                return dialect.delimiter
        except Exception:
            return ';' if ext == '.csv' else '\t'

    def load_preview(self, file_path: Union[str, Path], preview_rows: int = 200) -> pl.DataFrame:
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        ext = self.file_path.suffix.lower()

        if ext in ['.csv', '.txt']:
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

    def apply_schema(self, new_headers: List[str], new_types: List[str]) -> pl.DataFrame:
        """
        Applies new column names and data types to the DataFrame.
        """
        if self.preview_df is None:
            raise ValueError("No data loaded to apply schema to.")
            
        if len(new_headers) != len(self.headers):
            raise ValueError("Number of new headers does not match existing columns.")

        # 1. Rename columns mapping old names to new names
        rename_map = dict(zip(self.headers, new_headers))
        df = self.preview_df.rename(rename_map)

        # 2. Cast data types
        cast_exprs = []
        for col_name, type_str in zip(new_headers, new_types):
            pl_type = self.TYPE_MAPPING.get(type_str, pl.String)
            # strict=False means if a string can't be parsed to Int (e.g. "apple"), it becomes Null
            # instead of crashing the entire application.
            cast_exprs.append(pl.col(col_name).cast(pl_type, strict=False))

        df = df.with_columns(cast_exprs)

        # 3. Update internal state
        self.preview_df = df
        self._extract_schema()
        
        return self.preview_df

    def _extract_schema(self) -> None:
        if self.preview_df is not None:
            self.headers = self.preview_df.columns
            self.dtypes = {col: str(dtype) for col, dtype in zip(self.headers, self.preview_df.dtypes)}

    def get_headers(self) -> List[str]:
        return self.headers

    def get_dtypes(self) -> Dict[str, str]:
        return self.dtypes

