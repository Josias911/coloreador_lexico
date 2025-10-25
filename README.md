# Proyecto 2 – Coloreador Léxico (Python / Tkinter)

Coloreador Léxico con fondo oscuro que **lee un archivo**, **tokeniza** y **colorea** según reglas del enunciado.
Se **detiene en el primer error** léxico e informa **línea y columna**. También genera un **reporte CSV** de tokens.

## ✅ Reglas de color
- **Palabras reservadas**: azul
- **Números / constantes / booleanos (`true/false` o `verdadero/falso`) / `nil`**: anaranjado
- **Signos de agrupación** `() [] {}`: blanco
- **Comparación / lógicos** (`> < == = != <> >= <= and or not`): amarillo
- **Cadenas** `"..."` o `'...'`: verde claro
- **Identificadores** (variables): rosado
- **Comentarios** (`//` o `/* ... */`): gris
- **Error**: **fondo rojo + texto blanco** (se detiene el análisis)

Fondo: tema **dark** (estilo editor).

> Palabras reservadas por defecto: estilo **PSeInt/Pseudocódigo** (e.g., `Algoritmo, Definir, Si, Entonces, FinSi, ...`). Puedes ampliarlas en `Lexer(custom_keywords=...)`.

## 🗂 Estructura
```
coloreador_lexico/
├─ src/
│  ├─ __init__.py
│  ├─ lexer.py
│  ├─ colors.py
│  └─ main.py         # GUI (Tkinter) y CLI
├─ tests/
│  ├─ valido1.pseudo
│  ├─ valido2.pseudo
│  ├─ valido3.pseudo
│  ├─ invalido1.pseudo
│  ├─ invalido2.pseudo
│  └─ invalido3.pseudo
├─ README.md
└─ requirements.txt
```

## ▶️ Cómo ejecutar (Visual Studio Code)
1. **Abrir carpeta** `coloreador_lexico` en VS Code.
2. Crear/usar un **entorno** de Python 3.10+ (Windows/macOS/Linux).
3. (No hay dependencias externas) – `requirements.txt` está vacío.
4. **Ejecutar GUI**:
   ```bash
   python -m src.main --gui
   ```
   o simplemente:
   ```bash
   python src/main.py
   ```
5. **Modo consola**:
   ```bash
   python -m src.main tests/valido1.pseudo
   ```

## 🧪 Archivos de prueba
- En `tests/` hay **3 válidos** y **3 inválidos** (se detiene en el primer error).

## 📝 Reporte
Al analizar por GUI se genera `reports/<archivo>.tokens.csv` con:
`type, value, line, col, ui_color_hex`.

## 🔧 Personalización de palabras reservadas
```python
from src.lexer import Lexer
code = open("tests/valido1.pseudo","r",encoding="utf-8").read()
lexer = Lexer(code, custom_keywords=["begin","end","var","procedure","function","if","then","else","while","for","return"])
```

---

Hecho con ❤️ para el curso de **Autómatas y Lenguajes Formales**.
