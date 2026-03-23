"""
数据导出模块

提供训练数据的导出和上传功能。
使用Python标准库实现，零第三方依赖，支持嵌入式环境移植。

功能：
- 导出训练数据为JSON格式
- 支持gzip压缩
- HTTP上传到远程服务器
- 断点续传支持（待实现）
"""

import gzip
import json
import urllib.request
import urllib.error
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import Config
from src.database import Database, Session, SquatRecord


class DataExporter:
    """
    数据导出器
    
    负责将本地训练数据导出为标准格式并上传到服务器。
    设计考虑嵌入式环境移植，仅使用Python标准库。
    """
    
    # 应用元数据
    APP_ID = "fitness-pose-validator"
    CLIENT_VERSION = "2.0.0"
    DATA_FORMAT_VERSION = "1.0"
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化数据导出器
        
        Args:
            db_path: 数据库路径，默认使用配置中的路径
        """
        self.db = Database(db_path)
    
    def export_session(self, session_id: int, include_records: bool = True) -> Dict[str, Any]:
        """
        导出单个训练会话数据
        
        Args:
            session_id: 会话ID
            include_records: 是否包含逐帧记录
            
        Returns:
            dict: 标准化的会话数据
        """
        # 获取会话信息
        session = self.db.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # 构建导出数据
        export_data = {
            "version": self.DATA_FORMAT_VERSION,
            "export_time": datetime.now().isoformat(),
            "client": {
                "app_id": self.APP_ID,
                "version": self.CLIENT_VERSION,
                "platform": self._get_platform_info()
            },
            "session": asdict(session),
            "records": [],
            "summary": {}
        }
        
        # 获取训练记录
        if include_records:
            records = self._get_session_records(session_id)
            export_data["records"] = [asdict(r) for r in records]
        
        # 生成摘要统计
        export_data["summary"] = self._generate_summary(session)
        
        return export_data
    
    def export_all_sessions(self, limit: int = 10) -> Dict[str, Any]:
        """
        导出多个训练会话
        
        Args:
            limit: 最大会话数量
            
        Returns:
            dict: 包含所有会话的数据
        """
        sessions = self.db.get_recent_sessions(limit)
        
        export_data = {
            "version": self.DATA_FORMAT_VERSION,
            "export_time": datetime.now().isoformat(),
            "client": {
                "app_id": self.APP_ID,
                "version": self.CLIENT_VERSION,
                "platform": self._get_platform_info()
            },
            "sessions": []
        }
        
        for session in sessions:
            session_data = self.export_session(session.id, include_records=True)
            export_data["sessions"].append(session_data)
        
        return export_data
    
    def export_to_json(
        self, 
        session_id: int, 
        output_path: Optional[Path] = None,
        compress: bool = False,
        indent: int = 2
    ) -> Path:
        """
        导出会话数据为JSON文件
        
        Args:
            session_id: 会话ID
            output_path: 输出路径，默认为 data/export/session_{id}.json
            compress: 是否使用gzip压缩
            indent: JSON缩进
            
        Returns:
            Path: 输出文件路径
        """
        # 导出数据
        data = self.export_session(session_id)
        
        # 确定输出路径
        if output_path is None:
            export_dir = Config.PROJECT_ROOT / "data" / "export"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            suffix = ".json.gz" if compress else ".json"
            output_path = export_dir / f"session_{session_id}{suffix}"
        
        # 序列化为JSON
        json_str = json.dumps(data, ensure_ascii=False, indent=indent)
        
        # 写入文件
        if compress:
            with gzip.open(output_path, 'wt', encoding='utf-8') as f:
                f.write(json_str)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return output_path
    
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
            
        Raises:
            urllib.error.URLError: 网络错误
            urllib.error.HTTPError: HTTP错误
        """
        # 导出数据
        data = self.export_session(session_id)
        json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        # 压缩数据
        if compress:
            body = gzip.compress(json_bytes)
            content_encoding = "gzip"
        else:
            body = json_bytes
            content_encoding = None
        
        # 构建请求
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"{self.APP_ID}/{self.CLIENT_VERSION}"
        }
        
        if content_encoding:
            headers["Content-Encoding"] = content_encoding
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        # 发送请求
        request = urllib.request.Request(
            server_url,
            data=body,
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ""
            raise urllib.error.HTTPError(
                e.url, e.code, 
                f"Upload failed: {e.reason}. Response: {error_body}", 
                e.headers, e.fp
            )
    
    def _get_session_records(self, session_id: int) -> List[SquatRecord]:
        """获取会话的所有训练记录"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, session_id, timestamp, left_angle, right_angle, 
                       avg_angle, state, rep_count
                FROM squat_records 
                WHERE session_id = ?
                ORDER BY timestamp
                """,
                (session_id,)
            )
            return [SquatRecord(*row) for row in cursor.fetchall()]
    
    def _generate_summary(self, session: Session) -> Dict[str, Any]:
        """生成会话摘要统计"""
        records = self._get_session_records(session.id)
        
        if not records:
            return {"error": "No records found"}
        
        angles = [r.avg_angle for r in records if r.avg_angle is not None]
        states = [r.state for r in records if r.state]
        
        if not angles:
            return {"error": "No angle data"}
        
        return {
            "total_records": len(records),
            "total_squats": session.total_squats,
            "avg_angle": sum(angles) / len(angles),
            "min_angle": min(angles),
            "max_angle": max(angles),
            "standing_count": states.count("STANDING"),
            "squatting_count": states.count("SQUATTING"),
            "duration_seconds": self._calculate_duration(session)
        }
    
    def _calculate_duration(self, session: Session) -> Optional[float]:
        """计算会话持续时间（秒）"""
        if not session.end_time:
            return None
        
        try:
            start = datetime.fromisoformat(session.start_time)
            end = datetime.fromisoformat(session.end_time)
            return (end - start).total_seconds()
        except (ValueError, TypeError):
            return None
    
    def _get_platform_info(self) -> Dict[str, str]:
        """获取平台信息"""
        import platform
        import sys
        
        return {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": sys.version.split()[0]
        }


class DataUploader:
    """
    数据上传器（轻量级版本）
    
    专为嵌入式环境设计，最小化内存使用。
    """
    
    def __init__(self, server_url: str, auth_token: Optional[str] = None):
        """
        初始化上传器
        
        Args:
            server_url: 服务器URL
            auth_token: 认证令牌
        """
        self.server_url = server_url
        self.auth_token = auth_token
        self.exporter = DataExporter()
    
    def upload(self, session_id: int, compress: bool = True) -> bool:
        """
        上传单个会话
        
        Args:
            session_id: 会话ID
            compress: 是否压缩
            
        Returns:
            bool: 是否上传成功
        """
        try:
            result = self.exporter.upload_session(
                session_id=session_id,
                server_url=self.server_url,
                auth_token=self.auth_token,
                compress=compress
            )
            return result.get("status") == "success"
        except Exception as e:
            print(f"Upload failed: {e}")
            return False
    
    def upload_batch(self, session_ids: List[int]) -> Dict[str, int]:
        """
        批量上传会话
        
        Args:
            session_ids: 会话ID列表
            
        Returns:
            dict: 统计结果 {"success": int, "failed": int}
        """
        results = {"success": 0, "failed": 0}
        
        for session_id in session_ids:
            if self.upload(session_id):
                results["success"] += 1
            else:
                results["failed"] += 1
        
        return results
