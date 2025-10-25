import sys, os, csv, time
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

# --- Flexible imports ---
try:
    from .lexer import Lexer, LexError
    from .colors import TOKEN_COLORS, BACKGROUND, FOREGROUND, ERROR_BG
except Exception:
    sys.path.append(os.path.dirname(__file__))
    from lexer import Lexer, LexError
    from colors import TOKEN_COLORS, BACKGROUND, FOREGROUND, ERROR_BG

APP_TITLE = "Coloreador Léxico – Proyecto II"
STATUS_OK = "✅ Archivo válido"
STATUS_ERR = "❌ Error léxico"

def _safe_basename(path: str) -> str:
    name = os.path.basename(path)
    # quita caracteres problemáticos para nombre de archivo
    return "".join(ch for ch in name if ch not in '\\/:*?"<>|')

def _timestamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")



def _write_report_txt(tokens, report_dir, in_path, *, had_error=False, err_line=None, err_col=None, err_msg=None, code_text=""):
    """
    Genera **solo** un TXT de resumen breve, nombrado como el archivo original + '.reporte.txt'.
    Formato:
      Archivo, Fecha, Estado, (Tokens procesados si OK) o (Línea, Columna, Mensaje y caret si ERROR).
    """
    os.makedirs(report_dir, exist_ok=True)
    base = os.path.basename(in_path)
    safe = _safe_basename(base)
    txt_path = os.path.join(report_dir, f"{safe}.reporte.txt")
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # Contenido
    lines = []
    lines.append(f"Archivo: {in_path}")
    lines.append(f"Fecha: {stamp}")
    lines.append(f"Estado: {'ERROR' if had_error else 'OK'}")
    if had_error:
        lines.append(f"Línea: {err_line}, Columna: {err_col}")
        if err_msg:
            lines.append(f"Mensaje: {err_msg}")
        # caret
        if code_text and err_line:
            src_lines = code_text.splitlines()
            if 1 <= err_line <= len(src_lines):
                L = src_lines[err_line-1]
                lines.append("")
                lines.append(L)
                caret = " "*(max(0, (err_col or 1)-1)) + "^"
                lines.append(caret)
    else:
        # contar tokens (excluyendo NL y EOF)
        count = sum(1 for t in tokens if getattr(t, "type", "") not in ("NL","EOF"))
        lines.append(f"Tokens procesados: {count}")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return txt_path
def colorize_text(text_widget: ScrolledText, code: str, tokens):
    text_widget.config(state="normal")
    text_widget.delete("1.0", "end")
    text_widget.insert("1.0", code)

    # Prepare tags
    text_widget.tag_configure("default", foreground=FOREGROUND, background=BACKGROUND)
    for ttype, fg in TOKEN_COLORS.items():
        if ttype == "ERROR":
            text_widget.tag_configure("ERROR", foreground=TOKEN_COLORS["ERROR"], background=ERROR_BG, underline=1)
        else:
            text_widget.tag_configure(ttype, foreground=fg, background=BACKGROUND)

    # Apply default
    text_widget.tag_add("default", "1.0", "end")

    # Walk tokens and tag spans
    for tok in tokens:
        if tok.type in ("EOF","NL"):
            continue
        start_index = f"{tok.line}.{tok.col-1}"
        end_index = f"{tok.line}.{tok.col-1+len(tok.value)}"
        tag = tok.type if tok.type in TOKEN_COLORS else "default"
        text_widget.tag_add(tag, start_index, end_index)

    text_widget.config(state="disabled")

def analyze_file(path, root, text_widget, status_label, report_dir, save_invalid=True):
    try:
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")
        return

