# ⚡ Guia Rápido - Chatbot OpenAI

## 🎯 Setup em 3 Passos

### 1️⃣ Obter Chave API
```
1. Acesse: https://platform.openai.com/api-keys
2. Clique em "Create new secret key"
3. Copie a chave (começa com sk-)
```

### 2️⃣ Configurar Backend
```powershell
cd backend
Copy-Item .env.example .env
# Edite .env e cole sua chave API
```

No arquivo `.env`:
```
OPENAI_API_KEY=sk-sua-chave-aqui
```

### 3️⃣ Iniciar Servidor
```powershell
cd src
python app.py
```

## ✅ Testar

Acesse: http://127.0.0.1:5000/pages/dashboard.html

**Teste no chat:**
```
"Agendar vacinação para Thor amanhã"
```

## 💡 Exemplos Rápidos

| Comando | Resultado |
|---------|-----------|
| `Vacina para Thor amanhã` | Agenda vacinação para amanhã |
| `Banho para Mimi próxima semana` | Agenda banho daqui 7 dias |
| `Consulta para Moana no dia 25` | Agenda consulta no dia 25 |

## 🚨 Problemas Comuns

**"Chatbot não configurado"**
→ Verifique se o arquivo `.env` existe e tem a chave API

**"Não encontrei o pet"**
→ Use o nome exato cadastrado no sistema

**Servidor não inicia**
→ Instale dependências: `pip install -r requirements.txt`

## 📚 Documentação Completa

Veja: `CHATBOT_OPENAI.md`

---

**🐾 PetCloud - Gestão Inteligente de Pets**
