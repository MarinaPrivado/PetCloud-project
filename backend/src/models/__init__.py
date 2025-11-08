import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy.orm import relationship
from config.database import Base
# Import models
from .User import User
from .Pet import Pet


try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False
if not TYPE_CHECKING:
    User.pets = relationship("Pet", back_populates="owner", lazy="joined")
    Pet.owner = relationship("User", back_populates="pets", lazy="joined")

__all__ = ['User', 'Pet', 'Base']
