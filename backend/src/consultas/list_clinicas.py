import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config.database import SessionLocal
from src.models.Clinica import Clinica

def list_clinicas():
    db = SessionLocal()
    try:
        clinicas = db.query(Clinica).all()
        print(f"\n=== CLÍNICAS NO BANCO DE DADOS ===")
        print(f"Total de clínicas: {len(clinicas)}\n")
        
        if clinicas:
            for clinica in clinicas:
                print(f"ID: {clinica.id}")
                print(f"Nome: {clinica.nome}")
                print(f"Tipo de Serviço: {clinica.tipo_servico}")
                print(f"Preço do Serviço: R$ {clinica.preco_servico if clinica.preco_servico else 'Não definido'}")
                print(f"Veterinário: {clinica.veterinario if clinica.veterinario else 'Não definido'}")
                print("-" * 50)
        else:
            print("Nenhuma clínica encontrada no banco de dados.")
            print("\nTabela 'clinicas' criada com sucesso!")
    
    except Exception as e:
        print(f"Erro ao listar clínicas: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_clinicas()
