from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base

class Servico(Base):
    __tablename__ = 'servicos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pet_id = Column(Integer, ForeignKey('pets.id'), nullable=False)
    clinica_id = Column(Integer, ForeignKey('clinicas.id'), nullable=True)
    tipo = Column(String(50), nullable=False)  # 'banho', 'vacinacao', 'consulta'
    data_agendada = Column(Date, nullable=False)
    preco = Column(Float, nullable=True)
    clinica = Column(String(100), nullable=True)  # Deprecated - usar clinica_id
    veterinario = Column(String(100), nullable=True)
    
    # Relacionamento com Pet
    pet = relationship("Pet", back_populates="servicos")
    # Relacionamento com Clinica
    clinica_rel = relationship("Clinica", back_populates="servicos")
    
    def to_dict(self):
        return {
            'id': self.id,
            'pet_id': self.pet_id,
            'clinica_id': self.clinica_id,
            'tipo': self.tipo,
            'data_agendada': self.data_agendada.isoformat() if self.data_agendada else None,
            'preco': self.preco,
            'clinica': self.clinica,
            'veterinario': self.veterinario
        }
