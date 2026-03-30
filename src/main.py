1# src/main.py
import sys
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow

def main() -> None:
    """Entry point for the application."""
    app = QApplication(sys.argv)
    
    # Modern style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()