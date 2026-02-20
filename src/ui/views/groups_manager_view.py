import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from src.core.config import AppConfig
from src.ui.views.add_group_view import AddGroupWindow
from src.ui.views.edit_group_view import EditGroupWindow


class GroupsManagerWindow:
    def __init__(self, parent: tk.Tk, config: AppConfig, groups_repo):
        self.parent = parent
        self.config = config
        self.groups_repo = groups_repo

        self.changed = False  # True si se creó o actualizó algo

        self.win = tk.Toplevel(parent)
        self.win.title("Groups Manager")
        self.win.geometry("760x420")
        self.win.minsize(700, 380)

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
        self._load_groups()

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
            text="Groups",
            bg=self.bg,
            fg=self.text_color,
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left")

        btns = tk.Frame(top, bg=self.bg)
        btns.pack(side="right")

        add_btn = tk.Button(
            btns, text="Agregar", command=self._add_group,
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

        cols = ("GroupCode", "GroupName", "ServiceName")
        self.tree = ttk.Treeview(inner, columns=cols, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(inner, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)

        for c in cols:
            self.tree.heading(c, text=c)

        self.tree.column("GroupCode", width=120, anchor="w", stretch=False)
        self.tree.column("GroupName", width=280, anchor="w")
        self.tree.column("ServiceName", width=260, anchor="w")

        self.tree.bind("<Double-1>", lambda e: self._edit_selected())

    def _load_groups(self):
        try:
            groups = self.groups_repo.list_groups(limit=5000)

            for item in self.tree.get_children():
                self.tree.delete(item)

            for g in groups:
                self.tree.insert("", "end", values=(g.group_code, g.group_name, g.service_name))

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los groups:\n{e}")

    def _add_group(self):
        w = AddGroupWindow(self.win, self.config, self.groups_repo)
        self.win.wait_window(w.win)
        if w.created:
            self.changed = True
            self._load_groups()

    def _edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Groups", "Selecciona un Group para editar.")
            return

        item_id = sel[0]
        values = self.tree.item(item_id, "values")
        group_code, group_name, service_name = values[0], values[1], values[2]

        w = EditGroupWindow(self.win, self.config, self.groups_repo, group_code, group_name, service_name)
        self.win.wait_window(w.win)
        if w.updated:
            self.changed = True
            self._load_groups()
