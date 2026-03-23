# -*- coding: utf-8 -*-
"""训练数据路由 - 提供数据上传和查询接口"""

import gzip
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer

from auth import get_current_user
from database import get_db
from models import SessionUpload, UploadResponse, SuccessResponse

router = APIRouter(tags=["训练数据"])
security = HTTPBearer(auto_error=False)


@router.post("/sessions/upload", response_model=UploadResponse)
async def upload_session(
    data: SessionUpload,
    user: dict = Depends(get_current_user)
):
    """
    上传训练数据（需要认证）
    
    - **version**: 数据版本
    - **client**: 客户端信息
    - **session**: 会话信息
    - **records**: 训练记录列表
    - **exercise_type**: 运动类型 (squat/pushup/lunge)
    """
    user_id = user["user_id"]
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 1. 保存或更新客户端信息
            client_info = data.client or {}
            app_id = client_info.app_id or "unknown"
            
            cursor.execute(
                "SELECT id FROM clients WHERE app_id = ?", 
                (app_id,)
            )
            row = cursor.fetchone()
            
            now = datetime.now().isoformat()
            
            if row:
                client_id = row["id"]
                cursor.execute(
                    "UPDATE clients SET version=?, platform=?, last_seen=? WHERE id=?",
                    (
                        client_info.version or "",
                        json.dumps(client_info.platform or {}),
                        now,
                        client_id
                    )
                )
            else:
                cursor.execute(
                    "INSERT INTO clients (app_id, version, platform, first_seen, last_seen) VALUES (?, ?, ?, ?, ?)",
                    (
                        app_id,
                        client_info.version or "",
                        json.dumps(client_info.platform or {}),
                        now,
                        now
                    )
                )
                client_id = cursor.lastrowid
            
            # 2. 保存会话数据
            session_info = data.session or {}
            exercise_type = data.exercise_type or "squat"
            
            cursor.execute(
                """
                INSERT INTO uploaded_sessions 
                (client_id, client_session_id, start_time, end_time, total_frames, total_squats, upload_time, raw_data, user_id, exercise_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    client_id,
                    session_info.id,
                    session_info.start_time,
                    session_info.end_time,
                    session_info.total_frames or 0,
                    session_info.total_squats or 0,
                    now,
                    json.dumps(data.model_dump(), ensure_ascii=False),
                    user_id,
                    exercise_type
                )
            )
            
            session_id = cursor.lastrowid
            
            # 3. 保存训练记录
            records_count = 0
            for record in data.records:
                cursor.execute(
                    """
                    INSERT INTO uploaded_records 
                    (session_id, timestamp, left_angle, right_angle, avg_angle, state, rep_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        record.timestamp,
                        record.left_angle,
                        record.right_angle,
                        record.avg_angle,
                        record.state,
                        record.rep_count or 0
                    )
                )
                records_count += 1
            
            conn.commit()
            
        return UploadResponse(
            status="success",
            data={
                "server_session_id": session_id,
                "records_stored": records_count,
                "upload_time": now
            }
        )
        
    except Exception as e:
        return UploadResponse(
            status="error",
            error_code="PROCESSING_ERROR",
            message=str(e)
        )


@router.get("/sessions")
async def get_sessions(
    limit: int = 20,
    offset: int = 0,
    user: dict = Depends(get_current_user)
):
    """
    获取当前用户的训练列表（需要认证）
    
    - **limit**: 返回数量限制
    - **offset**: 偏移量
    """
    user_id = user["user_id"]
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT s.id, s.client_session_id, s.start_time, s.end_time,
                   s.total_frames, s.total_squats, s.exercise_type, s.upload_time
            FROM uploaded_sessions s
            WHERE s.user_id = ?
            ORDER BY s.id DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset)
        )
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "server_session_id": row["id"],
                "client_session_id": row["client_session_id"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "total_frames": row["total_frames"],
                "total_squats": row["total_squats"],
                "exercise_type": row["exercise_type"],
                "upload_time": row["upload_time"]
            })
        
        return {"status": "success", "data": sessions}


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: int,
    user: dict = Depends(get_current_user)
):
    """获取单个训练会话详情（需要认证）"""
    user_id = user["user_id"]
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 验证会话属于当前用户
        cursor.execute(
            "SELECT * FROM uploaded_sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id)
        )
        session = cursor.fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 获取训练记录
        cursor.execute(
            "SELECT * FROM uploaded_records WHERE session_id = ? ORDER BY id",
            (session_id,)
        )
        
        records = []
        for row in cursor.fetchall():
            records.append({
                "timestamp": row["timestamp"],
                "left_angle": row["left_angle"],
                "right_angle": row["right_angle"],
                "avg_angle": row["avg_angle"],
                "state": row["state"],
                "rep_count": row["rep_count"]
            })
        
        return {
            "status": "success",
            "data": {
                "session": dict(session),
                "records": records
            }
        }