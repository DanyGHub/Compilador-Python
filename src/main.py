# src/main.py
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow

# Importar desde la carpeta ui
from ui.ui_test import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        # Obtener referencias a los widgets (usando los nombres del .ui)
        self.button.clicked.connect(self.on_button_clicked)
        self.actionUno.triggered.connect(lambda: self.on_menu_action("Uno"))
        self.actionDos.triggered.connect(lambda: self.on_menu_action("Dos"))
        self.actionThree.triggered.connect(lambda: self.on_menu_action("Three"))
        self.actionCuatro.triggered.connect(lambda: self.on_menu_action("Cuatro"))
    
    def on_button_clicked(self):
        """Método llamado al hacer clic en el botón"""
        self.label.setText("¡Presionado! 🎉")
        print("Botón clickeado")
    
    def on_menu_action(self, action_name):
        """Manejador para las acciones del menú"""
        print(f"Acción seleccionada: {action_name}")
        self.label.setText(f"Menú: {action_name}")

def load_stylesheet(app):
    """Carga el archivo QSS desde resources"""
    # Construir ruta al archivo QSS
    qss_path = Path(__file__).parent / "resources" / "style.qss"
    
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as file:
            app.setStyleSheet(file.read())
        print(f"✓ Estilo cargado desde: {qss_path}")
    else:
        print(f"✗ Archivo QSS no encontrado: {qss_path}")

def main():
    app = QApplication(sys.argv)
    
    # Cargar estilos
    load_stylesheet(app)
    
    # Crear y mostrar ventana
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()