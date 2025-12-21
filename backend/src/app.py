
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
from models.Concurso import Concurso
from config.database import SessionLocal, Base, engine
from openai import OpenAI
from dotenv import load_dotenv
import json

# Load environment variables from parent directory (backend/.env)
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

# Initialize OpenAI client
openai_client = None
if os.environ.get('OPENAI_API_KEY'):
    openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    print(f"[OPENAI] Cliente inicializado com sucesso")
else:
    print(f"[OPENAI] AVISO: Chave API não encontrada em {env_path}")




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
        user_email = request.form.get('user_email')  # Email do usuário logado
        
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
        user_email = data.get('user_email')  # Email do usuário logado
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
    
    # Buscar owner_id pelo email do usuário
    owner_id = None
    if user_email:
        user = db.query(User).filter(User.email == user_email).first()
        if user:
            owner_id = user.id
            print(f"[CADASTRO] Usuário encontrado: {user.name} (ID: {owner_id})")
        else:
            print(f"[CADASTRO] Usuário com email {user_email} não encontrado")
    else:
        print(f"[CADASTRO] Nenhum email de usuário fornecido")
    
    pet = Pet(
        name=name, 
        breed=breed, 
        birth_date=birth_date_dt, 
        type=pet_type, 
        photo_url=photo_url,
        owner_id=owner_id  # Associar ao dono
    )
    
    # Adicionar tags de comportamento
    if behavior_tags:
        pet.behavior_tags = json.dumps(behavior_tags)
    
    db.add(pet)
    db.commit()
    db.refresh(pet)
    print(f"[CADASTRO] Pet cadastrado: id={pet.id}, nome={pet.name}, tipo={pet.type}, raca={pet.breed}, nascimento={pet.birth_date}, foto={pet.photo_url}, tags={behavior_tags}, owner_id={pet.owner_id}")
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
        # Obter email do usuário dos parâmetros da query
        user_email = request.args.get('user_email')
        
        if user_email:
            # Buscar o usuário pelo email
            user = db.query(User).filter(User.email == user_email).first()
            if not user:
                print(f"[LISTAGEM] Usuário com email {user_email} não encontrado")
                return jsonify({
                    'success': False,
                    'message': 'Usuário não encontrado'
                }), 404
            
            # Filtrar pets pelo owner_id do usuário
            pets = db.query(Pet).filter(Pet.owner_id == user.id).all()
            print(f"[LISTAGEM] Retornando {len(pets)} pets do usuário {user.name} (ID: {user.id})")
        else:
            # Se não passar email, retorna todos os pets (modo legado)
            pets = db.query(Pet).all()
            print(f"[LISTAGEM] Nenhum user_email fornecido. Retornando todos os {len(pets)} pets")
        
        pets_list = []
        for pet in pets:
            pets_list.append({
                'id': pet.id,
                'name': pet.name,
                'type': pet.type,
                'breed': pet.breed,
                'birth_date': pet.birth_date.strftime('%Y-%m-%d') if pet.birth_date else None,
                'photo_url': pet.photo_url if hasattr(pet, 'photo_url') else None,
                'owner_id': pet.owner_id if hasattr(pet, 'owner_id') else None
            })
        
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


@app.route('/api/users', methods=['GET'])
def listar_usuarios():
    """Endpoint para listar usuários (com filtro opcional por email)"""
    db = SessionLocal()
    try:
        email = request.args.get('email')
        
        if email:
            users = db.query(User).filter(User.email == email).all()
        else:
            users = db.query(User).all()
        
        users_list = []
        for user in users:
            users_list.append({
                'id': user.id,
                'name': user.name,
                'email': user.email
            })
        
        return jsonify({
            'success': True,
            'users': users_list
        }), 200
        
    except Exception as e:
        print(f"[ERRO] Erro ao listar usuários: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao listar usuários'
        }), 500
    finally:
        db.close()


# Rota para estatísticas do dashboard
@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    db = SessionLocal()
    try:
        # Obter email do usuário dos parâmetros da query
        user_email = request.args.get('user_email')
        
        if not user_email:
            return jsonify({
                'success': False,
                'message': 'Email do usuário não fornecido'
            }), 400
        
        # Buscar o usuário pelo email
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuário não encontrado'
            }), 404
        
        # Total de pets registrados DO USUÁRIO
        total_pets = db.query(Pet).filter(Pet.owner_id == user.id).count()
        
        # Calcular gastos do mês atual (dezembro/2025)
        hoje = datetime.now()
        primeiro_dia_mes_atual = hoje.replace(day=1)
        ultimo_dia_mes_atual = (primeiro_dia_mes_atual.replace(month=primeiro_dia_mes_atual.month % 12 + 1, day=1) - timedelta(days=1)) if primeiro_dia_mes_atual.month < 12 else primeiro_dia_mes_atual.replace(day=31)
        
        # Buscar IDs dos pets do usuário
        pet_ids = [pet.id for pet in db.query(Pet).filter(Pet.owner_id == user.id).all()]
        
        # Buscar serviços do mês atual (1 a 31 de dezembro) com preço DOS PETS DO USUÁRIO
        servicos_mes = db.query(Servico).filter(
            Servico.pet_id.in_(pet_ids),
            Servico.data_agendada >= primeiro_dia_mes_atual,
            Servico.data_agendada <= ultimo_dia_mes_atual,
            Servico.preco.isnot(None)
        ).all()
        
        total_gastos = sum(servico.preco for servico in servicos_mes if servico.preco)
        
        # Calcular vacinas vencidas
        vacinas_vencidas = 0
        data_limite = hoje - timedelta(days=365)  # 1 ano atrás
        
        # Buscar todos os pets DO USUÁRIO
        todos_pets = db.query(Pet).filter(Pet.owner_id == user.id).all()
        
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
        
        print(f"[DASHBOARD] Usuário: {user.name} (ID: {user.id})")
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

