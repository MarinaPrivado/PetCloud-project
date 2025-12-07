from datetime import datetime
import json
from typing import List, Optional, Dict, Any
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime
import json
from dateutil.relativedelta import relativedelta
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from config.database import Base

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .User import User

class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    breed = Column(String, nullable=False)
    birth_date = Column(DateTime, nullable=False)  # Usado como idade
    type = Column(String, nullable=True)  # Espécie opcional
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    photo_url = Column(String, nullable=True)  # URL da foto do pet
    behavior_tags = Column(String, default=json.dumps([]), nullable=True)  # Tags de comportamento
    health_records = Column(String, default=json.dumps([]), nullable=True)
    feeding_schedule = Column(String, default=json.dumps([]), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship with User model - will be set in __init__.py
    owner = None  # type: Optional[User]
    
    # Relationship with Servico model
    servicos = relationship("Servico", back_populates="pet", cascade="all, delete-orphan")

    def get_health_records(self) -> List[Dict]:
        """Get health records as a Python list"""
        return json.loads(self.health_records) if self.health_records else []

    def set_health_records(self, records: List[Dict]) -> None:
        """Set health records from a Python list"""
        self.health_records = json.dumps(records)

    def get_feeding_schedule(self) -> List[Dict]:
        """Get feeding schedule as a Python list"""
        return json.loads(self.feeding_schedule) if self.feeding_schedule else []

    def set_feeding_schedule(self, schedule: List[Dict]) -> None:
        """Set feeding schedule from a Python list"""
        self.feeding_schedule = json.dumps(schedule)

    def get_behavior_tags(self) -> List[str]:
        """Get behavior tags as a Python list"""
        return json.loads(self.behavior_tags) if self.behavior_tags else []

    def set_behavior_tags(self, tags: List[str]) -> None:
        """Set behavior tags from a Python list"""
        self.behavior_tags = json.dumps(tags)

    def set_owner(self, user: Optional['User']) -> None:
        """Set the owner of the pet."""
        self.owner = user
        self.updated_at = datetime.now()

    def add_health_record(self, record: Dict[str, Any]) -> None:
        """Add a health record."""
        self.health_records.append({
            **record,
            'date': datetime.now()
        })
        self.updated_at = datetime.now()

    def add_feeding_schedule(self, time: datetime, portion: float, food_type: str) -> None:
        """Add a feeding schedule entry."""
        self.feeding_schedule.append({
            'time': time,
            'portion': portion,
            'food_type': food_type,
            'created_at': datetime.now()
        })
        self.updated_at = datetime.now()

    def update(self, name: Optional[str] = None, type: Optional[str] = None,
               breed: Optional[str] = None, birth_date: Optional[datetime] = None) -> None:
        """Update pet information."""
        if name:
            self.name = name
        if type:
            self.type = type
        if breed:
            self.breed = breed
        if birth_date:
            self.birth_date = birth_date
        self.updated_at = datetime.now()

    def get_age(self) -> Dict[str, int]:
        """Calculate pet's age."""
        today = datetime.now()
        rd = relativedelta(today, self.birth_date)
        return {
            'years': rd.years,
            'months': rd.months,
            'days': rd.days
        }

    def get_recent_health_records(self, limit: int = 5) -> List[Dict]:
        """Get recent health records."""
        sorted_records = sorted(
            self.health_records,
            key=lambda x: x['date'],
            reverse=True
        )
        return sorted_records[:limit]

    def get_today_feeding_schedule(self) -> List[Dict]:
        """Get feeding schedule for today."""
        today = datetime.now().date()
        return [
            schedule for schedule in self.feeding_schedule
            if schedule['time'].date() == today
        ]

    def to_dict(self) -> Dict:
        """Convert pet data to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'breed': self.breed,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'age': self.get_age() if hasattr(self, 'get_age') else None,
            'photo_url': self.photo_url if hasattr(self, 'photo_url') else None,
            'behavior_tags': self.get_behavior_tags() if hasattr(self, 'behavior_tags') else [],
            'owner': {'id': self.owner.id, 'name': self.owner.name} if hasattr(self, 'owner') and self.owner else None,
            'health_records': self.health_records if hasattr(self, 'health_records') else [],
            'feeding_schedule': [
                ({**s, 'time': s['time'].isoformat()} if isinstance(s, dict) and 'time' in s and hasattr(s['time'], 'isoformat') else s)
                for s in getattr(self, 'feeding_schedule', []) if s
            ],
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None,
            'updated_at': self.updated_at.isoformat() if hasattr(self, 'updated_at') and self.updated_at else None
        }

    def __str__(self) -> str:
        return f"Pet(id={self.id}, name={self.name}, type={self.type}, breed={self.breed})"