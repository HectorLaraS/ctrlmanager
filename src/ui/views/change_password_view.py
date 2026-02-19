import tkinter as tk
from tkinter import messagebox

from src.core.config import AppConfig


class ChangePasswordWindow:
    """
    Modal window.
    After closing:
      - self.changed == True if password was updated
      - self.new_password contains the new password (only for immediate re-login flow)
    """
    def __init__(self, config: AppConfig, username: str, auth_service):
        self.config = config
        self.username = username
        self.auth_service = auth_service

        self.changed = False
        self.new_password = None

        self.win = tk.Toplevel()
        self.win.title("Cambiar password")
        self.win.geometry("460x240")
        self.win.resizable(False, False)

        # Theme
        self.bg = self.config.back_color
        self.label_bg = self.config.label_color
        self.button_bg = self.config.button_color
        self.accent = self.config.accent_color
        self.text_color = self.config.text_color
        self.button_text_color = self.config.button_text_color
        self.input_bg = self.config.input_bg
        self.input_text_color = self.config.input_text_color
        self.box_bg = self.config.box_color

        self.win.configure(bg=self.bg)

        # Modal behavior
        self.win.transient()
        self.win.grab_set()

        # Prevent closing without action (opcional)
        self.win.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self._build_ui()
        self.win.bind("<Return>", lambda e: self._on_save())

    def _build_ui(self):
        root = tk.Frame(self.win, bg=self.bg)
        root.pack(fill="both", expand=True, padx=18, pady=18)

        title = tk.Label(
            root,
            text=f"Usuario: {self.username}",
            bg=self.bg,
            fg=self.text_color,
            font=("Segoe UI", 11, "bold"),
        )
        title.pack(anchor="w", pady=(0, 12))

        form = tk.Frame(root, bg=self.bg)
        form.pack(fill="x")

        tk.Label(form, text="Nuevo password", bg=self.label_bg, fg="#111111", padx=10, pady=6).grid(
            row=0, column=0, sticky="e", padx=(0, 12), pady=8
        )
        self.new_entry = tk.Entry(
            form,
            show="*",
            bg=self.input_bg,
            fg=self.input_text_color,
            relief="flat",
            highlightthickness=2,
            highlightbackground=self.box_bg,
            highlightcolor=self.button_bg,
            insertbackground=self.input_text_color,
            width=26
        )
        self.new_entry.grid(row=0, column=1, pady=8)
        self.new_entry.focus_set()

        tk.Label(form, text="Confirmar", bg=self.label_bg, fg="#111111", padx=10, pady=6).grid(
            row=1, column=0, sticky="e", padx=(0, 12), pady=8
        )
        self.confirm_entry = tk.Entry(
            form,
            show="*",
            bg=self.input_bg,
            fg=self.input_text_color,
            relief="flat",
            highlightthickness=2,
            highlightbackground=self.box_bg,
            highlightcolor=self.button_bg,
            insertbackground=self.input_text_color,
            width=26
        )
        self.confirm_entry.grid(row=1, column=1, pady=8)

        buttons = tk.Frame(root, bg=self.bg)
        buttons.pack(fill="x", pady=(16, 0))

        cancel_btn = tk.Button(
            buttons,
            text="Cancelar",
            command=self._on_cancel,
            bg=self.box_bg,
            fg=self.text_color,
            relief="flat",
            cursor="hand2",
            width=14
        )
        cancel_btn.pack(side="left")

        save_btn = tk.Button(
            buttons,
            text="Guardar",
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

    def _on_cancel(self):
        # No cambió password
        self.changed = False
        self.new_password = None
        self.win.destroy()

    def _on_save(self):
        new_pw = (self.new_entry.get() or "").strip()
        confirm_pw = (self.confirm_entry.get() or "").strip()

        if not new_pw or not confirm_pw:
            messagebox.showwarning("Password", "Completa ambos campos.")
            return

        if new_pw != confirm_pw:
            messagebox.showerror("Password", "Los passwords no coinciden.")
            return

        try:
            self.auth_service.change_password(self.username, new_pw)
            self.changed = True
            self.new_password = new_pw
            messagebox.showinfo("Password", "Password actualizado correctamente.")
            self.win.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))
