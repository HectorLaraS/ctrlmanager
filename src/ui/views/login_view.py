# src/ui/views/login_view.py
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk

from src.core.config import AppConfig
from src.storage.database import Database
from src.storage.user_repository import UserRepository
from src.service.auth_service import AuthService, AuthError

# NUEVO: usamos UserService para cambiar password (argon2)
from src.service.user_service import UserService

# IMPORT QUE ME PEDISTE (ojo: tu ruta)
from src.ui.main_window import MainWindow

# NUEVO: modal reutilizable
from src.ui.views.change_password_view import ChangePasswordWindow


class LoginWindow:
    def __init__(self, config: AppConfig):
        self.config = config

        self.root = tk.Tk()
        self.root.title(self.config.title)
        self.root.geometry(f"{self.config.width}x{self.config.height}")
        self.root.resizable(False, False)

        # ===== Theme (ALL from .env via AppConfig) =====
        self.bg = self.config.back_color
        self.card_bg = self.bg

        self.box_bg = self.config.box_color
        self.label_bg = self.config.label_color
        self.button_bg = self.config.button_color
        self.accent = self.config.accent_color

        self.text_color = self.config.text_color
        self.button_text_color = self.config.button_text_color

        self.input_bg = self.config.input_bg
        self.input_text_color = self.config.input_text_color

        # Keep reference to image (avoid GC)
        self._logo_imgtk = None

        self.root.configure(bg=self.bg)

        # Services
        self.db = Database()
        self.user_repo = UserRepository(self.db)
        self.auth = AuthService(self.user_repo)

        # UserService (para cambio de password)
        self.user_service = UserService(self.user_repo)

        self._build_ui()

    def _build_ui(self):
        main = tk.Frame(self.root, bg=self.card_bg)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # Ratio columns 1:2 (logo : form)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(0, weight=1)

        left = tk.Frame(main, bg=self.card_bg)
        right = tk.Frame(main, bg=self.card_bg)

        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        right.grid(row=0, column=1, sticky="nsew")

        # ==== Logo box ====
        logo_box = tk.Frame(
            left,
            bg=self.box_bg,
            width=self.config.logo_box_w,
            height=self.config.logo_box_h,
            highlightthickness=2,
            highlightbackground=self.accent
        )
        logo_box.pack(expand=True)
        logo_box.pack_propagate(False)

        self._render_logo(logo_box)

        # ==== Form container (grid-only, stable layout) ====
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        form = tk.Frame(right, bg=self.card_bg)
        form.grid(row=0, column=0, sticky="w")  # stable (no place)

        self._build_labeled_entry(form, row=0, label_text="Usuario", is_password=False)
        self._build_labeled_entry(form, row=1, label_text="Password", is_password=True)

        # Login button
        btn = tk.Button(
            form,
            text="Login",
            command=self._on_login,
            width=24,
            bg=self.button_bg,
            fg=self.button_text_color,
            relief="flat",
            activebackground=self.accent,
            activeforeground=self.button_text_color,
            cursor="hand2"
        )
        btn.grid(row=2, column=0, columnspan=2, pady=(18, 0), sticky="ew")

        # Hover effect
        btn.bind("<Enter>", lambda e: btn.configure(bg=self.accent))
        btn.bind("<Leave>", lambda e: btn.configure(bg=self.button_bg))

        # Enter triggers login (ensure only bound once)
        self.root.bind("<Return>", lambda e: self._on_login())

    def _build_labeled_entry(self, parent: tk.Frame, row: int, label_text: str, is_password: bool):
        lbl = tk.Label(
            parent,
            text=label_text,
            bg=self.label_bg,
            fg="#111111",
            padx=10,
            pady=6,
            width=10,
            anchor="center"
        )
        lbl.grid(row=row, column=0, padx=(0, 15), pady=8)

        entry = tk.Entry(
            parent,
            show="*" if is_password else "",
            width=24,
            bg=self.input_bg,
            fg=self.input_text_color,
            relief="flat",
            highlightthickness=2,
            highlightbackground=self.box_bg,
            highlightcolor=self.button_bg,
            insertbackground=self.input_text_color
        )
        entry.grid(row=row, column=1, pady=8)

        if label_text.lower().startswith("usuario"):
            self.user_entry = entry
            self.user_entry.focus_set()
        else:
            self.pass_entry = entry

    def _render_logo(self, parent: tk.Frame):
        path = self.config.logo_path

        if not path:
            lbl = tk.Label(parent, text="LOGO", bg=self.box_bg, fg=self.text_color)
            lbl.pack(expand=True)
            return

        try:
            import os
            if not os.path.isfile(path):
                lbl = tk.Label(parent, text="LOGO", bg=self.box_bg, fg=self.text_color)
                lbl.pack(expand=True)
                return

            img = Image.open(path).convert("RGBA")
            img.thumbnail((self.config.logo_box_w - 24, self.config.logo_box_h - 24))
            self._logo_imgtk = ImageTk.PhotoImage(img)
            lbl = tk.Label(parent, image=self._logo_imgtk, bg=self.box_bg)
            lbl.pack(expand=True)
        except Exception:
            lbl = tk.Label(parent, text="LOGO", bg=self.box_bg, fg=self.text_color)
            lbl.pack(expand=True)

    def _on_login(self):
        username = (self.user_entry.get() or "").strip()
        password = (self.pass_entry.get() or "").strip()

        if not username or not password:
            messagebox.showwarning("Login", "Ingresa usuario y password.")
            return

        try:
            result = self.auth.login(username, password)

            # ===== Must change password flow =====
            if result.must_change_password:
                messagebox.showwarning(
                    "Cambio requerido",
                    "Debes cambiar tu password antes de continuar."
                )

                cp = ChangePasswordWindow(
                    parent=self.root,
                    config=self.config,
                    user_service=self.user_service,
                    mode="self",
                    logged_username=result.username,
                )
                self.root.wait_window(cp.win)

                # User cancelled
                if not cp.changed:
                    return

                # Re-login automatically with new password
                result2 = self.auth.login(result.username, cp.new_password)

                if result2.must_change_password:
                    messagebox.showwarning(
                        "Cambio requerido",
                        "Aún se requiere cambio de password. Revisa la actualización en DB."
                    )
                    return

                messagebox.showinfo("Login", f"Bienvenido, {result2.username}")

                # Close login and open MainWindow
                self.root.destroy()
                MainWindow(
                    self.config,
                    user_id=result2.user_id,
                    username=result2.username,
                    role_code=getattr(result2, "role_code", "")
                ).run()
                return

            # ===== Normal login flow =====
            messagebox.showinfo("Login", f"Bienvenido, {result.username}")

            self.root.destroy()
            MainWindow(
                self.config,
                user_id=result.user_id,
                username=result.username,
                role_code=getattr(result, "role_code", "")
            ).run()

        except AuthError as e:
            messagebox.showerror("Login", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar/consultar la DB:\n{e}")

    def run(self):
        self.root.mainloop()