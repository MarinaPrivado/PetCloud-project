from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from config.database import Base

class Concurso(Base):
    __tablename__ = "concursos"
    
    id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey('pets.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    imagem_url = Column(String(500), nullable=False)
    descricao = Column(Text, nullable=True)
    votos = Column(Integer, default=0)
    data_envio = Column(DateTime, default=datetime.now)
    
    # Relationships
    pet = relationship("Pet", backref="concurso_fotos")
    user = relationship("User", backref="concurso_envios")
    
    def to_dict(self):
        return {
            'id': self.id,
            'pet_id': self.pet_id,
            'user_id': self.user_id,
            'imagem_url': self.imagem_url,
            'descricao': self.descricao,
            'votos': self.votos,
            'data_envio': self.data_envio.isoformat() if self.data_envio else None,
            'pet_name': self.pet.name if self.pet else None,
            'user_name': self.user.name if self.user else None,
            'user_email': self.user.email if self.user else None
        }
