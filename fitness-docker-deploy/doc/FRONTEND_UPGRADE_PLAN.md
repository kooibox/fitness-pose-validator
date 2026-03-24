# 前端升级方案 - Fitness Dashboard 2.0

> **文档版本**: v1.0  
> **生成日期**: 2026-03-23  
> **项目性质**: 参赛项目，追求完成度，设计从简

---

## 一、项目现状分析

### 1.1 系统架构概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           系统架构图                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────┐  │
│   │   Client    │────▶│   FastAPI   │────▶│      SQLite DB          │  │
│   │  (Python)   │     │   Server    │     │  - users                │  │
│   └─────────────┘     │             │     │  - sessions             │  │
│                       │  ┌───────┐  │     │  - records              │  │
│   ┌─────────────┐     │  │ Auth  │  │     │  - clients              │  │
│   │  Dashboard  │────▶│  │ JWT   │  │     └─────────────────────────┘  │
│   │  (Browser)  │     │  └───────┘  │                                    │
│   └─────────────┘     │             │     ┌─────────────────────────┐  │
│                       │  ┌───────┐  │     │      LLM API            │  │
│                       │  │ LLM   │──┼────▶│  (SiliconFlow/Qwen)     │  │
│                       │  │分析器  │  │     └─────────────────────────┘  │
│                       │  └───────┘  │                                    │
│                       └─────────────┘                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 后端 API 清单

| 模块 | 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|------|
| **Auth** | `/api/v1/auth/login` | POST | 无 | 用户登录，返回 JWT |
| | `/api/v1/auth/me` | GET | 需要 | 获取当前用户信息 |
| **Sessions** | `/api/v1/sessions/upload` | POST | 需要 | 上传训练数据 |
| | `/api/v1/sessions` | GET | 需要 | 获取训练列表 |
| | `/api/v1/sessions/{id}` | GET | 需要 | 获取会话详情 |
| **Dashboard** | `/api/v1/dashboard/overview` | GET | 可选 | 概览统计 |
| | `/api/v1/dashboard/trend` | GET | 可选 | 趋势数据 |
| | `/api/v1/dashboard/distribution` | GET | 可选 | 分布数据 |
| | `/api/v1/dashboard/heatmap` | GET | 可选 | 热力图数据 |
| | `/api/v1/dashboard/radar` | GET | 可选 | 雷达图数据 |
| | `/api/v1/dashboard/best-records` | GET | 可选 | 最佳记录 |
| | `/api/v1/dashboard/recent-sessions` | GET | 可选 | 最近会话 |
| **LLM** | `/api/v1/llm/analyze` | POST | 可选 | 提交分析请求 |
| | `/api/v1/llm/status/{id}` | GET | 可选 | 查询分析状态 |
| | `/api/v1/llm/types` | GET | 可选 | 获取分析类型 |

### 1.3 LLM 分析类型

| 类型 | 名称 | 用途 |
|------|------|------|
| `session` | 单次训练分析 | 分析单次训练表现，提供改进建议 |
| `trend` | 趋势分析 | 分析多日训练趋势和进步情况 |
| `comparison` | 对比分析 | 对比不同训练会话的表现差异 |
| `advice` | 个性化建议 | 基于训练历史提供个性化改进建议 |
| `goal` | 目标设定 | 根据训练水平推荐合适的训练目标 |

### 1.4 前端现状

**文件结构：**
```
dashboard/
├── index.html          # 主页面（4个页面：概览、趋势、训练、能力）
├── css/
│   └── styles.css      # 样式（深色科技风主题）
└── js/
    ├── api.js          # API 接口封装
    ├── app.js          # 应用主逻辑
    └── charts.js       # ECharts 图表配置
```

**当前功能：**
- ✅ 概览页：KPI 卡片、趋势图、雷达图、最近训练列表
- ✅ 趋势页：详细趋势图、时段分布、深度分布
- ✅ 训练页：训练列表、训练详情（含 AI 分析展示）
- ✅ 能力页：综合评分、能力雷达图、维度详情
- ❌ **用户登录**：无
- ❌ **运动类型筛选**：无（仅支持深蹲）
- ⚠️ **LLM 分析**：有基础展示，但不完整

---

## 二、升级需求

