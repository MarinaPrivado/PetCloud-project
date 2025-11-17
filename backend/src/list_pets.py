
from models.Pet import Pet
from models.Vaccine import Vaccine  # Importar Vaccine para resolver a relação
from config.database import SessionLocal, Base, engine

# Garante que as tabelas existam no banco antes de consultar
Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    db = SessionLocal()
    pets = db.query(Pet).all()
    for pet in pets:
        print(pet.to_dict())
    db.close()
