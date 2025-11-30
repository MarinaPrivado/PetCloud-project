from config.database import SessionLocal, engine
from models import User

def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            print(f"\nID: {user.id}")
            print(f"Nome: {user.name}")
            print(f"Email: {user.email}")
            print(f"Data de criação: {user.created_at}")
            print("-" * 50)
    finally:
        db.close()

if __name__ == "__main__":
    print("Usuários cadastrados:")
    print("=" * 50)
    list_users()