# Rota para detalhes de vacinas vencidas
@app.route('/api/dashboard/vacinas-vencidas', methods=['GET'])
def vacinas_vencidas_detalhes():
    db = SessionLocal()
    try:
        # Obter email do usuário da query string
        user_email = request.args.get('user_email', '')
        
        hoje = datetime.now()
        data_limite = hoje - timedelta(days=365)  # 1 ano atrás
        
        vacinas_vencidas_lista = []
        
        # Buscar usuário pelo email
        user = db.query(User).filter(User.email == user_email).first() if user_email else None
        
        # Buscar pets do usuário ou todos se não autenticado
        if user:
            todos_pets = db.query(Pet).filter(Pet.owner_id == user.id).all()
        else:
            todos_pets = db.query(Pet).all()
        
        for pet in todos_pets:
            # Buscar todas as vacinações do pet (serviços do tipo 'vacinacao')
            vacinacoes_pet = db.query(Servico).filter(
                Servico.pet_id == pet.id,
                Servico.tipo == 'vacinacao'
            ).order_by(Servico.data_agendada.desc()).all()
            
            if not vacinacoes_pet:
                # Pet sem nenhuma vacinação agendada - considera como muito atrasado
                vacinas_vencidas_lista.append({
                    'pet_id': pet.id,
                    'pet_name': pet.name,
                    'status': 'sem_vacinacao',
                    'mensagem': 'Nenhuma vacinação cadastrada',
                    'dias_apos_vencimento': 999  # Valor alto para indicar que nunca foi vacinado
                })
                print(f"[VACINAS VENCIDAS] Pet {pet.name} sem vacinação - adicionado à lista")
            else:
                # Verificar a última vacinação
                ultima_vacinacao = vacinacoes_pet[0]
                if ultima_vacinacao.data_agendada < data_limite.date():
                    # Calcular total de dias desde a vacinação
                    dias_desde_vacinacao = (hoje.date() - ultima_vacinacao.data_agendada).days
                    # Calcular há quantos dias está vencida (após 1 ano do vencimento)
                    dias_apos_vencimento = dias_desde_vacinacao - 365
                    
                    vacinas_vencidas_lista.append({
                        'pet_id': pet.id,
                        'pet_name': pet.name,
                        'status': 'vencida',
                        'ultima_vacinacao': ultima_vacinacao.data_agendada.isoformat(),
                        'dias_desde_vacinacao': dias_desde_vacinacao,
                        'dias_apos_vencimento': dias_apos_vencimento,
                        'mensagem': f'Vencida há {dias_apos_vencimento} dias'
                    })
                    print(f"[VACINAS VENCIDAS] Pet {pet.name} com vacinação vencida há {dias_apos_vencimento} dias - adicionado à lista")
                else:
                    print(f"[VACINAS VENCIDAS] Pet {pet.name} com vacinação em dia - NÃO adicionado")
        
        print(f"[VACINAS VENCIDAS] Total: {len(vacinas_vencidas_lista)}")
        if len(vacinas_vencidas_lista) > 0:
            print(f"[VACINAS VENCIDAS] Pets encontrados:")
            for v in vacinas_vencidas_lista:
                print(f"  - {v['pet_name']} ({v['status']})")
        
        return jsonify({
            'success': True,
            'vacinas_vencidas': vacinas_vencidas_lista,
            'total': len(vacinas_vencidas_lista)
        }), 200
        
    except Exception as e:
        print(f"[ERRO] Erro ao buscar vacinas vencidas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar vacinas vencidas'
        }), 500
    finally:
        db.close()

# Rota para próximos agendamentos
@app.route('/api/dashboard/proximos-agendamentos', methods=['GET'])
def proximos_agendamentos():
    db = SessionLocal()
    try:
        # Obter email do usuário da query string
        user_email = request.args.get('user_email', '')
        
        hoje = datetime.now().date()
        # Buscar agendamentos futuros (próximo ano) e recentes atrasados (últimos 7 dias)
        data_limite_futura = hoje + timedelta(days=365)
        data_limite_passada = hoje - timedelta(days=7)
        
        # Buscar usuário pelo email
        user = db.query(User).filter(User.email == user_email).first() if user_email else None
        
        # Filtrar agendamentos por usuário
        if user:
            # Buscar agendamentos dos pets do usuário (incluindo atrasados recentes)
            agendamentos = db.query(Servico).join(Pet).filter(
                Pet.owner_id == user.id,
                Servico.data_agendada >= data_limite_passada,
                Servico.data_agendada <= data_limite_futura
            ).order_by(Servico.data_agendada.asc()).all()
        else:
            agendamentos = db.query(Servico).filter(
                Servico.data_agendada >= data_limite_passada,
                Servico.data_agendada <= data_limite_futura
            ).order_by(Servico.data_agendada.asc()).all()
        
        agendamentos_lista = []
        
        for servico in agendamentos:
            pet = db.query(Pet).filter(Pet.id == servico.pet_id).first()
            
            if pet:
                dias_ate_agendamento = (servico.data_agendada - hoje).days
                atrasado = dias_ate_agendamento < 0
                
                # Definir ícone e tipo baseado no serviço
                if servico.tipo == 'vacinacao':
                    icone = 'fa-syringe'
                    tipo_label = 'Vacinação'
                elif servico.tipo == 'banho':
                    icone = 'fa-cut'
                    tipo_label = 'Banho'
                elif servico.tipo == 'consulta':
                    icone = 'fa-notes-medical'
                    tipo_label = 'Consulta'
                else:
                    icone = 'fa-calendar-check'
                    tipo_label = servico.tipo.capitalize()
                
                agendamentos_lista.append({
                    'pet_id': pet.id,
                    'pet_name': pet.name,
                    'tipo': servico.tipo,
                    'tipo_label': tipo_label,
                    'data_agendada': servico.data_agendada.isoformat(),
                    'dias_ate': dias_ate_agendamento,
                    'atrasado': atrasado,
                    'clinica': servico.clinica,
                    'veterinario': servico.veterinario,
                    'icone': icone
                })
        
        print(f"[AGENDAMENTOS] Total de próximos agendamentos: {len(agendamentos_lista)}")
        
        return jsonify({
            'success': True,
            'agendamentos': agendamentos_lista,
            'total': len(agendamentos_lista)
        }), 200
        
    except Exception as e:
        print(f"[ERRO] Erro ao buscar próximos agendamentos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar próximos agendamentos'
        }), 500
    finally:
        db.close()

