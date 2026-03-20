"""
上传工作线程

在后台执行数据上传，避免阻塞UI。
"""

import gzip
import json
import sqlite3
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal


class UploadWorker(QThread):
    """
    上传工作线程
    
    在后台执行数据上传，通过信号报告进度和结果。
    """
    
    # 信号定义
    progress = pyqtSignal(int, int)  # 当前进度, 总数
    status_update = pyqtSignal(str)  # 状态信息
    upload_success = pyqtSignal(dict)  # 上传成功，返回服务器响应
    upload_failed = pyqtSignal(str)  # 上传失败，返回错误信息
    
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
            parent: 父对象
        """
        super().__init__(parent)
        
        self.session_ids = session_ids
        self.server_url = server_url
        self.api_key = api_key
        self.db_path = db_path or Path(__file__).parent.parent.parent / "data" / "fitness_data.db"
        
        self._is_cancelled = False
    
    def run(self):
        """执行上传任务"""
        total = len(self.session_ids)
        
        for i, session_id in enumerate(self.session_ids):
            if self._is_cancelled:
                self.status_update.emit("上传已取消")
                return
            
            self.progress.emit(i, total)
            self.status_update.emit(f"正在上传会话 {session_id}... ({i+1}/{total})")
            
            try:
                result = self._upload_session(session_id)
                self.upload_success.emit(result)
            except Exception as e:
                self.upload_failed.emit(f"会话 {session_id} 上传失败: {e}")
                return
        
        self.progress.emit(total, total)
        self.status_update.emit(f"上传完成! 成功上传 {total} 个会话")
    
    def cancel(self):
        """取消上传"""
        self._is_cancelled = True
    
    def _upload_session(self, session_id: int) -> dict:
        """
        上传单个会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            dict: 服务器响应
        """
        # 1. 从SQLite读取数据
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取会话信息
        cursor.execute(
            "SELECT id, start_time, end_time, total_frames, total_squats FROM sessions WHERE id = ?",
            (session_id,)
        )
        session_row = cursor.fetchone()
        if not session_row:
            conn.close()
            raise ValueError(f"会话 {session_id} 不存在")
        
        session = {
            "id": session_row[0],
            "start_time": session_row[1],
            "end_time": session_row[2],
            "total_frames": session_row[3],
            "total_squats": session_row[4]
        }
        
        # 获取训练记录
        cursor.execute(
            """
            SELECT timestamp, left_angle, right_angle, avg_angle, state, rep_count
            FROM squat_records 
            WHERE session_id = ?
            ORDER BY timestamp
            """,
            (session_id,)
        )
        records = [
            {
                "timestamp": row[0],
                "left_angle": row[1],
                "right_angle": row[2],
                "avg_angle": row[3],
                "state": row[4],
                "rep_count": row[5]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        # 2. 构建上传数据
        import sys
        upload_data = {
            "version": "1.0",
            "export_time": "2026-03-20T14:00:00",
            "client": {
                "app_id": "fitness-pose-validator",
                "version": "2.0.0",
                "platform": {
                    "system": "Windows",
                    "machine": "x86_64",
                    "python_version": sys.version.split()[0]
                }
            },
            "session": session,
            "records": records,
            "summary": {
                "total_records": len(records),
                "total_squats": session["total_squats"]
            }
        }
        
        # 3. 序列化并压缩
        json_bytes = json.dumps(upload_data, ensure_ascii=False).encode('utf-8')
        compressed = gzip.compress(json_bytes)
        
        # 4. 上传到服务器
        headers = {
            "Content-Type": "application/json",
            "Content-Encoding": "gzip",
            "User-Agent": "fitness-pose-validator/2.0.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        request = urllib.request.Request(
            self.server_url,
            data=compressed,
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ""
            raise urllib.error.HTTPError(
                e.url, e.code,
                f"上传失败: {e.reason}. 响应: {error_body}",
                e.headers, e.fp
            )
