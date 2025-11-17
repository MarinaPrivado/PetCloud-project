from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base

class Vaccine(Base):
    __tablename__ = 'vaccines'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type = Column(String, nullable=False)  # Tipo de vacina (ex: V8, Antirrábica)
    scheduled_date = Column(Date, nullable=False)  # Data programada
    veterinarian = Column(String, nullable=True)  # Veterinário responsável
    pet_id = Column(Integer, ForeignKey('pets.id'), nullable=False)  # Pet relacionado
    
    # Relacionamento com Pet
    pet = relationship("Pet", back_populates="vaccines")

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'scheduled_date': self.scheduled_date.strftime('%Y-%m-%d') if self.scheduled_date else None,
            'veterinarian': self.veterinarian,
            'pet_id': self.pet_id
        }
