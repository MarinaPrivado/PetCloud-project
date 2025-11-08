-- Consultar todos os usuários
SELECT * FROM users;

-- Consultar usuários por email
-- SELECT * FROM users WHERE email = 'email@exemplo.com';

-- Consultar total de usuários cadastrados
-- SELECT COUNT(*) as total_users FROM users;

-- Consultar usuários ordenados por data de criação
-- SELECT * FROM users ORDER BY created_at DESC;

-- Consultar usuários e seus pets
-- SELECT u.name as usuario, u.email, p.name as pet_name
-- FROM users u
-- LEFT JOIN pets p ON u.id = p.owner_id;