### 2.1 新增功能

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 用户登录系统 | 🔴 高 | 支持用户登录/登出，数据隔离 |
| LLM 分析展示 | 🔴 高 | 完整展示 5 种分析类型的结果 |
| 运动类型支持 | 🟡 中 | 支持深蹲、俯卧撑、弓步蹲 |
| 分析结果持久化 | 🟡 中 | 保存用户查看过的分析结果 |
| 数据导出 | 🟢 低 | 导出训练数据为 CSV/JSON |

### 2.2 改进项

| 改进点 | 说明 |
|--------|------|
| API 调用携带 Token | 登录后所有请求携带 JWT |
| 错误处理优化 | 统一错误提示，Token 过期处理 |
| 加载状态优化 | 骨架屏、加载动画 |
| 响应式优化 | 移动端体验提升 |

---

## 三、技术方案

### 3.1 用户登录系统

#### 3.1.1 登录流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           登录流程图                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│   │ 打开页面 │───▶│ 检查 Token  │───▶│ Token 有效? │───▶│ 显示主页    │ │
│   └─────────┘    └─────────────┘    └──────┬──────┘    └─────────────┘ │
│                                            │ No                        │
│                                            ▼                           │
│                                     ┌─────────────┐                    │
│                                     │ 显示登录弹窗 │                    │
│                                     └──────┬──────┘                    │
│                                            │                           │
│                                            ▼                           │
│                                     ┌─────────────┐                    │
│                                     │ 输入用户名   │                    │
│                                     │ 输入密码     │                    │
│                                     │ 点击登录     │                    │
│                                     └──────┬──────┘                    │
│                                            │                           │
│                                            ▼                           │
│                                     ┌─────────────┐                    │
│                                     │ POST /login │                    │
│                                     └──────┬──────┘                    │
│                                            │                           │
│                              ┌──────────────┴──────────────┐           │
│                              ▼                             ▼           │
│                       ┌─────────────┐              ┌─────────────┐     │
│                       │ 登录成功    │              │ 登录失败    │     │
│                       │ 存储 Token  │              │ 显示错误    │     │
│                       └──────┬──────┘              └─────────────┘     │
│                              │                                         │
│                              ▼                                         │
│                       ┌─────────────┐                                  │
│                       │ 显示主页    │                                  │
│                       └─────────────┘                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.1.2 前端实现

**新增文件：`js/auth.js`**

```javascript
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
        const response = await fetch('/api/v1/auth/me', {
            headers: this.getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            this.setUser(data.data);
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
```

#### 3.1.3 登录弹窗 UI

**添加到 `index.html`：**

```html
<!-- 登录弹窗 -->
<div class="login-modal" id="loginModal">
    <div class="login-card">
        <div class="login-header">
            <div class="login-logo">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
            </div>
            <h2>欢迎回来</h2>
            <p>登录以查看您的训练数据</p>
        </div>
        
        <form id="loginForm" class="login-form">
            <div class="form-group">
                <label for="username">用户名</label>
                <input type="text" id="username" name="username" 
                       placeholder="请输入用户名" required autocomplete="username">
            </div>
            
            <div class="form-group">
                <label for="password">密码</label>
                <input type="password" id="password" name="password" 
                       placeholder="请输入密码" required autocomplete="current-password">
            </div>
            
            <div class="login-error" id="loginError" style="display: none;"></div>
            
            <button type="submit" class="login-btn" id="loginBtn">
                <span>登 录</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
            </button>
        </form>
        
        <div class="login-footer">
            <p>预置账号: admin / admin123</p>
        </div>
    </div>
</div>
```

**添加到 `styles.css`：**

