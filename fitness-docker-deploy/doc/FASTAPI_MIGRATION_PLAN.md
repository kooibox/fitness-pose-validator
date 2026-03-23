# FastAPI 迁移方案

> **文档版本**: v1.0  
> **生成日期**: 2026-03-23  
> **项目性质**: 参赛项目，追求完成度，设计从简

---

## 一、迁移目标

1. 将现有 `http.server` 迁移到 FastAPI
2. 添加简易用户系统（登录即可，无需注册/找回密码）
3. 支持多动作类型（深蹲、俯卧撑、弓步蹲）
4. 保持代码简洁，避免过度设计

---

## 二、技术选型（从简原则）

| 组件 | 选型 | 理由 |
|------|------|------|
| Web 框架 | FastAPI | 自动文档、类型验证、依赖注入 |
| 数据库 | **SQLite + 原生 SQL** | 不引入 ORM，保持简单 |
| 认证 | JWT (python-jose) | 轻量，无状态 |
| 密码 | passlib + bcrypt | 单函数调用即可 |
| 服务器 | uvicorn | FastAPI 标配 |

**不引入**：SQLAlchemy、Alembic、Pydantic 复杂特性、OAuth2 完整流程

---

## 三、目录结构

```
server/
├── main.py                 # FastAPI 入口（替代 run_server.py）
├── database.py             # 数据库连接和初始化
├── auth.py                 # 简易 JWT 认证
├── models.py               # Pydantic 数据模型
├── routers/
│   ├── __init__.py
│   ├── auth.py             # 登录接口
│   ├── sessions.py         # 训练数据接口
│   ├── dashboard.py        # 大屏数据接口
│   └── llm.py              # LLM 分析接口
├── analysis/               # 保留现有分析模块
│   ├── __init__.py
│   ├── dashboard_analyzer.py
│   ├── data_preprocessor.py
│   ├── llm_analyzer.py
│   ├── llm_analyzer_real.py
│   └── prompt_templates.py
└── requirements.txt
```

---

## 四、数据库改动（最小化）

### 4.1 新增用户表

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
```

### 4.2 修改现有表

```sql
-- 为训练会话添加用户关联
ALTER TABLE uploaded_sessions ADD COLUMN user_id INTEGER;

-- 不设外键约束，保持简单
```

### 4.3 预置账号

```sql
-- 开发阶段预置账号，避免注册逻辑
INSERT INTO users (username, password_hash) VALUES 
('admin', '$2b$12$...'),  -- 密码: admin123
('demo', '$2b$12$...');   -- 密码: demo123
```

---

## 五、核心代码示例

### 5.1 入口文件 (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from database import init_db
from routers import auth, sessions, dashboard, llm

app = FastAPI(title="Fitness Pose Server")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(llm.router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    init_db()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### 5.2 认证模块 (auth.py)

```python
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
import sqlite3

