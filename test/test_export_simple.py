#!/usr/bin/env python3
"""
数据导出测试脚本（简化版）

直接测试数据导出功能，避免导入不必要的依赖。
使用方法：
    python3 test_export_simple.py              # 测试导出最近会话
    python3 test_export_simple.py --session 1  # 测试导出指定会话
"""

import argparse
import gzip
import json
import sys
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# 数据类定义（避免导入src模块）
@dataclass
class Session:
    id: int
    start_time: str
    end_time: Optional[str]
    total_frames: int
    total_squats: int


@dataclass
class SquatRecord:
    id: int
    session_id: int
    timestamp: str
    left_angle: float
    right_angle: float
    avg_angle: float
    state: str
    rep_count: int


class SimpleDataExporter:
    """简化版数据导出器（零依赖测试）"""
    
    APP_ID = "fitness-pose-validator"
    CLIENT_VERSION = "2.0.0"
    DATA_FORMAT_VERSION = "1.0"
    
    def __init__(self, db_path: Path = None):
        import sqlite3
        self.db_path = db_path or Path(__file__).parent / "data" / "fitness_data.db"
        self._conn = None
    
    def _get_connection(self):
        import sqlite3
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn
    
    def get_recent_sessions(self, limit: int = 10) -> List[Session]:
        """获取最近的训练会话"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, start_time, end_time, total_frames, total_squats 
            FROM sessions 
            ORDER BY id DESC 
            LIMIT ?
            """,
            (limit,)
        )
        return [Session(*row) for row in cursor.fetchall()]
    
    def get_session(self, session_id: int) -> Optional[Session]:
        """获取指定会话"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, start_time, end_time, total_frames, total_squats FROM sessions WHERE id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        return Session(*row) if row else None
    
    def get_session_records(self, session_id: int) -> List[SquatRecord]:
        """获取会话的所有训练记录"""
        conn = self._get_connection()
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
    
    def export_session(self, session_id: int) -> Dict[str, Any]:
        """导出单个会话数据"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        records = self.get_session_records(session_id)
        
        # 生成摘要
        angles = [r.avg_angle for r in records if r.avg_angle is not None]
        states = [r.state for r in records if r.state]
        
        summary = {
            "total_records": len(records),
            "total_squats": session.total_squats,
            "avg_angle": sum(angles) / len(angles) if angles else 0,
            "min_angle": min(angles) if angles else 0,
            "max_angle": max(angles) if angles else 0,
            "standing_count": states.count("STANDING"),
            "squatting_count": states.count("SQUATTING"),
        }
        
        return {
            "version": self.DATA_FORMAT_VERSION,
            "export_time": datetime.now().isoformat(),
            "client": {
                "app_id": self.APP_ID,
                "version": self.CLIENT_VERSION,
                "platform": self._get_platform_info()
            },
            "session": asdict(session),
            "records": [asdict(r) for r in records],
            "summary": summary
        }
    
    def export_to_json(
        self, 
        session_id: int, 
        output_path: Path = None,
        compress: bool = False,
        indent: int = 2
    ) -> Path:
        """导出会话数据为JSON文件"""
        data = self.export_session(session_id)
        
        if output_path is None:
            export_dir = Path(__file__).parent / "data" / "export"
            export_dir.mkdir(parents=True, exist_ok=True)
            suffix = ".json.gz" if compress else ".json"
            output_path = export_dir / f"session_{session_id}{suffix}"
        
        json_str = json.dumps(data, ensure_ascii=False, indent=indent)
        
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
        auth_token: str = None,
        compress: bool = True,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """上传会话数据到服务器"""
        data = self.export_session(session_id)
        json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        if compress:
            body = gzip.compress(json_bytes)
            content_encoding = "gzip"
        else:
            body = json_bytes
            content_encoding = None
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"{self.APP_ID}/{self.CLIENT_VERSION}"
        }
        
        if content_encoding:
            headers["Content-Encoding"] = content_encoding
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        request = urllib.request.Request(
            server_url,
            data=body,
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_data = response.read().decode('utf-8')
            return json.loads(response_data)
    
    def _get_platform_info(self) -> Dict[str, str]:
        """获取平台信息"""
        import platform
        return {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": sys.version.split()[0]
        }
    
    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None


def test_export_session(session_id: int, compress: bool = False):
    """测试导出单个会话"""
    print(f"\n{'='*60}")
    print(f"测试导出会话 {session_id}")
    print(f"{'='*60}")
    
    try:
        exporter = SimpleDataExporter()
        
        # 导出为JSON
        output_path = exporter.export_to_json(
            session_id=session_id,
            compress=compress
        )
        
        print(f"✓ 导出成功: {output_path}")
        
        # 显示文件大小
        file_size = output_path.stat().st_size
        print(f"  文件大小: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        # 验证JSON格式
        if compress:
            with gzip.open(output_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
        else:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        print(f"  会话ID: {data['session']['id']}")
        print(f"  记录数: {len(data['records'])}")
        print(f"  深蹲次数: {data['summary'].get('total_squats', 'N/A')}")
        
        exporter.close()
        return True
        
    except Exception as e:
        print(f"✗ 导出失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def list_sessions(limit: int = 10):
    """列出所有会话"""
    print(f"\n{'='*60}")
    print(f"训练会话列表 (最近 {limit} 个)")
    print(f"{'='*60}")
    
    try:
        exporter = SimpleDataExporter()
        sessions = exporter.get_recent_sessions(limit)
        
        if not sessions:
            print("没有找到训练记录")
            exporter.close()
            return
        
        print(f"\n{'ID':<8} {'开始时间':<26} {'深蹲次数':<10} {'总帧数':<10}")
        print("-" * 60)
        
        for session in sessions:
            print(f"{session.id:<8} {session.start_time:<26} {session.total_squats:<10} {session.total_frames:<10}")
        
        print(f"\n共 {len(sessions)} 个会话")
        exporter.close()
        
    except Exception as e:
        print(f"✗ 列出会话失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="数据导出测试工具")
    
    parser.add_argument("-s", "--session", type=int, help="导出指定会话ID")
    parser.add_argument("-l", "--list", action="store_true", help="列出所有会话")
    parser.add_argument("--compress", action="store_true", help="使用gzip压缩")
    
    args = parser.parse_args()
    
    if args.list:
        list_sessions()
        return
    
    if args.session:
        test_export_session(args.session, args.compress)
        return
    
    # 默认：列出会话
    list_sessions()


if __name__ == "__main__":
    main()