```css
/* 登录弹窗 */
.login-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(10, 15, 28, 0.95);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    backdrop-filter: blur(8px);
}

.login-modal.hidden {
    display: none;
}

.login-card {
    width: 100%;
    max-width: 400px;
    padding: var(--spacing-2xl);
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: var(--shadow-glow);
}

.login-header {
    text-align: center;
    margin-bottom: var(--spacing-xl);
}

.login-logo {
    width: 60px;
    height: 60px;
    margin: 0 auto var(--spacing-md);
    background: var(--gradient-primary);
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--bg-primary);
}

.login-logo svg {
    width: 32px;
    height: 32px;
}

.login-header h2 {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: var(--spacing-xs);
}

.login-header p {
    color: var(--text-muted);
    font-size: 0.875rem;
}

.login-form {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
}

.form-group label {
    display: block;
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xs);
}

.form-group input {
    width: 100%;
    padding: var(--spacing-md);
    background: var(--bg-tertiary);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-size: 1rem;
    transition: all var(--transition-fast);
}

.form-group input:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 245, 160, 0.1);
}

.login-error {
    padding: var(--spacing-sm) var(--spacing-md);
    background: rgba(255, 87, 87, 0.1);
    border: 1px solid rgba(255, 87, 87, 0.3);
    border-radius: var(--radius-sm);
    color: var(--accent-danger);
    font-size: 0.875rem;
}

.login-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
    background: var(--gradient-primary);
    border: none;
    border-radius: var(--radius-md);
    color: var(--bg-primary);
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-base);
}

.login-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 245, 160, 0.3);
}

.login-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
}

.login-btn svg {
    width: 20px;
    height: 20px;
}

.login-footer {
    margin-top: var(--spacing-lg);
    text-align: center;
    color: var(--text-muted);
    font-size: 0.75rem;
}

/* 用户信息 */
.user-info {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--bg-tertiary);
    border-radius: var(--radius-md);
}

.user-avatar {
    width: 32px;
    height: 32px;
    background: var(--gradient-primary);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--bg-primary);
    font-weight: 600;
    font-size: 0.875rem;
}

.user-name {
    font-size: 0.875rem;
    color: var(--text-primary);
}

.logout-btn {
    padding: var(--spacing-xs) var(--spacing-sm);
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-sm);
    color: var(--text-muted);
    font-size: 0.75rem;
    cursor: pointer;
    transition: all var(--transition-fast);
}

.logout-btn:hover {
    border-color: var(--accent-danger);
    color: var(--accent-danger);
}
```

### 3.2 API 模块升级

**修改 `js/api.js`：**

```javascript
/**
 * API Module - 服务器端 API 接口封装（升级版）
 */

const API_BASE = '/api/v1';

const API = {
    // ============ 认证相关 ============
    
    async login(username, password) {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '登录失败');
        }
        
        return response.json();
    },
    
    async getCurrentUser() {
        const response = await this._fetch('/auth/me');
        return response.status === 'success' ? response.data : null;
    },
    
    // ============ 训练数据 ============
    
    async getSessions(limit = 20, offset = 0, exerciseType = null) {
        let url = `${API_BASE}/sessions?limit=${limit}&offset=${offset}`;
        if (exerciseType) url += `&exercise_type=${exerciseType}`;
        
        const response = await this._fetch(url);
        return response.status === 'success' ? response.data : [];
    },
    
    async getSessionDetail(sessionId) {
        const response = await this._fetch(`${API_BASE}/sessions/${sessionId}`);
        return response.status === 'success' ? response.data : null;
    },
    
    // ============ Dashboard ============
    
    async getOverview(exerciseType = null) {
        let url = `${API_BASE}/dashboard/overview`;
        if (exerciseType) url += `?exercise_type=${encodeURIComponent(exerciseType)}`;
        
        const response = await this._fetch(url);
        return response.status === 'success' ? response.data : null;
    },
    
    async getTrend(metric = 'squats', period = '30d', exerciseType = null) {
        let url = `${API_BASE}/dashboard/trend?metric=${encodeURIComponent(metric)}&period=${encodeURIComponent(period)}`;
        if (exerciseType) url += `&exercise_type=${encodeURIComponent(exerciseType)}`;
        
        const response = await this._fetch(url);
        return response.status === 'success' ? response.data : null;
    },
    
    async getDistribution(metric = 'depth', exerciseType = null) {
        let url = `${API_BASE}/dashboard/distribution?metric=${encodeURIComponent(metric)}`;
        if (exerciseType) url += `&exercise_type=${encodeURIComponent(exerciseType)}`;
        
        const response = await this._fetch(url);
        return response.status === 'success' ? response.data : null;
    },
    
    async getRadar(exerciseType = null) {
        let url = `${API_BASE}/dashboard/radar`;
        if (exerciseType) url += `?exercise_type=${encodeURIComponent(exerciseType)}`;
        
        const response = await this._fetch(url);
        return response.status === 'success' ? response.data : null;
    },
    
    async getRecentSessions(limit = 10, exerciseType = null) {
        let url = `${API_BASE}/dashboard/recent-sessions?limit=${limit}`;
        if (exerciseType) url += `&exercise_type=${encodeURIComponent(exerciseType)}`;
        
        const response = await this._fetch(url);
        return response.status === 'success' ? response.data : [];
    },
    
    // ============ LLM 分析 ============
    
    async requestAnalysis(sessionIds, analysisType = 'session', context = null) {
        const response = await this._fetch(`${API_BASE}/llm/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_ids: sessionIds,
                analysis_type: analysisType,
                context: context,
                language: 'zh'
            })
        });
        
        return response.status === 'success' ? response.data : null;
    },
    
    async getAnalysisStatus(requestId) {
        const response = await this._fetch(`${API_BASE}/llm/status/${requestId}`);
        return response.status === 'success' ? response.data : null;
    },
    
    async getAnalysisTypes() {
        const response = await this._fetch(`${API_BASE}/llm/types`);
        return response.status === 'success' ? response.data : [];
    },
    
    // ============ 内部方法 ============
    
    async _fetch(url, options = {}) {
        // 添加认证头
        const headers = {
            ...options.headers,
            ...Auth.getAuthHeaders()
        };
        
        const response = await fetch(url, { ...options, headers });
        
        // 处理 401 未授权
        if (response.status === 401) {
            Auth.logout();
            throw new Error('登录已过期，请重新登录');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '请求失败');
        }
        
        return data;
    }
};

