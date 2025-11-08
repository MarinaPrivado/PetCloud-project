class AuthService {
    constructor() {
        this.users = new Map(); // In-memory storage (replace with database in production)
    }

    // Register a new user
    async register(name, email, password) {
        // Check if user already exists
        if (this.users.has(email)) {
            throw new Error('User already exists');
        }

        // Create new user (in production, password should be hashed)
        const user = new User(
            Date.now().toString(), // Simple ID generation (use UUID in production)
            name,
            email,
            password
        );

        // Store user
        this.users.set(email, user);
        return user;
    }

    // Login user
    async login(email, password) {
        const user = this.users.get(email);

        // Check if user exists and password matches
        if (!user || user.password !== password) { // In production, use proper password comparison
            throw new Error('Invalid credentials');
        }

        return user;
    }

    // Change password
    async changePassword(email, currentPassword, newPassword) {
        const user = await this.login(email, currentPassword); // Verify current credentials
        user.changePassword(newPassword);
        return true;
    }

    // Reset password (in production, this would involve email verification)
    async resetPassword(email) {
        const user = this.users.get(email);
        if (!user) {
            throw new Error('User not found');
        }

        // In production:
        // 1. Generate reset token
        // 2. Save token with expiration
        // 3. Send reset email
        // 4. Create endpoint to verify token and set new password

        const tempPassword = Math.random().toString(36).slice(-8);
        user.changePassword(tempPassword);
        
        return tempPassword; // In production, don't return password, send via email
    }
}