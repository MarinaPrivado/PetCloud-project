
from flask import Flask, request, jsonify, send_from_directory
from services.AuthService import AuthService
from flask_cors import CORS
import os
from models.Pet import Pet
from models.Vaccine import Vaccine
from config.database import SessionLocal



app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Obtém o diretório raiz do projeto
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Rota para redirecionar '/' para o index.html da raiz
@app.route('/')
def home():
    return send_from_directory(ROOT_DIR, 'index.html')

# Rota para cadastro de pet
@app.route('/api/pets', methods=['POST'])
def cadastrar_pet():
    data = request.get_json()
    name = data.get('nome')
    breed = data.get('raca')
    birth_date = data.get('birth_date')
    pet_type = data.get('especie')  # Captura o campo especie (opcional)

    # Validação dos campos obrigatórios
    if not all([name, breed, birth_date]):
        return jsonify({
            'success': False,
            'message': 'Nome, raça e data de nascimento são obrigatórios.'
        }), 400

    # Converte birth_date para datetime
    from datetime import datetime
    try:
        birth_date_dt = datetime.strptime(birth_date, '%Y-%m-%d')
    except Exception:
        return jsonify({
            'success': False,
            'message': 'Data de nascimento inválida. Use o formato YYYY-MM-DD.'
        }), 400

    db = SessionLocal()
    pet = Pet(name=name, breed=breed, birth_date=birth_date_dt, type=pet_type)
    db.add(pet)
    db.commit()
    db.refresh(pet)
    print(f"[CADASTRO] Pet cadastrado: id={pet.id}, nome={pet.name}, tipo={pet.type}, raca={pet.breed}, nascimento={pet.birth_date}")
    db.close()
    return jsonify({
        'success': True,
        'message': 'Pet cadastrado com sucesso!',
        'pet': pet.to_dict() if hasattr(pet, 'to_dict') else {
            'id': pet.id,
            'name': pet.name,
            'breed': pet.breed,
            'birth_date': pet.birth_date.strftime('%Y-%m-%d')
        }
    }), 201

# Rota para listar todos os pets
@app.route('/api/pets', methods=['GET'])
def listar_pets():
    db = SessionLocal()
    try:
        pets = db.query(Pet).all()
        pets_list = []
        for pet in pets:
            pets_list.append({
                'id': pet.id,
                'name': pet.name,
                'type': pet.type,
                'breed': pet.breed,
                'birth_date': pet.birth_date.strftime('%Y-%m-%d') if pet.birth_date else None
            })
        print(f"[LISTAGEM] Retornando {len(pets_list)} pets")
        return jsonify({
            'success': True,
            'pets': pets_list
        }), 200
    except Exception as e:
        print(f"[ERRO] Erro ao listar pets: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao listar pets'
        }), 500
    finally:
        db.close()

