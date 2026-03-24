/**
 * Auth Module - 用户认证管理
 */

const Auth = {
    // Token 存储 key
    TOKEN_KEY: 'fitness_token',
    USER_KEY: 'fitness_user',
    
    // 获取 Token
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },
    
    // 设置 Token
    setToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    },
    
    // 移除 Token
    removeToken() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
    },
    
    // 获取用户信息
    getUser() {
        const userStr = localStorage.getItem(this.USER_KEY);
        return userStr ? JSON.parse(userStr) : null;
    },
    
    // 设置用户信息
    setUser(user) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    },
    
    // 检查是否已登录
    isLoggedIn() {
        return !!this.getToken();
    },
    
    // 登录
    async login(username, password) {
        const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '登录失败');
        }
        
        const data = await response.json();
        this.setToken(data.access_token);
        
        // 获取用户信息
        await this.fetchUserInfo();
        
        return true;
    },
    
    // 获取用户信息
    async fetchUserInfo() {
        try {
            const response = await fetch('/api/v1/auth/me', {
                headers: this.getAuthHeaders()
            });
            
            if (response.ok) {
                const data = await response.json();
                this.setUser(data.data);
            }
        } catch (e) {
            console.error('获取用户信息失败:', e);
        }
    },
    
    // 登出
    logout() {
        this.removeToken();
        window.location.reload();
    },
    
    // 获取认证请求头
    getAuthHeaders() {
        const token = this.getToken();
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }
};

window.Auth = Auth;