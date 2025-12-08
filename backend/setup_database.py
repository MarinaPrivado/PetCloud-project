"""
Script para criar as tabelas do banco de dados e popular com dados iniciais
Execução: python setup_database.py
"""

import sys
import os
from datetime import datetime, timedelta

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.database import Base, engine, SessionLocal
from models.User import User
from models.Pet import Pet
from models.Clinica import Clinica
from models.Servico import Servico
from models.Concurso import Concurso

def criar_tabelas():
    """Cria todas as tabelas no banco de dados"""
    print("🔧 Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas com sucesso!")

def popular_dados_iniciais():
    """Popula o banco com dados iniciais para demonstração"""
    db = SessionLocal()
    
    try:
        print("\n📦 Populando banco de dados com dados iniciais...")
        
        # Verificar se já existem dados
        if db.query(User).count() > 0:
            print("⚠️  Banco de dados já contém dados. Pulando população inicial.")
            return
        
        # 1. CRIAR USUÁRIOS
        print("\n👤 Criando usuários...")
        user1 = User(
            name="Italo Reis",
            email="italoreis99@gmail.com",
            password="senha123"  # Em produção, usar hash
        )
        user2 = User(
            name="Marina Privado",
            email="luandapc3@gmail.com",
            password="senha123"
        )
        db.add(user1)
        db.add(user2)
        db.commit()
        print(f"   ✓ {user1.name}")
        print(f"   ✓ {user2.name}")
        
        # 2. CRIAR PETS
        print("\n🐾 Criando pets...")
        pet1 = Pet(
            name="Moana",
            species="Cachorro",
            breed="Golden Retriever",
            age=3,
            weight=25.5,
            owner_id=user1.id
        )
        pet2 = Pet(
            name="Teste",
            species="Gato",
            breed="Siamês",
            age=2,
            weight=4.5,
            owner_id=user1.id
        )
        pet3 = Pet(
            name="Hulk",
            species="Cachorro",
            breed="Bulldog",
            age=5,
            weight=22.0,
            owner_id=user1.id
        )
        pet4 = Pet(
            name="Mimi",
            species="Gato",
            breed="Persa",
            age=1,
            weight=3.8,
            owner_id=user2.id
        )
        db.add_all([pet1, pet2, pet3, pet4])
        db.commit()
        print(f"   ✓ {pet1.name} (dono: {user1.name})")
        print(f"   ✓ {pet2.name} (dono: {user1.name})")
        print(f"   ✓ {pet3.name} (dono: {user1.name})")
        print(f"   ✓ {pet4.name} (dono: {user2.name})")
        
        # 3. CRIAR CLÍNICAS
        print("\n🏥 Criando clínicas veterinárias...")
        clinicas = [
            Clinica(
                nome="Clínica Veterinária São Francisco",
                endereco="Rua das Flores, 123",
                telefone="(11) 98765-4321",
                email="contato@clinicasf.com.br",
                horario_funcionamento="Seg-Sex: 8h-18h, Sáb: 9h-13h"
            ),
            Clinica(
                nome="PetCare Center",
                endereco="Av. Paulista, 1000",
                telefone="(11) 3456-7890",
                email="atendimento@petcare.com.br",
                horario_funcionamento="Seg-Sex: 7h-19h, Sáb-Dom: 8h-14h"
            ),
            Clinica(
                nome="Hospital Veterinário 24h",
                endereco="Rua Augusta, 456",
                telefone="(11) 99999-8888",
                email="emergencia@hospvet24h.com.br",
                horario_funcionamento="24 horas"
            ),
            Clinica(
                nome="Clínica Bichos & Cia",
                endereco="Rua Oscar Freire, 789",
                telefone="(11) 2345-6789",
                email="info@bichosecia.com.br",
                horario_funcionamento="Seg-Sex: 9h-18h"
            ),
            Clinica(
                nome="VetLife Animal Care",
                endereco="Av. Faria Lima, 2000",
                telefone="(11) 3344-5566",
                email="contato@vetlife.com.br",
                horario_funcionamento="Seg-Sáb: 8h-20h"
            ),
            Clinica(
                nome="Centro Veterinário PetSaúde",
                endereco="Rua dos Pinheiros, 321",
                telefone="(11) 4567-8901",
                email="atendimento@petsaude.com.br",
                horario_funcionamento="Seg-Sex: 8h-17h, Sáb: 9h-12h"
            )
        ]
        db.add_all(clinicas)
        db.commit()
        for clinica in clinicas:
            print(f"   ✓ {clinica.nome}")
        
        # 4. CRIAR SERVIÇOS (Exemplo: vacinas e consultas)
        print("\n💉 Criando serviços...")
        
        # Vacinas passadas e futuras para Moana
        vacina1 = Servico(
            pet_id=pet1.id,
            tipo="Vacina",
            descricao="V10 - Polivalente",
            data=datetime.now() - timedelta(days=90),
            valor=120.00,
            veterinario="Dr. João Silva",
            observacoes="Reforço anual aplicado"
        )
        
        vacina2 = Servico(
            pet_id=pet1.id,
            tipo="Vacina",
            descricao="Antirrábica",
            data=datetime.now() + timedelta(days=30),
            valor=80.00,
            veterinario="Dr. João Silva",
            observacoes="Agendado para próximo mês"
        )
        
        # Consulta para Teste
        consulta1 = Servico(
            pet_id=pet2.id,
            tipo="Consulta",
            descricao="Check-up anual",
            data=datetime.now() - timedelta(days=15),
            valor=150.00,
            veterinario="Dra. Maria Santos",
            observacoes="Animal saudável"
        )
        
        # Banho e Tosa para Hulk
        servico1 = Servico(
            pet_id=pet3.id,
            tipo="Banho e Tosa",
            descricao="Banho completo e tosa higiênica",
            data=datetime.now() - timedelta(days=7),
            valor=100.00,
            veterinario="Equipe PetShop",
            observacoes="Animal comportado"
        )
        
        db.add_all([vacina1, vacina2, consulta1, servico1])
        db.commit()
        print(f"   ✓ Vacina V10 para {pet1.name}")
        print(f"   ✓ Vacina Antirrábica agendada para {pet1.name}")
        print(f"   ✓ Consulta para {pet2.name}")
        print(f"   ✓ Banho e Tosa para {pet3.name}")
        
        print("\n✅ Dados iniciais carregados com sucesso!")
        print(f"\n📊 Resumo:")
        print(f"   • {db.query(User).count()} usuários")
        print(f"   • {db.query(Pet).count()} pets")
        print(f"   • {db.query(Clinica).count()} clínicas")
        print(f"   • {db.query(Servico).count()} serviços")
        
        print(f"\n🔐 Credenciais de acesso:")
        print(f"   Email: italoreis99@gmail.com | Senha: senha123")
        print(f"   Email: luandapc3@gmail.com   | Senha: senha123")
        
    except Exception as e:
        print(f"\n❌ Erro ao popular dados: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Função principal"""
    print("=" * 60)
    print("🐾 SETUP DO BANCO DE DADOS - PETCLOUD")
    print("=" * 60)
    
    try:
        criar_tabelas()
        popular_dados_iniciais()
        
        print("\n" + "=" * 60)
        print("✅ Setup concluído com sucesso!")
        print("=" * 60)
        print("\n💡 Próximos passos:")
        print("   1. Certifique-se de ter o arquivo .env configurado")
        print("   2. Execute: cd backend/src && python app.py")
        print("   3. Acesse: http://127.0.0.1:5000/pages/index.html")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Erro durante o setup: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
