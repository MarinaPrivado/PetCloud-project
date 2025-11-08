# c:\Users\Marina\Documents\Desenv. Web\PetCloud\app.py
import os
from flask import Flask, request, render_template, url_for, flash, redirect, session
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from datetime import timedelta

# --- Configuração do App Flask ---
app = Flask(__name__)

# Chave secreta para segurança da sessão e do token. MUDE ISSO!
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-forte-e-dificil-de-adivinhar'

# Configuração do Flask-Mail (use variáveis de ambiente em produção)
# Para o Gmail, você precisa gerar uma "Senha de App".
# 1. Acesse sua Conta Google -> Segurança
# 2. Ative a "Verificação em duas etapas"
# 3. Vá para "Senhas de app", crie uma nova e use a senha gerada aqui.
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'seu-email@gmail.com') # <-- SEU E-MAIL AQUI
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'sua-senha-de-app-aqui') # <-- SUA SENHA DE APP AQUI
app.config['MAIL_DEFAULT_SENDER'] = ('PetCloud', app.config['MAIL_USERNAME'])

mail = Mail(app)

# Serializer para gerar e verificar tokens. O 'salt' adiciona uma camada de segurança.
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'], salt='password-reset-salt')

# --- Banco de Dados Fictício ---
# Em um projeto real, isso viria de um banco de dados como PostgreSQL, MySQL, etc.
users = {
    "usuario@exemplo.com": {"nome": "Tutor Exemplo", "password": "123"},
    "marina@petcloud.com": {"nome": "Marina", "password": "abc"}
}

# --- Rotas da Aplicação ---

@app.route('/')
def index():
    """
    Renderiza a página inicial do projeto.
    """
    return render_template('index.html')

@app.route('/templates/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """
    Exibe o formulário para solicitar a recuperação e processa o envio.
    """
    if request.method == 'POST':
        email = request.form.get('email')
        
        if email not in users:
            flash('Este e-mail não está cadastrado no sistema.', 'warning')
            return redirect(url_for('forgot_password'))

        # Gera o token com o e-mail do usuário
        token = serializer.dumps(email)

        # Cria o link de redefinição
        reset_url = url_for('reset_with_token', token=token, _external=True)

        # Renderiza o corpo do e-mail a partir de um template
        html_body = render_template('email/reset_password_email.html', reset_url=reset_url)
        
        # Envia o e-mail
        msg = Message(
            subject="PetCloud - Redefinição de Senha",
            recipients=[email],
            html=html_body
        )
        mail.send(msg)

        flash('Um link para redefinição de senha foi enviado para o seu e-mail.', 'success')
        return redirect(url_for('forgot_password'))

    # Usa o template já existente, mas agora ele será servido pelo Flask
    return render_template('forgot_password.html')


@app.route('/resetar-senha/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    """
    Valida o token e exibe o formulário para criar uma nova senha.
    """
    try:
        # Valida o token e o tempo de expiração (definido para 1 hora)
        email = serializer.loads(token, max_age=3600)
    except SignatureExpired:
        flash('O link de redefinição de senha expirou. Por favor, solicite um novo.', 'danger')
        return redirect(url_for('forgot_password'))
    except (BadTimeSignature, TypeError, ValueError):
        flash('O link de redefinição de senha é inválido. Por favor, tente novamente.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not new_password or new_password != confirm_password:
            flash('As senhas não conferem ou estão em branco. Tente novamente.', 'warning')
            return render_template('reset_password.html', token=token)
        
        # Em um app real, você deve fazer o HASH da senha antes de salvar!
        users[email]['password'] = new_password
        print(f"Senha do usuário {email} foi atualizada para: {new_password}") # Log para debug

        flash('Sua senha foi redefinida com sucesso! Você já pode fazer o login.', 'success')
        # Redireciona para a página de login do seu projeto
        return redirect(url_for('login')) # Supondo que você tenha uma rota 'login'

    return render_template('reset_password.html', token=token)


# Rota de login apenas para o redirecionamento funcionar
@app.route('/login')
def login():
    # Você pode renderizar sua página de login aqui
    return render_template('login.html')

# --- Execução do App ---
if __name__ == '__main__':
    # Ativa o modo de debug para desenvolvimento
    app.run(debug=True)