window.API = API;
```

### 3.3 LLM 分析展示

#### 3.3.1 分析类型选择器

**新增组件：分析类型选择器**

```html
<!-- 添加到训练详情弹窗 -->
<div class="analysis-section">
    <div class="analysis-header">
        <h3>🤖 AI 智能分析</h3>
        <div class="analysis-type-selector">
            <select id="analysisType" class="analysis-select">
                <option value="session">单次训练分析</option>
                <option value="trend">趋势分析</option>
                <option value="comparison">对比分析</option>
                <option value="advice">个性化建议</option>
                <option value="goal">目标设定</option>
            </select>
            <button class="analyze-btn" id="startAnalysis">
                开始分析
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
            </button>
        </div>
    </div>
    
    <div class="analysis-result" id="analysisResult">
        <div class="analysis-loading" id="analysisLoading" style="display: none;">
            <div class="loading-spinner"></div>
            <span>AI 正在分析中...</span>
        </div>
        
        <div class="analysis-content" id="analysisContent" style="display: none;">
            <!-- 动态填充 -->
        </div>
    </div>
</div>
```

#### 3.3.2 分析结果展示组件

**新增 JavaScript 函数：**

```javascript
/**
 * 渲染 LLM 分析结果
 */
function renderAnalysisResult(analysis) {
    const container = document.getElementById('analysisContent');
    
    if (!analysis) {
        container.innerHTML = '<p class="no-data">暂无分析结果</p>';
        return;
    }
    
    // 计算评分等级
    const score = analysis.score || 0;
    const scoreLevel = getScoreLevel(score);
    const scoreColor = getScoreColor(score);
    
    container.innerHTML = `
        <!-- 综合评分 -->
        <div class="analysis-score">
            <div class="score-circle" style="background: conic-gradient(${scoreColor} ${score * 3.6}deg, var(--bg-tertiary) 0deg)">
                <div class="score-inner">
                    <span class="score-value">${score.toFixed(1)}</span>
                    <span class="score-label">${scoreLevel}</span>
                </div>
            </div>
        </div>
        
        <!-- 总结 -->
        <div class="analysis-summary">
            <h4>📝 训练总结</h4>
            <p>${analysis.summary || '暂无总结'}</p>
        </div>
        
        <!-- 洞察 -->
        <div class="analysis-insights">
            <h4>💡 深度洞察</h4>
            <ul class="insight-list">
                ${(analysis.insights || []).map(insight => `
                    <li class="insight-item">
                        <span class="insight-dot"></span>
                        <span>${insight}</span>
                    </li>
                `).join('')}
            </ul>
        </div>
        
        <!-- 建议 -->
        <div class="analysis-suggestions">
            <h4>📌 改进建议</h4>
            <div class="suggestion-cards">
                ${(analysis.suggestions || []).map((suggestion, i) => `
                    <div class="suggestion-card">
                        <span class="suggestion-num">${i + 1}</span>
                        <p>${suggestion}</p>
                    </div>
                `).join('')}
            </div>
        </div>
        
        ${analysis.metadata ? `
        <!-- 元数据 -->
        <div class="analysis-metadata">
            <h4>📊 详细评估</h4>
            <div class="metadata-grid">
                ${Object.entries(analysis.metadata).map(([key, value]) => `
                    <div class="metadata-item">
                        <span class="metadata-label">${formatMetadataKey(key)}</span>
                        <span class="metadata-value">${formatMetadataValue(value)}</span>
                    </div>
                `).join('')}
            </div>
        </div>
        ` : ''}
        
        <!-- 时间戳 -->
        <div class="analysis-timestamp">
            分析时间: ${formatDateTime(analysis.completed_at)}
        </div>
    `;
    
    container.style.display = 'block';
}