# Rota para obter um pet por ID
@app.route('/api/pets/<int:pet_id>', methods=['GET'])
def obter_pet(pet_id):
    db = SessionLocal()
    try:
        pet = db.query(Pet).filter(Pet.id == pet_id).first()
        if not pet:
            return jsonify({'success': False, 'message': 'Pet não encontrado'}), 404

        pet_data = {
            'id': pet.id,
            'name': pet.name,
            'type': pet.type,
            'breed': pet.breed,
            'birth_date': pet.birth_date.strftime('%Y-%m-%d') if pet.birth_date else None,
            'owner_id': pet.owner_id if hasattr(pet, 'owner_id') else None,
            'health_records': pet.health_records if hasattr(pet, 'health_records') else None,
            'feeding_schedule': pet.feeding_schedule if hasattr(pet, 'feeding_schedule') else None
        }
        print(f"[OBTER] Pet encontrado: id={pet.id}, nome={pet.name}")
        return jsonify({'success': True, 'pet': pet_data}), 200
    except Exception as e:
        print(f"[ERRO] Erro ao obter pet {pet_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro ao buscar pet'}), 500
    finally:
        db.close()

# Rota para atualizar um pet por ID
@app.route('/api/pets/<int:pet_id>', methods=['PUT'])
def atualizar_pet(pet_id):
    db = SessionLocal()
    try:
        pet = db.query(Pet).filter(Pet.id == pet_id).first()
        if not pet:
            return jsonify({'success': False, 'message': 'Pet não encontrado'}), 404

        data = request.get_json()
        
        # Atualiza os campos se fornecidos
        if 'nome' in data or 'name' in data:
            pet.name = data.get('nome') or data.get('name')
        if 'raca' in data or 'breed' in data:
            pet.breed = data.get('raca') or data.get('breed')
        if 'especie' in data or 'type' in data:
            pet.type = data.get('especie') or data.get('type')
        if 'birth_date' in data:
            from datetime import datetime
            try:
                pet.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d')
            except Exception as e:
                return jsonify({'success': False, 'message': 'Data de nascimento inválida'}), 400

        db.commit()
        db.refresh(pet)
        
        print(f"[ATUALIZAR] Pet atualizado: id={pet.id}, nome={pet.name}, tipo={pet.type}, raca={pet.breed}")
        
        return jsonify({
            'success': True,
            'message': 'Pet atualizado com sucesso!',
            'pet': {
                'id': pet.id,
                'name': pet.name,
                'type': pet.type,
                'breed': pet.breed,
                'birth_date': pet.birth_date.strftime('%Y-%m-%d') if pet.birth_date else None
            }
        }), 200
    except Exception as e:
        db.rollback()
        print(f"[ERRO] Erro ao atualizar pet {pet_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro ao atualizar pet'}), 500
    finally:
        db.close()

# =========================================== 
# Rotas de Vacinas
# ===========================================

# Rota para cadastrar uma vacina
@app.route('/api/vaccines', methods=['POST'])
def cadastrar_vacina():
    db = SessionLocal()
    try:
        data = request.get_json()
        tipo = data.get('type') or data.get('tipo')
        data_programada = data.get('scheduled_date') or data.get('data_programada')
        veterinario = data.get('veterinarian') or data.get('veterinario')
        pet_id = data.get('pet_id')

        # Validação dos campos obrigatórios
        if not all([tipo, data_programada, pet_id]):
            return jsonify({
                'success': False,
                'message': 'Tipo, data programada e pet_id são obrigatórios.'
            }), 400

        # Verifica se o pet existe
        pet = db.query(Pet).filter(Pet.id == pet_id).first()
        if not pet:
            return jsonify({
                'success': False,
                'message': 'Pet não encontrado.'
            }), 404

        # Converte data_programada para date
        from datetime import datetime
        try:
            data_programada_dt = datetime.strptime(data_programada, '%Y-%m-%d').date()
        except Exception:
            return jsonify({
                'success': False,
                'message': 'Data programada inválida. Use o formato YYYY-MM-DD.'
            }), 400

        vacina = Vaccine(
            type=tipo,
            scheduled_date=data_programada_dt,
            veterinarian=veterinario,
            pet_id=pet_id
        )
        db.add(vacina)
        db.commit()
        db.refresh(vacina)
        
        print(f"[CADASTRO] Vacina cadastrada: id={vacina.id}, tipo={vacina.type}, pet_id={vacina.pet_id}")
        
        return jsonify({
            'success': True,
            'message': 'Vacina cadastrada com sucesso!',
            'vaccine': vacina.to_dict()
        }), 201
    except Exception as e:
        db.rollback()
        print(f"[ERRO] Erro ao cadastrar vacina: {e}")
        return jsonify({'success': False, 'message': 'Erro ao cadastrar vacina'}), 500
    finally:
        db.close()

# Rota para listar todas as vacinas
@app.route('/api/vaccines', methods=['GET'])
def listar_vacinas():
    db = SessionLocal()
    try:
        vacinas = db.query(Vaccine).all()
        vacinas_list = [vacina.to_dict() for vacina in vacinas]
        
        print(f"[LISTAGEM] Retornando {len(vacinas_list)} vacinas")
        return jsonify({
            'success': True,
            'vaccines': vacinas_list
        }), 200
    except Exception as e:
        print(f"[ERRO] Erro ao listar vacinas: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao listar vacinas'
        }), 500
    finally:
        db.close()

# Rota para listar vacinas de um pet específico
@app.route('/api/pets/<int:pet_id>/vaccines', methods=['GET'])
def listar_vacinas_pet(pet_id):
    db = SessionLocal()
    try:
        # Verifica se o pet existe
        pet = db.query(Pet).filter(Pet.id == pet_id).first()
        if not pet:
            return jsonify({
                'success': False,
                'message': 'Pet não encontrado'
            }), 404

        vacinas = db.query(Vaccine).filter(Vaccine.pet_id == pet_id).all()
        vacinas_list = [vacina.to_dict() for vacina in vacinas]
        
        print(f"[LISTAGEM] Retornando {len(vacinas_list)} vacinas do pet {pet_id}")
        return jsonify({
            'success': True,
            'vaccines': vacinas_list
        }), 200
    except Exception as e:
        print(f"[ERRO] Erro ao listar vacinas do pet {pet_id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao listar vacinas'
        }), 500
    finally:
        db.close()

