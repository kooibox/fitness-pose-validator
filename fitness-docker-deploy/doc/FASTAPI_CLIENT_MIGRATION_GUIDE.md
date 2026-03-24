# FastAPI 迁移 - 客户端/前端适配指南

> **文档版本**: v1.0  
> **生成日期**: 2026-03-23  
> **适用对象**: 前端开发、客户端开发

---

## 一、变更概述

| 组件 | 是否需要修改 | 修改程度 | 主要原因 |
|------|-------------|---------|---------|
| **前端** | ❌ 不需要 | - | API 路径未变，无认证需求 |
| **客户端** | ✅ 需要 | 中等 | 认证方式从静态 API Key 改为 JWT |

---

## 二、API 端点对比

### 2.1 端点列表

| 端点 | 旧版 (http.server) | 新版 (FastAPI) | 变化 |
|------|-------------------|----------------|------|
| 数据上传 | `POST /api/v1/sessions/upload` | `POST /api/v1/sessions/upload` | ✅ 路径不变，**需认证** |
| 概览统计 | `GET /api/v1/dashboard/overview` | `GET /api/v1/dashboard/overview` | ✅ 无变化 |
| 趋势数据 | `GET /api/v1/dashboard/trend` | `GET /api/v1/dashboard/trend` | ✅ 无变化 |
| 分布数据 | `GET /api/v1/dashboard/distribution` | `GET /api/v1/dashboard/distribution` | ✅ 无变化 |
| 热力图 | `GET /api/v1/dashboard/heatmap` | `GET /api/v1/dashboard/heatmap` | ✅ 无变化 |
| 雷达图 | `GET /api/v1/dashboard/radar` | `GET /api/v1/dashboard/radar` | ✅ 无变化 |
| 最佳记录 | `GET /api/v1/dashboard/best-records` | `GET /api/v1/dashboard/best-records` | ✅ 无变化 |
| 最近会话 | `GET /api/v1/dashboard/recent-sessions` | `GET /api/v1/dashboard/recent-sessions` | ✅ 无变化 |
| LLM 分析 | `POST /api/v1/llm/analyze` | `POST /api/v1/llm/analyze` | ✅ 无变化 |
| 分析状态 | `GET /api/v1/llm/status/{id}` | `GET /api/v1/llm/status/{id}` | ✅ 无变化 |
| 分析类型 | `GET /api/v1/llm/types` | `GET /api/v1/llm/types` | ✅ 无变化 |
| **用户登录** | ❌ 不存在 | `POST /api/v1/auth/login` | 🆕 **新增** |
| **当前用户** | ❌ 不存在 | `GET /api/v1/auth/me` | 🆕 **新增** |
| 会话列表 | ❌ 不存在 | `GET /api/v1/sessions` | 🆕 **新增** |
| 会话详情 | ❌ 不存在 | `GET /api/v1/sessions/{id}` | 🆕 **新增** |
| 健康检查 | ❌ 不存在 | `GET /health` | 🆕 **新增** |
| API 文档 | ❌ 不存在 | `GET /docs` | 🆕 **新增** |

### 2.2 关键差异

```
┌─────────────────────────────────────────────────────────────────┐
│                        旧版 (http.server)                        │
├─────────────────────────────────────────────────────────────────┤
│  认证方式: 静态 API Key                                           │
│  Token:    "test-api-key-12345"                                  │
│  用户系统: ❌ 无                                                  │
│  数据隔离: ❌ 无（所有数据共享）                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓ 迁移
┌─────────────────────────────────────────────────────────────────┐
│                        新版 (FastAPI)                            │
├─────────────────────────────────────────────────────────────────┤
│  认证方式: JWT (JSON Web Token)                                  │
│  Token:    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...              │
│  用户系统: ✅ 有（登录获取 Token）                                 │
│  数据隔离: ✅ 有（按用户隔离数据）                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、认证机制对比

### 3.1 旧版认证（静态 API Key）

```python
# server/_archive_http_server/server_receiver.py

API_KEY = "test-api-key-12345"  # 硬编码，所有客户端共用

