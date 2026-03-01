import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow

# Importamos Interfaz
from ui.ui_main import Ui_MainWindow 

class CompilerIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Cargar estilos QSS
        self.load_stylesheet()

    def load_stylesheet(self):
        # Ruta al archivo de estilos
        # os.path funciona sin importar desde dónde el script
        base_path = os.path.dirname(__file__)
        style_path = os.path.join(base_path, "resources", "style.qss")
        
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"Advertencia: No se encontró el archivo de estilos en {style_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Aplicar estilos a nivel de App para que afecten a diálogos emergentes también
    window = CompilerIDE()
    window.show()
    
    sys.exit(app.exec())