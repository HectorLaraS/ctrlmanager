# src/ui/views/add_job_view.py
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from src.core.config import AppConfig


class AddJobWindow:
    """
    Modal para crear Jobs.
    - groups: lista de GroupInfo (group_code, group_name, service_name)
    - jobs_repo: para insertar el Job (Severity INT en DB)
    """

    # UI Priority -> DB Severity (int)
    PRIORITY_TO_SEVERITY = {
        "Priority 2": 3,  # ServiceNow P2
        "Priority 3": 4,  # ServiceNow P3
        "Priority 4": 5,  # ServiceNow P4
    }

    # DB Severity -> UI Priority (lo usaremos luego en Edit)
    SEVERITY_TO_PRIORITY = {v: k for k, v in PRIORITY_TO_SEVERITY.items()}

    def __init__(self, parent: tk.Tk, config: AppConfig, jobs_repo, groups):
        self.parent = parent
        self.config = config
        self.jobs_repo = jobs_repo
        self.groups = groups or []

        self.created = False  # True si insertó

        self.win = tk.Toplevel(parent)
        self.win.title("Agregar Job")
        self.win.geometry("540x340")
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

        # Modal
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

        # Asegura que combobox se vea bien con tema claro
        style.configure(
            "TCombobox",
            fieldbackground=self.input_bg,
            background=self.input_bg,
            foreground=self.input_text_color
        )

    def _build_ui(self):
        root = tk.Frame(self.win, bg=self.bg)
        root.pack(fill="both", expand=True, padx=18, pady=18)

        title = tk.Label(
            root,
            text="Nuevo Job",
            bg=self.bg,
            fg=self.text_color,
            font=("Segoe UI", 12, "bold"),
        )
        title.pack(anchor="w", pady=(0, 12))

        form = tk.Frame(root, bg=self.bg)
        form.pack(fill="x")

        # Vars
        self.type_var = tk.StringVar(value="controlm")
        self.jobname_var = tk.StringVar()

        # ----- Group dropdown values -----
        self.group_map = {}  # display -> group_code
        group_display_list = []
        for g in self.groups:
            display = f"{g.group_code} - {g.group_name}".strip()
            if getattr(g, "service_name", ""):
                display = f"{display} ({g.service_name})"
            self.group_map[display] = g.group_code
            group_display_list.append(display)

        self.group_var = tk.StringVar(value=group_display_list[0] if group_display_list else "")

        # ----- Incident Priority (UI) -----
        pri_values = list(self.PRIORITY_TO_SEVERITY.keys())
        self.priority_var = tk.StringVar(value="Priority 4")  # default (menos crítico)

        # Rows
        self._row_entry(form, 0, "Type", self.type_var)
        self._row_entry(form, 1, "JobName", self.jobname_var)
        self._row_combo(form, 2, "Group", self.group_var, values=group_display_list)
        self._row_combo(form, 3, "Incident Priority", self.priority_var, values=pri_values)

        # Buttons
        buttons = tk.Frame(root, bg=self.bg)
        buttons.pack(fill="x", pady=(18, 0))

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

        self._type_entry.focus_set()

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
            width=32
        )
        entry.grid(row=row, column=1, sticky="w", pady=8)

        if label == "Type":
            self._type_entry = entry

    def _row_combo(self, parent: tk.Frame, row: int, label: str, var: tk.StringVar, values):
        tk.Label(parent, text=label, bg=self.label_bg, fg="#111111", padx=10, pady=6).grid(
            row=row, column=0, sticky="e", padx=(0, 12), pady=8
        )
        combo = ttk.Combobox(
            parent,
            textvariable=var,
            values=values,
            state="readonly",
            width=31
        )
        combo.grid(row=row, column=1, sticky="w", pady=8)

    def _on_cancel(self):
        self.created = False
        self.win.destroy()

    def _on_save(self):
        type_ = (self.type_var.get() or "").strip()
        job_name = (self.jobname_var.get() or "").strip()
        group_display = (self.group_var.get() or "").strip()
        priority_display = (self.priority_var.get() or "").strip()

        if not type_:
            messagebox.showwarning("Validación", "Type es requerido.")
            return
        if not job_name:
            messagebox.showwarning("Validación", "JobName es requerido.")
            return
        if not group_display:
            messagebox.showwarning("Validación", "Selecciona un Group.")
            return

        group_code = self.group_map.get(group_display, "")
        if not group_code:
            messagebox.showerror("Validación", "Group seleccionado inválido.")
            return

        severity = self.PRIORITY_TO_SEVERITY.get(priority_display)
        if severity is None:
            messagebox.showerror("Validación", "Incident Priority inválida.")
            return

        try:
            # Guardamos en DB severity INT (3/4/5)
            self.jobs_repo.add_job(
                type_=type_,
                job_name=job_name,
                group_code=group_code,
                severity=int(severity)
            )
            self.created = True
            messagebox.showinfo("Jobs", "Job creado correctamente.")
            self.win.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el job:\n{e}")