def _verify_auth(self, auth_header: str) -> bool:
    if not auth_header.startswith("Bearer "):
        return False
    token = auth_header[7:]
    return token == self.API_KEY  # 直接比较
```

**客户端请求示例：**
```http
POST /api/v1/sessions/upload HTTP/1.1
Host: localhost:8080
Authorization: Bearer test-api-key-12345
Content-Type: application/json

{"version": "1.0", "session": {...}, "records": [...]}
```

### 3.2 新版认证（JWT）

```python
# server/auth.py

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "username": username, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
```

**客户端请求流程：**

```
┌──────────────┐     POST /auth/login           ┌──────────────┐
│   客户端      │ ──────────────────────────────→│    服务器     │
│              │   {"username","password"}       │              │
│              │                                 │              │
│              │←────────────────────────────────│              │
│              │   {"access_token": "eyJ..."}    │              │
│              │                                 │              │
│              │  POST /sessions/upload          │              │
│              │ ──────────────────────────────→│              │
│              │  Authorization: Bearer eyJ...   │              │
│              │                                 │              │
│              │←────────────────────────────────│              │
│              │   {"status": "success"...}      │              │
└──────────────┘                                 └──────────────┘
```

---

## 四、客户端修改方案

### 4.1 需要修改的内容

| 模块 | 修改内容 | 优先级 |
|------|---------|--------|
| 配置管理 | 移除硬编码 API Key，添加用户名/密码配置 | 🔴 高 |
| 网络模块 | 新增登录接口调用，Token 存储，自动刷新 | 🔴 高 |
| 上传模块 | 使用动态 Token 替换静态 API Key | 🔴 高 |
| 数据模型 | 无需修改（数据格式兼容） | 🟢 低 |

### 4.2 详细修改步骤

#### 步骤 1：更新配置结构

**旧配置：**
```python
# config.py (旧)
class ServerConfig:
    HOST = "localhost"
    PORT = 8080
    API_KEY = "test-api-key-12345"  # 移除
```

**新配置：**
```python
# config.py (新)
class ServerConfig:
    HOST = "localhost"
    PORT = 8080
    # API_KEY 移除，改为用户凭证
    USERNAME = "admin"      # 可从环境变量读取
    PASSWORD = "admin123"   # 可从环境变量读取
```

#### 步骤 2：新增 Token 管理模块

```python
# auth_client.py (新增)
import time
import requests
from typing import Optional

