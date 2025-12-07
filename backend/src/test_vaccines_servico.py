from config.database import SessionLocal
from models.Pet import Pet
from models.Servico import Servico
from datetime import datetime, timedelta

db = SessionLocal()

print("=== VERIFICANDO VACINAÇÕES (via Servico) ===\n")

hoje = datetime.now()
data_limite = hoje - timedelta(days=365)

pets = db.query(Pet).all()
print(f"Total de pets: {len(pets)}\n")

vacinas_vencidas = 0

for pet in pets:
    vacinacoes = db.query(Servico).filter(
        Servico.pet_id == pet.id,
        Servico.tipo == 'vacinacao'
    ).order_by(Servico.data_agendada.desc()).all()
    
    print(f"Pet: {pet.name} (ID: {pet.id})")
    print(f"  Vacinações cadastradas: {len(vacinacoes)}")
    
    if vacinacoes:
        for v in vacinacoes:
            dias = (hoje.date() - v.data_agendada).days
            print(f"    - Data: {v.data_agendada} (há {dias} dias)")
            if v.veterinario:
                print(f"      Veterinário: {v.veterinario}")
            if v.clinica:
                print(f"      Clínica: {v.clinica}")
        
        ultima = vacinacoes[0]
        if ultima.data_agendada < data_limite.date():
            print(f"  ❌ VENCIDA - Última vacinação há mais de 1 ano")
            vacinas_vencidas += 1
        else:
            print(f"  ✅ OK - Vacinação em dia")
    else:
        print("    - Nenhuma vacinação cadastrada")
        print(f"  ❌ VENCIDA - Sem vacinações")
        vacinas_vencidas += 1
    
    print()

print(f"\n📊 TOTAL DE VACINAS VENCIDAS: {vacinas_vencidas}")

db.close()
