import sqlite3
from config.database import DATABASE_PATH

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

print(f"Verificando tabelas no banco: {DATABASE_PATH}\n")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

if tables:
    print("Tabelas encontradas:")
    for table in tables:
        print(f"- {table[0]}")
else:
    print("Nenhuma tabela encontrada.")

conn.close()
