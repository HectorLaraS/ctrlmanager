import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from src.core.config import AppConfig
from src.service.user_service import UserService, UserServiceError


class EditUserWindow:
    def __init__(self, parent: tk.Tk, config: AppConfig, user_service: UserService, user_row: dict):
        self.parent = parent
        self.config = config
        self.user_service = user_service
        self.user_row = user_row

        self.updated = False

        self.win = tk.Toplevel(parent)
        self.win.title("Editar usuario")
        self.win.geometry("430x520")
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

        username = self.user_row["username"]

        tk.Label(
            root,
            text=f"Editar usuario: {username}",
            bg=self.bg,
            fg=self.text_color,
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        form = tk.Frame(root, bg=self.bg)
        form.pack(fill="x")

        self.display_var = tk.StringVar(value=self.user_row.get("display_name", ""))
        self.email_var = tk.StringVar(value=self.user_row.get("email", ""))
        self.role_var = tk.StringVar(value=self.user_row.get("role_code", "viewer"))
        self.active_var = tk.IntVar(value=int(self.user_row.get("is_active", 1)))

        # Username (readonly label)
        tk.Label(form, text="Username", bg=self.label_bg, fg="#111111", padx=10, pady=6).grid(
            row=0, column=0, sticky="e", padx=(0, 12), pady=8
        )
        tk.Label(form, text=username, bg=self.bg, fg=self.text_color, font=("Segoe UI", 10, "bold")).grid(
            row=0, column=1, sticky="w", pady=8
        )

        self._row_entry(form, 1, "Display Name", self.display_var)
        self._row_entry(form, 2, "Email", self.email_var)
        self._row_combo(form, 3, "Role", self.role_var, values=["admin", "operator", "viewer"])

        # Active checkbox
        tk.Label(form, text="Activo", bg=self.label_bg, fg="#111111", padx=10, pady=6).grid(
            row=4, column=0, sticky="e", padx=(0, 12), pady=8
        )
        tk.Checkbutton(
            form,
            text="is_active",
            variable=self.active_var,
            onvalue=1,
            offvalue=0,
            bg=self.bg,
            fg=self.text_color,
            activebackground=self.bg,
            activeforeground=self.text_color,
            selectcolor=self.bg
        ).grid(row=4, column=1, sticky="w", pady=8)

        # Reset password section
        sep = tk.Frame(root, bg=self.accent, height=2)
        sep.pack(fill="x", pady=(16, 12))

        tk.Label(
            root,
            text="Reset password (temporal)",
            bg=self.bg,
            fg=self.text_color,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        reset_row = tk.Frame(root, bg=self.bg)
        reset_row.pack(fill="x", pady=(8, 0))

        self.temp_pw_var = tk.StringVar()

        tk.Label(reset_row, text="Temp Password", bg=self.label_bg, fg="#111111", padx=10, pady=6).pack(
            side="left", padx=(0, 12)
        )
        tk.Entry(
            reset_row,
            textvariable=self.temp_pw_var,
            show="*",
            bg=self.input_bg,
            fg=self.input_text_color,
            relief="flat",
            highlightthickness=2,
            highlightbackground=self.box_bg,
            highlightcolor=self.button_bg,
            insertbackground=self.input_text_color,
            width=26
        ).pack(side="left")

        reset_btn = tk.Button(
            reset_row,
            text="Reset",
            command=self._on_reset_password,
            bg=self.button_bg,
            fg=self.button_text_color,
            relief="flat",
            cursor="hand2",
            activebackground=self.accent,
            activeforeground=self.button_text_color,
            width=10
        )
        reset_btn.pack(side="left", padx=(12, 0))
        reset_btn.bind("<Enter>", lambda e: reset_btn.configure(bg=self.accent))
        reset_btn.bind("<Leave>", lambda e: reset_btn.configure(bg=self.button_bg))

        # Segunda línea divisoria (entre reset y botones finales)
        sep2 = tk.Frame(root, bg=self.accent, height=2)
        sep2.pack(fill="x", pady=(16, 12))

        # Bottom buttons
        buttons = tk.Frame(root, bg=self.bg)
        buttons.pack(fill="x", pady=(18, 0))

        tk.Button(
            buttons,
            text="Cerrar",
            command=self._on_cancel,
            bg=self.box_bg,
            fg=self.text_color,
            relief="flat",
            cursor="hand2",
            width=14
        ).pack(side="left")

        save_btn = tk.Button(
            buttons,
            text="Guardar cambios",
            command=self._on_save,
            bg=self.button_bg,
            fg=self.button_text_color,
            relief="flat",
            cursor="hand2",
            activebackground=self.accent,
            activeforeground=self.button_text_color,
            width=16
        )
        save_btn.pack(side="right")
        save_btn.bind("<Enter>", lambda e: save_btn.configure(bg=self.accent))
        save_btn.bind("<Leave>", lambda e: save_btn.configure(bg=self.button_bg))

    def _row_entry(self, parent: tk.Frame, row: int, label: str, var: tk.StringVar):
        tk.Label(parent, text=label, bg=self.label_bg, fg="#111111", padx=10, pady=6).grid(
            row=row, column=0, sticky="e", padx=(0, 12), pady=8
        )
        tk.Entry(
            parent,
            textvariable=var,
            bg=self.input_bg,
            fg=self.input_text_color,
            relief="flat",
            highlightthickness=2,
            highlightbackground=self.box_bg,
            highlightcolor=self.button_bg,
            insertbackground=self.input_text_color,
            width=34
        ).grid(row=row, column=1, sticky="w", pady=8)

    def _row_combo(self, parent: tk.Frame, row: int, label: str, var: tk.StringVar, values):
        tk.Label(parent, text=label, bg=self.label_bg, fg="#111111", padx=10, pady=6).grid(
            row=row, column=0, sticky="e", padx=(0, 12), pady=8
        )
        ttk.Combobox(
            parent,
            textvariable=var,
            values=values,
            state="readonly",
            width=33
        ).grid(row=row, column=1, sticky="w", pady=8)

    def _on_cancel(self):
        self.win.destroy()

    def _on_save(self):
        username = self.user_row["username"]

        try:
            self.user_service.update_user(
                username=username,
                display_name=(self.display_var.get() or "").strip(),
                email=(self.email_var.get() or "").strip() or None,
                role_code=(self.role_var.get() or "").strip(),
                is_active=int(self.active_var.get()),
            )
            self.updated = True
            messagebox.showinfo("Usuarios", "Usuario actualizado correctamente.")
            self.win.destroy()
        except UserServiceError as e:
            messagebox.showerror("Validación", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el usuario:\n{e}")

    def _on_reset_password(self):
        username = self.user_row["username"]
        temp_pw = (self.temp_pw_var.get() or "").strip()

        if not temp_pw:
            messagebox.showwarning("Reset password", "Ingresa un password temporal.")
            return

        try:
            self.user_service.reset_password(username, temp_pw)
            self.updated = True
            self.temp_pw_var.set("")
            messagebox.showinfo("Usuarios", "Password reseteado. El usuario deberá cambiarlo al iniciar sesión.")
        except UserServiceError as e:
            messagebox.showerror("Validación", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo resetear el password:\n{e}")