# Rota para chatbot - agendar com OpenAI
@app.route('/api/chatbot/agendar', methods=['POST'])
def chatbot_agendar():
    """
    Endpoint para processar mensagens do chatbot usando OpenAI GPT.
    Extrai intenção de agendamento e cria registro no banco de dados.
    """
    print("[CHATBOT] Endpoint /api/chatbot/agendar chamado")
    
    if not openai_client:
        print("[CHATBOT] ERRO: Cliente OpenAI não inicializado")
        return jsonify({
            'success': False,
            'message': 'Chatbot não configurado. Configure a chave OPENAI_API_KEY no arquivo .env'
        }), 503
    
    db = SessionLocal()
    try:
        data = request.get_json()
        print(f"[CHATBOT] Dados recebidos: {data}")
        mensagem = data.get('mensagem', '').strip()
        historico = data.get('historico', [])  # Histórico de mensagens anteriores
        user_email = data.get('user_email', '').strip()  # Email do usuário autenticado
        
        if not mensagem:
            return jsonify({
                'success': False,
                'message': 'Por favor, envie uma mensagem'
            }), 400
        
        # Buscar usuário pelo email
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuário não autenticado. Por favor, faça login novamente.'
            }), 401
        
        print(f"[CHATBOT] Usuário autenticado: {user.name} (ID: {user.id}, Email: {user.email})")
        
        # Buscar lista de pets do usuário para contexto
        pets = db.query(Pet).filter(Pet.owner_id == user.id).all()
        pets_context = [{"nome": pet.name, "tipo": pet.type} for pet in pets]
        
        print(f"[CHATBOT] Pets do usuário: {[p.name for p in pets]}")
        
        # Criar mapeamento nome -> pet para validação posterior (apenas pets deste usuário)
        pets_map = {pet.name.lower(): pet for pet in pets}
        
        # Buscar serviços agendados futuros do usuário
        pet_ids = [pet.id for pet in pets]
        hoje = datetime.now().date()
        servicos_futuros = db.query(Servico).filter(
            Servico.pet_id.in_(pet_ids),
            Servico.data_agendada >= hoje
        ).order_by(Servico.data_agendada.asc()).all()
        
        servicos_context = []
        servicos_map = {}  # Mapeamento para encontrar serviço por ID
        for servico in servicos_futuros:
            pet = next((p for p in pets if p.id == servico.pet_id), None)
            if pet:
                servico_info = {
                    "id": servico.id,
                    "pet_nome": pet.name,
                    "tipo": servico.tipo,
                    "data": servico.data_agendada.strftime('%Y-%m-%d'),
                    "clinica": servico.clinica_rel.nome if servico.clinica_rel else servico.clinica
                }
                servicos_context.append(servico_info)
                servicos_map[servico.id] = servico
        
        print(f"[CHATBOT] Serviços futuros do usuário: {len(servicos_context)}")
        
        # Buscar clínicas disponíveis (agrupadas por tipo de serviço)
        clinicas = db.query(Clinica).all()
        clinicas_por_servico = {}
        clinicas_map = {}  # Mapeamento nome -> clinica para validação
        
        for c in clinicas:
            if c.tipo_servico not in clinicas_por_servico:
                clinicas_por_servico[c.tipo_servico] = []
            clinicas_por_servico[c.tipo_servico].append({
                "nome": c.nome,
                "preco": c.preco_servico,
                "veterinario": c.veterinario
            })
            clinicas_map[c.nome.lower()] = c
        
        # System prompt com instruções detalhadas
        system_prompt = f"""Você é um assistente de agendamento para o PetCloud, uma plataforma de gerenciamento de pets.

Pets disponíveis: {json.dumps(pets_context, ensure_ascii=False)}

Clínicas disponíveis por tipo de serviço: {json.dumps(clinicas_por_servico, ensure_ascii=False)}

Serviços agendados (futuros): {json.dumps(servicos_context, ensure_ascii=False)}

⚠️ REGRA CRÍTICA DE MEMÓRIA ⚠️
ANTES DE FAZER QUALQUER PERGUNTA, você DEVE:
1. LER TODAS as mensagens anteriores do histórico da conversa
2. IDENTIFICAR se o usuário já mencionou: pet, tipo de serviço, data ou clínica
3. EXTRAIR essas informações das mensagens anteriores
4. NUNCA perguntar algo que já foi mencionado no histórico

EXEMPLOS DE COMO USAR O HISTÓRICO:
- Se o usuário disse "Agendar banho para Mia na próxima sexta" → você JÁ TEM: pet=Mia, tipo=banho, data=próxima sexta
- Se depois ele disser apenas "Sim, confirmar" → você DEVE LEMBRAR dos dados anteriores
- Se ele disse "próxima sexta feira" → NÃO pergunte "Qual dia da próxima semana?"

Sua função é extrair informações de agendamentos das mensagens dos usuários e retornar um JSON válido.

🔄 FUNCIONALIDADE DE REMARCAÇÃO:
Você também pode REMARCAR serviços existentes. Quando o usuário mencionar "remarcar", "mudar data", "alterar agendamento":

1. Liste os serviços agendados disponíveis (fornecidos acima)
2. Pergunte qual serviço deseja remarcar (exemplo: "Qual agendamento você gostaria de remarcar?\n1. Banho para Mia em 20/12/2025 na PetShop Amigo\n2. Consulta para Thor em 22/12/2025 na Clínica VetCare")
3. Após usuário escolher, pergunte a nova data
4. Retorne JSON com acao: "remarcar", servico_id, nova_data

REGRAS CRÍTICAS DE VALIDAÇÃO:
1. NOME DO PET é OBRIGATÓRIO - Se não foi mencionado NO HISTÓRICO COMPLETO, retorne sucesso: false
2. DATA PRECISA é OBRIGATÓRIA - Se não foi mencionada NO HISTÓRICO COMPLETO, retorne sucesso: false
3. TIPO DE AGENDAMENTO é OBRIGATÓRIO - Se não foi mencionado NO HISTÓRICO COMPLETO, retorne sucesso: false
4. CLÍNICA é OBRIGATÓRIA - O usuário DEVE escolher uma clínica da lista disponível

FLUXO DE VALIDAÇÃO (EXECUTE NESTA ORDEM):

🔍 PASSO 1 - ANÁLISE DO HISTÓRICO (OBRIGATÓRIO):
Leia TODAS as mensagens anteriores e extraia:
- Nome do pet mencionado (ex: "Mia", "Thor", etc.)
- Tipo de serviço mencionado (ex: "banho", "vacina", "consulta")
- Data mencionada (ex: "sexta", "próxima sexta-feira", "amanhã", "15/12")
- Clínica mencionada (se houver)

🎯 PASSO 2 - INTERPRETAÇÃO DE DATAS:
- "próxima sexta" ou "sexta-feira" = calcule a próxima sexta-feira a partir de hoje
- "amanhã" = adicione 1 dia
- "depois de amanhã" = adicione 2 dias
- "segunda da próxima semana" = próxima segunda-feira
- APENAS "próxima semana" SEM dia específico = pergunte qual dia

✅ PASSO 3 - VALIDAÇÃO:
- Se tem pet+tipo+data do histórico mas não tem clínica → mostre clínicas
- Se falta pet → pergunte qual pet
- Se falta tipo → pergunte qual serviço
- Se falta data → pergunte qual data
- Se tem tudo → sucesso: true

⚠️ EXEMPLO CRÍTICO:
Histórico: ["Agende banho para Mia na próxima sexta"]
Nova mensagem: "Confirmar"
→ Você JÁ TEM: pet="Mia", tipo="banho", data="próxima sexta-feira"
→ Se falta só clínica, mostre as opções de clínicas

Tipos de serviço disponíveis:
- vacinacao (vacinação, vacina)
- banho (banho, tosa, banho e tosa)
- consulta (consulta, check-up)

Para datas relativas (SOMENTE estas são aceitas):
- "amanhã" = adicione 1 dia à data atual
- "depois de amanhã" = adicione 2 dias à data atual
- "segunda-feira", "terça-feira", etc. = próximo dia da semana mencionado
- "segunda da próxima semana" = segunda-feira da próxima semana
- "daqui a X dias" = adicione X dias à data atual
- Data específica (dia/mês ou completa) = formate como YYYY-MM-DD

Datas NÃO ACEITAS (retorne sucesso: false):
- "próxima semana" (sem dia específico)
- "semana que vem" (sem dia específico)
- "em breve", "logo", "qualquer dia", "quando possível"

⚠️ FORMATO DE RESPOSTA OBRIGATÓRIO ⚠️
Você DEVE responder APENAS E EXCLUSIVAMENTE com um objeto JSON puro, sem texto antes ou depois.
NÃO inclua explicações, markdown (```json), ou qualquer texto adicional.
APENAS o JSON puro conforme o formato abaixo:

PARA NOVO AGENDAMENTO:
{{
    "sucesso": true/false,
    "acao": "agendar",
    "tipo": "vacinacao" | "banho" | "consulta" (ou null se não informado),
    "pet_nome": "nome do pet" (ou null se não informado),
    "data": "YYYY-MM-DD" (ou null se não informado),
    "clinica_nome": "nome da clínica escolhida" (ou null),
    "observacoes": "texto com detalhes",
    "mensagem_usuario": "mensagem amigável de confirmação ou pedido de esclarecimento"
}}

PARA REMARCAÇÃO:
{{
    "sucesso": true/false,
    "acao": "remarcar",
    "servico_id": 123 (ID do serviço a remarcar),
    "nova_data": "YYYY-MM-DD",
    "mensagem_usuario": "mensagem de confirmação da remarcação"
}}

NOTA: Retorne apenas os NOMES e IDs corretos. O sistema fará a conversão automaticamente.

🏥 COMO LISTAR CLÍNICAS (INSTRUÇÕES CRÍTICAS):
Quando tem pet+tipo+data mas NÃO tem clínica, você DEVE:

1. ACESSAR o objeto "Clínicas disponíveis por tipo de serviço" fornecido no início deste prompt
2. BUSCAR a chave correspondente ao tipo: "banho", "vacinacao" ou "consulta"
3. LISTAR TODAS as clínicas daquele tipo no formato:

"Clínicas disponíveis para [tipo]:\n1. [nome] - R$ [preco] (Dr./Dra. [veterinario])\n2. [nome2] - R$ [preco2] (Dr./Dra. [veterinario2])\n...\n\nQual clínica você prefere? (Responda com o número ou nome)"

EXEMPLO REAL:
Se tipo = "banho" e as clínicas de banho são:
[{{"nome": "PetShop Amigo", "preco": 50.0, "veterinario": "Dra. Silva"}}]

Você deve retornar na mensagem_usuario:
"Clínicas disponíveis para banho:\n1. PetShop Amigo - R$ 50.00 (Dra. Silva)\n\nQual clínica você prefere?"

🎯 QUANDO O USUÁRIO ESCOLHE A CLÍNICA:
- Se disser "primeira", "1", "opção 1" → use o nome da primeira clínica da lista
- Se disser "segunda", "2", "opção 2" → use o nome da segunda clínica
- Se disser o nome da clínica → use esse nome exato
- Preencha "clinica_nome" com o nome EXATO da clínica (não o número)

Exemplos de validação (AGENDAMENTO):
- "Agendar vacina" → sucesso: false, mensagem: "Para qual pet você gostaria de agendar a vacinação? Pets disponíveis: [lista]"
- "Vacina para Thor" → sucesso: false, mensagem: "Para qual data você gostaria de agendar?"
- "Vacina para Thor amanhã" → sucesso: false, mensagem: "Clínicas disponíveis para vacinação:\n1. [Nome] - R$ [preço] (Dr. [vet])\n2. [Nome2] - R$ [preço2]\nQual clínica você prefere?"
- "Primeira clínica" → sucesso: true, acao: "agendar" (seleciona clínica 1 com preço correto)

Exemplos de validação (REMARCAÇÃO):
- "Quero remarcar um agendamento" → sucesso: false, mensagem: "Qual agendamento você gostaria de remarcar?\n1. Banho para Mia em 20/12/2025\n2. Consulta para Thor em 22/12/2025"
- "O primeiro" (após listar) → sucesso: false, mensagem: "Para qual nova data você gostaria de remarcar?"
- "Para amanhã" (após escolher serviço) → sucesso: true, acao: "remarcar", servico_id: 1, nova_data: "2025-12-15"
- "Remarcar o banho da Mia para próxima segunda" → sucesso: false, liste os serviços de banho da Mia, confirme qual, depois pergunte nova data

Data de hoje: {datetime.now().strftime('%Y-%m-%d')}"""

        # Chamada para OpenAI
        print(f"[CHATBOT] Processando mensagem: {mensagem}")
        print(f"[CHATBOT] Histórico: {len(historico)} mensagens anteriores")
        print(f"[CHATBOT] Clínicas disponíveis: {json.dumps(clinicas_por_servico, ensure_ascii=False, indent=2)}")
        
        # Construir mensagens com histórico
        messages = [{"role": "system", "content": system_prompt}]
        
        # Adicionar histórico de conversas (últimas 10 mensagens)
        for i, msg in enumerate(historico[-10:]):
            msg_content = msg.get("content", "")
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg_content
            })
            print(f"[CHATBOT] Histórico [{i}] {msg.get('role', 'user')}: {msg_content}")
        
        # Adicionar mensagem atual
        messages.append({"role": "user", "content": mensagem})
        print(f"[CHATBOT] Mensagem atual: {mensagem}")
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,  # Temperatura mais baixa para respostas consistentes
            max_tokens=500,
            response_format={ "type": "json_object" }  # Força resposta em JSON
        )
        
        # Extrair resposta
        resposta_texto = response.choices[0].message.content.strip()
        print(f"[CHATBOT] Resposta OpenAI: {resposta_texto}")
        
        # Parse JSON da resposta
        try:
            # Remover markdown code blocks se existirem
            if resposta_texto.startswith('```'):
                resposta_texto = resposta_texto.split('```')[1]
                if resposta_texto.startswith('json'):
                    resposta_texto = resposta_texto[4:]
                resposta_texto = resposta_texto.strip()
            
            resposta_json = json.loads(resposta_texto)
        except json.JSONDecodeError as e:
            print(f"[ERRO] Erro ao fazer parse do JSON: {e}")
            print(f"[ERRO] Resposta recebida: {resposta_texto}")
            return jsonify({
                'success': False,
                'message': 'Desculpe, não consegui processar sua solicitação. Tente reformular a mensagem.'
            }), 200
        
        # Se não foi possível extrair informações completas
        if not resposta_json.get('sucesso', False):
            return jsonify({
                'success': False,
                'message': resposta_json.get('mensagem_usuario', 'Não entendi sua solicitação. Pode reformular?')
            }), 200
        
        # Verificar qual ação foi solicitada
        acao = resposta_json.get('acao', 'agendar')
        
        # ============ REMARCAÇÃO ============
        if acao == 'remarcar':
            servico_id = resposta_json.get('servico_id')
            nova_data_str = resposta_json.get('nova_data')
            
            if not servico_id or not nova_data_str:
                return jsonify({
                    'success': False,
                    'message': 'Informações incompletas para remarcação.'
                }), 200
            
            # Buscar serviço
            servico = servicos_map.get(servico_id)
            if not servico:
                return jsonify({
                    'success': False,
                    'message': 'Serviço não encontrado ou não pertence a você.'
                }), 200
            
            # Armazenar data antiga antes de substituir
            data_antiga = servico.data_agendada
            
            # Atualizar data (substitui a data antiga pela nova)
            try:
                nova_data = datetime.strptime(nova_data_str, '%Y-%m-%d').date()
                servico.data_agendada = nova_data
                db.commit()
                
                print(f"[CHATBOT] Serviço {servico_id} remarcado: {data_antiga} → {nova_data} (data antiga excluída/substituída)")
                
                data_formatada = nova_data.strftime('%d/%m/%Y')
                pet = db.query(Pet).filter(Pet.id == servico.pet_id).first()
                tipo_texto = {
                    'vacinacao': 'vacinação',
                    'banho': 'banho',
                    'consulta': 'consulta'
                }.get(servico.tipo, 'serviço')
                
                return jsonify({
                    'success': True,
                    'message': f"✅ Remarcação confirmada! {tipo_texto.capitalize()} de {pet.name} remarcado para {data_formatada}."
                }), 200
                
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Formato de data inválido.'
                }), 200
        
        # ============ NOVO AGENDAMENTO ============
        # Validar e buscar pet pelo nome
        pet_nome = resposta_json.get('pet_nome', '').strip()
        pet = pets_map.get(pet_nome.lower())
        if not pet:
            return jsonify({
                'success': False,
                'message': f"Não encontrei o pet '{pet_nome}'. Pets disponíveis: {', '.join([p.name for p in pets])}"
            }), 200
        
        print(f"[CHATBOT] Pet encontrado: {pet.name} (ID: {pet.id})")
        
        # Validar e buscar clínica pelo nome
        clinica_nome = resposta_json.get('clinica_nome', '').strip()
        clinica = clinicas_map.get(clinica_nome.lower())
        if not clinica:
            return jsonify({
                'success': False,
                'message': f"Não encontrei a clínica '{clinica_nome}'. Por favor, escolha uma das clínicas disponíveis."
            }), 200
        
        print(f"[CHATBOT] Clínica encontrada: {clinica.nome} (ID: {clinica.id})")
        
        # Buscar e remover agendamentos atrasados do mesmo tipo para o mesmo pet
        # Isso evita que alertas de consultas atrasadas fiquem duplicados
        hoje = datetime.now().date()
        tipo_servico = resposta_json.get('tipo')
        
        agendamentos_atrasados = db.query(Servico).filter(
            Servico.pet_id == pet.id,
            Servico.tipo == tipo_servico,
            Servico.data_agendada < hoje
        ).all()
        
        if agendamentos_atrasados:
            print(f"[CHATBOT] Removendo {len(agendamentos_atrasados)} agendamento(s) atrasado(s) do tipo {tipo_servico} para {pet.name}")
            for agendamento_antigo in agendamentos_atrasados:
                print(f"[CHATBOT] - Removendo agendamento ID {agendamento_antigo.id} de {agendamento_antigo.data_agendada}")
                db.delete(agendamento_antigo)
        
        # Criar serviço no banco de dados
        novo_servico = Servico(
            tipo=resposta_json.get('tipo'),
            data_agendada=datetime.strptime(resposta_json.get('data'), '%Y-%m-%d'),
            pet_id=pet.id,
            clinica_id=clinica.id,
            veterinario=clinica.veterinario,
            preco=clinica.preco_servico
        )
        
        print(f"[CHATBOT] Criando serviço: pet_id={pet.id}, clinica_id={clinica.id}, tipo={resposta_json.get('tipo')}, data={resposta_json.get('data')}")
        
        db.add(novo_servico)
        db.commit()
        db.refresh(novo_servico)
        
        print(f"[CHATBOT] Agendamento criado com sucesso - ID: {novo_servico.id}")
        
        # Mensagem de confirmação
        tipo_texto = {
            'vacinacao': 'vacinação',
            'banho': 'banho',
            'consulta': 'consulta'
        }.get(resposta_json.get('tipo'), 'serviço')
        
        data_formatada = datetime.strptime(resposta_json.get('data'), '%Y-%m-%d').strftime('%d/%m/%Y')
        
        mensagem_confirmacao = resposta_json.get('mensagem_usuario', 
            f"✅ Agendamento confirmado! {tipo_texto.capitalize()} para {pet.name} em {data_formatada}."
        )
        
        return jsonify({
            'success': True,
            'message': mensagem_confirmacao,
            'agendamento': {
                'id': novo_servico.id,
                'tipo': novo_servico.tipo,
                'data': novo_servico.data_agendada.strftime('%d/%m/%Y'),
                'pet_nome': pet.name
            }
        }), 200
        
    except Exception as e:
        print(f"[ERRO] Erro no chatbot: {e}")
        print(f"[ERRO] Tipo do erro: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        db.rollback()
        
        # Mensagem de erro mais específica
        erro_msg = str(e)
        if 'API key' in erro_msg or 'authentication' in erro_msg.lower():
            return jsonify({
                'success': False,
                'message': 'Erro de autenticação com OpenAI. Verifique a chave API.'
            }), 500
        elif 'rate limit' in erro_msg.lower():
            return jsonify({
                'success': False,
                'message': 'Limite de requisições atingido. Aguarde alguns minutos.'
            }), 500
        else:
            return jsonify({
                'success': False,
                'message': 'Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente.'
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
        
        # Deletar serviços relacionados (vacinas, consultas, etc)
        from models.Servico import Servico
        servicos = db.query(Servico).filter(Servico.pet_id == pet_id).all()
        for servico in servicos:
            db.delete(servico)
        print(f"[DELETE] {len(servicos)} serviço(s) relacionado(s) deletado(s)")
        
        # Deletar fotos do concurso relacionadas
        from models.Concurso import Concurso
        concursos = db.query(Concurso).filter(Concurso.pet_id == pet_id).all()
        for concurso in concursos:
            # Deletar arquivo físico da foto do concurso
            if concurso.imagem_url:
                concurso_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(concurso.imagem_url))
                if os.path.exists(concurso_photo_path):
                    os.remove(concurso_photo_path)
                    print(f"[DELETE] Arquivo do concurso deletado: {concurso_photo_path}")
            db.delete(concurso)
        print(f"[DELETE] {len(concursos)} submissão(ões) de concurso deletada(s)")
        
        # Deletar foto do perfil do pet se existir
        if pet.photo_url:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(pet.photo_url))
            if os.path.exists(photo_path):
                os.remove(photo_path)
                print(f"[DELETE] Foto do pet deletada: {photo_path}")
        
        # Deletar o pet
        pet_name = pet.name
        db.delete(pet)
        db.commit()
        
        print(f"[DELETE] Pet {pet_name} (ID: {pet_id}) deletado com sucesso")
        return jsonify({
            'success': True,
            'message': f'Pet {pet_name} e todos os registros relacionados foram deletados com sucesso'
        }), 200
        
    except Exception as e:
        db.rollback()
        print(f"[ERRO] Erro ao deletar pet: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Erro ao deletar pet: {str(e)}'
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
            'behavior_tags': pet.get_behavior_tags() if hasattr(pet, 'behavior_tags') else [],
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
        
        # Buscar e remover agendamentos atrasados do mesmo tipo para o mesmo pet
        # Isso evita que alertas de consultas atrasadas fiquem duplicados
        hoje = datetime.now().date()
        tipo_servico = data['tipo']
        
        agendamentos_atrasados = db.query(Servico).filter(
            Servico.pet_id == data['pet_id'],
            Servico.tipo == tipo_servico,
            Servico.data_agendada < hoje
        ).all()
        
        if agendamentos_atrasados:
            print(f"[SERVICO] Removendo {len(agendamentos_atrasados)} agendamento(s) atrasado(s) do tipo {tipo_servico} para {pet.name}")
            for agendamento_antigo in agendamentos_atrasados:
                print(f"[SERVICO] - Removendo agendamento ID {agendamento_antigo.id} de {agendamento_antigo.data_agendada}")
                db.delete(agendamento_antigo)
        
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
        print(f'[ERRO] Erro ao criar serviço: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db.close()

@app.route('/api/servicos/<int:servico_id>', methods=['DELETE'])
def deletar_servico(servico_id):
    """Deleta um serviço agendado"""
    db = SessionLocal()
    try:
        servico = db.query(Servico).filter(Servico.id == servico_id).first()
        
        if not servico:
            return jsonify({'success': False, 'message': 'Serviço não encontrado.'}), 404
        
        # Armazenar informações para log
        tipo_servico = servico.tipo
        pet_id = servico.pet_id
        
        db.delete(servico)
        db.commit()
        
        print(f'[SERVICO] Agendamento deletado: ID={servico_id}, tipo={tipo_servico}, pet_id={pet_id}')
        
        return jsonify({
            'success': True,
            'message': 'Serviço deletado com sucesso!'
        }), 200
        
    except Exception as e:
        db.rollback()
        print(f'[ERRO] Erro ao deletar serviço: {e}')
        return jsonify({'success': False, 'message': 'Erro ao deletar serviço.'}), 500
    finally:
        db.close()

@app.route('/api/servicos', methods=['GET'])
def listar_servicos():
    """Lista todos os serviços agendados de um usuário (futuros e passados)"""
    db = SessionLocal()
    try:
        user_email = request.args.get('user_email')
        incluir_passados = request.args.get('incluir_passados', 'false').lower() == 'true'
        
        if not user_email:
            return jsonify({'success': False, 'message': 'Email do usuário é obrigatório.'}), 400
        
        # Buscar usuário
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            return jsonify({'success': False, 'message': 'Usuário não encontrado.'}), 404
        
        # Buscar pets do usuário
        pets = db.query(Pet).filter(Pet.owner_id == user.id).all()
        pet_ids = [pet.id for pet in pets]
        
        # Buscar serviços dos pets
        query = db.query(Servico).filter(Servico.pet_id.in_(pet_ids))
        
        # Filtrar apenas futuros se necessário
        if not incluir_passados:
            hoje = datetime.now().date()
            query = query.filter(Servico.data_agendada >= hoje)
        
        servicos = query.order_by(Servico.data_agendada.asc()).all()
        
        # Montar resposta com informações do pet
        servicos_lista = []
        for servico in servicos:
            pet = db.query(Pet).filter(Pet.id == servico.pet_id).first()
            servico_dict = servico.to_dict()
            servico_dict['pet_nome'] = pet.name if pet else 'Desconhecido'
            servicos_lista.append(servico_dict)
        
        print(f'[SERVICOS] Listados {len(servicos_lista)} serviços para usuário {user.name}')
        
        return jsonify({
            'success': True,
            'servicos': servicos_lista
        }), 200
        
    except Exception as e:
        print(f'[ERRO] Erro ao listar serviços: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db.close()

@app.route('/api/servicos/<int:servico_id>', methods=['PUT'])
def atualizar_servico(servico_id):
    """Atualiza/remarca um serviço agendado"""
    db = SessionLocal()
    try:
        data = request.json
        
        servico = db.query(Servico).filter(Servico.id == servico_id).first()
        if not servico:
            return jsonify({'success': False, 'message': 'Serviço não encontrado.'}), 404
        
        # Atualizar campos se fornecidos
        if 'data_agendada' in data:
            try:
                nova_data = datetime.strptime(data['data_agendada'], '%Y-%m-%d').date()
                servico.data_agendada = nova_data
            except ValueError:
                return jsonify({'success': False, 'message': 'Formato de data inválido. Use YYYY-MM-DD.'}), 400
        
        if 'clinica_id' in data:
            clinica = db.query(Clinica).filter(Clinica.id == data['clinica_id']).first()
            if not clinica:
                return jsonify({'success': False, 'message': 'Clínica não encontrada.'}), 404
            servico.clinica_id = data['clinica_id']
            servico.preco = clinica.preco_servico
            servico.veterinario = clinica.veterinario
        
        if 'tipo' in data:
            servico.tipo = data['tipo']
        
        db.commit()
        db.refresh(servico)
        
        print(f'[SERVICO] Agendamento atualizado: ID={servico_id}, nova data={servico.data_agendada}')
        
        return jsonify({
            'success': True,
            'message': 'Serviço atualizado com sucesso!',
            'servico': servico.to_dict()
        }), 200
        
    except Exception as e:
        print(f'[ERRO] Erro ao atualizar serviço: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db.close()


# ==================== ENDPOINTS DE CONCURSO ====================

@app.route('/api/concurso/enviar', methods=['POST'])
def enviar_foto_concurso():
    """Endpoint para enviar foto ao concurso"""
    db = SessionLocal()
    try:
        # Verificar se há arquivo na requisição
        if 'imagem' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhuma imagem foi enviada.'}), 400
        
        file = request.files['imagem']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhuma imagem selecionada.'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Formato de arquivo não permitido. Use PNG, JPG, JPEG, GIF ou WEBP.'}), 400
        
        # Obter dados do formulário
        pet_id = request.form.get('pet_id')
        user_email = request.form.get('user_email')
        descricao = request.form.get('descricao', '')
        
        if not pet_id or not user_email:
            return jsonify({'success': False, 'message': 'Pet e usuário são obrigatórios.'}), 400
        
        # Verificar se usuário existe
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            return jsonify({'success': False, 'message': 'Usuário não encontrado.'}), 404
        
        # Verificar se pet existe e pertence ao usuário
        pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == user.id).first()
        if not pet:
            return jsonify({'success': False, 'message': 'Pet não encontrado ou não pertence a este usuário.'}), 404
        
        # Verificar se o pet já tem foto no concurso
        concurso_existente = db.query(Concurso).filter(Concurso.pet_id == pet_id).first()
        if concurso_existente:
            return jsonify({'success': False, 'message': f'{pet.name} já tem uma foto enviada no concurso!'}), 400
        
        # Salvar arquivo com nome único
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f'{timestamp}_{secrets.token_hex(8)}_{filename}'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Criar registro no banco
        novo_concurso = Concurso(
            pet_id=pet_id,
            user_id=user.id,
            imagem_url=f'/uploads/{unique_filename}',
            descricao=descricao,
            votos=0
        )
        
        db.add(novo_concurso)
        db.commit()
        db.refresh(novo_concurso)
        
        print(f'[CONCURSO] Foto enviada: Pet {pet.name} (ID: {pet_id}) - User: {user.name}')
        
        return jsonify({
            'success': True,
            'message': f'Foto de {pet.name} enviada com sucesso para o concurso!',
            'concurso': novo_concurso.to_dict()
        }), 201
        
    except Exception as e:
        db.rollback()
        print(f'[ERRO] Erro ao enviar foto ao concurso: {e}')
        return jsonify({'success': False, 'message': 'Erro ao enviar foto.'}), 500
    finally:
        db.close()


@app.route('/api/concurso/fotos', methods=['GET'])
def listar_fotos_concurso():
    """Endpoint para listar todas as fotos do concurso"""
    db = SessionLocal()
    try:
        fotos = db.query(Concurso).order_by(Concurso.votos.desc(), Concurso.data_envio.desc()).all()
        
        return jsonify({
            'success': True,
            'total': len(fotos),
            'fotos': [foto.to_dict() for foto in fotos]
        }), 200
        
    except Exception as e:
        print(f'[ERRO] Erro ao listar fotos do concurso: {e}')
        return jsonify({'success': False, 'message': 'Erro ao carregar fotos.'}), 500
    finally:
        db.close()


@app.route('/api/concurso/votar/<int:concurso_id>', methods=['POST'])
def votar_foto_concurso(concurso_id):
    """Endpoint para votar em uma foto do concurso"""
    db = SessionLocal()
    try:
        foto = db.query(Concurso).filter(Concurso.id == concurso_id).first()
        
        if not foto:
            return jsonify({'success': False, 'message': 'Foto não encontrada.'}), 404
        
        foto.votos += 1
        db.commit()
        
        print(f'[CONCURSO] Voto registrado: Foto ID {concurso_id} - Total: {foto.votos} votos')
        
        return jsonify({
            'success': True,
            'message': 'Voto registrado com sucesso!',
            'votos': foto.votos
        }), 200
        
    except Exception as e:
        db.rollback()
        print(f'[ERRO] Erro ao registrar voto: {e}')
        return jsonify({'success': False, 'message': 'Erro ao registrar voto.'}), 500
    finally:
        db.close()


@app.route('/api/concurso/deletar/<int:concurso_id>', methods=['DELETE'])
def deletar_foto_concurso(concurso_id):
    """Endpoint para deletar uma foto do concurso"""
    db = SessionLocal()
    try:
        # Obter dados do usuário
        user_email = request.args.get('user_email')
        
        print(f"[CONCURSO DELETE] Recebido user_email: {user_email}")
        print(f"[CONCURSO DELETE] request.args: {request.args}")
        print(f"[CONCURSO DELETE] concurso_id: {concurso_id}")
        
        if not user_email:
            return jsonify({'success': False, 'message': 'Email do usuário é obrigatório.'}), 400
        
        # Verificar se usuário existe
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            return jsonify({'success': False, 'message': 'Usuário não encontrado.'}), 404
        
        # Buscar foto do concurso
        foto = db.query(Concurso).filter(Concurso.id == concurso_id).first()
        
        if not foto:
            return jsonify({'success': False, 'message': 'Foto não encontrada.'}), 404
        
        # Verificar se o usuário é o dono da foto
        if foto.user_id != user.id:
            return jsonify({'success': False, 'message': 'Você não tem permissão para deletar esta foto.'}), 403
        
        # Deletar arquivo físico
        if foto.imagem_url:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(foto.imagem_url))
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f'[CONCURSO] Arquivo deletado: {filepath}')
        
        # Deletar do banco
        pet_name = foto.pet.name if foto.pet else 'Unknown'
        db.delete(foto)
        db.commit()
        
        print(f'[CONCURSO] Foto deletada: ID {concurso_id} - Pet: {pet_name} - User: {user.name}')
        
        return jsonify({
            'success': True,
            'message': 'Foto deletada com sucesso!'
        }), 200
        
    except Exception as e:
        db.rollback()
        print(f'[ERRO] Erro ao deletar foto: {e}')
        return jsonify({'success': False, 'message': 'Erro ao deletar foto.'}), 500
    finally:
        db.close()


