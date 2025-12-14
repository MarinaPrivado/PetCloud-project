// ==================== NAVEGAÇÃO ====================
document.querySelectorAll('.nav-link').forEach(function(link) {
    if (window.location.pathname === link.getAttribute('href')) {
        link.classList.add('active');
    } else {
        link.classList.remove('active');
    }
});

// ==================== MODAL DE ENVIO ====================

function abrirModalEnvio() {
    document.getElementById('modalEnvio').style.display = 'block';
    carregarPetsUsuario();
}

function fecharModalEnvio() {
    document.getElementById('modalEnvio').style.display = 'none';
    document.getElementById('formEnvioFoto').reset();
    document.getElementById('nomeArquivo').textContent = 'Clique para escolher uma foto';
}

function mostrarNomeArquivo() {
    const input = document.getElementById('imagemInput');
    const label = document.getElementById('nomeArquivo');
    if (input.files.length > 0) {
        label.textContent = input.files[0].name;
    } else {
        label.textContent = 'Clique para escolher uma foto';
    }
}

// Fechar modal clicando fora
window.onclick = function(event) {
    const modal = document.getElementById('modalEnvio');
    if (event.target === modal) {
        fecharModalEnvio();
    }
}

// ==================== CARREGAR PETS DO USUÁRIO ====================

async function carregarPetsUsuario() {
    try {
        const userData = JSON.parse(localStorage.getItem('user') || '{}');
        const userEmail = userData.email;
        
        if (!userEmail) {
            alert('Você precisa estar logado para enviar fotos!');
            fecharModalEnvio();
            window.location.href = '/login.html';
            return;
        }
        
        const response = await fetch('http://127.0.0.1:5000/api/pets');
        const data = await response.json();
        
        if (data.success) {
            // Filtrar apenas pets do usuário logado
            const user = await fetch(`http://127.0.0.1:5000/api/users?email=${encodeURIComponent(userEmail)}`).then(r => r.json());
            const userId = user.users?.[0]?.id;
            
            const meusPets = data.pets.filter(pet => pet.owner_id === userId);
            
            const select = document.getElementById('petSelect');
            select.innerHTML = '<option value="">-- Selecione um pet --</option>';
            
            if (meusPets.length === 0) {
                select.innerHTML = '<option value="">Você não tem pets cadastrados</option>';
                return;
            }
            
            meusPets.forEach(pet => {
                const option = document.createElement('option');
                option.value = pet.id;
                option.textContent = `${pet.name} (${pet.type})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar pets:', error);
        alert('Erro ao carregar seus pets. Tente novamente.');
    }
}

// ==================== ENVIAR FOTO ====================

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('formEnvioFoto').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const btnEnviar = document.getElementById('btnEnviar');
        btnEnviar.disabled = true;
        btnEnviar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
        
        try {
            const userData = JSON.parse(localStorage.getItem('user') || '{}');
            const userEmail = userData.email;
            
            const formData = new FormData();
            formData.append('pet_id', document.getElementById('petSelect').value);
            formData.append('user_email', userEmail);
            formData.append('descricao', document.getElementById('descricaoInput').value);
            formData.append('imagem', document.getElementById('imagemInput').files[0]);
            
            const response = await fetch('http://127.0.0.1:5000/api/concurso/enviar', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert(data.message);
                fecharModalEnvio();
                carregarFotosConcurso();
            } else {
                alert(data.message);
            }
        } catch (error) {
            console.error('Erro ao enviar foto:', error);
            alert('Erro ao enviar foto. Tente novamente.');
        } finally {
            btnEnviar.disabled = false;
            btnEnviar.innerHTML = '<i class="fas fa-paper-plane"></i> Enviar Foto';
        }
    });
    
    // Carregar fotos ao iniciar a página
    carregarFotosConcurso();
});

// ==================== CARREGAR FOTOS DO CONCURSO ====================

async function carregarFotosConcurso() {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/concurso/fotos');
        const data = await response.json();
        
        const grid = document.querySelector('.submissions-grid');
        
        // Obter usuário logado para verificar permissões
        const userData = JSON.parse(localStorage.getItem('user') || '{}');
        const userEmail = userData.email || '';
        
        if (data.success && data.fotos.length > 0) {
            grid.innerHTML = '';
            
            data.fotos.forEach(foto => {
                const card = document.createElement('div');
                card.className = 'submission-card';
                
                // Verificar se o usuário logado é o dono da foto
                const isDono = userEmail && foto.user_email === userEmail;
                const btnDeletar = isDono ? `
                    <button onclick="deletarFoto(${foto.id}); return false;" class="btn-delete" title="Deletar minha foto">
                        ×
                    </button>
                ` : '';
                
                card.innerHTML = `
                    ${btnDeletar}
                    <div class="photo-placeholder" style="background-image: url('http://127.0.0.1:5000${foto.imagem_url}'); background-size: cover; background-position: center;"></div>
                    <div class="submission-details">
                        <h4>${foto.descricao || 'Sem descrição'}</h4>
                        <p>Submetido por: ${foto.user_name}</p>
                        <a href="#" onclick="votarFoto(${foto.id}); return false;" class="btn-vote">
                            <i class="fas fa-heart"></i> Votar (${foto.votos})
                        </a>
                    </div>
                `;
                grid.appendChild(card);
            });
        } else {
            grid.innerHTML = '<p style="text-align: center; color: #1a1a1a; padding: 40px; width: 100%; font-size: 18px;"><i class="fas fa-paw" style="font-size: 48px; color: #ff7700; margin-bottom: 20px;"></i><br><br>Nenhuma foto enviada ainda. Seja o primeiro a participar!</p>';
        }
    } catch (error) {
        console.error('Erro ao carregar fotos do concurso:', error);
        const grid = document.querySelector('.submissions-grid');
        grid.innerHTML = '<p style="text-align: center; color: #ff7700; padding: 40px; width: 100%; font-size: 18px;"><i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 20px;"></i><br><br>Erro ao carregar fotos. Tente novamente mais tarde.</p>';
    }
}

// ==================== VOTAR EM FOTO ====================

async function votarFoto(concursoId) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/api/concurso/votar/${concursoId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            carregarFotosConcurso();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Erro ao votar:', error);
        alert('Erro ao registrar voto. Tente novamente.');
    }
}

// ==================== DELETAR FOTO ====================

async function deletarFoto(concursoId) {
    if (!confirm('Tem certeza que deseja deletar esta foto do concurso?')) {
        return;
    }
    
    try {
        const userString = localStorage.getItem('user');
        console.log('[DEBUG] User string from localStorage:', userString);
        
        if (!userString) {
            alert('Você precisa estar logado para deletar fotos!');
            return;
        }
        
        const userData = JSON.parse(userString);
        const userEmail = userData.email;
        console.log('[DEBUG] User email:', userEmail);
        
        if (!userEmail) {
            alert('Email não encontrado. Faça login novamente!');
            return;
        }
        
        const url = `http://127.0.0.1:5000/api/concurso/deletar/${concursoId}?user_email=${encodeURIComponent(userEmail)}`;
        console.log('[DEBUG] DELETE request URL:', url);
        
        const response = await fetch(url, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            await carregarFotosConcurso();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Erro ao deletar foto:', error);
        alert('Erro ao deletar foto. Tente novamente.');
    }
}
