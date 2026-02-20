import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from src.core.config import AppConfig
from src.ui.views.edit_user_view import EditUserWindow
from src.ui.views.add_user_view import AddUserWindow


class UsersManagerWindow:
    def __init__(self, parent: tk.Tk, config: AppConfig, user_repo, user_service):
        self.parent = parent
        self.config = config
        self.user_repo = user_repo
        self.user_service = user_service

        self.changed = False

        self.win = tk.Toplevel(parent)
        self.win.title("Users Manager")
        self.win.geometry("820x460")
        self.win.minsize(760, 420)

        # Theme
        self.bg = self.config.back_color
        self.box_bg = self.config.box_color
        self.button_bg = self.config.button_color
        self.accent = self.config.accent_color
        self.text_color = self.config.text_color
        self.button_text_color = self.config.button_text_color
        self.input_bg = self.config.input_bg
        self.input_text_color = self.config.input_text_color

        self.win.configure(bg=self.bg)
        self.win.transient(parent)
        self.win.grab_set()

        self._setup_ttk_style()
        self._build_ui()
        self._load_users()

    def _setup_ttk_style(self):
        style = ttk.Style(self.win)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Treeview",
            background=self.input_bg,
            fieldbackground=self.input_bg,
            foreground=self.input_text_color,
            rowheight=24,
            borderwidth=0,
        )
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        top = tk.Frame(self.win, bg=self.bg)
        top.pack(fill="x", padx=16, pady=(14, 8))

        tk.Label(
            top,
            text="Usuarios",
            bg=self.bg,
            fg=self.text_color,
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left")

        btns = tk.Frame(top, bg=self.bg)
        btns.pack(side="right")

        add_btn = tk.Button(
            btns, text="Agregar", command=self._add_user,
            bg=self.button_bg, fg=self.button_text_color, relief="flat",
            cursor="hand2", activebackground=self.accent, activeforeground=self.button_text_color,
            width=10
        )
        add_btn.pack(side="left", padx=(0, 8))
        add_btn.bind("<Enter>", lambda e: add_btn.configure(bg=self.accent))
        add_btn.bind("<Leave>", lambda e: add_btn.configure(bg=self.button_bg))

        edit_btn = tk.Button(
            btns, text="Editar", command=self._edit_selected,
            bg=self.button_bg, fg=self.button_text_color, relief="flat",
            cursor="hand2", activebackground=self.accent, activeforeground=self.button_text_color,
            width=10
        )
        edit_btn.pack(side="left")
        edit_btn.bind("<Enter>", lambda e: edit_btn.configure(bg=self.accent))
        edit_btn.bind("<Leave>", lambda e: edit_btn.configure(bg=self.button_bg))

        table_box = tk.Frame(self.win, bg=self.bg)
        table_box.pack(fill="both", expand=True, padx=16, pady=(6, 16))

        border = tk.Frame(table_box, bg=self.accent)
        border.pack(fill="both", expand=True)

        inner = tk.Frame(border, bg=self.bg)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        cols = ("Username", "DisplayName", "Email", "Role", "Active", "MustChange")
        self.tree = ttk.Treeview(inner, columns=cols, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(inner, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)

        for c in cols:
            self.tree.heading(c, text=c)

        self.tree.column("Username", width=120, anchor="w", stretch=False)
        self.tree.column("DisplayName", width=210, anchor="w")
        self.tree.column("Email", width=220, anchor="w")
        self.tree.column("Role", width=90, anchor="w", stretch=False)
        self.tree.column("Active", width=70, anchor="center", stretch=False)
        self.tree.column("MustChange", width=95, anchor="center", stretch=False)

        self.tree.bind("<Double-1>", lambda e: self._edit_selected())

    def _load_users(self):
        try:
            users = self.user_repo.list_users(limit=5000)

            for item in self.tree.get_children():
                self.tree.delete(item)

            for u in users:
                self.tree.insert(
                    "", "end",
                    values=(u.username, u.display_name, u.email, u.role_code, u.is_active, u.must_change_password)
                )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar usuarios:\n{e}")

    def _add_user(self):
        w = AddUserWindow(self.win, self.config, self.user_service)
        self.win.wait_window(w.win)
        if w.created:
            self.changed = True
            self._load_users()

    def _edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Usuarios", "Selecciona un usuario.")
            return

        item_id = sel[0]
        v = self.tree.item(item_id, "values")

        user_row = {
            "username": v[0],
            "display_name": v[1],
            "email": v[2],
            "role_code": v[3],
            "is_active": int(v[4]),
            "must_change_password": int(v[5]),
        }

        w = EditUserWindow(self.win, self.config, self.user_service, user_row)
        self.win.wait_window(w.win)
        if w.updated:
            self.changed = True
            self._load_users()