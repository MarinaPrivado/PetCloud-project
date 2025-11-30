import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import SessionLocal
from models.Vaccine import Vaccine

def list_all_vaccines():
    db = SessionLocal()
    try:
        vaccines = db.query(Vaccine).all()
        
        if not vaccines:
            print("Nenhuma vacina cadastrada no banco de dados.")
            return
        
        print(f"\nVacinas cadastradas: {len(vaccines)}")
        print("=" * 80)
        
        for vaccine in vaccines:
            print(f"\nID: {vaccine.id}")
            print(f"Tipo: {vaccine.type}")
            print(f"Data Programada: {vaccine.scheduled_date}")
            print(f"Veterinário: {vaccine.veterinarian}")
            print(f"Pet ID: {vaccine.pet_id}")
            print("-" * 80)
    
    except Exception as e:
        print(f"Erro ao listar vacinas: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_all_vaccines()
