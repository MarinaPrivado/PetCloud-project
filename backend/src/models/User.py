import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import relationship, Mapped
from config.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)  # Note: In production, this should be hashed
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship with Pet model - will be set in __init__.py
    pets = []  # type: List['Pet']

    def add_pet(self, pet: 'Pet') -> None:
        """Add a pet to the user's collection."""
        pet.set_owner(self)
        self.pets.append(pet)
        self.updated_at = datetime.now()

    def remove_pet(self, pet_id: str) -> bool:
        """Remove a pet from the user's collection."""
        for i, pet in enumerate(self.pets):
            if pet.id == pet_id:
                pet.set_owner(None)
                self.pets.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def get_pets(self) -> List['Pet']:
        """Get all pets for this user."""
        return self.pets

    def update(self, name: Optional[str] = None, email: Optional[str] = None) -> None:
        """Update user information."""
        if name:
            self.name = name
        if email:
            self.email = email
        self.updated_at = datetime.now()

    def change_password(self, new_password: str) -> None:
        """Change password."""
        self.password = new_password  # Note: In production, this should be hashed
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        """Convert user data to dictionary (excluding sensitive information)."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'pets': [pet.to_dict() for pet in self.pets],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __str__(self) -> str:
        return f"User(id={self.id}, name={self.name}, email={self.email})"

# Definir a classe User primeiro
User_class = User

if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Criar engine para SQLite em memória para teste
    engine = create_engine('sqlite:///:memory:')
    
    # Criar todas as tabelas
    Base.metadata.create_all(engine)
    
    # Criar uma sessão
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
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
    from .Pet import Pet
    
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