function getScoreLevel(score) {
    if (score >= 90) return '卓越';
    if (score >= 80) return '优秀';
    if (score >= 70) return '良好';
    if (score >= 60) return '一般';
    return '待提升';
}

function getScoreColor(score) {
    if (score >= 80) return 'var(--accent-primary)';
    if (score >= 60) return 'var(--accent-warning)';
    return 'var(--accent-danger)';
}

function formatMetadataKey(key) {
    const keyMap = {
        'depth_assessment': '深度评估',
        'symmetry_assessment': '对称性评估',
        'stability_assessment': '稳定性评估',
        'trend_direction': '趋势方向',
        'improvement_rate': '进步幅度',
        'current_level': '当前水平',
    };
    return keyMap[key] || key;
}

function formatMetadataValue(value) {
    if (typeof value === 'number') {
        return value.toFixed(1) + (value < 1 ? '' : '');
    }
    if (typeof value === 'string') {
        const valueMap = {
            '良好': '<span class="tag-success">良好</span>',
            '一般': '<span class="tag-warning">一般</span>',
            '需改进': '<span class="tag-danger">需改进</span>',
            '上升': '<span class="tag-success">↑ 上升</span>',
            '平稳': '<span class="tag-info">→ 平稳</span>',
            '下降': '<span class="tag-danger">↓ 下降</span>',
        };
        return valueMap[value] || value;
    }
    return String(value);
}
```

#### 3.3.3 分析结果样式

```css
/* 分析结果 */
.analysis-section {
    margin-top: var(--spacing-xl);
    padding: var(--spacing-lg);
    background: var(--bg-tertiary);
    border-radius: var(--radius-lg);
    border: 1px solid rgba(0, 245, 160, 0.1);
}

.analysis-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
}

.analysis-header h3 {
    font-size: 1rem;
    color: var(--accent-primary);
}

.analysis-type-selector {
    display: flex;
    gap: var(--spacing-sm);
}

.analysis-select {
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--bg-secondary);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    font-size: 0.875rem;
}

.analyze-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--gradient-primary);
    border: none;
    border-radius: var(--radius-sm);
    color: var(--bg-primary);
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
}

.analyze-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 10px rgba(0, 245, 160, 0.3);
}

.analyze-btn svg {
    width: 16px;
    height: 16px;
}

/* 分析评分 */
.analysis-score {
    display: flex;
    justify-content: center;
    margin-bottom: var(--spacing-xl);
}

.score-circle {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.score-inner {
    width: 100px;
    height: 100px;
    background: var(--bg-secondary);
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.score-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent-primary);
}

.score-label {
    font-size: 0.75rem;
    color: var(--text-muted);
}

/* 分析总结/洞察/建议 */
.analysis-summary,
.analysis-insights,
.analysis-suggestions,
.analysis-metadata {
    margin-bottom: var(--spacing-lg);
}

.analysis-summary h4,
.analysis-insights h4,
.analysis-suggestions h4,
.analysis-metadata h4 {
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: var(--spacing-sm);
    color: var(--text-secondary);
}

.analysis-summary p {
    color: var(--text-primary);
    line-height: 1.6;
}

.insight-list {
    list-style: none;
    padding: 0;
}

