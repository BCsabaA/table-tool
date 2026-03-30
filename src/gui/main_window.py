# src/gui/main_window.py
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QTableView, QMessageBox,
    QTableWidget, QTableWidgetItem, QComboBox, QSplitter, QPushButton,
    QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from src.core.data_loader import DataLoader
from src.gui.models.dataframe_model import DataFrameModel

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
        self.current_file_path: Optional[Path] = None  # Eltároljuk a bedobott fájl útvonalát
        self._setup_ui()

    def _setup_ui(self) -> None:
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
        
        # --- ÚJ: Fejléc Checkbox ---
        self.header_checkbox = QCheckBox("A forrásfájl tartalmaz fejlécet az első sorban")
        self.header_checkbox.setChecked(True)
        self.header_checkbox.setEnabled(False) # Csak fájl betöltése után él
        self.header_checkbox.toggled.connect(self._on_header_toggled)
        layout.addWidget(self.header_checkbox)
        
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(self.splitter)
        
        # Settings Table
        self.settings_table = QTableWidget(2, 0)
        self.settings_table.setVerticalHeaderLabels(["Fejléc", "Típus"])
        self.settings_table.setFixedHeight(110) 
        self.splitter.addWidget(self.settings_table)
        
        # Data Table View
        self.table_view = QTableView()
        self.splitter.addWidget(self.table_view)
        
        # Action Button
        self.apply_btn = QPushButton("Fejlécek és típusok véglegesítése")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._validate_and_apply)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        layout.addWidget(self.apply_btn)
        
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return
            
        self.current_file_path = Path(urls[0].toLocalFile())
        self.header_checkbox.setEnabled(True)
        self.apply_btn.setEnabled(True)
        
        # Hívjuk meg a közös betöltő függvényt
        self._load_current_file()

    def _on_header_toggled(self, checked: bool) -> None:
        """Újratölti a fájlt, ha a felhasználó átváltja a fejléc opciót."""
        if self.current_file_path:
            self._load_current_file()

    def _load_current_file(self) -> None:
        """Közös logika a fájl beolvasására és a UI frissítésére."""
        try:
            has_header = self.header_checkbox.isChecked()
            df = self.data_loader.load_preview(self.current_file_path, has_header=has_header)
            self.drop_label.setText(f"Betöltve: {self.current_file_path.name}")
            
            model = DataFrameModel(df)
            self.table_view.setModel(model)
            
            self._populate_settings_table(has_header)
            
            self.settings_table.horizontalScrollBar().valueChanged.connect(
                self.table_view.horizontalScrollBar().setValue
            )
            self.table_view.horizontalScrollBar().valueChanged.connect(
                self.settings_table.horizontalScrollBar().setValue
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Nem sikerült betölteni a fájlt:\n{str(e)}")

    def _populate_settings_table(self, has_header: bool) -> None:
        headers = self.data_loader.get_headers()
        dtypes = self.data_loader.get_dtypes()
        
        col_count = len(headers)
        self.settings_table.setColumnCount(col_count)
        
        for col_idx, header in enumerate(headers):
            # Ha nincs fejléc, a Polars "column_1", "column_2"-t ad vissza.
            # Mi ehelyett üres stringet teszünk be, hogy rákényszerítsük a felhasználót a kitöltésre!
            display_header = header if has_header else ""
            header_item = QTableWidgetItem(display_header)
            self.settings_table.setItem(0, col_idx, header_item)
            
            combo = QComboBox()
            combo.addItems(POLARS_TYPES)
            
            current_type = dtypes.get(header, "String")
            if current_type in POLARS_TYPES:
                combo.setCurrentText(current_type)
            else:
                combo.setCurrentText("String")
                
            self.settings_table.setCellWidget(1, col_idx, combo)

    def _validate_and_apply(self) -> None:
        """Validates the headers for uniqueness and emptiness, then applies changes."""
        col_count = self.settings_table.columnCount()
        new_headers = []
        new_types = []
        
        for col in range(col_count):
            header_item = self.settings_table.item(0, col)
            header_text = header_item.text().strip() if header_item else ""
            
            if not header_text:
                QMessageBox.warning(self, "Validációs hiba", f"A(z) {col + 1}. oszlop fejléce üres!\nMinden fejléc kitöltése kötelező.")
                return
                
            if header_text in new_headers:
                QMessageBox.warning(self, "Validációs hiba", f"A(z) '{header_text}' fejléc többször szerepel!\nMinden fejlécnek egyedinek kell lennie.")
                return
                
            new_headers.append(header_text)
            
            combo = self.settings_table.cellWidget(1, col)
            new_types.append(combo.currentText())
            
        try:
            updated_df = self.data_loader.apply_schema(new_headers, new_types)
            new_model = DataFrameModel(updated_df)
            self.table_view.setModel(new_model)
            
            # Betöltés után visszaállítjuk a pipát igazra, hiszen most már VAN fejléce a DataFramenek!
            self.header_checkbox.setChecked(True)
            self._populate_settings_table(has_header=True)
            
            QMessageBox.information(self, "Siker", "A fejlécek és az adattípusok sikeresen frissültek a DataFrame-ben!")
            
        except Exception as e:
            QMessageBox.critical(self, "Hiba az alkalmazás során", f"A változtatások érvényesítése sikertelen:\n{str(e)}")