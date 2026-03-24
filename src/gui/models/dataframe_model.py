# src/gui/models/dataframe_model.py
import polars as pl
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import Any

class DataFrameModel(QAbstractTableModel):
    """
    A Qt Table Model that interfaces with a Polars DataFrame.
    Read-only for the initial preview.
    """
    
    def __init__(self, data: pl.DataFrame, parent: Any = None):
        super().__init__(parent)
        self._data = data

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return self._data.height

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return self._data.width

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
            
        if role == Qt.ItemDataRole.DisplayRole:
            # Polars .item(row, col) is the fastest and safest way to get a single scalar value
            value = self._data.item(index.row(), index.column())
            
            # Convert nulls/None to empty string for display
            return str(value) if value is not None else ""
            
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._data.columns[section]
            if orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return None