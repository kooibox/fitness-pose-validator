#!/usr/bin/env python3
"""
测试完整的上传流程

1. 启动服务器
2. 上传数据
3. 验证结果
"""

import gzip
import json
import sqlite3
import sys
import urllib.request
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_upload(session_id: int = 44):
    """测试上传单个会话"""
    print(f"\n{'='*60}")
    print(f"测试上传会话 {session_id}")
    print(f"{'='*60}")
    
    try:
        # 1. 从SQLite读取数据
        db_path = project_root / "data" / "fitness_data.db"
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
        
        print(f"✓ 读取数据成功: {len(records)} 条记录")
        
        # 2. 构建上传数据
        upload_data = {
            "version": "1.0",
            "export_time": "2026-03-20T14:00:00",
            "client": {
                "app_id": "fitness-pose-validator",
                "version": "2.0.0",
                "platform": {
                    "system": "Linux",
                    "machine": "x86_64",
                    "python_version": "3.12.3"
                }
            },
            "session": session,
            "records": records,
            "summary": {
                "total_records": len(records),
                "total_squats": session["total_squats"]
            }
        }
        
        # 3. 序列化为JSON
        json_bytes = json.dumps(upload_data, ensure_ascii=False).encode('utf-8')
        print(f"✓ JSON序列化完成: {len(json_bytes)} bytes")
        
        # 4. gzip压缩
        compressed = gzip.compress(json_bytes)
        print(f"✓ gzip压缩完成: {len(compressed)} bytes (压缩率: {len(compressed)/len(json_bytes)*100:.1f}%)")
        
        # 5. HTTP POST上传
        server_url = "http://localhost:8080/api/v1/sessions/upload"
        api_key = "test-api-key-12345"
        
        request = urllib.request.Request(
            server_url,
            data=compressed,
            headers={
                "Content-Type": "application/json",
                "Content-Encoding": "gzip",
                "Authorization": f"Bearer {api_key}"
            },
            method="POST"
        )
        
        print(f"✓ 发送POST请求到 {server_url}")
        
        with urllib.request.urlopen(request, timeout=30) as response:
            response_data = response.read().decode('utf-8')
            result = json.loads(response_data)
        
        print(f"✓ 上传成功!")
        print(f"  服务器响应: {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ 上传失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_server_storage():
    """验证服务器端存储"""
    print(f"\n{'='*60}")
    print(f"验证服务器端存储")
    print(f"{'='*60}")
    
    try:
        db_path = project_root / "server_data.db"
        if not db_path.exists():
            print("✗ 服务器数据库不存在")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查客户端表
        cursor.execute("SELECT COUNT(*) FROM clients")
        client_count = cursor.fetchone()[0]
        print(f"✓ 客户端数量: {client_count}")
        
        # 检查会话表
        cursor.execute("SELECT COUNT(*) FROM uploaded_sessions")
        session_count = cursor.fetchone()[0]
        print(f"✓ 上传会话数量: {session_count}")
        
        # 检查记录表
        cursor.execute("SELECT COUNT(*) FROM uploaded_records")
        record_count = cursor.fetchone()[0]
        print(f"✓ 训练记录数量: {record_count}")
        
        # 显示最近的会话
        cursor.execute(
            """
            SELECT s.id, s.client_session_id, s.total_squats, s.upload_time, c.app_id
            FROM uploaded_sessions s
            JOIN clients c ON s.client_id = c.id
            ORDER BY s.id DESC
            LIMIT 5
            """
        )
        sessions = cursor.fetchall()
        
        if sessions:
            print(f"\n最近上传的会话:")
            print(f"{'服务器ID':<10} {'客户端ID':<10} {'深蹲次数':<10} {'上传时间':<26} {'客户端'}")
            print("-" * 80)
            for s in sessions:
                print(f"{s[0]:<10} {s[1]:<10} {s[2]:<10} {s[3]:<26} {s[4]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        return False


def main():
    print("=" * 60)
    print("测试完整上传流程")
    print("=" * 60)
    
    # 测试上传
    if test_upload(44):
        # 验证存储
        verify_server_storage()
    else:
        print("\n上传测试失败")


if __name__ == "__main__":
    main()