.insight-item {
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.insight-dot {
    width: 6px;
    height: 6px;
    background: var(--accent-primary);
    border-radius: 50%;
    margin-top: 8px;
    flex-shrink: 0;
}

/* 建议卡片 */
.suggestion-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-sm);
}

.suggestion-card {
    display: flex;
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.suggestion-num {
    width: 24px;
    height: 24px;
    background: var(--accent-primary);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--bg-primary);
    font-size: 0.75rem;
    font-weight: 700;
    flex-shrink: 0;
}

.suggestion-card p {
    font-size: 0.875rem;
    color: var(--text-secondary);
    line-height: 1.5;
}

/* 元数据网格 */
.metadata-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: var(--spacing-sm);
}

.metadata-item {
    display: flex;
    justify-content: space-between;
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--bg-secondary);
    border-radius: var(--radius-sm);
}

.metadata-label {
    color: var(--text-muted);
    font-size: 0.75rem;
}

.metadata-value {
    font-size: 0.875rem;
    font-weight: 500;
}

/* 标签样式 */
.tag-success { color: var(--accent-primary); }
.tag-warning { color: var(--accent-warning); }
.tag-danger { color: var(--accent-danger); }
.tag-info { color: var(--accent-secondary); }

/* 时间戳 */
.analysis-timestamp {
    text-align: right;
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: var(--spacing-md);
}
```

### 3.4 运动类型支持

#### 3.4.1 运动类型配置

```javascript
/**
 * 运动类型配置
 */
const ExerciseTypes = {
    squat: {
        id: 'squat',
        name: '深蹲',
        nameEn: 'Squat',
        icon: '🏋️',
        metrics: {
            primary: 'squats',
            primaryLabel: '深蹲次数',
            angle: '膝关节角度',
            angleRange: [70, 180]
        },
        radarDimensions: ['深度', '对称性', '节奏', '稳定性', '频率']
    },
    pushup: {
        id: 'pushup',
        name: '俯卧撑',
        nameEn: 'Push-up',
        icon: '💪',
        metrics: {
            primary: 'reps',
            primaryLabel: '俯卧撑次数',
            angle: '肘关节角度',
            angleRange: [60, 170]
        },
        radarDimensions: ['深度', '对称性', '节奏', '稳定性', '频率']
    },
    lunge: {
        id: 'lunge',
        name: '弓步蹲',
        nameEn: 'Lunge',
        icon: '🦵',
        metrics: {
            primary: 'reps',
            primaryLabel: '弓步蹲次数',
            angle: ['左膝角度', '右膝角度'],
            angleRange: [70, 180]
        },
        radarDimensions: ['深度', '左右平衡', '节奏', '稳定性', '频率']
    }
};

window.ExerciseTypes = ExerciseTypes;
```

#### 3.4.2 运动类型选择器

```html
<!-- 添加到 Header -->
<div class="exercise-selector">
    <button class="exercise-btn active" data-type="squat">
        <span class="exercise-icon">🏋️</span>
        <span class="exercise-name">深蹲</span>
    </button>
    <button class="exercise-btn" data-type="pushup">
        <span class="exercise-icon">💪</span>
        <span class="exercise-name">俯卧撑</span>
    </button>
    <button class="exercise-btn" data-type="lunge">
        <span class="exercise-icon">🦵</span>
        <span class="exercise-name">弓步蹲</span>
    </button>
</div>
```

```css
/* 运动类型选择器 */
.exercise-selector {
    display: flex;
    gap: var(--spacing-xs);
    background: var(--bg-tertiary);
    padding: 4px;
    border-radius: var(--radius-md);
}

.exercise-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-md);
    background: transparent;
    border: none;
    border-radius: var(--radius-sm);
    color: var(--text-muted);
    font-size: 0.75rem;
    cursor: pointer;
    transition: all var(--transition-fast);
}

.exercise-btn:hover {
    color: var(--text-primary);
}

.exercise-btn.active {
    background: var(--bg-secondary);
    color: var(--accent-primary);
}

