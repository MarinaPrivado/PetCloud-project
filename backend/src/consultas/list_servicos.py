import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config.database import SessionLocal
from src.models.Servico import Servico
from src.models.Pet import Pet

def list_servicos():
    db = SessionLocal()
    try:
        servicos = db.query(Servico).all()
        print(f"\n=== SERVIÇOS NO BANCO DE DADOS ===")
        print(f"Total de serviços: {len(servicos)}\n")
        
        if servicos:
            for servico in servicos:
                pet = db.query(Pet).filter(Pet.id == servico.pet_id).first()
                pet_name = pet.name if pet else "Pet não encontrado"
                print(f"ID: {servico.id}")
                print(f"Pet: {pet_name} (ID: {servico.pet_id})")
                print(f"Tipo: {servico.tipo}")
                print(f"Data Agendada: {servico.data_agendada}")
                print(f"Preço: R$ {servico.preco if servico.preco else 'Não definido'}")
                print("-" * 50)
        else:
            print("Nenhum serviço encontrado no banco de dados.")
            print("\nTabela 'servicos' criada com sucesso!")
    
    except Exception as e:
        print(f"Erro ao listar serviços: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_servicos()
