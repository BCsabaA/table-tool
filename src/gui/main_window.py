# src/gui/main_window.py
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QTableView, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from src.core.data_loader import DataLoader
from src.gui.models.dataframe_model import DataFrameModel


class MainWindow(QMainWindow):
    """
    Main application window containing the drag-and-drop zone and data tables.
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Data Tool v1")
        self.resize(1024, 768)
        
        # Initialize backend core
        self.data_loader = DataLoader()
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initializes the user interface components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Drag and Drop Label
        self.drop_label = QLabel("Drag and Drop a file here (CSV, TXT, XLSX)")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                padding: 20px;
                background-color: #f9f9f9;
                color: #333;
                font-size: 16px;
            }
        """)
        layout.addWidget(self.drop_label)
        
        # Data Table View
        self.table_view = QTableView()
        layout.addWidget(self.table_view)
        
        # Enable drag and drop on the main window
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Accepts the drag event if it contains URLs (files)."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handles the dropped file."""
        urls = event.mimeData().urls()
        if not urls:
            return
            
        # Take the first dropped file
        file_path = Path(urls[0].toLocalFile())
        
        try:
            # 1. Load preview data via core logic
            df = self.data_loader.load_preview(file_path)
            
            # 2. Update UI
            self.drop_label.setText(f"Loaded: {file_path.name}")
            
            # 3. Bind data to table view
            model = DataFrameModel(df)
            self.table_view.setModel(model)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")