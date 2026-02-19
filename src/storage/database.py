import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
        self.server = os.getenv("DB_SERVER", "localhost")
        self.database = os.getenv("DB_DATABASE", "")
        self.username = os.getenv("DB_USER", "")
        self.password = os.getenv("DB_PASSWORD", "")
        self.trusted = os.getenv("DB_TRUSTED_CONNECTION", "0").strip() in (
            "1", "true", "True", "yes", "YES"
        )

    def get_connection(self):
        if self.trusted:
            conn_str = (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                "Trusted_Connection=yes;"
                "TrustServerCertificate=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
                "TrustServerCertificate=yes;"
            )

        return pyodbc.connect(conn_str)
