
from flask import Flask, request, jsonify, send_from_directory
from services.AuthService import AuthService
from flask_cors import CORS
import os
from models.Pet import Pet
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