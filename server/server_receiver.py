"""
健身数据接收服务器

使用Python标准库实现的轻量级HTTP服务器，
专为嵌入式环境设计，零第三方依赖。

功能：
- 接收客户端上传的训练数据
- 数据验证和存储
- 简单的认证机制
- 数据大屏 API
- LLM 分析 API
"""

import gzip
import json
import sqlite3
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent))

from api.dashboard import DashboardAPIHandler
from api.llm import LLMAPIHandler


class FitnessDataReceiver:
    """
    健身数据接收器
    
    负责接收、验证和存储客户端上传的训练数据。
    """
    
    def __init__(self, db_path: Path = None):
        """
        初始化数据接收器
        
        Args:
            db_path: 服务器端数据库路径
        """
        self.db_path = db_path or Path("server_data.db")
        self._init_database()
    
    def _init_database(self):
        """初始化服务器端数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 客户端设备表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id TEXT NOT NULL,
                version TEXT,
                platform TEXT,
                first_seen TEXT,
                last_seen TEXT
            )
        """)
        
        # 上传会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploaded_sessions (
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
            )
        """)
        
        # 训练记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploaded_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TEXT,
                left_angle REAL,
                right_angle REAL,
                avg_angle REAL,
                state TEXT,
                rep_count INTEGER,
                FOREIGN KEY (session_id) REFERENCES uploaded_sessions(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def process_upload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理上传的数据
        
        Args:
            data: 客户端上传的JSON数据
            
        Returns:
            dict: 处理结果
        """
        try:
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
                    "records_stored": records_count,
                    "upload_time": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_code": "PROCESSING_ERROR",
                "message": str(e)
            }
    
    def _validate_data(self, data: Dict[str, Any]):
        """验证上传数据格式"""
        required_fields = ["version", "session", "records"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(data.get("records"), list):
            raise ValueError("Records must be a list")
    
    def _save_client(self, client_info: Dict[str, Any]) -> int:
        """保存或更新客户端信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        app_id = client_info.get("app_id", "unknown")
        version = client_info.get("version", "")
        platform = json.dumps(client_info.get("platform", {}))
        now = datetime.now().isoformat()
        
        # 检查是否已存在
        cursor.execute("SELECT id FROM clients WHERE app_id = ?", (app_id,))
        row = cursor.fetchone()
        
        if row:
            client_id = row[0]
            cursor.execute(
                "UPDATE clients SET version=?, platform=?, last_seen=? WHERE id=?",
                (version, platform, now, client_id)
            )
        else:
            cursor.execute(
                "INSERT INTO clients (app_id, version, platform, first_seen, last_seen) VALUES (?, ?, ?, ?, ?)",
                (app_id, version, platform, now, now)
            )
            client_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return client_id
    
    def _save_session(self, client_id: int, data: Dict[str, Any]) -> int:
        """保存会话数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        session = data.get("session", {})
        
        cursor.execute(
            """
            INSERT INTO uploaded_sessions 
            (client_id, client_session_id, start_time, end_time, total_frames, total_squats, upload_time, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                session.get("id"),
                session.get("start_time"),
                session.get("end_time"),
                session.get("total_frames", 0),
                session.get("total_squats", 0),
                datetime.now().isoformat(),
                json.dumps(data, ensure_ascii=False)
            )
        )
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def _save_records(self, session_id: int, records: list) -> int:
        """保存训练记录"""
        if not records:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for record in records:
            cursor.execute(
                """
                INSERT INTO uploaded_records 
                (session_id, timestamp, left_angle, right_angle, avg_angle, state, rep_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    record.get("timestamp"),
                    record.get("left_angle"),
                    record.get("right_angle"),
                    record.get("avg_angle"),
                    record.get("state"),
                    record.get("rep_count", 0)
                )
            )
        
        conn.commit()
        conn.close()
        return len(records)


class FitnessHTTPHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
    receiver = FitnessDataReceiver()
    dashboard_handler = DashboardAPIHandler()
    llm_handler = LLMAPIHandler()
    API_KEY = "test-api-key-12345"
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.startswith("/api/v1/dashboard/"):
            if not self.dashboard_handler.handle_request(self, self.path, "GET"):
                self._send_error(404, "Dashboard endpoint not found")
        elif parsed_path.path.startswith("/api/v1/llm/"):
            if not self.llm_handler.handle_request(self, self.path, "GET"):
                self._send_error(404, "LLM endpoint not found")
        else:
            self._send_error(404, "Endpoint not found")
    
    def do_POST(self):
        """处理 POST 请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/api/v1/sessions/upload":
            self._handle_upload()
        elif parsed_path.path.startswith("/api/v1/llm/"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            if not self.llm_handler.handle_request(self, self.path, "POST", body):
                self._send_error(404, "LLM endpoint not found")
        else:
            self._send_error(404, "Endpoint not found")
    
    def _handle_upload(self):
        """处理数据上传"""
        try:
            # 1. 验证认证
            auth_header = self.headers.get("Authorization", "")
            if not self._verify_auth(auth_header):
                self._send_json_response(401, {
                    "status": "error",
                    "error_code": "UNAUTHORIZED",
                    "message": "Invalid or missing authentication"
                })
                return
            
            # 2. 读取请求体
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self._send_json_response(400, {
                    "status": "error",
                    "error_code": "EMPTY_BODY",
                    "message": "Request body is empty"
                })
                return
            
            body = self.rfile.read(content_length)
            
            # 3. 解压（如果压缩）
            if self.headers.get("Content-Encoding") == "gzip":
                body = gzip.decompress(body)
            
            # 4. 解析JSON
            try:
                data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError as e:
                self._send_json_response(400, {
                    "status": "error",
                    "error_code": "INVALID_JSON",
                    "message": f"Invalid JSON: {e}"
                })
                return
            
            # 5. 处理数据
            result = self.receiver.process_upload(data)
            
            # 6. 返回响应
            if result["status"] == "success":
                self._send_json_response(200, result)
            else:
                self._send_json_response(500, result)
                
        except Exception as e:
            self._send_json_response(500, {
                "status": "error",
                "error_code": "SERVER_ERROR",
                "message": str(e)
            })
    
    def _verify_auth(self, auth_header: str) -> bool:
        """验证认证令牌"""
        if not auth_header.startswith("Bearer "):
            return False
        
        token = auth_header[7:]  # 移除 "Bearer " 前缀
        return token == self.API_KEY
    
    def _send_json_response(self, status_code: int, data: Dict[str, Any]):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        
        response = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.wfile.write(response)
    
    def _send_error(self, status_code: int, message: str):
        """发送错误响应"""
        self._send_json_response(status_code, {
            "status": "error",
            "message": message
        })
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().isoformat()}] {format % args}")


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """启动服务器"""
    server = HTTPServer((host, port), FitnessHTTPHandler)
    
    print("=" * 60)
    print("Fitness Data Server v2.0")
    print("=" * 60)
    print(f"监听地址: {host}:{port}")
    print()
    print("API 端点:")
    print(f"  数据上传:    POST  http://{host}:{port}/api/v1/sessions/upload")
    print(f"  概览统计:    GET   http://{host}:{port}/api/v1/dashboard/overview")
    print(f"  趋势数据:    GET   http://{host}:{port}/api/v1/dashboard/trend")
    print(f"  分布数据:    GET   http://{host}:{port}/api/v1/dashboard/distribution")
    print(f"  热力图:      GET   http://{host}:{port}/api/v1/dashboard/heatmap")
    print(f"  雷达图:      GET   http://{host}:{port}/api/v1/dashboard/radar")
    print(f"  最佳记录:    GET   http://{host}:{port}/api/v1/dashboard/best-records")
    print(f"  最近会话:    GET   http://{host}:{port}/api/v1/dashboard/recent-sessions")
    print(f"  LLM 分析:    POST  http://{host}:{port}/api/v1/llm/analyze")
    print(f"  分析状态:    GET   http://{host}:{port}/api/v1/llm/status/{{request_id}}")
    print(f"  分析类型:    GET   http://{host}:{port}/api/v1/llm/types")
    print()
    print(f"API密钥: {FitnessHTTPHandler.API_KEY}")
    print("=" * 60)
    print("\n按 Ctrl+C 停止服务器\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.server_close()


if __name__ == "__main__":
    run_server()
