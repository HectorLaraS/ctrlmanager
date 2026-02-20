import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


def _get_color(name: str, default: str) -> str:
    # Acepta #RRGGBB. Si viene vacío o inválido, cae al default.
    v = (os.getenv(name, default) or "").strip()
    if len(v) == 7 and v.startswith("#"):
        return v
    return default


def app_base_dir() -> Path:
    """
    Base para resolver rutas relativas de assets.
    - En PyInstaller onedir: carpeta donde está el .exe (dist\\CTLManager\\)
    - En desarrollo: carpeta actual (cwd)
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def load_env() -> None:
    """
    Carga variables desde:
    1) C:\\ProgramData\\CTLManager\\config.env  (instalación/servidor)
    2) .env local (desarrollo)
    """
    program_data = Path(os.getenv("PROGRAMDATA", r"C:\ProgramData"))
    config_path = program_data / "CTLManager" / "config.env"

    if config_path.exists():
        load_dotenv(dotenv_path=config_path, override=True)
        # print(f"Config cargado desde: {config_path}")
    else:
        load_dotenv(override=True)
        # print("Config cargado desde .env local (modo desarrollo)")


def resolve_path(raw_path: str) -> str:
    """
    - Si el path es absoluto, lo respeta.
    - Si es relativo, lo resuelve desde app_base_dir().
    """
    raw_path = (raw_path or "").strip()
    if not raw_path:
        return str(app_base_dir() / "assets" / "logo.png")

    p = Path(raw_path)
    if p.is_absolute():
        return str(p)
    return str(app_base_dir() / p)


@dataclass(frozen=True)
class AppConfig:
    # Window
    title: str
    width: int
    height: int
    main_width: int
    main_height: int

    # Logo
    logo_path: str
    logo_box_w: int
    logo_box_h: int

    # Theme colors (ALL from env)
    back_color: str
    label_color: str
    button_color: str
    box_color: str
    accent_color: str
    text_color: str
    button_text_color: str
    input_bg: str
    input_text_color: str

    @staticmethod
    def from_env() -> "AppConfig":
        # 👇 Cargar env una sola vez, aquí (o en tu main al inicio; elige uno)
        load_env()

        return AppConfig(
            title=os.getenv("APP_TITLE", "CTLManager").strip(),
            width=_get_int("APP_WIDTH", 760),
            height=_get_int("APP_HEIGHT", 380),
            main_width=_get_int("MAIN_WIDTH", 980),
            main_height=_get_int("MAIN_HEIGHT", 520),

            # 👇 Resuelve ruta segura para exe / dev
            logo_path=resolve_path(os.getenv("LOGO_PATH", "assets/logo.png")),
            logo_box_w=_get_int("LOGO_BOX_W", 260),
            logo_box_h=_get_int("LOGO_BOX_H", 260),

            back_color=_get_color("BACK_COLOR", "#1F2328"),
            label_color=_get_color("LABEL_COLOR", "#D4AF37"),
            button_color=_get_color("BUTTON_COLOR", "#C02032"),
            box_color=_get_color("BOX_COLOR", "#2A2F36"),
            accent_color=_get_color("ACCENT_COLOR", "#D4AF37"),
            text_color=_get_color("TEXT_COLOR", "#E8E8E8"),
            button_text_color=_get_color("BUTTON_TEXT_COLOR", "#FFFFFF"),
            input_bg=_get_color("INPUT_BG", "#FFFFFF"),
            input_text_color=_get_color("INPUT_TEXT_COLOR", "#111111"),
        )