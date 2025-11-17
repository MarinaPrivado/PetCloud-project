from config.database import SessionLocal
from models.User import User

def list_all_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            print("Nenhum usuário cadastrado.")
        for user in users:
            print(f"ID: {user.id}")
            print(f"Nome: {user.name}")
            print(f"Email: {user.email}")
            print(f"Criado em: {user.created_at}")
            print("-" * 40)
    finally:
        db.close()

if __name__ == "__main__":
    print("Usuários cadastrados:")
    print("=" * 40)
    list_all_users()