# Rota para limpar agendamentos atrasados (remove duplicatas antigas)
@app.route('/api/servicos/limpar-atrasados', methods=['POST'])
def limpar_agendamentos_atrasados():
    """Remove agendamentos atrasados para evitar alertas duplicados"""
    db = SessionLocal()
    try:
        data = request.json or {}
        user_email = data.get('user_email', '')
        
        hoje = datetime.now().date()
        
        # Buscar usuário pelo email
        user = db.query(User).filter(User.email == user_email).first() if user_email else None
        
        if user:
            # Buscar agendamentos atrasados dos pets do usuário
            agendamentos_atrasados = db.query(Servico).join(Pet).filter(
                Pet.owner_id == user.id,
                Servico.data_agendada < hoje
            ).all()
        else:
            # Se não tiver email, buscar todos os agendamentos atrasados (admin)
            agendamentos_atrasados = db.query(Servico).filter(
                Servico.data_agendada < hoje
            ).all()
        
        total_removidos = len(agendamentos_atrasados)
        
        if total_removidos > 0:
            print(f"[LIMPEZA] Removendo {total_removidos} agendamento(s) atrasado(s)...")
            for agendamento in agendamentos_atrasados:
                pet = db.query(Pet).filter(Pet.id == agendamento.pet_id).first()
                pet_name = pet.name if pet else "Unknown"
                print(f"[LIMPEZA] - Removendo {agendamento.tipo} de {pet_name} (ID: {agendamento.id}, Data: {agendamento.data_agendada})")
                db.delete(agendamento)
            
            db.commit()
            print(f"[LIMPEZA] {total_removidos} agendamento(s) atrasado(s) removido(s) com sucesso")
        else:
            print("[LIMPEZA] Nenhum agendamento atrasado encontrado")
        
        return jsonify({
            'success': True,
            'message': f'{total_removidos} agendamento(s) atrasado(s) removido(s).',
            'total_removidos': total_removidos
        }), 200
        
    except Exception as e:
        db.rollback()
        print(f'[ERRO] Erro ao limpar agendamentos atrasados: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Erro ao limpar agendamentos atrasados.'
        }), 500
    finally:
        db.close()


if __name__ == '__main__':

    app.run(debug=True, port=5000)