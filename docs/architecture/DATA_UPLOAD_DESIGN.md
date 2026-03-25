# 数据上传功能设计文档

## 目录

1. [概述](#概述)
2. [系统架构](#系统架构)
3. [数据流程](#数据流程)
4. [技术实现](#技术实现)
5. [数据格式](#数据格式)
6. [安全设计](#安全设计)
7. [部署方案](#部署方案)
8. [嵌入式移植](#嵌入式移植)
9. [API参考](#api参考)
10. [故障排除](#故障排除)

---

## 概述

### 功能目标

数据上传功能实现了将本地训练数据从桌面客户端上传到远程服务器的能力，支持：

- **集中数据存储**：多设备数据汇聚到统一服务器
- **数据大屏展示**：为后续数据可视化提供数据源
- **LLM分析**：为AI分析提供训练数据
- **跨平台同步**：支持Windows、Linux、嵌入式设备

### 设计原则

| 原则 | 说明 |
|------|------|
| **零依赖** | 客户端仅使用Python标准库，便于嵌入式移植 |
| **轻量级** | 最小化资源占用，适合资源受限环境 |
| **可扩展** | 模块化设计，易于功能扩展 |
| **安全可靠** | 支持认证、压缩、错误重试 |

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端（Desktop/Embedded）                 │
│                                                                 │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐     │
│  │   SQLite    │ ───▶ │ DataExporter│ ───▶ │ HTTP Client │     │
│  │ fitness.db  │      │ (JSON+gzip) │      │ (urllib)    │     │
│  └─────────────┘      └─────────────┘      └──────┬──────┘     │
│                                                   │              │
└───────────────────────────────────────────────────┼──────────────┘
                                                    │
                                              HTTP POST
                                            (JSON/gzip压缩)
                                                    │
┌───────────────────────────────────────────────────┼──────────────┐
│                        服务器端                     │              │
│                                                   ▼              │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐     │
│  │ PostgreSQL  │ ◀─── │ DataReceiver│ ◀─── │ HTTP Server │     │
│  │ (持久化存储) │      │ (验证+存储) │      │ (FastAPI)   │     │
│  └─────────────┘      └─────────────┘      └─────────────┘     │
│                                                                 │
│  ┌─────────────────────┐    ┌─────────────────────┐            │
│  │    大屏展示          │    │    LLM分析          │            │
│  │    (数据可视化)      │    │    (AI分析)         │            │
│  └─────────────────────┘    └─────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### 组件说明

#### 客户端组件

| 组件 | 文件 | 职责 |
|------|------|------|
| **DataExporter** | `src/data_exporter.py` | 数据导出、序列化、上传 |
| **UploadWorker** | `gui/workers/upload_worker.py` | GUI后台上传线程 |
| **SettingsPage** | `gui/pages/settings_page.py` | 服务器配置界面 |
| **HistoryPage** | `gui/pages/history_page.py` | 上传按钮和进度显示 |

#### 服务器端组件

| 组件 | 文件 | 职责 |
|------|------|------|
| **FitnessHTTPHandler** | `server_receiver.py` | HTTP请求处理 |
| **FitnessDataReceiver** | `server_receiver.py` | 数据验证和存储 |

---

## 数据流程

### 上传流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端上传流程                             │
└─────────────────────────────────────────────────────────────────┘

1. 用户操作
   │
   ▼
2. 选择会话 ─────────────────────────────────────────────────────┐
   │                                                              │
   ▼                                                              │
3. 读取SQLite数据库                                                │
   │  - sessions表：会话元数据                                     │
   │  - squat_records表：训练记录                                  │
   ▼                                                              │
4. 构建JSON数据结构                                               │
   │  - version: 数据格式版本                                      │
   │  - client: 客户端信息                                         │
   │  - session: 会话数据                                          │
   │  - records: 训练记录数组                                      │
   │  - summary: 统计摘要                                          │
   ▼                                                              │
5. gzip压缩 ──────────────────────────────────────────────────────┤
   │  压缩率：约 20-25%                                            │
   │  96KB → 21KB (典型值)                                         │
   ▼                                                              │
6. HTTP POST请求                                                  │
   │  - Content-Type: application/json                            │
   │  - Content-Encoding: gzip                                    │
   │  - Authorization: Bearer <token>                             │
   ▼                                                              │
7. 等待服务器响应                                                 │
   │                                                              │
   ▼                                                              │
8. 处理响应                                                       │
   │  - 成功：显示成功消息                                         │
   │  - 失败：显示错误信息                                         │
   │                                                              │
└──────────────────────────────────────────────────────────────────┘
```

### 服务器接收流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        服务器接收流程                            │
└─────────────────────────────────────────────────────────────────┘

1. 接收HTTP请求
   │
   ▼
2. 验证认证令牌
   │  - 检查Authorization头
   │  - 验证Bearer令牌
   │  - 失败返回401
   ▼
3. 读取请求体
   │
   ▼
4. 解压gzip数据
   │
   ▼
5. 解析JSON
   │
   ▼
6. 验证数据格式
   │  - 必需字段检查
   │  - 数据类型验证
   │  - 失败返回400
   ▼
7. 存储客户端信息
   │  - 检查是否已存在
   │  - 更新或插入
   ▼
8. 存储会话数据
   │  - 保存到uploaded_sessions表
   │  - 保存原始JSON（raw_data）
   ▼
9. 存储训练记录
   │  - 批量插入uploaded_records表
   │
   ▼
10. 返回成功响应
    │
    ▼
11. 记录日志
```

---

## 技术实现

### 客户端实现

#### DataExporter类

```python
class DataExporter:
    """
    数据导出器
    
    负责将本地训练数据导出为标准格式并上传到服务器。
    设计考虑嵌入式环境移植，仅使用Python标准库。
    """
    
    APP_ID = "fitness-pose-validator"
    CLIENT_VERSION = "2.0.0"
    DATA_FORMAT_VERSION = "1.0"
    
    def export_session(self, session_id: int) -> Dict[str, Any]:
        """导出单个会话数据"""
        # 1. 读取会话信息
        session = self.db.get_session(session_id)
        
        # 2. 读取训练记录
        records = self._get_session_records(session_id)
        
        # 3. 生成统计摘要
        summary = self._generate_summary(session)
        
        # 4. 构建标准格式
        return {
            "version": self.DATA_FORMAT_VERSION,
            "export_time": datetime.now().isoformat(),
            "client": {...},
            "session": asdict(session),
            "records": [asdict(r) for r in records],
            "summary": summary
        }
    
    def upload_session(
        self, 
        session_id: int, 
        server_url: str,
        auth_token: Optional[str] = None,
        compress: bool = True
    ) -> Dict[str, Any]:
        """
        上传会话数据到服务器
        
        使用Python标准库实现，零第三方依赖：
        - json: JSON序列化
        - gzip: 数据压缩
        - urllib.request: HTTP客户端
        """
        # 1. 导出数据
        data = self.export_session(session_id)
        json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        # 2. 压缩数据
        if compress:
            body = gzip.compress(json_bytes)
            content_encoding = "gzip"
        else:
            body = json_bytes
            content_encoding = None
        
        # 3. 构建请求
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"{self.APP_ID}/{self.CLIENT_VERSION}"
        }
        
        if content_encoding:
            headers["Content-Encoding"] = content_encoding
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        # 4. 发送请求
        request = urllib.request.Request(
            server_url,
            data=body,
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
```

#### UploadWorker线程

```python
class UploadWorker(QThread):
    """
    上传工作线程
    
    在后台执行数据上传，通过信号报告进度和结果。
    避免阻塞GUI主线程。
    """
    
    # 信号定义
    progress = pyqtSignal(int, int)  # 当前进度, 总数
    status_update = pyqtSignal(str)  # 状态信息
    upload_success = pyqtSignal(dict)  # 上传成功
    upload_failed = pyqtSignal(str)  # 上传失败
    
    def run(self):
        """执行上传任务"""
        total = len(self.session_ids)
        
        for i, session_id in enumerate(self.session_ids):
            if self._is_cancelled:
                return
            
            self.progress.emit(i, total)
            self.status_update.emit(f"正在上传会话 {session_id}...")
            
            try:
                result = self._upload_session(session_id)
                self.upload_success.emit(result)
            except Exception as e:
                self.upload_failed.emit(str(e))
                return
```

### 服务器端实现

#### HTTP服务器

```python
class FitnessHTTPHandler(BaseHTTPRequestHandler):
    """
    HTTP请求处理器
    
    使用Python标准库http.server实现。
    """
    
    def do_POST(self):
        """处理POST请求"""
        if self.path == "/api/v1/sessions/upload":
            self._handle_upload()
    
    def _handle_upload(self):
        """处理数据上传"""
        # 1. 验证认证
        auth_header = self.headers.get("Authorization", "")
        if not self._verify_auth(auth_header):
            self._send_json_response(401, {"error": "Unauthorized"})
            return
        
        # 2. 读取请求体
        body = self.rfile.read(int(self.headers["Content-Length"]))
        
        # 3. 解压gzip
        if self.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        
        # 4. 解析JSON
        data = json.loads(body.decode('utf-8'))
        
        # 5. 处理数据
        result = self.receiver.process_upload(data)
        
        # 6. 返回响应
        self._send_json_response(200, result)
```

#### 数据接收器

```python
class FitnessDataReceiver:
    """
    数据接收器
    
    负责接收、验证和存储客户端上传的训练数据。
    """
    
    def process_upload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理上传的数据"""
        # 1. 验证数据格式
        self._validate_data(data)
        
        # 2. 存储客户端信息
        client_id = self._save_client(data.get("client", {}))
        
        # 3. 存储会话数据
        session_id = self._save_session(client_id, data)
        
        # 4. 存储训练记录
        records_count = self._save_records(session_id, data.get("records", []))
        
        return {
            "status": "success",
            "data": {
                "server_session_id": session_id,
                "records_stored": records_count
            }
        }
```

---

## 数据格式

### 请求数据结构

```json
{
  "version": "1.0",
  "export_time": "2026-03-20T14:00:00",
  "client": {
    "app_id": "fitness-pose-validator",
    "version": "2.0.0",
    "platform": {
      "system": "Windows",
      "release": "10",
      "machine": "x86_64",
      "python_version": "3.12.3"
    }
  },
  "session": {
    "id": 44,
    "start_time": "2026-03-20T08:57:31.821453",
    "end_time": "2026-03-20T09:05:22.123456",
    "total_frames": 533,
    "total_squats": 3
  },
  "records": [
    {
      "timestamp": "2026-03-20T08:57:36.629161",
      "left_angle": 167.38,
      "right_angle": 172.55,
      "avg_angle": 169.96,
      "state": "STANDING",
      "rep_count": 0
    },
    {
      "timestamp": "2026-03-20T08:57:36.704566",
      "left_angle": 66.0,
      "right_angle": 107.1,
      "avg_angle": 86.55,
      "state": "SQUATTING",
      "rep_count": 0
    }
  ],
  "summary": {
    "total_records": 528,
    "total_squats": 3,
    "avg_angle": 125.3,
    "min_angle": 50.5,
    "max_angle": 177.8,
    "standing_count": 280,
    "squatting_count": 248
  }
}
```

### 响应数据结构

#### 成功响应 (200 OK)

```json
{
  "status": "success",
  "data": {
    "server_session_id": 2,
    "records_stored": 528,
    "upload_time": "2026-03-20T12:56:46.554184"
  }
}
```

#### 错误响应 (4xx/5xx)

```json
{
  "status": "error",
  "error_code": "INVALID_TOKEN",
  "message": "Authentication failed"
}
```

### 数据库表结构

#### 服务器端表

```sql
-- 客户端设备表
CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id TEXT NOT NULL,
    version TEXT,
    platform TEXT,
    first_seen TEXT,
    last_seen TEXT
);

-- 上传会话表
CREATE TABLE uploaded_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    client_session_id INTEGER,
    start_time TEXT,
    end_time TEXT,
    total_frames INTEGER,
    total_squats INTEGER,
    upload_time TEXT,
    raw_data TEXT,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

-- 训练记录表
CREATE TABLE uploaded_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    timestamp TEXT,
    left_angle REAL,
    right_angle REAL,
    avg_angle REAL,
    state TEXT,
    rep_count INTEGER,
    FOREIGN KEY (session_id) REFERENCES uploaded_sessions(id)
);
```

---

## 安全设计

### 认证机制

#### Bearer Token认证

```http
POST /api/v1/sessions/upload HTTP/1.1
Host: server.example.com
Authorization: Bearer test-api-key-12345
Content-Type: application/json
Content-Encoding: gzip
```

#### 验证流程

```python
def _verify_auth(self, auth_header: str) -> bool:
    """验证认证令牌"""
    if not auth_header.startswith("Bearer "):
        return False
    
    token = auth_header[7:]  # 移除 "Bearer " 前缀
    return token == self.API_KEY
```

### 数据安全

| 措施 | 说明 |
|------|------|
| **gzip压缩** | 减少传输数据量，降低被截获风险 |
| **HTTPS** | 生产环境应使用HTTPS加密传输 |
| **令牌验证** | 防止未授权访问 |
| **数据验证** | 防止恶意数据注入 |

### 生产环境建议

1. **使用JWT令牌**
   - 短期访问令牌（15-30分钟）
   - 刷新令牌机制
   - 令牌撤销支持

2. **HTTPS强制**
   - 所有通信加密
   - 证书验证

3. **速率限制**
   - 防止DDoS攻击
   - 限制每个IP的请求频率

4. **数据备份**
   - 定期备份数据库
   - 异地容灾

---

## 部署方案

### 开发环境

#### WSL服务器部署

```bash
# 1. 创建服务器目录
mkdir -p ~/fitness-server
cd ~/fitness-server

# 2. 复制服务器代码
cp /mnt/e/code/fitness-pose-validator/server_receiver.py ./

# 3. 启动服务器
python3 server_receiver.py

# 输出：
# ============================================================
# Fitness Data Server
# ============================================================
# 监听地址: 0.0.0.0:8080
# 上传端点: POST http://0.0.0.0:8080/api/v1/sessions/upload
# API密钥: test-api-key-12345
# ============================================================
```

### 生产环境

#### FastAPI服务器

```python
# server/fastapi_server.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI(title="Fitness Data Server")
security = HTTPBearer()

class SquatRecord(BaseModel):
    timestamp: str
    left_angle: float
    right_angle: float
    avg_angle: float
    state: str
    rep_count: int

class SessionUpload(BaseModel):
    version: str
    export_time: str
    client: dict
    session: dict
    records: List[SquatRecord]
    summary: dict

@app.post("/api/v1/sessions/upload")
async def upload_session(
    data: SessionUpload,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """接收客户端上传的训练数据"""
    # 验证令牌
    if not verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # 存储数据
    session_id = await save_to_database(data)
    
    return {
        "status": "success",
        "data": {"server_session_id": session_id}
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

#### Docker部署

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ .

EXPOSE 8080

CMD ["uvicorn", "fastapi_server:app", "--host", "0.0.0.0", "--port", "8080"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  fitness-server:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/fitness
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=fitness
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 嵌入式移植

### 移植优势

本方案专为嵌入式环境设计，具有以下优势：

| 特性 | 说明 |
|------|------|
| **零依赖** | 仅使用Python标准库 |
| **轻量级** | 核心模块<300行代码 |
| **跨平台** | 支持任何Python环境 |
| **低资源** | 内存占用<10MB |

### 支持的平台

| 平台 | Python版本 | 状态 |
|------|-----------|------|
| Windows | Python 3.8+ | ✓ 支持 |
| Linux | Python 3.8+ | ✓ 支持 |
| macOS | Python 3.8+ | ✓ 支持 |
| RK3588 | Python 3.8+ | ✓ 支持 |
| 鸿蒙 | Python 3.9+ | ✓ 支持 |

### 移植步骤

#### 1. 复制核心模块

```bash
# 复制数据导出模块
scp src/data_exporter.py user@embedded:/path/to/project/src/

# 复制配置
scp src/config.py user@embedded:/path/to/project/src/
scp src/database.py user@embedded:/path/to/project/src/
```

#### 2. 配置服务器地址

```python
# 编辑配置文件
SERVER_URL = "http://your-server.com:8080/api/v1/sessions/upload"
API_KEY = "your-api-key"
```

#### 3. 调用上传功能

```python
from src.data_exporter import DataExporter

# 创建导出器
exporter = DataExporter()

# 上传数据
result = exporter.upload_session(
    session_id=1,
    server_url=SERVER_URL,
    auth_token=API_KEY
)

print(f"上传成功: {result}")
```

### 内存优化

对于内存受限的嵌入式设备，可以采用以下优化：

```python
def upload_session_streaming(self, session_id: int, server_url: str):
    """
    流式上传（内存优化版本）
    
    不一次性加载所有数据到内存，
    而是分块读取和上传。
    """
    # 1. 分块读取记录
    chunk_size = 100
    offset = 0
    
    while True:
        records = self._get_records_chunk(session_id, offset, chunk_size)
        if not records:
            break
        
        # 2. 上传当前块
        self._upload_chunk(records)
        
        offset += chunk_size
```

---

## API参考

### 客户端API

#### DataExporter

```python
class DataExporter:
    """数据导出器"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化数据导出器
        
        Args:
            db_path: 数据库路径，默认使用配置中的路径
        """
    
    def export_session(self, session_id: int, include_records: bool = True) -> Dict[str, Any]:
        """
        导出单个训练会话数据
        
        Args:
            session_id: 会话ID
            include_records: 是否包含逐帧记录
            
        Returns:
            dict: 标准化的会话数据
        """
    
    def export_to_json(
        self, 
        session_id: int, 
        output_path: Optional[Path] = None,
        compress: bool = False
    ) -> Path:
        """
        导出会话数据为JSON文件
        
        Args:
            session_id: 会话ID
            output_path: 输出路径
            compress: 是否使用gzip压缩
            
        Returns:
            Path: 输出文件路径
        """
    
    def upload_session(
        self, 
        session_id: int, 
        server_url: str,
        auth_token: Optional[str] = None,
        compress: bool = True,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        上传会话数据到服务器
        
        Args:
            session_id: 会话ID
            server_url: 服务器URL
            auth_token: 认证令牌
            compress: 是否压缩数据
            timeout: 请求超时时间（秒）
            
        Returns:
            dict: 服务器响应
        """
```

#### UploadWorker

```python
class UploadWorker(QThread):
    """上传工作线程"""
    
    # 信号
    progress = pyqtSignal(int, int)  # 进度更新
    status_update = pyqtSignal(str)  # 状态更新
    upload_success = pyqtSignal(dict)  # 上传成功
    upload_failed = pyqtSignal(str)  # 上传失败
    
    def __init__(
        self,
        session_ids: list,
        server_url: str,
        api_key: str = "",
        db_path: Optional[Path] = None,
        parent=None
    ):
        """
        初始化上传工作线程
        
        Args:
            session_ids: 要上传的会话ID列表
            server_url: 服务器URL
            api_key: API密钥
            db_path: 数据库路径
        """
    
    def run(self):
        """执行上传任务"""
    
    def cancel(self):
        """取消上传"""
```

### 服务器API

#### 端点

```
POST /api/v1/sessions/upload
```

#### 请求头

| 头部 | 必需 | 说明 |
|------|------|------|
| Content-Type | 是 | application/json |
| Content-Encoding | 否 | gzip（推荐） |
| Authorization | 是 | Bearer <token> |
| User-Agent | 否 | 客户端标识 |

#### 请求体

参见[数据格式](#数据格式)章节

#### 响应

| 状态码 | 说明 |
|--------|------|
| 200 | 上传成功 |
| 400 | 请求格式错误 |
| 401 | 认证失败 |
| 500 | 服务器错误 |

---

## 故障排除

### 常见问题

#### 1. 连接超时

**症状**：上传时提示"Connection timed out"

**原因**：
- 服务器未启动
- 防火墙阻止
- 网络不通

**解决方案**：

```bash
# 1. 检查服务器是否运行
ps aux | grep server_receiver

# 2. 检查端口是否监听
ss -tuln | grep 8080

# 3. 测试网络连通性
ping 172.19.46.244
telnet 172.19.46.244 8080

# 4. 检查防火墙
sudo ufw status
```

#### 2. 认证失败

**症状**：上传时提示"401 Unauthorized"

**原因**：
- API密钥错误
- 令牌格式错误

**解决方案**：

```python
# 检查配置文件
cat data/gui_settings.json

# 确保配置正确
{
  "server_url": "http://172.19.46.244:8080/api/v1/sessions/upload",
  "api_key": "test-api-key-12345"
}
```

#### 3. 数据库锁定

**症状**：提示"database is locked"

**原因**：
- 多个进程同时访问数据库

**解决方案**：

```python
# 使用WAL模式
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA journal_mode=WAL")
```

#### 4. 内存不足

**症状**：上传大文件时程序崩溃

**解决方案**：

```python
# 使用流式上传
def upload_session_streaming(self, session_id: int):
    """分块上传，减少内存占用"""
    chunk_size = 100
    # ... 实现分块上传
```

### 调试技巧

#### 启用详细日志

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### 测试上传

```bash
# 使用测试脚本
cd test/
python3 test_gui_upload.py

# 查看详细输出
python3 -v test_gui_upload.py
```

#### 查看服务器日志

```bash
# 查看服务器输出
tail -f ~/fitness-server/server.log

# 查看数据库内容
cd ~/fitness-server
sqlite3 server_data.db "SELECT * FROM uploaded_sessions;"
```

---

## 附录

### 术语表

| 术语 | 说明 |
|------|------|
| **Session** | 一次训练会话，包含开始时间、结束时间、总帧数、总深蹲数 |
| **Record** | 单条训练记录，包含时间戳、膝关节角度、状态等 |
| **gzip** | 数据压缩算法，可减少约75%的数据量 |
| **Bearer Token** | HTTP认证令牌，用于API访问授权 |

### 参考资料

- [Python urllib官方文档](https://docs.python.org/3/library/urllib.request.html)
- [Python gzip官方文档](https://docs.python.org/3/library/gzip.html)
- [HTTP/1.1规范](https://www.rfc-editor.org/rfc/rfc7231)
- [JSON规范](https://www.json.org/)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)

### 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-03-20 | 初始版本，支持基本上传功能 |

---

**文档维护者**: Fitness Pose Validator Team  
**最后更新**: 2026-03-20
