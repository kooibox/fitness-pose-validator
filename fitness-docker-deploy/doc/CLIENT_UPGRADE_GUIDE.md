# 客户端升级指南

> 本文档总结了服务端 v2.4.0 的重大改动，指导客户端开发者进行相应升级。

---

## 一、版本概览

| 版本 | 发布日期 | 主要改动 |
|------|----------|----------|
| v2.4.0 | 2026-03-24 | FastAPI 迁移、JWT 认证、运动类型筛选、LLM 分析增强 |
| v2.3.0 | 2026-03-23 | 初始 http.server 架构 |

---

## 二、Breaking Changes（必须修改）

### 2.1 API 基础路径变更

**旧版本:**
```
http://localhost:8080/
```

**新版本:**
```
http://localhost:8000/api/v1/
```

所有 API 端点现在都位于 `/api/v1` 前缀下。

---

### 2.2 认证系统（新增）

服务端现在 **强制要求认证** 才能上传数据。

#### 2.2.1 登录接口

```
POST /api/v1/auth/login
```

**请求体:**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 2.2.2 获取当前用户信息

```
GET /api/v1/auth/me
Authorization: Bearer {access_token}
```

**响应:**
```json
{
  "status": "success",
  "data": {
    "user_id": 1,
    "username": "demo"
  }
}
```

#### 2.2.3 Token 使用方式

所有需要认证的接口，必须在请求头中携带 Token：

```
Authorization: Bearer {access_token}
```

**Token 有效期:** 24 小时

#### 2.2.4 预置账号

| 用户名 | 密码 |
|--------|------|
| demo | demo123 |
| admin | admin123 |

---

### 2.3 数据上传接口变更

#### 接口路径

**旧版本:**
```
POST /upload
```

**新版本:**
```
POST /api/v1/sessions/upload
```

#### 请求体新增字段

**新增 `exercise_type` 字段（运动类型）:**

```json
{
  "version": "1.0",
  "client": {
    "app_id": "fitness-pose-validator",
    "version": "1.0.0",
    "platform": {
      "os": "Android",
      "version": "12"
    }
  },
  "session": {
    "id": 12345,
    "start_time": "2026-03-24T10:00:00",
    "end_time": "2026-03-24T10:15:00",
    "total_frames": 4500,
    "total_squats": 30
  },
  "records": [
    {
      "timestamp": "2026-03-24T10:00:01.000",
      "left_angle": 95.5,
      "right_angle": 92.3,
      "avg_angle": 93.9,
      "state": "down",
      "rep_count": 1
    }
  ],
  "exercise_type": "squat"  // 新增：运动类型
}
```

#### exercise_type 可选值

| 值 | 说明 |
|----|------|
| `squat` | 深蹲（默认） |
| `pushup` | 俯卧撑 |
| `lunge` | 弓步蹲 |

**向后兼容:** 如果不传 `exercise_type`，默认值为 `squat`。

#### 响应格式

```json
{
  "status": "success",
  "data": {
    "server_session_id": 123,
    "records_stored": 4500,
    "upload_time": "2026-03-24T10:15:30"
  }
}
```

#### 错误响应

```json
{
  "status": "error",
  "error_code": "PROCESSING_ERROR",
  "message": "错误详情"
}
```

#### 认证失败响应

```json
{
  "detail": "认证失败"
}
```

HTTP 状态码: `401 Unauthorized`

---

## 三、新增功能

### 3.1 运动类型筛选

Dashboard API 的所有端点现在支持按运动类型筛选：

```
GET /api/v1/dashboard/overview?exercise_type=squat
GET /api/v1/dashboard/trend?metric=squats&period=30d&exercise_type=pushup
GET /api/v1/dashboard/distribution?metric=depth&exercise_type=lunge
GET /api/v1/dashboard/heatmap?period=90d&exercise_type=squat
GET /api/v1/dashboard/radar?exercise_type=squat
GET /api/v1/dashboard/best-records?limit=5&exercise_type=squat
GET /api/v1/dashboard/recent-sessions?limit=10&exercise_type=pushup
```

---

### 3.2 LLM 分析接口

#### 提交分析请求

```
POST /api/v1/llm/analyze
Authorization: Bearer {token}  // 可选
```

**请求体:**
```json
{
  "request_id": "optional-custom-id",
  "session_ids": [1, 2, 3],
  "analysis_type": "session",
  "context": {
    "user_goal": "improve_depth"
  },
  "language": "zh"
}
```

**analysis_type 可选值:**

| 值 | 说明 |
|----|------|
| `session` | 单次训练分析 |
| `trend` | 趋势分析 |
| `comparison` | 对比分析 |
| `advice` | 个性化建议 |
| `goal` | 目标设定 |

**响应:**
```json
{
  "status": "success",
  "data": {
    "request_id": "req-xxx",
    "status": "completed",
    "summary": "本次训练整体表现良好...",
    "insights": ["洞察1", "洞察2"],
    "suggestions": ["建议1", "建议2"],
    "score": 82.5,
    "metadata": {
      "total_squats": 25,
      "avg_depth": 95.3
    },
    "completed_at": "2026-03-24T10:30:00"
  }
}
```

#### 查询分析状态

```
GET /api/v1/llm/status/{request_id}
```

#### 获取分析类型列表

```
GET /api/v1/llm/types
```

---

### 3.3 训练记录查询接口

#### 获取训练列表

```
GET /api/v1/sessions?limit=20&offset=0
Authorization: Bearer {token}
```