# Rota para obter o veterinário principal de um pet (baseado nas vacinas)
@app.route('/api/pets/<int:pet_id>/main-veterinarian', methods=['GET'])
def obter_veterinario_principal(pet_id):
    db = SessionLocal()
    try:
        # Verifica se o pet existe
        pet = db.query(Pet).filter(Pet.id == pet_id).first()
        if not pet:
            return jsonify({
                'success': False,
                'message': 'Pet não encontrado'
            }), 404

        # Busca todas as vacinas do pet
        vacinas = db.query(Vaccine).filter(Vaccine.pet_id == pet_id).all()
        
        if not vacinas:
            return jsonify({
                'success': True,
                'main_veterinarian': None,
                'message': 'Nenhuma vacina cadastrada para este pet'
            }), 200

        # Conta a frequência de cada veterinário
        from collections import Counter
        veterinarios = [v.veterinarian for v in vacinas if v.veterinarian]
        
        if not veterinarios:
            return jsonify({
                'success': True,
                'main_veterinarian': None,
                'message': 'Nenhum veterinário informado nas vacinas'
            }), 200

        # Pega o veterinário mais frequente
        contador = Counter(veterinarios)
        veterinario_principal = contador.most_common(1)[0][0]
        frequencia = contador.most_common(1)[0][1]
        
        print(f"[VETERINARIO] Pet {pet_id} - Veterinário principal: {veterinario_principal} ({frequencia} vacinas)")
        
        return jsonify({
            'success': True,
            'main_veterinarian': veterinario_principal,
            'frequency': frequencia,
            'total_vaccines': len(vacinas)
        }), 200
    except Exception as e:
        print(f"[ERRO] Erro ao obter veterinário principal do pet {pet_id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao obter veterinário principal'
        }), 500
    finally:
        db.close()

# Rota para servir arquivos estáticos da raiz (css, imagens, etc)
@app.route('/<path:filename>')
def serve_static(filename):
    if os.path.exists(os.path.join(ROOT_DIR, filename)):
        return send_from_directory(ROOT_DIR, filename)
    elif os.path.exists(os.path.join(ROOT_DIR, 'pages', filename)):
        return send_from_directory(os.path.join(ROOT_DIR, 'pages'), filename)
    return "File not found", 404

# Rotas específicas para cada página
@app.route('/login.html')
def login_page():
    return send_from_directory(os.path.join(ROOT_DIR, 'pages'), 'login.html')

@app.route('/cadastro.html')
def cadastro_page():
    return send_from_directory(os.path.join(ROOT_DIR, 'pages'), 'cadastro.html')

@app.route('/recuperar-senha.html')
def recuperar_senha_page():
    return send_from_directory(os.path.join(ROOT_DIR, 'pages'), 'recuperar-senha.html')

@app.route('/dashboard.html')
def dashboard_page():
    return send_from_directory(os.path.join(ROOT_DIR, 'pages'), 'dashboard.html')

@app.route('/listagem.html')
def listagem_page():
    return send_from_directory(os.path.join(ROOT_DIR, 'pages'), 'listagem.html')

@app.route('/detalhes.html')
def detalhes_page():
    return send_from_directory(os.path.join(ROOT_DIR, 'pages'), 'detalhes.html')

@app.route('/detalhes-mimi.html')
def detalhes_mimi_page():
    return send_from_directory(os.path.join(ROOT_DIR, 'pages'), 'detalhes-mimi.html')

@app.route('/concurso.html')
def concurso_page():
    return send_from_directory(os.path.join(ROOT_DIR, 'pages'), 'concurso.html')

auth_service = AuthService()

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({
            'success': False,
            'message': 'Email e senha são obrigatórios'
        }), 400
    
    success, message, user = auth_service.login(email, password)
    
    if not success:
        return jsonify({
            'success': False,
            'message': message
        }), 401
    
    return jsonify({
        'success': True,
        'message': message,
        'user': user.to_dict() if user else None
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not all([name, email, password]):
        return jsonify({
            'success': False,
            'message': 'Nome, email e senha são obrigatórios'
        }), 400
    
    success, message, user = auth_service.register(name, email, password)
    
    if not success:
        return jsonify({
            'success': False,
            'message': message
        }), 400
    
    return jsonify({
        'success': True,
        'message': message,
        'user': user.to_dict() if user else None
    }), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)