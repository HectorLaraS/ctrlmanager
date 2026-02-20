# src/ui/views/change_password_view.py
import tkinter as tk
from tkinter import messagebox

from src.core.config import AppConfig
from src.service.user_service import (
    UserService,
    ChangeOwnPasswordRequest,
    AdminChangePasswordRequest,
)


class ChangePasswordWindow:
    """
    Modal reutilizable para cambio de password.

    mode="self":
      - Cambia el password del usuario loggeado
      - Requiere current_password

    mode="admin":
      - Admin cambia password de cualquier usuario
      - No requiere current_password
      - Permite forzar must_change_password

    Salidas:
      - changed (bool): True si se guardó
      - new_password (str): el nuevo password (para re-login si aplica)
      - target_username (str): usuario al que se cambió
    """

    def __init__(
        self,
        parent,
        config: AppConfig,
        user_service: UserService,
        *,
        mode: str,
        logged_username: str,
        target_username: str | None = None,
    ):
        self.parent = parent
        self.config = config
        self.user_service = user_service

        self.mode = (mode or "").lower().strip()
        if self.mode not in ("self", "admin"):
            raise ValueError("mode inválido. Usa 'self' o 'admin'.")

        self.logged_username = (logged_username or "").strip()
        if not self.logged_username:
            raise ValueError("logged_username es requerido.")

        # resultados
        self.changed = False
        self.new_password = ""
        self.target_username = ""

        # ventana
        self.win = tk.Toplevel(parent)
        self.win.title("Cambiar password")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        # theme
        self.bg = self.config.back_color
        self.text_color = self.config.text_color
        self.input_bg = self.config.input_bg
        self.input_text_color = self.config.input_text_color
        self.box_bg = self.config.box_color
        self.button_bg = self.config.button_color
        self.accent = self.config.accent_color

        self.win.configure(bg=self.bg)

        container = tk.Frame(self.win, bg=self.bg)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        title = "Cambiar password"
        tk.Label(
            container,
            text=title,
            bg=self.bg,
            fg=self.text_color,
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # ========= Vars =========
        # admin: usuario objetivo editable
        # self: usuario objetivo fijo al loggeado
        default_target = (target_username or "").strip() or self.logged_username
        self.target_user_var = tk.StringVar(value=default_target)

        # self: current password
        self.current_pw_var = tk.StringVar()

        # ambos: new / confirm
        self.new_pw_var = tk.StringVar()
        self.confirm_pw_var = tk.StringVar()

        # admin: forzar cambio
        self.must_change_var = tk.IntVar(value=0)

        row = 1

        # ========= Mode: admin => usuario objetivo =========
        if self.mode == "admin":
            tk.Label(container, text="Usuario objetivo", bg=self.bg, fg=self.text_color).grid(
                row=row, column=0, sticky="w"
            )
            self.target_user_entry = tk.Entry(
                container,
                textvariable=self.target_user_var,
                bg=self.input_bg,
                fg=self.input_text_color,
                relief="flat",
                highlightthickness=2,
                highlightbackground=self.box_bg,
                highlightcolor=self.button_bg,
                insertbackground=self.input_text_color,
                width=30,
            )
            self.target_user_entry.grid(row=row, column=1, sticky="ew", padx=(10, 0))
            row += 1
        else:
            # self mode: mostramos el user fijo
            tk.Label(
                container,
                text=f"Usuario: {self.logged_username}",
                bg=self.bg,
                fg=self.text_color,
                font=("Segoe UI", 10, "bold"),
            ).grid(row=row, column=0, columnspan=2, sticky="w")
            self.target_user_var.set(self.logged_username)
            row += 1

        # ========= Mode: self => password actual =========
        if self.mode == "self":
            tk.Label(container, text="Password actual", bg=self.bg, fg=self.text_color).grid(
                row=row, column=0, sticky="w", pady=(8, 0)
            )
            self.current_pw_entry = tk.Entry(
                container,
                textvariable=self.current_pw_var,
                bg=self.input_bg,
                fg=self.input_text_color,
                relief="flat",
                highlightthickness=2,
                highlightbackground=self.box_bg,
                highlightcolor=self.button_bg,
                insertbackground=self.input_text_color,
                show="*",
                width=30,
            )
            self.current_pw_entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=(8, 0))
            row += 1

        # ========= Nuevo password =========
        tk.Label(container, text="Nuevo password", bg=self.bg, fg=self.text_color).grid(
            row=row, column=0, sticky="w", pady=(8, 0)
        )
        self.new_pw_entry = tk.Entry(
            container,
            textvariable=self.new_pw_var,
            bg=self.input_bg,
            fg=self.input_text_color,
            relief="flat",
            highlightthickness=2,
            highlightbackground=self.box_bg,
            highlightcolor=self.button_bg,
            insertbackground=self.input_text_color,
            show="*",
            width=30,
        )
        self.new_pw_entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=(8, 0))
        row += 1

        # ========= Confirmar =========
        tk.Label(container, text="Confirmar", bg=self.bg, fg=self.text_color).grid(
            row=row, column=0, sticky="w", pady=(8, 0)
        )
        self.confirm_pw_entry = tk.Entry(
            container,
            textvariable=self.confirm_pw_var,
            bg=self.input_bg,
            fg=self.input_text_color,
            relief="flat",
            highlightthickness=2,
            highlightbackground=self.box_bg,
            highlightcolor=self.button_bg,
            insertbackground=self.input_text_color,
            show="*",
            width=30,
        )
        self.confirm_pw_entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=(8, 0))
        row += 1

        # ========= Admin: checkbox =========
        if self.mode == "admin":
            self.must_change_chk = tk.Checkbutton(
                container,
                text="Forzar cambio al siguiente login",
                variable=self.must_change_var,
                bg=self.bg,
                fg=self.text_color,
                activebackground=self.bg,
                activeforeground=self.text_color,
                selectcolor=self.bg,
            )
            self.must_change_chk.grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 0))
            row += 1

        # ========= Buttons =========
        btns = tk.Frame(container, bg=self.bg)
        btns.grid(row=row, column=0, columnspan=2, sticky="e", pady=(14, 0))

        cancel_btn = tk.Button(
            btns,
            text="Cancelar",
            command=self._on_cancel,
            bg=self.box_bg,
            fg=self.text_color,
            relief="flat",
            padx=14,
            pady=6,
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        save_btn = tk.Button(
            btns,
            text="Guardar",
            command=self._on_save,
            bg=self.button_bg,
            fg=self.text_color,
            relief="flat",
            activebackground=self.accent,
            activeforeground=self.text_color,
            padx=14,
            pady=6,
        )
        save_btn.pack(side="left")

        container.columnconfigure(1, weight=1)

        # focus inicial
        if self.mode == "admin":
            self.target_user_entry.focus_set()
        else:
            self.current_pw_entry.focus_set()

        self.win.bind("<Return>", lambda _e: self._on_save())
        self.win.bind("<Escape>", lambda _e: self._on_cancel())

    def _on_cancel(self):
        self.changed = False
        self.new_password = ""
        self.target_username = ""
        self.win.destroy()

    def _on_save(self):
        target_user = (self.target_user_var.get() or "").strip()
        current_pw = (self.current_pw_var.get() or "").strip()
        new_pw = (self.new_pw_var.get() or "").strip()
        confirm = (self.confirm_pw_var.get() or "").strip()

        if not target_user:
            messagebox.showerror("Error", "Debes indicar el usuario.")
            return

        if len(new_pw) < 8:
            messagebox.showerror("Error", "El nuevo password debe tener al menos 8 caracteres.")
            return

        if new_pw != confirm:
            messagebox.showerror("Error", "El password y la confirmación no coinciden.")
            return

        if self.mode == "self":
            if not current_pw:
                messagebox.showerror("Error", "Ingresa el password actual.")
                return
            if new_pw == current_pw:
                messagebox.showerror("Error", "El nuevo password debe ser diferente al actual.")
                return

        try:
            if self.mode == "admin":
                req = AdminChangePasswordRequest(
                    target_username=target_user,
                    new_password=new_pw,
                    must_change_password=int(self.must_change_var.get()),
                )
                self.user_service.admin_change_password(req)
            else:
                req = ChangeOwnPasswordRequest(
                    username=self.logged_username,
                    current_password=current_pw,
                    new_password=new_pw,
                )
                self.user_service.change_own_password(req)

            self.changed = True
            self.new_password = new_pw
            self.target_username = target_user
            self.win.destroy()

        except Exception as e:
            messagebox.showerror("Error", str(e))