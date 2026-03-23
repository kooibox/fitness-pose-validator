# -*- coding: utf-8 -*-
"""数据库初始化模块 - 使用 SQLite + 原生 SQL"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional


# 数据库路径
DB_PATH = Path(os.environ.get("SERVER_DB_PATH", Path(__file__).parent / "server_data.db"))


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 支持字典式访问
    return conn


@contextmanager
def get_db():
    """数据库连接上下文管理器"""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """初始化数据库表结构"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. 客户端设备表
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
    
    # 2. 用户表（新增）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # 3. 上传会话表
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
            user_id INTEGER,
            exercise_type TEXT DEFAULT 'squat',
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    
    # 4. 训练记录表
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
    
    # 5. 检查并添加 user_id 列（兼容旧数据库）
    cursor.execute("PRAGMA table_info(uploaded_sessions)")
    columns = [row[1] for row in cursor.fetchall()]
    if "user_id" not in columns:
        cursor.execute("ALTER TABLE uploaded_sessions ADD COLUMN user_id INTEGER")
    
    if "exercise_type" not in columns:
        cursor.execute("ALTER TABLE uploaded_sessions ADD COLUMN exercise_type TEXT DEFAULT 'squat'")
    
    # 6. 创建预置用户账号
    _create_preset_users(cursor)
    
    conn.commit()
    conn.close()
    print(f"[数据库] 初始化完成: {DB_PATH}")


def _create_preset_users(cursor):
    """创建预置用户账号"""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    preset_users = [
        ("admin", "admin123"),
        ("demo", "demo123"),
    ]
    
    for username, password in preset_users:
        # 检查用户是否已存在
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone() is None:
            password_hash = pwd_context.hash(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            print(f"[数据库] 创建预置用户: {username}")


def get_user_by_username(username: str) -> Optional[dict]:
    """根据用户名获取用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_user_by_id(user_id: int) -> Optional[dict]:
    """根据用户ID获取用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


if __name__ == "__main__":
    init_db()