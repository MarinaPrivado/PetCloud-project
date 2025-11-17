from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from User import User
from Pet import Pet
from config.database import Base

if __name__ == "__main__":
    # Criar engine para SQLite em memória para teste
    engine = create_engine('sqlite:///:memory:', echo=True)
    
    # Criar todas as tabelas
    Base.metadata.create_all(engine)
    
    # Criar uma sessão
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Criar um usuário de teste
        novo_usuario = User(
            name="João Silva",
            email="joao@example.com",
            password="senha123"
        )
        
        # Adicionar à sessão e commit
        session.add(novo_usuario)
        session.commit()
        
        print("\nUsuário criado:")
        print(novo_usuario)
        
        # Testar atualização de informações
        novo_usuario.update(name="João Silva Santos")
        session.commit()
        
        print("\nUsuário após atualização do nome:")
        print(novo_usuario)
        
        # Testar mudança de senha
        novo_usuario.change_password("nova_senha123")
        session.commit()
        
        # Testar conversão para dicionário
        print("\nDados do usuário em formato de dicionário:")
        print(novo_usuario.to_dict())
        
        # Testar criação de pet
        novo_pet = Pet(
            name="Rex",
            type="dog",
            breed="Labrador",
            birth_date=datetime.now()
        )
        
        novo_usuario.add_pet(novo_pet)
        session.add(novo_pet)
        session.commit()
        
        print("\nPets do usuário:")
        for pet in novo_usuario.get_pets():
            print(f"- {pet.name} ({pet.type})")
            
    finally:
        session.close()