# Proyecto de Compiladores

## Generar Entorno Virtual:
- virtualenv {proyecto}

## Usar Entorno Virtual:
- $ cd venv
- $ cd Scripts
- $ .\activate

## Salir del entorno Virtual:
- $(venv) deactivate

## Instalar PyQt6
- En el entorno:
    * $(venv) python -m pip install --upgrade pip
    * $(venv) pip install PyQt6

## Estructura a Utilizar en el Proyecto:
Compiladores/                  # Carpeta raíz del proyecto
│
├── venv/                      # Entorno virtual
│   ├── Include/
│   ├── Lib/
│   ├── Scripts/
│   └── ...
│
├── src/                       # Código fuente
│   ├── main.py                # Punto de entrada del compilador
│   ├── ui/                    # Archivos .ui (Designer) y sus traducciones a Python
│   │   ├── ventana_principal.ui
│   │   └── ventana_principal.py  # (Generado desde el .ui)
│   ├── controllers/           # Lógica del compilador (eventos de botones, etc.)
│   │   └── main_controller.py
│   └── resources/             # Recursos estáticos (QSS, imágenes, iconos)
│       ├── style.qss          # Hoja de estilos QSS
│       └── images/
│
├── requirements.txt           # Dependencias del proyecto
└── README.md

## Transformar un archivo '.ui' -> '.py'
Dentro del entorno 'venv'
    Dentro de la carpeta '\src' y '\ui'
        * $(venv) pyuic6 mainWindow.ui -o ui_main.py

## Compilar Proyecto trasnformado (Abrir ventana desde terminal y python)
Dentro del entorno 'venv'
    Dentro de la carpeta '\src'
        * $(venv) python main.py