from .src.models.User import User
from .src.models.Pet import Pet
from .src.config.database import Base, engine

# Create all tables
Base.metadata.create_all(bind=engine)