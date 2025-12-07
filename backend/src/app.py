
from flask import Flask, request, jsonify, send_from_directory, redirect, session, url_for
from services.AuthService import AuthService
from services.GmailOAuthService import gmail_service
from flask_cors import CORS
import os
import secrets
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from models.Pet import Pet
from models.User import User
from models.PasswordReset import PasswordReset
from models.Servico import Servico
from models.Clinica import Clinica
from config.database import SessionLocal, Base, engine



app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'petcloud-secret-key-change-in-production')
CORS(app)  # Enable CORS for all routes

# Configurações de upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Criar pasta de uploads se não existir
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Cria todas as tabelas (incluindo password_resets)
Base.metadata.create_all(bind=engine)

# Obtém o diretório raiz do projeto
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Rota para redirecionar '/' para o index.html da raiz
@app.route('/')
def home():
    return send_from_directory(ROOT_DIR, 'index.html')

# Rota para servir arquivos de upload
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Rota para cadastro de pet
@app.route('/api/pets', methods=['POST'])
def cadastrar_pet():
    # Verificar se é JSON ou FormData
    if request.content_type and 'multipart/form-data' in request.content_type:
        # FormData com possível arquivo
        name = request.form.get('nome')
        breed = request.form.get('raca')
        birth_date = request.form.get('birth_date')
        pet_type = request.form.get('especie')
        descricao = request.form.get('descricao')
        
        # Processar tags de comportamento
        behavior_tags_str = request.form.get('behavior_tags', '[]')
        print(f"[DEBUG] behavior_tags recebido (string): {behavior_tags_str}")
        try:
            behavior_tags = json.loads(behavior_tags_str)
            print(f"[DEBUG] behavior_tags parseado (lista): {behavior_tags}")
        except Exception as e:
            print(f"[DEBUG] Erro ao parsear behavior_tags: {e}")
            behavior_tags = []
        
        # Processar imagem se enviada
        photo_url = None
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Adicionar timestamp para evitar conflitos
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                photo_url = f"/uploads/{filename}"
    else:
        # JSON tradicional
        data = request.get_json()
        name = data.get('nome')
        breed = data.get('raca')
        birth_date = data.get('birth_date')
        pet_type = data.get('especie')
        descricao = data.get('descricao')
        behavior_tags = data.get('behavior_tags', [])
        photo_url = None

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
    pet = Pet(name=name, breed=breed, birth_date=birth_date_dt, type=pet_type, photo_url=photo_url)
    
    # Adicionar tags de comportamento
    if behavior_tags:
        pet.behavior_tags = json.dumps(behavior_tags)
    
    db.add(pet)
    db.commit()
    db.refresh(pet)
    print(f"[CADASTRO] Pet cadastrado: id={pet.id}, nome={pet.name}, tipo={pet.type}, raca={pet.breed}, nascimento={pet.birth_date}, foto={pet.photo_url}, tags={behavior_tags}")
    db.close()
    return jsonify({
        'success': True,
        'message': 'Pet cadastrado com sucesso!',
        'pet': pet.to_dict() if hasattr(pet, 'to_dict') else {
            'id': pet.id,
            'name': pet.name,
            'breed': pet.breed,
            'birth_date': pet.birth_date.strftime('%Y-%m-%d'),
            'photo_url': pet.photo_url,
            'behavior_tags': behavior_tags
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
                'birth_date': pet.birth_date.strftime('%Y-%m-%d') if pet.birth_date else None,
                'photo_url': pet.photo_url if hasattr(pet, 'photo_url') else None
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

# Rota para estatísticas do dashboard
@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    db = SessionLocal()
    try:
        # Total de pets registrados
        total_pets = db.query(Pet).count()
        
        # Calcular gastos do último mês
        hoje = datetime.now()
        primeiro_dia_mes_atual = hoje.replace(day=1)
        
        # Buscar serviços do mês atual com preço
        servicos_mes = db.query(Servico).filter(
            Servico.data_agendada >= primeiro_dia_mes_atual,
            Servico.data_agendada <= hoje,
            Servico.preco.isnot(None)
        ).all()
        
        total_gastos = sum(servico.preco for servico in servicos_mes if servico.preco)
        
        # Calcular vacinas vencidas
        vacinas_vencidas = 0
        data_limite = hoje - timedelta(days=365)  # 1 ano atrás
        
        # Buscar todos os pets
        todos_pets = db.query(Pet).all()
        
        for pet in todos_pets:
            # Buscar todas as vacinações do pet (serviços do tipo 'vacinacao')
            vacinacoes_pet = db.query(Servico).filter(
                Servico.pet_id == pet.id,
                Servico.tipo == 'vacinacao'
            ).order_by(Servico.data_agendada.desc()).all()
            
            if not vacinacoes_pet:
                # Pet sem nenhuma vacinação agendada = vacina vencida
                vacinas_vencidas += 1
                print(f"[DASHBOARD] Pet {pet.name} (ID: {pet.id}) sem vacinações - VENCIDA")
            else:
                # Verificar a última vacinação
                ultima_vacinacao = vacinacoes_pet[0]
                if ultima_vacinacao.data_agendada < data_limite.date():
                    # Última vacinação há mais de 1 ano = vencida
                    vacinas_vencidas += 1
                    dias_vencida = (hoje.date() - ultima_vacinacao.data_agendada).days
                    print(f"[DASHBOARD] Pet {pet.name} (ID: {pet.id}) - última vacinação há {dias_vencida} dias - VENCIDA")
                else:
                    dias_desde = (hoje.date() - ultima_vacinacao.data_agendada).days
                    print(f"[DASHBOARD] Pet {pet.name} (ID: {pet.id}) - última vacinação há {dias_desde} dias - OK")
        
        print(f"[DASHBOARD] Total de pets: {total_pets}")
        print(f"[DASHBOARD] Gastos do mês: R$ {total_gastos:.2f} ({len(servicos_mes)} serviços)")
        print(f"[DASHBOARD] Vacinas vencidas: {vacinas_vencidas}")
        
        return jsonify({
            'success': True,
            'total_pets': total_pets,
            'gastos_mes': total_gastos,
            'vacinas_vencidas': vacinas_vencidas
        }), 200
        
    except Exception as e:
        print(f"[ERRO] Erro ao buscar estatísticas: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar estatísticas'
        }), 500
    finally:
        db.close()

# Rota para deletar pet
@app.route('/api/pets/<int:pet_id>', methods=['DELETE'])
def deletar_pet(pet_id):
    db = SessionLocal()
    try:
        pet = db.query(Pet).filter(Pet.id == pet_id).first()
        
        if not pet:
            return jsonify({
                'success': False,
                'message': 'Pet não encontrado'
            }), 404
        
        # Deletar foto se existir
        if pet.photo_url:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(pet.photo_url))
            if os.path.exists(photo_path):
                os.remove(photo_path)
        
        db.delete(pet)
        db.commit()
        
        print(f"[DELETE] Pet {pet.name} (ID: {pet_id}) deletado com sucesso")
        return jsonify({
            'success': True,
            'message': 'Pet deletado com sucesso'
        }), 200
        
    except Exception as e:
        db.rollback()
        print(f"[ERRO] Erro ao deletar pet: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao deletar pet'
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

        # Buscar serviços agendados para este pet
        servicos = db.query(Servico).filter(Servico.pet_id == pet_id).order_by(Servico.data_agendada.desc()).all()
        
        pet_data = {
            'id': pet.id,
            'name': pet.name,
            'type': pet.type,
            'breed': pet.breed,
            'birth_date': pet.birth_date.strftime('%Y-%m-%d') if pet.birth_date else None,
            'photo_url': pet.photo_url if hasattr(pet, 'photo_url') else None,
            'owner_id': pet.owner_id if hasattr(pet, 'owner_id') else None,
            'health_records': pet.health_records if hasattr(pet, 'health_records') else None,
            'feeding_schedule': pet.feeding_schedule if hasattr(pet, 'feeding_schedule') else None,
            'servicos': [servico.to_dict() for servico in servicos]
        }
        print(f"[OBTER] Pet encontrado: id={pet.id}, nome={pet.name}, serviços={len(servicos)}")
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

# Rota para atualizar foto do pet
@app.route('/api/pets/<int:pet_id>/photo', methods=['PUT'])
def atualizar_foto_pet(pet_id):
    db = SessionLocal()
    try:
        pet = db.query(Pet).filter(Pet.id == pet_id).first()
        if not pet:
            return jsonify({'success': False, 'message': 'Pet não encontrado'}), 404

        # Verificar se há arquivo
        if 'foto' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['foto']
        if not file or not file.filename:
            return jsonify({'success': False, 'message': 'Arquivo inválido'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'}), 400

        # Salvar arquivo
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Atualizar photo_url no banco
        pet.photo_url = f"/uploads/{filename}"
        db.commit()
        db.refresh(pet)
        
        print(f"[FOTO] Pet {pet_id} foto atualizada: {pet.photo_url}")
        
        return jsonify({
            'success': True,
            'message': 'Foto atualizada com sucesso!',
            'photo_url': pet.photo_url
        }), 200
        
    except Exception as e:
        db.rollback()
        print(f"[ERRO] Erro ao atualizar foto do pet {pet_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro ao atualizar foto'}), 500
    finally:
        db.close()

# Rota para obter o veterinário principal de um pet (baseado nos serviços)
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

        # Busca todos os serviços do pet que têm veterinário informado
        servicos = db.query(Servico).filter(
            Servico.pet_id == pet_id,
            Servico.veterinario.isnot(None)
        ).all()
        
        if not servicos:
            return jsonify({
                'success': True,
                'main_veterinarian': None,
                'message': 'Nenhum serviço com veterinário cadastrado para este pet'
            }), 200

        # Conta a frequência de cada veterinário
        from collections import Counter
        veterinarios = [s.veterinario for s in servicos if s.veterinario]
        
        if not veterinarios:
            return jsonify({
                'success': True,
                'main_veterinarian': None,
                'message': 'Nenhum veterinário informado nos serviços'
            }), 200

        # Pega o veterinário mais frequente
        contador = Counter(veterinarios)
        veterinario_principal = contador.most_common(1)[0][0]
        frequencia = contador.most_common(1)[0][1]
        
        print(f"[VETERINARIO] Pet {pet_id} - Veterinário principal: {veterinario_principal} ({frequencia} serviços)")
        
        return jsonify({
            'success': True,
            'main_veterinarian': veterinario_principal,
            'frequency': frequencia,
            'total_services': len(servicos)
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


# =========================================== 
# Rotas de Recuperação de Senha com OAuth
# ===========================================

@app.route('/api/auth/oauth-status', methods=['GET'])
def oauth_status():
    """Verifica se o OAuth está configurado"""
    is_auth = gmail_service.is_authenticated()
    return jsonify({
        'success': True,
        'authenticated': is_auth,
        'message': 'OAuth configurado' if is_auth else 'OAuth não configurado. Execute /api/auth/setup-oauth primeiro.'
    })


@app.route('/api/auth/setup-oauth', methods=['GET'])
def setup_oauth():
    """Inicia o fluxo OAuth - redireciona para a página de autorização do Google"""
    redirect_uri = url_for('oauth_callback', _external=True)
    auth_url, state = gmail_service.get_authorization_url(redirect_uri)
    
    # Salva o state na sessão para validação
    session['oauth_state'] = state
    
    return redirect(auth_url)


@app.route('/callback')
def oauth_callback():
    """Callback do OAuth - recebe o código de autorização e troca por token"""
    # Verifica se houve erro
    if 'error' in request.args:
        return jsonify({
            'success': False,
            'message': f'Erro na autorização: {request.args.get("error")}'
        }), 400
    
    # Obtém o código
    code = request.args.get('code')
    if not code:
        return jsonify({
            'success': False,
            'message': 'Código de autorização não fornecido'
        }), 400
    
    # Troca o código por token
    redirect_uri = url_for('oauth_callback', _external=True)
    try:
        gmail_service.exchange_code_for_token(code, redirect_uri)
        return '''
        <html>
            <head>
                <title>Autorização Concluída - PetCloud</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #a8e6f5 0%, #c4e9f7 100%);
                    }
                    .container {
                        background: white;
                        padding: 40px;
                        border-radius: 20px;
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                        text-align: center;
                    }
                    h1 { color: #FF9933; margin-bottom: 20px; }
                    p { color: #666; margin-bottom: 30px; }
                    .btn {
                        background: #FF9933;
                        color: white;
                        padding: 12px 30px;
                        border: none;
                        border-radius: 50px;
                        font-size: 16px;
                        font-weight: 700;
                        text-decoration: none;
                        display: inline-block;
                        cursor: pointer;
                    }
                    .btn:hover { background: #E68A2E; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ Autorização Concluída!</h1>
                    <p>O PetCloud agora pode enviar emails de recuperação de senha via Gmail.</p>
                    <a href="/dashboard.html" class="btn">Voltar ao Dashboard</a>
                </div>
            </body>
        </html>
        '''
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao trocar código por token: {str(e)}'
        }), 500


@app.route('/api/auth/request-password-reset', methods=['POST'])
def request_password_reset():
    """Solicita redefinição de senha - gera token e envia email"""
    data = request.get_json() or {}
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email é obrigatório.'}), 400
    
    db = SessionLocal()
    try:
        # Busca o usuário
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Por segurança, não revela se o email existe
            print(f'[RESET] Tentativa de reset para email não cadastrado: {email}')
            return jsonify({
                'success': True,
                'message': 'Se o e-mail estiver cadastrado, um link de recuperação foi enviado.'
            }), 200
        
        # Gera token único
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=1)
        
        # Salva o token no banco
        pr = PasswordReset(user_id=user.id, token=token, expires_at=expires)
        db.add(pr)
        db.commit()
        db.refresh(pr)
        
        # Monta o link de reset
        base_url = request.host_url.rstrip('/')
        reset_link = f"{base_url}/recuperar-senha.html?token={token}"
        
        # Prepara o email
        email_subject = 'Redefinição de senha - PetCloud'
        email_body = f"""Olá {user.name},

Você solicitou a redefinição de senha para sua conta no PetCloud.

Para redefinir sua senha, acesse o link abaixo (válido por 1 hora):

{reset_link}

Se você não solicitou esta redefinição, ignore este e-mail.

Atenciosamente,
Equipe PetCloud 🐾"""
        
        # Tenta enviar o email via OAuth
        if gmail_service.is_authenticated():
            success = gmail_service.send_email(user.email, email_subject, email_body)
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Link de recuperação enviado por e-mail.'
                }), 200
            else:
                # Se falhar, retorna o link para teste (dev)
                print(f'[RESET] Falha ao enviar email. Link de reset (dev): {reset_link}')
                return jsonify({
                    'success': True,
                    'message': 'Erro ao enviar e-mail. Use o link abaixo para teste:',
                    'reset_link': reset_link
                }), 200
        else:
            # OAuth não configurado - retorna link para teste
            print(f'[RESET] OAuth não configurado. Link de reset (dev): {reset_link}')
            return jsonify({
                'success': True,
                'message': 'OAuth não configurado. Configure primeiro em /api/auth/setup-oauth. Link para teste:',
                'reset_link': reset_link,
                'oauth_setup_url': '/api/auth/setup-oauth'
            }), 200
    
    except Exception as e:
        db.rollback()
        print(f'[ERRO] Erro ao criar token de reset: {e}')
        return jsonify({'success': False, 'message': 'Erro ao processar requisição'}), 500
    finally:
        db.close()


@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Aplica a redefinição de senha usando o token"""
    data = request.get_json() or {}
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token or not new_password:
        return jsonify({
            'success': False,
            'message': 'Token e nova senha são obrigatórios.'
        }), 400
    
    db = SessionLocal()
    try:
        # Busca o token
        pr = db.query(PasswordReset).filter(PasswordReset.token == token).first()
        if not pr:
            return jsonify({'success': False, 'message': 'Token inválido.'}), 400
        
        # Verifica expiração
        if pr.expires_at < datetime.utcnow():
            db.delete(pr)
            db.commit()
            return jsonify({'success': False, 'message': 'Token expirado.'}), 400
        
        # Busca o usuário
        user = db.query(User).filter(User.id == pr.user_id).first()
        if not user:
            return jsonify({'success': False, 'message': 'Usuário não encontrado.'}), 404
        
        # Atualiza a senha (usa hash do AuthService)
        auth = AuthService()
        hashed = auth._hash_password(new_password)
        user.password = hashed
        
        # Remove o token
        db.delete(pr)
        db.commit()
        
        print(f'[RESET] Senha redefinida para usuário id={user.id}, email={user.email}')
        
        return jsonify({
            'success': True,
            'message': 'Senha redefinida com sucesso.'
        }), 200
        
    except Exception as e:
        db.rollback()
        print(f'[ERRO] Erro ao redefinir senha: {e}')
        return jsonify({'success': False, 'message': 'Erro ao redefinir senha.'}), 500
    finally:
        db.close()


# ===== ROTAS DE CLÍNICAS =====

@app.route('/api/clinicas', methods=['GET'])
def get_clinicas():
    """Lista todas as clínicas cadastradas"""
    db = SessionLocal()
    try:
        tipo = request.args.get('tipo')  # Filtrar por tipo de serviço (opcional)
        
        query = db.query(Clinica)
        if tipo:
            query = query.filter(Clinica.tipo_servico == tipo)
        
        clinicas = query.all()
        
        return jsonify({
            'success': True,
            'clinicas': [clinica.to_dict() for clinica in clinicas]
        }), 200
        
    except Exception as e:
        print(f'[ERRO] Erro ao listar clínicas: {e}')
        return jsonify({'success': False, 'message': 'Erro ao listar clínicas.'}), 500
    finally:
        db.close()


# ===== ROTAS DE SERVIÇOS =====

@app.route('/api/servicos', methods=['POST'])
def create_servico():
    """Cria um novo agendamento de serviço"""
    db = SessionLocal()
    try:
        data = request.json
        
        # Validar campos obrigatórios
        required_fields = ['pet_id', 'tipo', 'data_agendada', 'clinica_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Campo {field} é obrigatório.'}), 400
        
        # Buscar clínica para pegar veterinário e preço
        clinica = db.query(Clinica).filter(Clinica.id == data['clinica_id']).first()
        if not clinica:
            return jsonify({'success': False, 'message': 'Clínica não encontrada.'}), 404
        
        # Verificar se o pet existe
        pet = db.query(Pet).filter(Pet.id == data['pet_id']).first()
        if not pet:
            return jsonify({'success': False, 'message': 'Pet não encontrado.'}), 404
        
        # Criar serviço
        servico = Servico(
            pet_id=data['pet_id'],
            clinica_id=data['clinica_id'],
            tipo=data['tipo'],
            data_agendada=datetime.strptime(data['data_agendada'], '%Y-%m-%d').date(),
            preco=clinica.preco_servico,
            clinica=clinica.nome,
            veterinario=clinica.veterinario
        )
        
        db.add(servico)
        db.commit()
        db.refresh(servico)
        
        print(f'[SERVICO] Agendamento criado: {servico.tipo} para pet {pet.name} na {clinica.nome}')
        
        return jsonify({
            'success': True,
            'message': 'Serviço agendado com sucesso!',
            'servico': servico.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'success': False, 'message': 'Formato de data inválido. Use YYYY-MM-DD.'}), 400
    except Exception as e:
        db.rollback()
        print(f'[ERRO] Erro ao criar serviço: {e}')
        return jsonify({'success': False, 'message': 'Erro ao agendar serviço.'}), 500
    finally:
        db.close()


if __name__ == '__main__':
    app.run(debug=True, port=5000)