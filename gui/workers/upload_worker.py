"""
上传工作线程

在后台执行数据上传，避免阻塞UI。
支持 JWT 认证和运动类型标识。
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
    支持 JWT 认证和运动类型标识。
    """
    
    progress = pyqtSignal(int, int)
    status_update = pyqtSignal(str)
    upload_success = pyqtSignal(dict)
    upload_failed = pyqtSignal(str)
    auth_required = pyqtSignal()
    
    def __init__(
        self,
        session_ids: list,
        server_url: str,
        auth_token: str = "",
        exercise_type: str = "squat",
        db_path: Optional[Path] = None,
        parent=None
    ):
        super().__init__(parent)
        
        self.session_ids = session_ids
        self.server_url = server_url
        self.auth_token = auth_token
        self.exercise_type = exercise_type
        self.db_path = db_path or Path(__file__).parent.parent.parent / "data" / "fitness_data.db"
        
        self._is_cancelled = False
    
    def run(self):
        total = len(self.session_ids)
        
        if not self.auth_token:
            self.auth_required.emit()
            self.upload_failed.emit("未登录，请先登录")
            return
        
        for i, session_id in enumerate(self.session_ids):
            if self._is_cancelled:
                self.status_update.emit("上传已取消")
                return
            
            self.progress.emit(i, total)
            self.status_update.emit(f"正在上传会话 {session_id}... ({i+1}/{total})")
            
            try:
                result = self._upload_session(session_id)
                self.upload_success.emit(result)
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    self.auth_required.emit()
                    self.upload_failed.emit("登录已过期，请重新登录")
                else:
                    self.upload_failed.emit(f"会话 {session_id} 上传失败: HTTP {e.code}")
                return
            except Exception as e:
                self.upload_failed.emit(f"会话 {session_id} 上传失败: {e}")
                return
        
        self.progress.emit(total, total)
        self.status_update.emit(f"上传完成! 成功上传 {total} 个会话")
    
    def cancel(self):
        self._is_cancelled = True
    
    def _upload_session(self, session_id: int) -> dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        
        import sys
        import platform
        
        upload_data = {
            "version": "1.0",
            "client": {
                "app_id": "fitness-pose-validator",
                "version": "2.4.0",
                "platform": {
                    "system": platform.system(),
                    "machine": platform.machine(),
                    "python_version": sys.version.split()[0]
                }
            },
            "session": session,
            "records": records,
            "exercise_type": self.exercise_type
        }
        
        json_bytes = json.dumps(upload_data, ensure_ascii=False).encode('utf-8')
        compressed = gzip.compress(json_bytes)
        
        headers = {
            "Content-Type": "application/json",
            "Content-Encoding": "gzip",
            "User-Agent": "fitness-pose-validator/2.4.0",
            "Authorization": f"Bearer {self.auth_token}"
        }
        
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
