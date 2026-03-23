"""
Windows端上传脚本

使用方法：
    python upload_to_wsl.py              # 上传最近的会话
    python upload_to_wsl.py --session 44 # 上传指定会话
    python upload_to_wsl.py --list       # 列出所有会话
"""

import gzip
import json
import sqlite3
import sys
import urllib.request
from pathlib import Path


# WSL服务器配置
WSL_SERVER_URL = "http://172.19.46.244:8080/api/v1/sessions/upload"
API_KEY = "test-api-key-12345"


def upload_session(session_id: int):
    """上传单个会话到WSL服务器"""
    print(f"\n{'='*60}")
    print(f"上传会话 {session_id} 到WSL服务器")
    print(f"{'='*60}")
    
    try:
        # 1. 从本地SQLite读取数据
        db_path = Path(__file__).parent / "data" / "fitness_data.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取会话信息
        cursor.execute(
            "SELECT id, start_time, end_time, total_frames, total_squats FROM sessions WHERE id = ?",
            (session_id,)
        )
        session_row = cursor.fetchone()
        if not session_row:
            print(f"✗ 会话 {session_id} 不存在")
            return False
        
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
        
        print(f"✓ 读取本地数据: {len(records)} 条记录")
        
        # 2. 构建上传数据
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
        
        print(f"✓ 数据压缩: {len(json_bytes)} → {len(compressed)} bytes ({len(compressed)/len(json_bytes)*100:.1f}%)")
        
        # 4. 上传到WSL服务器
        request = urllib.request.Request(
            WSL_SERVER_URL,
            data=compressed,
            headers={
                "Content-Type": "application/json",
                "Content-Encoding": "gzip",
                "Authorization": f"Bearer {API_KEY}"
            },
            method="POST"
        )
        
        print(f"✓ 正在上传到 {WSL_SERVER_URL}")
        
        with urllib.request.urlopen(request, timeout=30) as response:
            response_data = response.read().decode('utf-8')
            result = json.loads(response_data)
        
        print(f"✓ 上传成功!")
        print(f"  服务器响应: {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ 上传失败: {e}")
        return False


def list_sessions(limit: int = 10):
    """列出本地会话"""
    db_path = Path(__file__).parent / "data" / "fitness_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, start_time, total_squats, total_frames
        FROM sessions 
        ORDER BY id DESC 
        LIMIT ?
        """,
        (limit,)
    )
    sessions = cursor.fetchall()
    conn.close()
    
    if not sessions:
        print("没有找到训练记录")
        return
    
    print(f"\n{'ID':<8} {'开始时间':<26} {'深蹲次数':<10} {'总帧数':<10}")
    print("-" * 60)
    for s in sessions:
        print(f"{s[0]:<8} {s[1]:<26} {s[2]:<10} {s[3]:<10}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="上传训练数据到WSL服务器")
    parser.add_argument("-s", "--session", type=int, help="上传指定会话ID")
    parser.add_argument("-l", "--list", action="store_true", help="列出所有会话")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Windows → WSL 数据上传工具")
    print("=" * 60)
    print(f"服务器地址: {WSL_SERVER_URL}")
    
    if args.list:
        list_sessions()
        return
    
    if args.session:
        upload_session(args.session)
        return
    
    # 默认：列出会话
    list_sessions()


if __name__ == "__main__":
    main()
