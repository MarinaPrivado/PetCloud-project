# 🤖 Chatbot PetCloud - Integração com OpenAI

## 📋 Visão Geral

O chatbot do PetCloud usa **OpenAI GPT-4o-mini** para processar linguagem natural e agendar serviços automaticamente (vacinação, banho, consultas).

## ⚙️ Configuração

### 1. Obter Chave API da OpenAI

1. Acesse: https://platform.openai.com/api-keys
2. Faça login ou crie uma conta
3. Clique em **"Create new secret key"**
4. Copie a chave gerada (começa com `sk-`)
5. **Importante**: Você precisará adicionar créditos na sua conta OpenAI

### 2. Configurar o Backend

1. Navegue até a pasta `backend/`:
```powershell
cd backend
```

2. Copie o arquivo de exemplo:
```powershell
Copy-Item .env.example .env
```

3. Abra o arquivo `.env` e cole sua chave:
```
OPENAI_API_KEY=sk-sua-chave-aqui
```

4. Certifique-se de que as dependências estão instaladas:
```powershell
pip install -r requirements.txt
```

### 3. Iniciar o Servidor

```powershell
cd src
python app.py
```

O servidor iniciará em: `http://127.0.0.1:5000`

## 🚀 Como Usar

### Exemplos de Comandos

O chatbot entende linguagem natural. Exemplos:

**Vacinação:**
- "Agendar vacinação para Thor amanhã"
- "Vacina antirrábica para Mimi próxima semana"
- "Quero vacinar o Thor daqui a 5 dias"

**Banho:**
- "Agendar banho para Moana na sexta"
- "Banho e tosa para Thor no dia 25/05"

**Consulta:**
- "Marcar consulta para Mimi amanhã"
- "Check-up veterinário para Thor próxima semana"

### Informações Automáticas

O chatbot extrai automaticamente:
- ✅ **Tipo de serviço** (vacinação, banho, consulta)
- ✅ **Pet** (nome do seu pet)
- ✅ **Data** (datas relativas ou específicas)

### Datas Relativas Suportadas

- `amanhã` → +1 dia
- `próxima semana` → +7 dias
- `daqui a X dias` → +X dias
- Datas específicas: "25/05", "dia 15"

## 🔧 Estrutura Técnica

### Endpoint da API

```
POST http://127.0.0.1:5000/api/chatbot/agendar
Content-Type: application/json

{
    "mensagem": "Agendar vacinação para Thor amanhã"
}
```

### Resposta de Sucesso

```json
{
    "success": true,
    "message": "✅ Agendamento confirmado! Vacinação para Thor em 25/05/2024.",
    "agendamento": {
        "id": 123,
        "tipo": "vacinacao",
        "data": "25/05/2024",
        "pet_nome": "Thor"
    }
}
```

### Resposta de Erro/Esclarecimento

```json
{
    "success": false,
    "message": "Para qual pet você gostaria de agendar? Pets disponíveis: Thor, Mimi, Moana"
}
```

## 💰 Custos

O modelo **GPT-4o-mini** é econômico:

- **Entrada**: $0.150 / 1M tokens (~$0.0001 por mensagem)
- **Saída**: $0.600 / 1M tokens (~$0.0004 por mensagem)
- **Custo médio por agendamento**: ~$0.0005 (menos de 1 centavo)

Para 1000 agendamentos: ~$0.50

## 🛡️ Segurança

### Boas Práticas

1. ✅ **Nunca** compartilhe sua chave API publicamente
2. ✅ O arquivo `.env` está no `.gitignore` por padrão
3. ✅ Use variáveis de ambiente em produção
4. ✅ Monitore uso na plataforma OpenAI

### Verificar se .env está no .gitignore

```powershell
# No diretório raiz do projeto
Get-Content .gitignore | Select-String ".env"
```

Deve mostrar: `.env`

## 🐛 Solução de Problemas

### Erro: "Chatbot não configurado"

**Causa**: Chave API não encontrada

**Solução**:
1. Verifique se o arquivo `.env` existe em `backend/`
2. Confirme que a chave está no formato: `OPENAI_API_KEY=sk-...`
3. Reinicie o servidor Flask

### Erro: "Desculpe, não consegui processar"

**Causa**: Resposta da OpenAI não está em JSON válido

**Solução**:
- Reformule a mensagem de forma mais clara
- Exemplo: "Agendar vacinação para Thor amanhã"

### Erro: "Não encontrei o pet"

**Causa**: Nome do pet não corresponde aos cadastrados

**Solução**:
- Verifique os pets cadastrados no dashboard
- Use o nome exato do pet na mensagem

### Chatbot não responde

**Verificações**:

1. Servidor Flask está rodando?
```powershell
# Deve retornar algo
curl http://127.0.0.1:5000/api/dashboard/stats
```

2. Console do navegador mostra erros?
- Abra DevTools (F12) → Console

3. Chave API é válida?
- Teste em: https://platform.openai.com/playground

## 📊 Monitoramento

### Logs do Backend

O backend registra todas as operações:

```
[CHATBOT] Processando mensagem: Agendar vacinação para Thor amanhã
[CHATBOT] Resposta OpenAI: {"sucesso": true, "tipo": "vacinacao", ...}
[CHATBOT] Agendamento criado com sucesso - ID: 123
```

### Uso da API OpenAI

Monitore em: https://platform.openai.com/usage

## 🔄 Atualizações Automáticas

Após um agendamento bem-sucedido:
1. Registro é salvo na tabela `Servico`
2. Dashboard recarrega alertas automaticamente
3. Novo agendamento aparece em "Próximos Agendamentos"

## 📝 Notas Técnicas

### Modelo Usado
- **GPT-4o-mini**: Balanço ideal entre custo e qualidade
- Temperature: 0.3 (respostas mais consistentes)
- Max tokens: 500

### Sistema de Contexto
O chatbot recebe contexto automático:
- Lista de pets cadastrados
- Clínicas disponíveis
- Data atual do sistema
- Instruções de formatação JSON

### Validações
- Pet existe no banco de dados
- Data é válida e futura
- Tipo de serviço é reconhecido
- Formato de resposta é JSON válido

## 🆘 Suporte

Se precisar de ajuda:
1. Verifique os logs do servidor Flask
2. Console do navegador (F12)
3. Plataforma OpenAI: https://platform.openai.com/account/usage

---

**Desenvolvido para PetCloud** 🐾