SECRET_KEY = "your-secret-key-here"  # 生产环境用环境变量
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "username": username, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """依赖注入：获取当前登录用户"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的认证凭证")
        return {"user_id": user_id, "username": payload.get("username")}
    except JWTError:
        raise HTTPException(status_code=401, detail="认证失败")
```

### 5.3 数据模型 (models.py)

```python
from pydantic import BaseModel
from typing import Optional, List

# 认证相关
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# 训练数据相关
class RecordData(BaseModel):
    timestamp: str
    left_angle: float
    right_angle: float
    avg_angle: float
    state: str
    rep_count: int

class SessionUpload(BaseModel):
    version: str
    session: dict
    records: List[RecordData]
    exercise_type: str = "squat"  # 默认深蹲，兼容旧数据

# Dashboard 响应
class OverviewResponse(BaseModel):
    total_sessions: int
    total_reps: int
    avg_quality: float
    # ... 其他字段
```

### 5.4 路由示例 (routers/auth.py)

```python
from fastapi import APIRouter, HTTPException
from models import LoginRequest, TokenResponse
from auth import verify_password, create_access_token
import sqlite3

router = APIRouter()

@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """用户登录"""
    conn = sqlite3.connect("server_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (request.username,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not verify_password(request.password, row[1]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    return TokenResponse(
        access_token=create_access_token(row[0], request.username)
    )
```

### 5.5 路由示例 (routers/sessions.py)

```python
from fastapi import APIRouter, Depends
from models import SessionUpload
from auth import get_current_user
import sqlite3

router = APIRouter()

@router.post("/sessions/upload")
async def upload_session(
    data: SessionUpload,
    user: dict = Depends(get_current_user)  # 需要登录
):
    """上传训练数据"""
    user_id = user["user_id"]
    # 保存数据，关联 user_id
    # ...
    return {"status": "success", "message": "数据上传成功"}

@router.get("/sessions")
async def get_sessions(user: dict = Depends(get_current_user)):
    """获取当前用户的训练列表"""
    conn = sqlite3.connect("server_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM uploaded_sessions WHERE user_id = ? ORDER BY start_time DESC",
        (user["user_id"],)
    )
    sessions = cursor.fetchall()
    conn.close()
    return {"status": "success", "data": sessions}
```

---

## 六、迁移步骤

### Phase 1: 基础框架（0.5 天）

- [ ] 创建 FastAPI 项目结构
- [ ] 编写 `main.py` 入口
- [ ] 编写 `database.py` 数据库初始化
- [ ] 配置 `requirements.txt`
- [ ] 测试服务器启动

### Phase 2: 用户认证（0.5 天）

- [ ] 创建用户表
- [ ] 编写 `auth.py` 认证模块
- [ ] 编写登录接口
- [ ] 预置测试账号
- [ ] 测试登录流程

### Phase 3: 数据接口迁移（1 天）

- [ ] 迁移训练数据上传接口
- [ ] 迁移 Dashboard 数据接口（7 个端点）
- [ ] 迁移 LLM 分析接口（3 个端点）
- [ ] 添加用户数据隔离
- [ ] 运行现有分析模块（不改动）

### Phase 4: 测试与文档（0.5 天）

- [ ] 使用 Swagger UI 测试所有接口
- [ ] 验证前端兼容性
- [ ] 更新 Docker 配置
- [ ] 编写简要 API 文档

**总工期：2.5 天**

---

## 七、依赖清单

```txt
# requirements.txt
fastapi>=0.100.0
uvicorn>=0.23.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
openai>=1.0.0
```

---

## 八、兼容性处理

### 8.1 旧客户端兼容

```python
@router.post("/sessions/upload")
async def upload_session(data: SessionUpload, user: dict = Depends(get_current_user)):
    # 如果没有 exercise_type，默认为 "squat"（兼容旧客户端）
    exercise_type = data.exercise_type or "squat"
    # ...
```

### 8.2 无认证访问（可选）

```python
# Dashboard 公开接口，无需登录
@router.get("/dashboard/public-overview")
async def public_overview():
    # 返回全局统计（不涉及用户数据）
    pass
```

---

## 九、Docker 配置更新

```dockerfile
# Dockerfile.server
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ ./
RUN mkdir -p /data

ENV SERVER_DB_PATH=/data/server_data.db

EXPOSE 8080
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## 十、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 旧客户端不兼容 | 数据无法上传 | 保持旧接口兼容，exercise_type 可选 |
| JWT 密钥泄露 | 安全风险 | 使用环境变量存储密钥 |
| 数据库迁移失败 | 数据丢失 | 先备份，ALTER TABLE 不删除旧数据 |

---

## 十一、验收标准

- [ ] 所有现有 API 端点正常工作
- [ ] 登录接口返回 JWT token
- [ ] 需认证的接口必须携带 token
- [ ] Swagger UI 可访问 (`http://localhost:8080/docs`)
- [ ] 旧客户端数据可正常上传
- [ ] Dashboard 数据正常显示

---

**方案编写完毕，请审阅。**