.exercise-icon {
    font-size: 1rem;
}
```

#### 3.4.3 后端适配（需要修改）

**修改 `routers/dashboard.py`：**

```python
@router.get("/dashboard/overview")
async def get_overview(
    exercise_type: Optional[str] = Query(None),
    client_id: Optional[int] = Query(None),
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取概览统计数据"""
    stats = analyzer.get_overview_stats(
        client_id=client_id,
        exercise_type=exercise_type  # 新增参数
    )
    return {"status": "success", "data": stats}
```

**修改 `analysis/dashboard_analyzer.py`：**

```python
def get_overview_stats(
    self, 
    client_id: Optional[int] = None,
    exercise_type: Optional[str] = None  # 新增参数
) -> Dict[str, Any]:
    """获取概览统计数据"""
    # 构建查询条件
    where_conditions = []
    params = []
    
    if client_id:
        where_conditions.append("s.client_id = ?")
        params.append(client_id)
    
    if exercise_type:
        where_conditions.append("s.exercise_type = ?")
        params.append(exercise_type)
    
    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    
    # 执行查询...
```

---

## 四、实施计划

### 4.1 开发顺序

| 阶段 | 任务 | 预计时间 | 优先级 |
|------|------|---------|--------|
| **Phase 1** | 用户登录系统 | 0.5 天 | 🔴 高 |
| | - 创建 auth.js 模块 | | |
| | - 添加登录弹窗 UI | | |
| | - 修改 API 模块携带 Token | | |
| | - 处理 Token 过期逻辑 | | |
| **Phase 2** | LLM 分析展示 | 0.5 天 | 🔴 高 |
| | - 分析类型选择器 | | |
| | - 分析结果展示组件 | | |
| | - 加载状态和错误处理 | | |
| **Phase 3** | 运动类型支持 | 0.5 天 | 🟡 中 |
| | - 前端运动类型选择器 | | |
| | - 后端 API 添加 exercise_type 参数 | | |
| | - 图表和数据适配 | | |
| **Phase 4** | 优化完善 | 0.5 天 | 🟢 低 |
| | - 错误处理优化 | | |
| | - 加载状态优化 | | |
| | - 移动端适配 | | |

**总工期：2 天**

### 4.2 文件修改清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `dashboard/js/auth.js` | 新增 | 用户认证模块 |
| `dashboard/js/api.js` | 修改 | 添加认证头、运动类型参数 |
| `dashboard/js/app.js` | 修改 | 添加登录逻辑、运动类型切换 |
| `dashboard/js/charts.js` | 修改 | 支持不同运动类型的图表配置 |
| `dashboard/index.html` | 修改 | 添加登录弹窗、运动类型选择器 |
| `dashboard/css/styles.css` | 修改 | 添加登录、分析结果样式 |
| `server/routers/dashboard.py` | 修改 | 添加 exercise_type 参数 |
| `server/analysis/dashboard_analyzer.py` | 修改 | 添加运动类型过滤 |

### 4.3 测试清单

- [ ] 登录流程测试
  - [ ] 正确的用户名/密码登录
  - [ ] 错误的用户名/密码提示
  - [ ] Token 过期自动登出
  - [ ] 登出功能
  
- [ ] LLM 分析测试
  - [ ] 5 种分析类型都能正常工作
  - [ ] 分析结果正确展示
  - [ ] 加载状态显示
  - [ ] 错误处理
  
- [ ] 运动类型测试
  - [ ] 切换运动类型后数据更新
  - [ ] 图表标签正确显示
  - [ ] 无数据时的提示

---

## 五、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 后端 API 未支持 exercise_type | 运动类型切换无效 | 先添加后端支持，或前端仅做 UI 预留 |
| LLM API 调用失败 | 分析功能不可用 | 添加降级方案，显示友好错误提示 |
| Token 过期用户无感知 | 操作中断 | 添加全局 401 拦截，自动跳转登录 |
| 移动端样式问题 | 体验不佳 | 使用响应式设计，重点测试移动端 |

---

## 六、验收标准

### 功能验收

- [ ] 用户可以登录/登出
- [ ] 登录后数据按用户隔离显示
- [ ] LLM 分析 5 种类型均可正常使用
- [ ] 分析结果完整展示（评分、总结、洞察、建议）
- [ ] 可切换运动类型查看不同数据
- [ ] 错误提示友好、加载状态清晰

### UI 验收

- [ ] 登录弹窗居中、美观
- [ ] 分析结果布局清晰、层次分明
- [ ] 运动类型选择器直观易用
- [ ] 移动端布局正常

---

**方案编写完毕。**