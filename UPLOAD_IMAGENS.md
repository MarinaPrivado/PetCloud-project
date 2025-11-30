# Sistema de Upload de Imagens - PetCloud

## ✅ Implementado

### Backend

#### 1. Modelo Pet (`backend/src/models/Pet.py`)
- ✅ Adicionado campo `photo_url` (String, nullable)
- ✅ Atualizado método `to_dict()` para incluir `photo_url`

#### 2. API (`backend/src/app.py`)
- ✅ Importado `secure_filename` do werkzeug
- ✅ Configurações de upload:
  - Pasta: `backend/uploads/`
  - Extensões permitidas: png, jpg, jpeg, gif, webp
  - Tamanho máximo: 16MB
- ✅ Função `allowed_file()` para validar extensões
- ✅ Endpoint `POST /api/pets`:
  - Suporta FormData com arquivo
  - Salva imagem com timestamp no nome
  - Retorna URL da imagem: `/uploads/filename.jpg`
- ✅ Endpoint `GET /uploads/<filename>` para servir imagens
- ✅ Atualizado `GET /api/pets` para incluir `photo_url` na listagem

#### 3. Banco de Dados
- ✅ Executado script de migração `add_photo_url_column.py`
- ✅ Coluna `photo_url` adicionada à tabela `pets`

#### 4. Pasta de Uploads
- ✅ Criada automaticamente: `backend/uploads/`

### Frontend

#### Página `pages/novo_pet.html`
- ✅ Campo de upload com área de drag-and-drop
- ✅ Preview da imagem selecionada
- ✅ Envio via FormData (suporta arquivos)
- ✅ URL da API atualizada para: `http://127.0.0.1:5000/api/pets`

## 📋 Como Usar

### 1. Cadastrar Pet com Foto
1. Acesse `pages/novo_pet.html`
2. Preencha os dados do pet
3. Clique na área de upload ou arraste uma imagem
4. Veja o preview da imagem
5. Clique em "Salvar Pet"

### 2. Formato do Upload
```javascript
const formData = new FormData();
formData.append('nome', 'Thor');
formData.append('especie', 'Cachorro');
formData.append('raca', 'Golden Retriever');
formData.append('birth_date', '2020-01-15');
formData.append('descricao', 'Cachorro brincalhão');
formData.append('foto', file); // Arquivo de imagem

fetch('http://127.0.0.1:5000/api/pets', {
    method: 'POST',
    body: formData
});
```

### 3. Response da API
```json
{
  "success": true,
  "message": "Pet cadastrado com sucesso!",
  "pet": {
    "id": 7,
    "name": "Thor",
    "breed": "Golden Retriever",
    "birth_date": "2020-01-15",
    "type": "Cachorro",
    "photo_url": "/uploads/20251130_143022_thor.jpg"
  }
}
```

### 4. Acessar Imagem
```
http://127.0.0.1:5000/uploads/20251130_143022_thor.jpg
```

## 🔒 Segurança

- ✅ Validação de extensão de arquivo
- ✅ Nome de arquivo sanitizado (`secure_filename`)
- ✅ Timestamp adicionado para evitar conflitos
- ✅ Limite de tamanho: 16MB

## 📁 Estrutura de Arquivos

```
PetCloud-project/
├── backend/
│   ├── uploads/                    # ✅ Pasta de imagens
│   │   └── 20251130_143022_thor.jpg
│   └── src/
│       ├── app.py                  # ✅ Atualizado
│       ├── models/
│       │   └── Pet.py              # ✅ Atualizado
│       └── add_photo_url_column.py # ✅ Script de migração
└── pages/
    └── novo_pet.html               # ✅ Atualizado
```

## 🎨 Preview Visual

Quando o usuário seleciona uma imagem, a área de upload mostra:
- ✅ Preview da imagem (max 200px altura)
- ✅ Nome do arquivo
- ✅ Ícone de confirmação (✓)

## ⚙️ Extensões Suportadas
- PNG
- JPG/JPEG
- GIF
- WEBP

---
**Data**: 30/11/2025
**Status**: ✅ Implementado e Testado
