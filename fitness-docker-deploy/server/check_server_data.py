#!/usr/bin/env python3
"""
WSL服务器数据查看工具

使用方法：
    python3 check_server_data.py              # 查看概览
    python3 check_server_data.py --detail     # 查看详细数据
    python3 check_server_data.py --session 1  # 查看指定会话的记录
"""

import argparse
import json
import sqlite3
from pathlib import Path


def show_overview():
    """显示数据概览"""
    db_path = Path(__file__).parent / "server_data.db"
    
    if not db_path.exists():
        print("✗ 数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("WSL服务器数据概览")
    print("=" * 60)
    
    # 客户端信息
    cursor.execute("SELECT COUNT(*) FROM clients")
    client_count = cursor.fetchone()[0]
    print(f"\n[客户端设备]")
    print(f"  数量: {client_count}")
    
    cursor.execute("SELECT app_id, version, platform, last_seen FROM clients")
    for row in cursor.fetchall():
        print(f"  - {row[0]} v{row[1]} ({row[2]}) 最后上传: {row[3]}")
    
    # 会话信息
    cursor.execute("SELECT COUNT(*) FROM uploaded_sessions")
    session_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total_squats) FROM uploaded_sessions")
    total_squats = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(total_frames) FROM uploaded_sessions")
    total_frames = cursor.fetchone()[0] or 0
    
    print(f"\n[上传会话]")
    print(f"  数量: {session_count}")
    print(f"  总深蹲次数: {total_squats}")
    print(f"  总帧数: {total_frames}")
    
    # 记录信息
    cursor.execute("SELECT COUNT(*) FROM uploaded_records")
    record_count = cursor.fetchone()[0]
    print(f"\n[训练记录]")
    print(f"  数量: {record_count}")
    
    # 最近的会话
    print(f"\n[最近上传的会话]")
    cursor.execute(
        """
        SELECT s.id, s.client_session_id, s.start_time, s.total_squats, s.upload_time
        FROM uploaded_sessions s
        ORDER BY s.id DESC
        LIMIT 5
        """
    )
    sessions = cursor.fetchall()
    
    if sessions:
        print(f"{'服务器ID':<10} {'客户端ID':<10} {'开始时间':<26} {'深蹲':<6} {'上传时间'}")
        print("-" * 80)
        for s in sessions:
            print(f"{s[0]:<10} {s[1]:<10} {s[2]:<26} {s[3]:<6} {s[4]}")
    
    conn.close()


def show_detail():
    """显示详细数据"""
    db_path = Path(__file__).parent / "server_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("WSL服务器详细数据")
    print("=" * 60)
    
    # 显示所有会话
    cursor.execute(
        """
        SELECT s.id, s.client_session_id, s.start_time, s.end_time, 
               s.total_frames, s.total_squats, c.app_id
        FROM uploaded_sessions s
        JOIN clients c ON s.client_id = c.id
        ORDER BY s.id
        """
    )
    sessions = cursor.fetchall()
    
    print(f"\n[所有上传会话]")
    for s in sessions:
        print(f"\n会话 #{s[0]} (客户端会话ID: {s[1]})")
        print(f"  客户端: {s[6]}")
        print(f"  时间: {s[2]} ~ {s[3]}")
        print(f"  帧数: {s[4]}, 深蹲: {s[5]}")
        
        # 统计该会话的记录
        cursor.execute("SELECT COUNT(*) FROM uploaded_records WHERE session_id = ?", (s[0],))
        record_count = cursor.fetchone()[0]
        print(f"  已上传记录: {record_count} 条")
    
    conn.close()


def show_session_records(session_id: int):
    """显示指定会话的记录"""
    db_path = Path(__file__).parent / "server_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取会话信息
    cursor.execute(
        "SELECT client_session_id, total_squats, upload_time FROM uploaded_sessions WHERE id = ?",
        (session_id,)
    )
    session = cursor.fetchone()
    
    if not session:
        print(f"✗ 服务器会话 {session_id} 不存在")
        conn.close()
        return
    
    print("=" * 60)
    print(f"服务器会话 {session_id} (客户端会话ID: {session[0]})")
    print(f"深蹲次数: {session[1]}, 上传时间: {session[2]}")
    print("=" * 60)
    
    # 获取记录
    cursor.execute(
        """
        SELECT timestamp, left_angle, right_angle, avg_angle, state, rep_count
        FROM uploaded_records 
        WHERE session_id = ?
        ORDER BY timestamp
        LIMIT 20
        """,
        (session_id,)
    )
    records = cursor.fetchall()
    
    print(f"\n[训练记录 (前20条)]")
    print(f"{'时间戳':<30} {'左膝角':<10} {'右膝角':<10} {'平均角':<10} {'状态':<10} {'计数'}")
    print("-" * 90)
    
    for r in records:
        print(f"{r[0]:<30} {r[1]:<10.1f} {r[2]:<10.1f} {r[3]:<10.1f} {r[4]:<10} {r[5]}")
    
    # 总记录数
    cursor.execute("SELECT COUNT(*) FROM uploaded_records WHERE session_id = ?", (session_id,))
    total = cursor.fetchone()[0]
    if total > 20:
        print(f"\n... 还有 {total - 20} 条记录")
    
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="查看WSL服务器数据")
    parser.add_argument("-d", "--detail", action="store_true", help="显示详细信息")
    parser.add_argument("-s", "--session", type=int, help="显示指定会话的记录")
    
    args = parser.parse_args()
    
    if args.detail:
        show_detail()
    elif args.session:
        show_session_records(args.session)
    else:
        show_overview()


if __name__ == "__main__":
    main()
