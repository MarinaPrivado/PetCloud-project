from sqlalchemy import Column, Integer, String
from config.database import Base, engine

class TestTable(Base):
    __tablename__ = 'test_table'
    id = Column(Integer, primary_key=True)
    name = Column(String)

# Cria a tabela test_table
Base.metadata.create_all(bind=engine)

print("Tabela 'test_table' criada (se não existia).")
