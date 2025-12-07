from config.database import SessionLocal
from models.Pet import Pet
import json

def list_all_pets():
    db = SessionLocal()
    try:
        pets = db.query(Pet).all()
        if not pets:
            print("Nenhum pet cadastrado.")
        for pet in pets:
            print(f"ID: {pet.id}")
            print(f"Nome: {pet.name}")
            print(f"Espécie: {pet.type if pet.type else 'Não informado'}")
            print(f"Raça: {pet.breed}")
            print(f"Nascimento: {pet.birth_date}")
            print(f"Foto: {pet.photo_url if pet.photo_url else 'Sem foto'}")
            
            # Exibir tags de comportamento
            if hasattr(pet, 'behavior_tags') and pet.behavior_tags:
                try:
                    tags = json.loads(pet.behavior_tags)
                    print(f"Tags de Comportamento: {', '.join(tags) if tags else 'Nenhuma'}")
                except:
                    print(f"Tags de Comportamento: {pet.behavior_tags}")
            else:
                print(f"Tags de Comportamento: Nenhuma")
            
            print("-" * 40)
    finally:
        db.close()

if __name__ == "__main__":
    print("Pets cadastrados:")
    print("=" * 40)
    list_all_pets()
