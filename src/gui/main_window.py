# src/gui/main_window.py
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QTableView, QMessageBox,
    QTableWidget, QTableWidgetItem, QComboBox, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from src.core.data_loader import DataLoader
from src.gui.models.dataframe_model import DataFrameModel

# A Polars leggyakoribb adattípusai a legördülő menühöz (később bővíthető)
POLARS_TYPES = ["String", "Int64", "Float64", "Boolean", "Date", "Datetime"]

class MainWindow(QMainWindow):
    """
    Main application window containing the drag-and-drop zone,
    settings table (headers/types), and the data preview table.
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Data Tool v1")
        self.resize(1024, 768)
        
        self.data_loader = DataLoader()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initializes the user interface components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Drag and Drop Label
        self.drop_label = QLabel("Húzz ide egy fájlt (CSV, TXT, XLSX)")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                padding: 15px;
                background-color: #f9f9f9;
                color: #333;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.drop_label)
        
        # Splitter to allow resizing between settings and data tables
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(self.splitter)
        
        # Settings Table (2 rows)
        self.settings_table = QTableWidget(2, 0)
        self.settings_table.setVerticalHeaderLabels(["Fejléc", "Típus"])
        # Fix height so it doesn't take up too much space, but leaves room for scrollbar
        self.settings_table.setFixedHeight(110) 
        self.splitter.addWidget(self.settings_table)
        
        # Data Table View
        self.table_view = QTableView()
        self.splitter.addWidget(self.table_view)
        
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return
            
        file_path = Path(urls[0].toLocalFile())
        
        try:
            # 1. Load data
            df = self.data_loader.load_preview(file_path)
            self.drop_label.setText(f"Betöltve: {file_path.name}")
            
            # 2. Update Data Table
            model = DataFrameModel(df)
            self.table_view.setModel(model)
            
            # 3. Update Settings Table
            self._populate_settings_table()
            
            # 4. Sync horizontal scrolling (Optional but very helpful)
            self.settings_table.horizontalScrollBar().valueChanged.connect(
                self.table_view.horizontalScrollBar().setValue
            )
            self.table_view.horizontalScrollBar().valueChanged.connect(
                self.settings_table.horizontalScrollBar().setValue
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Nem sikerült betölteni a fájlt:\n{str(e)}")

    def _populate_settings_table(self) -> None:
        """Populates the top table with editable headers and type dropdowns."""
        headers = self.data_loader.get_headers()
        dtypes = self.data_loader.get_dtypes()
        
        col_count = len(headers)
        self.settings_table.setColumnCount(col_count)
        
        for col_idx, header in enumerate(headers):
            # Row 0: Editable Header
            header_item = QTableWidgetItem(header)
            self.settings_table.setItem(0, col_idx, header_item)
            
            # Row 1: Data Type Combobox
            combo = QComboBox()
            combo.addItems(POLARS_TYPES)
            
            # Match current type, fallback to String if unknown
            current_type = dtypes.get(header, "String")
            if current_type in POLARS_TYPES:
                combo.setCurrentText(current_type)
            else:
                combo.setCurrentText("String")
                
            self.settings_table.setCellWidget(1, col_idx, combo)