**响应:**
```json
{
  "status": "success",
  "data": [
    {
      "server_session_id": 123,
      "client_session_id": 456,
      "start_time": "2026-03-24T10:00:00",
      "end_time": "2026-03-24T10:15:00",
      "total_frames": 4500,
      "total_squats": 30,
      "exercise_type": "squat",
      "upload_time": "2026-03-24T10:15:30"
    }
  ]
}
```

#### 获取单个训练详情

```
GET /api/v1/sessions/{session_id}
Authorization: Bearer {token}
```

---

## 四、完整 API 列表

### 4.1 认证接口

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/v1/auth/login` | ❌ | 登录获取 Token |
| GET | `/api/v1/auth/me` | ✅ | 获取当前用户信息 |

### 4.2 训练数据接口

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/v1/sessions/upload` | ✅ | 上传训练数据 |
| GET | `/api/v1/sessions` | ✅ | 获取训练列表 |
| GET | `/api/v1/sessions/{id}` | ✅ | 获取训练详情 |

### 4.3 Dashboard 接口

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| GET | `/api/v1/dashboard/overview` | ❌ | 概览统计 |
| GET | `/api/v1/dashboard/trend` | ❌ | 趋势数据 |
| GET | `/api/v1/dashboard/distribution` | ❌ | 分布数据 |
| GET | `/api/v1/dashboard/heatmap` | ❌ | 热力图数据 |
| GET | `/api/v1/dashboard/radar` | ❌ | 雷达图数据 |
| GET | `/api/v1/dashboard/best-records` | ❌ | 最佳记录 |
| GET | `/api/v1/dashboard/recent-sessions` | ❌ | 最近会话 |

### 4.4 LLM 分析接口

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/v1/llm/analyze` | ❌ | 提交分析请求 |
| GET | `/api/v1/llm/status/{id}` | ❌ | 查询分析状态 |
| GET | `/api/v1/llm/types` | ❌ | 获取分析类型 |

---

## 五、客户端改造清单

### 5.1 必须修改

- [ ] **修改 API 基础路径**
  - 从 `/` 改为 `/api/v1`
  - 确认服务器端口从 8080 改为 8000

- [ ] **实现登录流程**
  - 添加登录界面
  - 调用 `/auth/login` 获取 Token
  - 本地存储 Token（推荐使用 Keychain/Keystore）

- [ ] **修改数据上传接口**
  - 路径改为 `/api/v1/sessions/upload`
  - 添加 `Authorization: Bearer {token}` 请求头
  - 请求体添加 `exercise_type` 字段

- [ ] **处理 401 认证失败**
  - Token 过期时引导用户重新登录
  - 清除本地存储的 Token

### 5.2 推荐修改

- [ ] **支持运动类型选择**
  - 训练开始前选择运动类型（squat/pushup/lunge）
  - 上传时传入 `exercise_type`

- [ ] **集成 LLM 分析功能**
  - 训练完成后请求分析
  - 展示分析结果（摘要、洞察、建议、评分）

- [ ] **训练历史记录**
  - 调用 `/sessions` 获取历史记录
  - 展示训练列表和详情

### 5.3 可选优化

- [ ] **Token 自动刷新**
  - Token 有效期 24 小时
  - 可在即将过期时自动刷新（需服务端支持）

- [ ] **离线缓存**
  - 登录信息缓存
  - 训练数据本地缓存

---

## 六、示例代码

### 6.1 登录流程 (JavaScript)

```javascript
class AuthManager {
  constructor() {
    this.TOKEN_KEY = 'fitness_token';
    this.API_BASE = '/api/v1';
  }

  async login(username, password) {
    const response = await fetch(`${this.API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '登录失败');
    }

    const data = await response.json();
    this.saveToken(data.access_token);
    return data;
  }

  saveToken(token) {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  getAuthHeaders() {
    const token = this.getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }

  logout() {
    localStorage.removeItem(this.TOKEN_KEY);
  }
}
```

### 6.2 数据上传 (JavaScript)

```javascript
async function uploadSession(sessionData, exerciseType = 'squat') {
  const auth = new AuthManager();
  
  const payload = {
    version: '1.0',
    client: {
      app_id: 'my-fitness-app',
      version: '2.0.0',
      platform: getPlatformInfo()
    },
    session: sessionData.session,
    records: sessionData.records,
    exercise_type: exerciseType  // 新增字段
  };

  const response = await fetch('/api/v1/sessions/upload', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...auth.getAuthHeaders()  // 添加认证头
    },
    body: JSON.stringify(payload)
  });

  if (response.status === 401) {
    // Token 过期，引导重新登录
    auth.logout();
    throw new Error('登录已过期，请重新登录');
  }

  return response.json();
}
```

### 6.3 错误处理示例

```javascript
async function apiRequest(url, options = {}) {
  const auth = new AuthManager();
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      ...auth.getAuthHeaders()
    }
  });

  if (response.status === 401) {
    auth.logout();
    // 跳转到登录页
    window.location.href = '/login';
    throw new Error('登录已过期');
  }

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || data.message || '请求失败');
  }

  return data;
}
```

---

## 七、常见问题

### Q1: 旧版本客户端还能用吗？

**A:** 不能。必须升级以支持新的认证机制和 API 路径。

### Q2: Token 过期怎么办？

**A:** Token 有效期 24 小时。过期后 API 返回 401，客户端应引导用户重新登录。

### Q3: 不传 exercise_type 会怎样？

**A:** 默认值为 `squat`，向后兼容。但建议显式传入。

### Q4: Dashboard API 需要认证吗？

**A:** Dashboard API 不强制认证，但推荐携带 Token 以获取用户特定数据。

### Q5: 如何测试新 API？

**A:** 可使用 Swagger UI：
```
http://localhost:8000/docs
```

---

## 八、联系方式

如有问题，请联系服务端开发团队。