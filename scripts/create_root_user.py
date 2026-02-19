import os
import pyodbc
from argon2 import PasswordHasher
from dotenv import load_dotenv


load_dotenv()

# ----------------------------
# CONFIG DB (usa tu .env luego)
# ----------------------------
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# ----------------------------
# Crear hash
# ----------------------------
ph = PasswordHasher()
hashed_password = ph.hash("viewer")

print("Hash generado correctamente.")

# ----------------------------
# Conexión SQL
# ----------------------------
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_DATABASE};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD};"
    "Encrypt=no;"
)

with pyodbc.connect(conn_str) as conn:
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO dbo.wt_users (
            username,
            display_name,
            email,
            password_hash,
            password_algo,
            role_code,
            is_active,
            must_change_password
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        "viewer",
        "viewer engineer",
        None,
        hashed_password,
        "argon2id",
        "viewer",
        1,
        1
    )

    conn.commit()

print("Usuario root creado exitosamente.")
