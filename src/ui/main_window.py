import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from src.core.config import AppConfig
from src.storage.database import Database
from src.storage.jobs_repository import JobsRepository
from src.storage.groups_repository import GroupsRepository


class MainWindow:
    # DB Severity -> Incident Priority (solo front)
    SEVERITY_TO_PRIORITY = {
        3: "Priority 2",
        4: "Priority 3",
        5: "Priority 4",
    }

    def __init__(self, config: AppConfig, username: str, role_code: str = ""):
        self.config = config
        self.username = username
        self.role_code = (role_code or "viewer").lower().strip()

        self.is_admin = self.role_code == "admin"
        self.is_operator = self.role_code == "operator"
        self.is_viewer = self.role_code == "viewer"
        self.can_edit = self.is_admin or self.is_operator

        self.root = tk.Tk()
        self.root.title(self.config.title)
        self.root.geometry(f"{self.config.main_width}x{self.config.main_height}")
        self.root.minsize(1000, 520)

        # Theme colors (.env)
        self.bg = self.config.back_color
        self.label_bg = self.config.label_color
        self.button_bg = self.config.button_color
        self.box_bg = self.config.box_color
        self.accent = self.config.accent_color
        self.text_color = self.config.text_color
        self.input_bg = self.config.input_bg
        self.input_text_color = self.config.input_text_color

        self.root.configure(bg=self.bg)

        # DB
        self.db = Database()
        self.jobs_repo = JobsRepository(self.db)
        self.groups_repo = GroupsRepository(self.db)

        self._search_after_id = None

        self._setup_ttk_style()
        self._build_menu()
        self._build_ui()
        self._load_jobs()

    # --------------------------------------------------
    # UI STYLE
    # --------------------------------------------------

    def _setup_ttk_style(self):
        style = ttk.Style()
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

        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
        )

    # --------------------------------------------------
    # MENU
    # --------------------------------------------------

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        # Jobs
        jobs_menu = tk.Menu(menubar, tearoff=0)
        if self.can_edit:
            jobs_menu.add_command(label="Agregar", command=self._jobs_add)
            jobs_menu.add_command(label="Editar", command=self._jobs_edit)
        menubar.add_cascade(label="Jobs", menu=jobs_menu)

        # Groups
        groups_menu = tk.Menu(menubar, tearoff=0)
        if self.can_edit:
            groups_menu.add_command(label="Agregar", command=self._groups_add)
            groups_menu.add_command(label="Editar", command=self._groups_edit)
        menubar.add_cascade(label="Groups", menu=groups_menu)

        # User
        user_menu = tk.Menu(menubar, tearoff=0)
        user_menu.add_command(label="Cambiar password", command=self._user_change_password)

        if self.is_admin:
            user_menu.add_command(label="Agregar usuario", command=self._user_add)
            user_menu.add_command(label="Editar usuario", command=self._user_edit)

        menubar.add_cascade(label="User", menu=user_menu)

        self.root.config(menu=menubar)

    # --------------------------------------------------
    # LAYOUT
    # --------------------------------------------------

    def _build_ui(self):
        # Top bar
        top = tk.Frame(self.root, bg=self.bg)
        top.pack(fill="x", padx=16, pady=(14, 8))

        user_lbl = tk.Label(
            top,
            text=f"Usuario: {self.username} ({self.role_code})",
            bg=self.bg,
            fg=self.text_color,
            font=("Segoe UI", 10, "bold"),
        )
        user_lbl.pack(side="left")

        search_frame = tk.Frame(top, bg=self.bg)
        search_frame.pack(side="right")

        tk.Label(
            search_frame,
            text="Search",
            bg=self.bg,
            fg=self.text_color,
            font=("Segoe UI", 10),
        ).pack(side="left", padx=(0, 10))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg=self.input_bg,
            fg=self.input_text_color,
            relief="flat",
            highlightthickness=2,
            highlightbackground=self.box_bg,
            highlightcolor=self.button_bg,
            insertbackground=self.input_text_color,
            width=36
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        # Table container
        table_box = tk.Frame(self.root, bg=self.bg)
        table_box.pack(fill="both", expand=True, padx=16, pady=(6, 16))

        border = tk.Frame(table_box, bg=self.accent)
        border.pack(fill="both", expand=True)

        inner = tk.Frame(border, bg=self.bg)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        cols = (
            "Id",
            "Type",
            "JobName",
            "GroupCode",
            "GroupName",
            "ServiceName",
            "IncidentPriority",
            "CreatedAtUtc",
        )

        self.tree = ttk.Treeview(inner, columns=cols, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(inner, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)

        for c in cols:
            self.tree.heading(c, text=c)

        self.tree.column("Id", width=60, anchor="w", stretch=False)
        self.tree.column("Type", width=110, anchor="w", stretch=False)
        self.tree.column("JobName", width=300, anchor="w")
        self.tree.column("GroupCode", width=120, anchor="w", stretch=False)
        self.tree.column("GroupName", width=220, anchor="w")
        self.tree.column("ServiceName", width=200, anchor="w")
        self.tree.column("IncidentPriority", width=130, anchor="w", stretch=False)
        self.tree.column("CreatedAtUtc", width=170, anchor="w", stretch=False)

    # --------------------------------------------------
    # DATA
    # --------------------------------------------------

    def _on_search_key(self, _event=None):
        if self._search_after_id:
            self.root.after_cancel(self._search_after_id)
        self._search_after_id = self.root.after(250, self._load_jobs)

    def _load_jobs(self):
        try:
            term = (self.search_var.get() or "").strip()
            jobs = self.jobs_repo.list_jobs(search=term if term else None, limit=2000)

            for item in self.tree.get_children():
                self.tree.delete(item)

            for j in jobs:
                severity_int = int(j.severity) if j.severity else None
                incident_priority = self.SEVERITY_TO_PRIORITY.get(severity_int, "")

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        j.id,
                        j.type,
                        j.job_name,
                        j.group_code,
                        j.group_name,
                        j.service_name,
                        incident_priority,
                        j.created_at_utc,
                    )
                )

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los jobs:\n{e}")

    # --------------------------------------------------
    # MENU ACTIONS
    # --------------------------------------------------

    def _jobs_add(self):
        if not self.can_edit:
            messagebox.showwarning("Permisos", "No tienes permisos para agregar Jobs.")
            return

        try:
            groups = self.groups_repo.list_groups(limit=2000)

            from src.ui.views.add_job_view import AddJobWindow
            w = AddJobWindow(self.root, self.config, self.jobs_repo, groups)
            self.root.wait_window(w.win)

            if w.created:
                self._load_jobs()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Agregar Job:\n{e}")

    def _jobs_edit(self):
        if not self.can_edit:
            messagebox.showwarning("Permisos", "No tienes permisos para editar Jobs.")
            return

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Jobs", "Selecciona un Job para editar.")
            return

        item_id = selected[0]
        values = self.tree.item(item_id, "values")

        # Columns order in tree:
        # ("Id","Type","JobName","GroupCode","GroupName","ServiceName","IncidentPriority","CreatedAtUtc")
        try:
            job_id = int(values[0])
        except Exception:
            messagebox.showerror("Jobs", "Id inválido en la selección.")
            return

        job = {
            "id": job_id,
            "type": values[1],
            "job_name": values[2],
            "group_code": values[3],
            "incident_priority": values[6],  # "Priority 2/3/4"
            # severity_int lo inferimos del priority
            "severity_int": None,
            "created_at_utc": values[7],
        }

        # Infer severity from IncidentPriority (front only)
        priority_to_sev = {
            "Priority 2": 3,
            "Priority 3": 4,
            "Priority 4": 5,
        }
        job["severity_int"] = priority_to_sev.get(job["incident_priority"])

        try:
            groups = self.groups_repo.list_groups(limit=2000)

            from src.ui.views.edit_job_view import EditJobWindow
            w = EditJobWindow(self.root, self.config, self.jobs_repo, groups, job)
            self.root.wait_window(w.win)

            if w.updated:
                self._load_jobs()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir Editar Job:\n{e}")


    def _groups_add(self):
        messagebox.showinfo("Groups", "Agregar Group (pendiente).")

    def _groups_edit(self):
        messagebox.showinfo("Groups", "Editar Group (pendiente).")

    def _user_change_password(self):
        messagebox.showinfo("User", "Cambiar password (pendiente aquí).")

    def _user_add(self):
        messagebox.showinfo("User", "Agregar usuario (pendiente).")

    def _user_edit(self):
        messagebox.showinfo("User", "Editar usuario (pendiente).")

    # --------------------------------------------------

    def run(self):
        self.root.mainloop()
