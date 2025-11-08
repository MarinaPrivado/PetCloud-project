import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import SessionLocal
from models.Pet import Pet

def clear_pets():
    db = SessionLocal()
    try:
        # Deleta todos os pets
        num_deleted = db.query(Pet).delete()
        db.commit()
        print(f"✓ {num_deleted} pets deletados com sucesso!")
    except Exception as e:
        db.rollback()
        print(f"✗ Erro ao deletar pets: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Limpando dados de pets do banco de dados...")
    print("========================================")
    clear_pets()
