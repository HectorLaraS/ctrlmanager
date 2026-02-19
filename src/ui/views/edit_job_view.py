import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from src.core.config import AppConfig


class EditJobWindow:
    """
    Modal para editar Job existente.
    - job: dict con campos mínimos
    - groups: lista GroupInfo (group_code, group_name, service_name)
    - jobs_repo: update_job()
    """

    PRIORITY_TO_SEVERITY = {
        "Priority 2": 3,
        "Priority 3": 4,
        "Priority 4": 5,
    }
    SEVERITY_TO_PRIORITY = {v: k for k, v in PRIORITY_TO_SEVERITY.items()}

    def __init__(self, parent: tk.Tk, config: AppConfig, jobs_repo, groups, job: dict):
        self.parent = parent
        self.config = config
        self.jobs_repo = jobs_repo
        self.groups = groups or []
        self.job = job

        self.updated = False  # True si guardó cambios

        self.win = tk.Toplevel(parent)
        self.win.title("Editar Job")
        self.win.geometry("560x360")
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
            text=f"Editar Job (Id: {self.job['id']})",
            bg=self.bg,
            fg=self.text_color,
            font=("Segoe UI", 12, "bold"),
        )
        title.pack(anchor="w", pady=(0, 12))

        form = tk.Frame(root, bg=self.bg)
        form.pack(fill="x")

        # Vars prefill
        self.type_var = tk.StringVar(value=self.job.get("type", ""))
        self.jobname_var = tk.StringVar(value=self.job.get("job_name", ""))

        # Groups mapping display -> code
        self.group_map = {}
        group_display_list = []
        for g in self.groups:
            display = f"{g.group_code} - {g.group_name}".strip()
            if getattr(g, "service_name", ""):
                display = f"{display} ({g.service_name})"
            self.group_map[display] = g.group_code
            group_display_list.append(display)

        # Preselect group display from job.group_code
        current_group_code = (self.job.get("group_code") or "").strip()
        selected_display = ""
        for disp, code in self.group_map.items():
            if code == current_group_code:
                selected_display = disp
                break

        # Si el GroupCode actual no existe en tabla Groups, lo dejamos visible para no romper edición
        if not selected_display and current_group_code:
            selected_display = f"{current_group_code} - (No encontrado en Groups)"
            self.group_map[selected_display] = current_group_code
            group_display_list = [selected_display] + group_display_list

        self.group_var = tk.StringVar(value=selected_display if selected_display else (group_display_list[0] if group_display_list else ""))

        # Priority prefill: viene como severity int o como priority string
        severity_val = self.job.get("severity_int")
        priority_val = self.job.get("incident_priority")

        if severity_val is not None:
            try:
                severity_val = int(severity_val)
            except Exception:
                severity_val = None

        if severity_val is not None:
            pre_priority = self.SEVERITY_TO_PRIORITY.get(severity_val, "Priority 4")
        else:
            # por si solo viene "Priority 2/3/4"
            pre_priority = priority_val if priority_val in self.PRIORITY_TO_SEVERITY else "Priority 4"

        self.priority_var = tk.StringVar(value=pre_priority)
        pri_values = list(self.PRIORITY_TO_SEVERITY.keys())

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
            width=34
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
            width=33
        )
        combo.grid(row=row, column=1, sticky="w", pady=8)

    def _on_cancel(self):
        self.updated = False
        self.win.destroy()

    def _on_save(self):
        job_id = int(self.job["id"])
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
            self.jobs_repo.update_job(
                job_id=job_id,
                type_=type_,
                job_name=job_name,
                group_code=group_code,
                severity=int(severity),
            )
            self.updated = True
            messagebox.showinfo("Jobs", "Job actualizado correctamente.")
            self.win.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el job:\n{e}")
