from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from config.database import Base

class Clinica(Base):
    __tablename__ = 'clinicas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    tipo_servico = Column(String(50), nullable=False)  # 'banho', 'vacinacao', 'consulta'
    preco_servico = Column(Float, nullable=True)
    veterinario = Column(String(100), nullable=True)
    
    # Relacionamento com Servico
    servicos = relationship("Servico", back_populates="clinica_rel", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'tipo_servico': self.tipo_servico,
            'preco_servico': self.preco_servico,
            'veterinario': self.veterinario
        }
