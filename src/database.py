"""
数据库模块

提供训练数据的持久化存储功能。
"""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional

from src.config import Config


@dataclass
class Session:
    """训练会话数据类"""
    id: int
    start_time: str
    end_time: Optional[str]
    total_frames: int
    total_squats: int


@dataclass
class SquatRecord:
    """深蹲记录数据类"""
    id: int
    session_id: int
    timestamp: str
    left_angle: float
    right_angle: float
    avg_angle: float
    state: str
    rep_count: int


class Database:
    """
    数据库管理类
    
    负责训练数据的持久化存储，包括会话管理和深蹲记录。
    
    Attributes:
        db_path: 数据库文件路径
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化数据库连接。
        
        Args:
            db_path: 数据库文件路径，默认使用配置中的路径
        """
        self.db_path = db_path or Config.DATABASE_PATH
        self._ensure_directory()
        self._init_tables()
    
    def _ensure_directory(self) -> None:
        """确保数据库目录存在"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _init_tables(self) -> None:
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建训练会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    total_frames INTEGER DEFAULT 0,
                    total_squats INTEGER DEFAULT 0
                )
            """)
            
            # 创建深蹲记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS squat_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    left_angle REAL,
                    right_angle REAL,
                    avg_angle REAL,
                    state TEXT,
                    rep_count INTEGER,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jumping_jack_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    left_hip_angle REAL,
                    right_hip_angle REAL,
                    avg_hip_angle REAL,
                    left_shoulder_angle REAL,
                    right_shoulder_angle REAL,
                    avg_shoulder_angle REAL,
                    state TEXT,
                    rep_count INTEGER,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        获取数据库连接的上下文管理器。
        
        Yields:
            sqlite3.Connection: 数据库连接对象
        """
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def create_session(self) -> int:
        """
        创建新的训练会话。
        
        Returns:
            int: 新创建的会话ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (start_time) VALUES (?)",
                (datetime.now().isoformat(),)
            )
            conn.commit()
            session_id = cursor.lastrowid
            assert session_id is not None, "Failed to create session"
            return session_id
    
    def update_session(self, session_id: int, total_frames: int, total_squats: int) -> None:
        """
        更新训练会话摘要。
        
        Args:
            session_id: 会话ID
            total_frames: 总帧数
            total_squats: 深蹲总次数
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE sessions 
                SET end_time = ?, total_frames = ?, total_squats = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), total_frames, total_squats, session_id)
            )
            conn.commit()
    
    def insert_records(self, records: List[tuple]) -> None:
        """
        批量插入深蹲记录。

        Args:
            records: 记录元组列表，每个元组格式为
                     (session_id, timestamp, left_angle, right_angle,
                      avg_angle, state, rep_count)
        """
        if not records:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT INTO squat_records
                (session_id, timestamp, left_angle, right_angle, avg_angle, state, rep_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                records
            )
            conn.commit()

    def insert_jumping_jack_records(self, records: List[tuple]) -> None:
        """
        批量插入开合跳记录。

        Args:
            records: 记录元组列表，每个元组格式为
                     (session_id, timestamp, left_hip_angle, right_hip_angle,
                      avg_hip_angle, left_shoulder_angle, right_shoulder_angle,
                      avg_shoulder_angle, state, rep_count)
        """
        if not records:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT INTO jumping_jack_records
                (session_id, timestamp, left_hip_angle, right_hip_angle, avg_hip_angle,
                 left_shoulder_angle, right_shoulder_angle, avg_shoulder_angle, state, rep_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records
            )
            conn.commit()
    
    def get_session(self, session_id: int) -> Optional[Session]:
        """
        获取指定会话信息。
        
        Args:
            session_id: 会话ID
            
        Returns:
            Session: 会话对象，不存在则返回None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, start_time, end_time, total_frames, total_squats FROM sessions WHERE id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            if row:
                return Session(*row)
            return None
    
    def get_recent_sessions(self, limit: int = 10) -> List[Session]:
        """
        获取最近的训练会话列表。
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[Session]: 会话对象列表
        """
        with self._get_connection() as conn:
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
    
    def delete_session(self, session_id: int) -> bool:
        """删除训练会话及其所有记录。"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM squat_records WHERE session_id = ?",
                (session_id,)
            )

            cursor.execute(
                "DELETE FROM jumping_jack_records WHERE session_id = ?",
                (session_id,)
            )

            cursor.execute(
                "DELETE FROM sessions WHERE id = ?",
                (session_id,)
            )

            conn.commit()

            return cursor.rowcount > 0
    
    def delete_sessions(self, session_ids: List[int]) -> int:
        """批量删除训练会话及其所有记录。"""
        if not session_ids:
            return 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            placeholders = ','.join('?' * len(session_ids))

            cursor.execute(
                f"DELETE FROM squat_records WHERE session_id IN ({placeholders})",
                session_ids
            )

            cursor.execute(
                f"DELETE FROM jumping_jack_records WHERE session_id IN ({placeholders})",
                session_ids
            )

            cursor.execute(
                f"DELETE FROM sessions WHERE id IN ({placeholders})",
                session_ids
            )

            deleted_count = cursor.rowcount
            conn.commit()

        return deleted_count