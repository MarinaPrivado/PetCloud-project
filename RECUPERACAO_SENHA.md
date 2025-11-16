# Sistema de Recuperação de Senha - PetCloud

## 📋 Visão Geral

O sistema de recuperação de senha foi implementado usando **OAuth 2.0 do Google** para enviar emails via Gmail API. O sistema possui dois fluxos principais:

1. **Configuração do OAuth** (primeira vez)
2. **Recuperação de senha** (uso normal)

---

## 🔧 Configuração Inicial do OAuth

### Passo 1: Configurar o OAuth (APENAS UMA VEZ)

Antes de usar a recuperação de senha, você precisa autorizar o PetCloud a enviar emails pela sua conta Gmail:

1. **Acesse no navegador:**
   ```
   http://127.0.0.1:5000/api/auth/setup-oauth
   ```

2. **Você será redirecionado para o Google**
   - Faça login com sua conta Gmail
   - Clique em "Permitir" para autorizar o PetCloud a enviar emails

3. **Após autorizar:**
   - Você será redirecionado de volta para `http://127.0.0.1:5000/callback`
   - Uma página confirmará que a autorização foi concluída
   - Um arquivo `token.json` será criado em `backend/src/` (contém suas credenciais)

4. **Pronto!** Agora o sistema pode enviar emails automaticamente.

---

## 🔐 Usando a Recuperação de Senha

### Como Usuário:

1. **Acesse a página de recuperação:**
   ```
   http://127.0.0.1:5000/recuperar-senha.html
   ```

2. **Digite seu email cadastrado e clique em "Enviar Link de Acesso"**

3. **Você receberá um email** com um link de redefinição (válido por 1 hora)

4. **Clique no link do email** (ou use o link que aparece na tela em modo dev)

5. **Digite sua nova senha** e confirme

6. **Pronto!** Sua senha foi redefinida. Você será redirecionado para o login.

---

## 🛠️ Modo Desenvolvedor (Sem Email)

Se o OAuth não estiver configurado, o sistema funciona em **modo desenvolvedor**:

- O link de redefinição aparece **diretamente na tela** após solicitar recuperação
- Basta clicar no link para testar o fluxo completo
- Útil para desenvolvimento e testes

---

## 📡 Endpoints da API

### 1. Verificar Status do OAuth
```http
GET /api/auth/oauth-status
```
**Resposta:**
```json
{
  "success": true,
  "authenticated": true,
  "message": "OAuth configurado"
}
```

### 2. Configurar OAuth (Primeira Vez)
```http
GET /api/auth/setup-oauth
```
Redireciona para autorização do Google.

### 3. Callback OAuth
```http
GET /callback?code=...
```
Recebe o código de autorização e salva o token.

### 4. Solicitar Recuperação de Senha
```http
POST /api/auth/request-password-reset
Content-Type: application/json

{
  "email": "usuario@example.com"
}
```

**Resposta (OAuth configurado):**
```json
{
  "success": true,
  "message": "Link de recuperação enviado por e-mail."
}
```

**Resposta (OAuth não configurado - modo dev):**
```json
{
  "success": true,
  "message": "OAuth não configurado. Configure primeiro em /api/auth/setup-oauth. Link para teste:",
  "reset_link": "http://127.0.0.1:5000/recuperar-senha.html?token=abc123...",
  "oauth_setup_url": "/api/auth/setup-oauth"
}
```

### 5. Redefinir Senha
```http
POST /api/auth/reset-password
Content-Type: application/json

{
  "token": "token_recebido_por_email",
  "new_password": "nova_senha_123"
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Senha redefinida com sucesso."
}
```

---

## 🗄️ Estrutura do Banco de Dados

### Tabela: `password_resets`

| Coluna      | Tipo     | Descrição                                |
|-------------|----------|------------------------------------------|
| id          | INTEGER  | ID único do token                        |
| user_id     | INTEGER  | ID do usuário (FK para `users.id`)       |
| token       | STRING   | Token único de redefinição               |
| expires_at  | DATETIME | Data/hora de expiração (1 hora)          |
| created_at  | DATETIME | Data/hora de criação                     |

---

## 🔒 Segurança

1. **Tokens únicos**: Cada solicitação gera um token aleatório único
2. **Expiração**: Tokens expiram em 1 hora
3. **Uso único**: Token é deletado após uso bem-sucedido
4. **Hashing**: Senhas são salvas com hash SHA-256
5. **Não revela emails**: Não informa se o email existe ou não

---

## 📝 Arquivos Criados/Modificados

### Novos Arquivos:
- `backend/src/models/PasswordReset.py` - Modelo de token de reset
- `backend/src/services/GmailOAuthService.py` - Serviço de email OAuth
- `backend/src/token.json` - Credenciais OAuth (criado após autorização)

### Arquivos Modificados:
- `backend/src/app.py` - Adicionadas rotas de OAuth e recuperação
- `backend/src/models/__init__.py` - Registrado modelo PasswordReset
- `pages/recuperar-senha.html` - Interface completa com JavaScript

---

## 🧪 Testando o Sistema

### Teste 1: Configurar OAuth (primeira vez)
1. Abra: `http://127.0.0.1:5000/api/auth/setup-oauth`
2. Autorize com sua conta Gmail
3. Verifique se `backend/src/token.json` foi criado

### Teste 2: Verificar Status
```bash
curl http://127.0.0.1:5000/api/auth/oauth-status
```

### Teste 3: Solicitar Recuperação
```bash
curl -X POST http://127.0.0.1:5000/api/auth/request-password-reset \
  -H "Content-Type: application/json" \
  -d '{"email":"seu-email@example.com"}'
```

### Teste 4: Verificar Email
- Acesse seu Gmail e verifique o email de recuperação

### Teste 5: Redefinir Senha
- Clique no link do email (ou use o token da resposta em modo dev)
- Digite a nova senha
- Confirme que consegue fazer login com a nova senha

---

## ⚠️ Troubleshooting

### Problema: "OAuth não configurado"
**Solução:** Execute `/api/auth/setup-oauth` primeiro

### Problema: "Token inválido"
**Solução:** O token pode ter expirado (1 hora). Solicite um novo.

### Problema: "Erro ao enviar email"
**Solução:** 
1. Verifique se o `token.json` existe
2. Tente reautorizar em `/api/auth/setup-oauth`
3. Verifique os logs do servidor Flask

### Problema: Token expirado frequentemente
**Solução:** O token OAuth pode precisar ser renovado. Delete `token.json` e reautorize.

---

## 🚀 Próximos Passos (Opcional)

- [ ] Adicionar limite de tentativas (rate limiting)
- [ ] Enviar email de confirmação após reset bem-sucedido
- [ ] Adicionar histórico de alterações de senha
- [ ] Implementar autenticação de 2 fatores (2FA)
- [ ] Melhorar templates de email com HTML

---

## 📞 Suporte

Se tiver problemas, verifique:
1. Servidor Flask está rodando (`python backend/src/app.py`)
2. OAuth foi configurado (`/api/auth/setup-oauth`)
3. Credenciais OAuth estão em `backend/src/OAuthID.json`
4. Logs do servidor para mensagens de erro
