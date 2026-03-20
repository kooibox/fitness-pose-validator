#!/usr/bin/env python3
"""
测试GUI上传功能

模拟GUI上传流程，验证上传功能是否正常工作。
"""

import gzip
import json
import sqlite3
import sys
import urllib.request
import urllib.error
from pathlib import Path


def test_upload_workflow():
    """测试上传工作流程"""
    print("=" * 60)
    print("测试GUI上传功能")
    print("=" * 60)
    
    # 1. 检查配置文件
    config_file = Path(__file__).parent / "data" / "gui_settings.json"
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        print(f"✓ 配置文件存在")
        print(f"  服务器地址: {settings.get('server_url', '未配置')}")
        print(f"  API密钥: {'已配置' if settings.get('api_key') else '未配置'}")
    else:
        print("✗ 配置文件不存在，使用默认配置")
        settings = {
            "server_url": "http://172.19.46.244:8080/api/v1/sessions/upload",
            "api_key": "test-api-key-12345"
        }
    
    # 2. 检查数据库
    db_path = Path(__file__).parent / "data" / "fitness_data.db"
    if not db_path.exists():
        print("✗ 数据库文件不存在")
        return False
    
    print(f"✓ 数据库文件存在: {db_path}")
    
    # 3. 获取最近的会话
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, total_squats FROM sessions ORDER BY id DESC LIMIT 1")
    session = cursor.fetchone()
    conn.close()
    
    if not session:
        print("✗ 没有找到训练记录")
        return False
    
    session_id = session[0]
    print(f"✓ 找到会话: ID={session_id}, 深蹲次数={session[1]}")
    
    # 4. 模拟上传
    server_url = settings.get("server_url", "").strip()
    api_key = settings.get("api_key", "").strip()
    
    if not server_url:
        print("✗ 服务器地址未配置")
        return False
    
    print(f"✓ 服务器地址: {server_url}")
    
    # 5. 读取数据
    print(f"\n正在准备上传会话 {session_id}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取会话信息
    cursor.execute(
        "SELECT id, start_time, end_time, total_frames, total_squats FROM sessions WHERE id = ?",
        (session_id,)
    )
    session_row = cursor.fetchone()
    
    session_data = {
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
    
    print(f"✓ 读取数据完成: {len(records)} 条记录")
    
    # 6. 构建上传数据
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
        "session": session_data,
        "records": records,
        "summary": {
            "total_records": len(records),
            "total_squats": session_data["total_squats"]
        }
    }
    
    # 7. 序列化并压缩
    json_bytes = json.dumps(upload_data, ensure_ascii=False).encode('utf-8')
    compressed = gzip.compress(json_bytes)
    
    print(f"✓ 数据压缩: {len(json_bytes)} → {len(compressed)} bytes ({len(compressed)/len(json_bytes)*100:.1f}%)")
    
    # 8. 上传到服务器
    print(f"\n正在上传到服务器...")
    
    headers = {
        "Content-Type": "application/json",
        "Content-Encoding": "gzip",
        "User-Agent": "fitness-pose-validator/2.0.0"
    }
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    request = urllib.request.Request(
        server_url,
        data=compressed,
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_data = response.read().decode('utf-8')
            result = json.loads(response_data)
        
        print(f"✓ 上传成功!")
        print(f"  服务器响应: {result}")
        return True
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ""
        print(f"✗ 上传失败: HTTP {e.code}")
        print(f"  错误信息: {e.reason}")
        if error_body:
            print(f"  服务器响应: {error_body}")
        return False
        
    except Exception as e:
        print(f"✗ 上传失败: {e}")
        return False


def main():
    """主函数"""
    success = test_upload_workflow()
    
    print("\n" + "=" * 60)
    if success:
        print("测试通过 ✓")
    else:
        print("测试失败 ✗")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