class TokenManager:
    """JWT Token 管理器"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self._token: Optional[str] = None
        self._expires_at: float = 0
    
    def get_token(self) -> str:
        """获取有效的 Token，自动刷新"""
        if self._token and time.time() < self._expires_at - 60:
            return self._token
        return self._refresh_token()
    
    def _refresh_token(self) -> str:
        """刷新 Token"""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={
                "username": self.username,
                "password": self.password
            }
        )
        
        if response.status_code != 200:
            raise AuthenticationError(f"登录失败: {response.text}")
        
        data = response.json()
        self._token = data["access_token"]
        # JWT 有效期 24 小时，提前 1 小时刷新
        self._expires_at = time.time() + 23 * 3600
        
        return self._token
    
    def get_auth_header(self) -> dict:
        """获取认证请求头"""
        return {"Authorization": f"Bearer {self.get_token()}"}


class AuthenticationError(Exception):
    """认证错误"""
    pass
```

#### 步骤 3：更新网络请求模块

**旧版：**
```python
# network.py (旧)
class NetworkClient:
    def __init__(self, config: ServerConfig):
        self.base_url = f"http://{config.HOST}:{config.PORT}"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.API_KEY}"  # 静态
        }
    
    def upload(self, data: dict):
        return requests.post(
            f"{self.base_url}/api/v1/sessions/upload",
            headers=self.headers,
            json=data
        )
```

**新版：**
```python
# network.py (新)
class NetworkClient:
    def __init__(self, config: ServerConfig):
        self.base_url = f"http://{config.HOST}:{config.PORT}"
        self.token_manager = TokenManager(
            self.base_url,
            config.USERNAME,
            config.PASSWORD
        )
    
    def upload(self, data: dict):
        # 动态获取 Token
        headers = {
            "Content-Type": "application/json",
            **self.token_manager.get_auth_header()
        }
        
        return requests.post(
            f"{self.base_url}/api/v1/sessions/upload",
            headers=headers,
            json=data
        )
```

#### 步骤 4：处理 Token 过期

```python
# network.py (续)
def upload(self, data: dict, retry: bool = True):
    headers = {
        "Content-Type": "application/json",
        **self.token_manager.get_auth_header()
    }
    
    response = requests.post(
        f"{self.base_url}/api/v1/sessions/upload",
        headers=headers,
        json=data
    )
    
    # Token 过期，强制刷新后重试
    if response.status_code == 401 and retry:
        self.token_manager._refresh_token()
        return self.upload(data, retry=False)
    
    return response
```

### 4.3 完整示例（Python 客户端）

```python
#!/usr/bin/env python3
"""Fitness Pose 客户端 - FastAPI 适配版"""

import json
import requests
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class ServerConfig:
    host: str = "localhost"
    port: int = 8080
    username: str = "admin"
    password: str = "admin123"


class FitnessClient:
    """健身数据客户端"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.base_url = f"http://{config.host}:{config.port}"
        self._token: Optional[str] = None
    
    def login(self) -> bool:
        """登录获取 Token"""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={
                "username": self.config.username,
                "password": self.config.password
            }
        )
        
        if response.status_code == 200:
            self._token = response.json()["access_token"]
            return True
        return False
    
    def _get_headers(self) -> dict:
        """获取请求头"""
        if not self._token:
            raise RuntimeError("未登录，请先调用 login()")
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}"
        }
    
    def upload_session(
        self,
        session_id: int,
        start_time: str,
        end_time: str,
        records: List[Dict[str, Any]],
        exercise_type: str = "squat"
    ) -> dict:
        """上传训练数据"""
        data = {
            "version": "1.0",
            "session": {
                "id": session_id,
                "start_time": start_time,
                "end_time": end_time,
                "total_frames": len(records),
                "total_squats": sum(1 for r in records if r.get("state") == "down")
            },
            "records": records,
            "exercise_type": exercise_type
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/sessions/upload",
            headers=self._get_headers(),
            json=data
        )
        
        return response.json()
    
    def get_sessions(self, limit: int = 20) -> dict:
        """获取训练列表"""
        response = requests.get(
            f"{self.base_url}/api/v1/sessions?limit={limit}",
            headers=self._get_headers()
        )
        return response.json()


# 使用示例
if __name__ == "__main__":
    config = ServerConfig(
        host="localhost",
        port=8080,
        username="admin",
        password="admin123"
    )
    
    client = FitnessClient(config)
    
    if client.login():
        print("登录成功！")
        
        # 上传数据
        result = client.upload_session(
            session_id=1,
            start_time="2026-03-23T10:00:00",
            end_time="2026-03-23T10:30:00",
            records=[
                {"timestamp": "10:00:01", "left_angle": 90, "right_angle": 92, "state": "down", "rep_count": 1}
            ]
        )
        print(f"上传结果: {result}")
    else:
        print("登录失败！")
