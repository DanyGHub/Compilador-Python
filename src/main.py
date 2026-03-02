import sys
from PyQt6.QtWidgets import QApplication
from ide_window import CompilerIDE

# Arranca el IDE
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CompilerIDE()
    window.show()
    sys.exit(app.exec())