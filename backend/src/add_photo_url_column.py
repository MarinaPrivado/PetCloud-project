"""
Script para adicionar coluna photo_url à tabela pets
"""
from config.database import engine
from sqlalchemy import text

def add_photo_url_column():
    with engine.connect() as conn:
        try:
            # Verificar se a coluna já existe
            result = conn.execute(text("PRAGMA table_info(pets)"))
            columns = [row[1] for row in result]
            
            if 'photo_url' not in columns:
                # Adicionar coluna photo_url
                conn.execute(text("ALTER TABLE pets ADD COLUMN photo_url VARCHAR"))
                conn.commit()
                print("✅ Coluna photo_url adicionada com sucesso à tabela pets!")
            else:
                print("ℹ️  Coluna photo_url já existe na tabela pets")
                
        except Exception as e:
            print(f"❌ Erro ao adicionar coluna: {e}")

if __name__ == "__main__":
    add_photo_url_column()