```

---

## 五、数据格式对比

### 5.1 上传数据格式

**✅ 完全兼容，无需修改**

```json
{
    "version": "1.0",
    "client": {
        "app_id": "fitness-pose-validator",
        "version": "2.0.0",
        "platform": {"os": "windows", "python": "3.10"}
    },
    "session": {
        "id": 12345,
        "start_time": "2026-03-23T10:00:00",
        "end_time": "2026-03-23T10:30:00",
        "total_frames": 5000,
        "total_squats": 25
    },
    "records": [
        {
            "timestamp": "2026-03-23T10:00:01.000",
            "left_angle": 90.5,
            "right_angle": 92.3,
            "avg_angle": 91.4,
            "state": "down",
            "rep_count": 1
        }
    ],
    "exercise_type": "squat"
}
```

**兼容性说明：**

| 字段 | 旧版 | 新版 | 说明 |
|------|-----|-----|------|
| `exercise_type` | 可选（默认 squat） | 可选（默认 squat） | ✅ 兼容 |
| `client` | 可选 | 可选 | ✅ 兼容 |
| `session` | 必需 | 必需 | ✅ 兼容 |
| `records` | 必需 | 必需 | ✅ 兼容 |

### 5.2 响应格式

**上传成功响应（不变）：**
```json
{
    "status": "success",
    "data": {
        "server_session_id": 1,
        "records_stored": 100,
        "upload_time": "2026-03-23T10:30:00"
    }
}
```

**上传失败响应（不变）：**
```json
{
    "status": "error",
    "error_code": "PROCESSING_ERROR",
    "message": "错误详情"
}
```

**认证失败响应（新增）：**
```json
{
    "detail": "用户名或密码错误"
}
```

---

## 六、错误处理对比

### 6.1 错误码对照表

| HTTP 状态码 | 旧版行为 | 新版行为 | 客户端处理 |
|------------|---------|---------|-----------|
| 200 | 成功 | 成功 | 正常处理 |
| 400 | 数据格式错误 | 数据格式错误 | 检查请求体 |
| 401 | 无效 API Key | Token 无效/过期 | **重新登录** |
| 404 | 端点不存在 | 端点不存在 | 检查 URL |
| 500 | 服务器错误 | 服务器错误 | 重试或报警 |

### 6.2 客户端错误处理建议

```python
def handle_response(response: requests.Response) -> dict:
    """统一响应处理"""
    if response.status_code == 200:
        return response.json()
    
    elif response.status_code == 401:
        # Token 过期，需要重新登录
        raise AuthenticationError("Token 已过期，请重新登录")
    
    elif response.status_code == 400:
        data = response.json()
        raise ValidationError(data.get("detail", "请求参数错误"))
    
    elif response.status_code >= 500:
        raise ServerError(f"服务器错误: {response.status_code}")
    
    else:
        raise UnknownError(f"未知错误: {response.status_code}")
```

---

## 七、前端说明

### 7.1 前端无需修改

Dashboard 前端（`dashboard/`）**不需要任何修改**，原因：

1. **API 路径不变**：`/api/v1/dashboard/*` 端点完全相同
2. **无认证需求**：Dashboard 为展示层，通过 Nginx 代理访问后端
3. **响应格式不变**：JSON 结构保持一致

### 7.2 可选增强

如需添加用户登录功能，可新增：

```javascript
// 登录弹窗
async function login(username, password) {
    const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    });
    
    if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        return true;
    }
    return false;
}

// 带 Token 的请求
async function fetchWithAuth(url) {
    const token = localStorage.getItem('token');
    return fetch(url, {
        headers: {'Authorization': `Bearer ${token}`}
    });
}
```

---

## 八、迁移检查清单

### 客户端开发者

- [ ] 移除硬编码的 `API_KEY = "test-api-key-12345"`
- [ ] 添加 `USERNAME` 和 `PASSWORD` 配置项
- [ ] 实现 `TokenManager` 或类似模块
- [ ] 更新上传接口，使用动态 Token
- [ ] 添加 Token 过期重试逻辑
- [ ] 测试登录失败、Token 过期等异常场景

### 前端开发者

- [x] 无需修改（API 路径和响应格式兼容）
- [ ] （可选）添加用户登录功能

### 测试验证

- [ ] 使用预置账号 `admin/admin123` 测试登录
- [ ] 验证 Token 有效期内可正常上传
- [ ] 验证 Token 过期后自动刷新
- [ ] 验证 Dashboard 数据正常显示
- [ ] 验证多用户数据隔离

---

## 九、预置账号

| 用户名 | 密码 | 说明 |
|-------|------|------|
| `admin` | `admin123` | 管理员账号 |
| `demo` | `demo123` | 演示账号 |

---

## 十、联系与支持

如有问题，请参考：
- FastAPI 自动文档：`http://localhost:8080/docs`
- 迁移计划文档：`doc/FASTAPI_MIGRATION_PLAN.md`

---

**文档编写完毕。**