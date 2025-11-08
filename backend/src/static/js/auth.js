// auth.js
async function login(email, password) {
    try {
        const response = await fetch('http://localhost:5000/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Erro ao fazer login:', error);
        return {
            success: false,
            message: 'Erro ao conectar com o servidor'
        };
    }
}

async function register(name, email, password) {
    try {
        const response = await fetch('http://localhost:5000/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, email, password })
        });

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Erro ao registrar:', error);
        return {
            success: false,
            message: 'Erro ao conectar com o servidor'
        };
    }
}

// Função para salvar os dados do usuário no localStorage após o login
function saveUserData(userData) {
    localStorage.setItem('user', JSON.stringify(userData));
}

// Função para verificar se o usuário está logado
function isLoggedIn() {
    return localStorage.getItem('user') !== null;
}

// Função para fazer logout
function logout() {
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}