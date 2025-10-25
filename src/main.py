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
         lexer = Lexer(code)
    tokens = []
    try:
        for tok in lexer.tokens():
            tokens.append(tok)
            if tok.type == "EOF":
                break
    except LexError as e:
        # Añadimos un token ERROR para resaltar
        line_text = code.splitlines()[e.line-1] if e.line-1 < len(code.splitlines()) else ""
        err_char = line_text[e.col-1:e.col] if e.col-1 < len(line_text) else ""
        tokens.append(type("T", (), {"type":"ERROR","value":err_char or "?", "line":e.line, "col":e.col})())

        # colorea y estado
        colorize_text(text_widget, code, tokens)
        status_label.config(text=f"{STATUS_ERR}: línea {e.line}, columna {e.col}", fg="#ff6b6b")

        # **GUARDAR SIEMPRE** reporte de inválidos si está activado
        if save_invalid:
            try:
                out = _write_report_txt(tokens, report_dir, path, had_error=True, err_line=e.line, err_col=e.col, err_msg=str(e), code_text=code)
                # indica dónde se guardó
                status_label.config(text=f"{STATUS_ERR}: línea {e.line}, columna {e.col} • TXT: {out}", fg="#ff6b6b")
            except Exception as we:
                messagebox.showwarning("Advertencia", f"No se pudo guardar el reporte del error:\n{we}")
        return
    except Exception as e:
        messagebox.showerror("Error", f"Fallo inesperado del analizador:\n{e}")
        return

    # Válido
    colorize_text(text_widget, code, tokens)
    status_label.config(text=STATUS_OK, fg="#51cf66")

    # Guardar reporte de válidos también
    try:
        out = _write_report_txt(tokens, report_dir, path, had_error=False, code_text=code)
        status_label.config(text=f"{STATUS_OK} • TXT: {out}", fg="#51cf66")
    except Exception as we:
        messagebox.showwarning("Advertencia", f"No se pudo guardar el reporte:\n{we}")

def main_cli():
    import argparse
    ap = argparse.ArgumentParser(description="Coloreador Léxico (CLI)")
    ap.add_argument("file", help="Ruta de archivo a analizar")
    ap.add_argument("--report-dir", default="reports", help="Carpeta para CSV de tokens")
    ap.add_argument("--no-save-invalid", action="store_true", help="No guarda reportes de archivos inválidos")
    args = ap.parse_args()

    code = open(args.file, "r", encoding="utf-8").read()
    lexer = Lexer(code)
    tokens = []
    try:
        for t in lexer.tokens():
            tokens.append(t)
        print("VALIDO")
        _write_report_txt(tokens, args.report_dir, args.file, had_error=False, code_text=code)
    except LexError as e:
        print(f"ERROR en línea {e.line}, columna {e.col}")
        if not args.no_save_invalid:
            # token de error para CSV
            tokens.append(type("T", (), {"type":"ERROR","value":"?", "line":e.line, "col":e.col})())
            _write_report_txt(tokens, args.report_dir, args.file, had_error=True, err_line=e.line, err_col=e.col, err_msg=str(e), code_text=code)
        sys.exit(1)

def main_gui():
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("1100x740")
    root.configure(bg=BACKGROUND)

    topbar = tk.Frame(root, bg=BACKGROUND)
    topbar.pack(fill="x", padx=10, pady=10)

    file_var = tk.StringVar()
    report_dir = tk.StringVar(value="reports")
    save_invalid_var = tk.BooleanVar(value=True)

    def pick_file():
        path = filedialog.askopenfilename(title="Selecciona un archivo de entrada",
                                          filetypes=[("Text files","*.txt *.pas *.psint *.pseudo *.alg *.pse"),("All","*.*")])
        if path:
            file_var.set(path)

    def pick_report_dir():
        path = filedialog.askdirectory(title="Selecciona carpeta de reportes")
        if path:
            report_dir.set(path)

    tk.Button(topbar, text="📂 Abrir archivo", command=pick_file).pack(side="left")
    tk.Entry(topbar, textvariable=file_var, width=70).pack(side="left", padx=8)

    tk.Label(topbar, text="📄 Reportes:", bg=BACKGROUND, fg=FOREGROUND).pack(side="left", padx=(12,4))
    tk.Entry(topbar, textvariable=report_dir, width=26).pack(side="left")
    tk.Button(topbar, text="…", command=pick_report_dir, width=3).pack(side="left", padx=(4,8))

    tk.Checkbutton(topbar, text="Guardar inválidos", variable=save_invalid_var, bg=BACKGROUND, fg=FOREGROUND, selectcolor=BACKGROUND, activebackground=BACKGROUND, activeforeground=FOREGROUND).pack(side="left", padx=10)

    text = ScrolledText(root, wrap="word", font=("Consolas", 12), bg=BACKGROUND, fg=FOREGROUND, insertbackground="#fff")
    text.pack(fill="both", expand=True, padx=10, pady=(0,10))

    status = tk.Label(root, text="Abre un archivo y presiona Analizar", bg=BACKGROUND, fg="#ced4da", anchor="w", justify="left")
    status.pack(fill="x", padx=10, pady=(0,10))

    def run_analyze():
        path = file_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showwarning("Atención", "Selecciona un archivo válido primero.")
            return
        try:
            analyze_file(path, root, text, status, report_dir.get(), save_invalid=save_invalid_var.get())
        except PermissionError as pe:
            messagebox.showerror("Permisos", f"No se pudo escribir en la carpeta de reportes.\nPrueba otra ruta (ej. C:\\Temp\\reports) o ejecuta VS Code con permisos adecuados.\n\nDetalle:\n{pe}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema al generar reportes:\n{e}")

    b = tk.Button(root, text="▶️ Analizar", command=run_analyze)
    b.pack(pady=(0,10))

    root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] not in ("-m","--gui"):
        main_cli()
    else:
        main_gui()
