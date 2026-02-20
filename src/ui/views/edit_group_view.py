import tkinter as tk
from tkinter import messagebox

from src.core.config import AppConfig


class EditGroupWindow:
    def __init__(self, parent: tk.Tk, config: AppConfig, groups_repo, group_code: str, group_name: str, service_name: str):
        self.parent = parent
        self.config = config
        self.groups_repo = groups_repo

        self.updated = False
        self.group_code = group_code

        self.win = tk.Toplevel(parent)
        self.win.title("Editar Group")
        self.win.geometry("520x280")
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

        self.name_var = tk.StringVar(value=group_name)
        self.service_var = tk.StringVar(value=service_name)

        self._build_ui()
        self.win.bind("<Return>", lambda e: self._on_save())

    def _build_ui(self):
        root = tk.Frame(self.win, bg=self.bg)
        root.pack(fill="both", expand=True, padx=18, pady=18)

        tk.Label(
            root,
            text=f"Editar Group: {self.group_code}",
            bg=self.bg,
            fg=self.text_color,
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        form = tk.Frame(root, bg=self.bg)
        form.pack(fill="x")

        # GroupCode solo lectura (label)
        tk.Label(form, text="GroupCode", bg=self.label_bg, fg="#111111", padx=10, pady=6).grid(
            row=0, column=0, sticky="e", padx=(0, 12), pady=8
        )
        tk.Label(form, text=self.group_code, bg=self.bg, fg=self.text_color, font=("Segoe UI", 10, "bold")).grid(
            row=0, column=1, sticky="w", pady=8
        )

        self._row_entry(form, 1, "GroupName", self.name_var)
        self._row_entry(form, 2, "ServiceName", self.service_var)

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
        entry = tk.Entry(
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
        )
        entry.grid(row=row, column=1, sticky="w", pady=8)

    def _on_cancel(self):
        self.updated = False
        self.win.destroy()

    def _on_save(self):
        name = (self.name_var.get() or "").strip()
        service = (self.service_var.get() or "").strip()

        if not name:
            messagebox.showwarning("Validación", "GroupName es requerido.")
            return

        try:
            self.groups_repo.update_group(self.group_code, name, service)
            self.updated = True
            messagebox.showinfo("Groups", "Group actualizado correctamente.")
            self.win.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el group:\n{e}")
