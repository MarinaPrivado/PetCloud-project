from config.database import SessionLocal, engine
from models import User, Pet
from sqlalchemy import func

def print_separator():
    print("\n" + "=" * 50 + "\n")

def list_users():
    db = SessionLocal()
    try:
        # 1. Todos os usuários
        print("Lista de todos os usuários:")
        users = db.query(User).all()
        for user in users:
            print(f"\nID: {user.id}")
            print(f"Nome: {user.name}")
            print(f"Email: {user.email}")
            print(f"Data de criação: {user.created_at}")
            print("-" * 30)
        
        print_separator()
        
        # 2. Total de usuários cadastrados
        total = db.query(func.count(User.id)).scalar()
        print(f"Total de usuários cadastrados: {total}")
        
        print_separator()
        
        # 3. Usuários mais recentes primeiro
        print("Usuários ordenados por data de criação (mais recentes primeiro):")
        recent_users = db.query(User).order_by(User.created_at.desc()).all()
        for user in recent_users:
            print(f"\nNome: {user.name}")
            print(f"Data de criação: {user.created_at}")
            print("-" * 30)
        
        print_separator()
        
        # 4. Usuários e seus pets
        print("Usuários e seus pets:")
        users_with_pets = db.query(User).all()
        for user in users_with_pets:
            print(f"\nUsuário: {user.name}")
            if user.pets:
                print("Pets:")
                for pet in user.pets:
                    print(f"  - {pet.name} ({pet.type})")
            else:
                print("Nenhum pet cadastrado")
            print("-" * 30)

    finally:
        db.close()

if __name__ == "__main__":
    print("\nConsulta aos dados do PetCloud")
    print_separator()
    list_users()