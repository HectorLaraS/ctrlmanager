from src.core.config import AppConfig
from src.ui.views.login_view import LoginWindow

def main():
    config = AppConfig.from_env()
    app = LoginWindow(config)
    app.run()

if __name__ == "__main__":
    main()
