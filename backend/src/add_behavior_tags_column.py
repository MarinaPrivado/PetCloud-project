import sqlite3
import json
import os

# Caminho do banco de dados
db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'petcloud_new.db')

try:
    # Conectar ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar se a coluna já existe
    cursor.execute("PRAGMA table_info(pets)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'behavior_tags' not in columns:
        # Adicionar a coluna behavior_tags
        cursor.execute("""
            ALTER TABLE pets 
            ADD COLUMN behavior_tags TEXT DEFAULT '[]'
        """)
        
        # Inicializar todos os pets existentes com array vazio
        cursor.execute("""
            UPDATE pets 
            SET behavior_tags = '[]' 
            WHERE behavior_tags IS NULL
        """)
        
        conn.commit()
        print("✅ Coluna behavior_tags adicionada com sucesso à tabela pets!")
    else:
        print("ℹ️ Coluna behavior_tags já existe na tabela pets.")
    
except Exception as e:
    print(f"❌ Erro ao adicionar coluna: {e}")
finally:
    if conn:
        conn.close()
