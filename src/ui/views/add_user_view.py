# src/ui/views/add_user_view.py
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from src.core.config import AppConfig
from src.service.user_service import UserService, UserServiceError, CreateUserRequest


class AddUserWindow:
    def __init__(self, parent: tk.Tk, config: AppConfig, user_service: UserService):
        self.parent = parent
        self.config = config
        self.user_service = user_service

        self.created = False

        self.win = tk.Toplevel(parent)
        self.win.title("Agregar usuario")
        self.win.geometry("560x380")
        self.win.resizable(False, False)

        # Theme
        self.bg = self.config.back_color
        self.box_bg = self.config.box_color
        self.label_bg = self.config.label_color
        self.button_bg = self.config.button_color
        self.accent = self.config.accent_color
        self.text_color = self.config.text_color
        self.button_text_color = self.config.button_text_color
        self.input_bg = self.config.input_bg
        self.input_text_color = self.config.input_text_color

        self.win.configure(bg=self.bg)
        self.win.transient(parent)
        self.win.grab_set()
        self.win.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self._setup_ttk_style()
        self._build_ui()
        self.win.bind("<Return>", lambda e: self._on_save())

    def _setup_ttk_style(self):
        style = ttk.Style(self.win)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "TCombobox",
            fieldbackground=self.input_bg,
            background=self.input_bg,
            foreground=self.input_text_color
        )

    def _build_ui(self):
        root = tk.Frame(self.win, bg=self.bg)
        root.pack(fill="both", expand=True, padx=18, pady=18)

        tk.Label(
            root,
            text="Nuevo usuario",
            bg=self.bg,
            fg=self.text_color,
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        form = tk.Frame(root, bg=self.bg)
        form.pack(fill="x")

        self.username_var = tk.StringVar()
        self.display_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.role_var = tk.StringVar(value="viewer")
        self.pw_var = tk.StringVar()

        self._row_entry(form, 0, "Username", self.username_var, focus=True)
        self._row_entry(form, 1, "Display Name", self.display_var)
        self._row_entry(form, 2, "Email (opcional)", self.email_var)
        self._row_combo(form, 3, "Role", self.role_var, values=["admin", "operator", "viewer"])
        self._row_entry(form, 4, "Password inicial", self.pw_var, is_password=True)

        hint = tk.Label(
            root,
            text="Nota: el usuario será creado con must_change_password=1 (debe cambiar password al entrar).",
            bg=self.bg,
            fg=self.text_color,
            font=("Segoe UI", 9),
        )
        hint.pack(anchor="w", pady=(10, 0))

        buttons = tk.Frame(root, bg=self.bg)
        buttons.pack(fill="x", pady=(18, 0))

        tk.Button(
            buttons,
            text="Cancelar",
            command=self._on_cancel,
            bg=self.box_bg,
            fg=self.text_color,
            relief="flat",
            cursor="hand2",
            width=14
        ).pack(side="left")

        save_btn = tk.Button(
            buttons,
            text="Crear",
            command=self._on_save,
            bg=self.button_bg,
            fg=self.button_text_color,
            relief="flat",
            cursor="hand2",
            activebackground=self.accent,
            activeforeground=self.button_text_color,
            width=14
        )
        save_btn.pack(side="right")
        save_btn.bind("<Enter>", lambda e: save_btn.configure(bg=self.accent))
        save_btn.bind("<Leave>", lambda e: save_btn.configure(bg=self.button_bg))

    def _row_entry(self, parent: tk.Frame, row: int, label: str, var: tk.StringVar, is_password: bool = False, focus: bool = False):
        tk.Label(parent, text=label, bg=self.label_bg, fg="#111111", padx=10, pady=6).grid(
            row=row, column=0, sticky="e", padx=(0, 12), pady=8
        )
        entry = tk.Entry(
            parent,
            textvariable=var,
            show="*" if is_password else "",
            bg=self.input_bg,
            fg=self.input_text_color,
            relief="flat",
            highlightthickness=2,
            highlightbackground=self.box_bg,
            highlightcolor=self.button_bg,
            insertbackground=self.input_text_color,
            width=34
        )
        entry.grid(row=row, column=1, sticky="w", pady=8)
        if focus:
            entry.focus_set()

    def _row_combo(self, parent: tk.Frame, row: int, label: str, var: tk.StringVar, values):
        tk.Label(parent, text=label, bg=self.label_bg, fg="#111111", padx=10, pady=6).grid(
            row=row, column=0, sticky="e", padx=(0, 12), pady=8
        )
        combo = ttk.Combobox(
            parent,
            textvariable=var,
            values=values,
            state="readonly",
            width=33
        )
        combo.grid(row=row, column=1, sticky="w", pady=8)

    def _on_cancel(self):
        self.created = False
        self.win.destroy()

    def _on_save(self):
        req = CreateUserRequest(
            username=(self.username_var.get() or "").strip(),
            display_name=(self.display_var.get() or "").strip(),
            email=(self.email_var.get() or "").strip() or None,
            role_code=(self.role_var.get() or "").strip(),
            initial_password=(self.pw_var.get() or "").strip(),
        )

        try:
            self.user_service.create_user(req)
            self.created = True
            messagebox.showinfo("Usuarios", "Usuario creado correctamente.")
            self.win.destroy()
        except UserServiceError as e:
            messagebox.showerror("Validación", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el usuario:\n{e}")