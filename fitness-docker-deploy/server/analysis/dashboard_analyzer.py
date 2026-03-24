"""
数据大屏分析器

为前端数据大屏提供各类统计数据和分析结果。
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class DashboardAnalyzer:
    """
    数据大屏分析器
    
    提供以下分析功能：
    1. 概览统计 - 总训练次数、总深蹲数、平均质量等
    2. 趋势数据 - 质量分数、深蹲次数随时间变化
    3. 分布数据 - 深度分布、状态分布
    4. 热力图数据 - 每日训练强度
    5. 雷达图数据 - 多维度能力评估
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化分析器
        
        Args:
            db_path: 数据库路径，默认使用服务器端数据库
        """
        import os
        if db_path:
            self.db_path = db_path
        else:
            env_path = os.environ.get("SERVER_DB_PATH")
            if env_path:
                self.db_path = Path(env_path)
            else:
                self.db_path = Path(__file__).parent.parent / "server_data.db"
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def get_overview_stats(self, client_id: Optional[int] = None, exercise_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取概览统计数据
        
        Args:
            client_id: 可选，指定客户端ID
            exercise_type: 可选，运动类型过滤
            
        Returns:
            dict: 概览统计
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            where_conditions = []
            params = []
            if client_id:
                where_conditions.append("s.client_id = ?")
                params.append(client_id)
            
            if exercise_type:
                where_conditions.append("s.exercise_type = ?")
                params.append(exercise_type)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # 总训练次数
            cursor.execute(f"SELECT COUNT(*) FROM uploaded_sessions s {where_clause}", params)
            total_sessions = cursor.fetchone()[0]
            
            # 总深蹲次数
            cursor.execute(f"SELECT COALESCE(SUM(s.total_squats), 0) FROM uploaded_sessions s {where_clause}", params)
            total_squats = cursor.fetchone()[0]
            
            # 总帧数
            cursor.execute(f"SELECT COALESCE(SUM(s.total_frames), 0) FROM uploaded_sessions s {where_clause}", params)
            total_frames = cursor.fetchone()[0]
            
            # 平均每次深蹲数
            avg_squats_per_session = total_squats / total_sessions if total_sessions > 0 else 0
            
            # 本周训练次数
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute(
                f"SELECT COUNT(*) FROM uploaded_sessions s {where_clause}{' AND' if where_clause else 'WHERE'} s.start_time >= ?",
                params + [week_ago]
            )
            weekly_sessions = cursor.fetchone()[0]
            
            # 本月训练次数
            month_ago = (datetime.now() - timedelta(days=30)).isoformat()
            cursor.execute(
                f"SELECT COUNT(*) FROM uploaded_sessions s {where_clause}{' AND' if where_clause else 'WHERE'} s.start_time >= ?",
                params + [month_ago]
            )
            monthly_sessions = cursor.fetchone()[0]

            
            # 计算平均训练时长（秒）
            cursor.execute(f"""
                SELECT AVG(
                    CAST((julianday(s.end_time) - julianday(s.start_time)) * 86400 AS REAL)
                )
                FROM uploaded_sessions s
                {where_clause}{' AND' if where_clause else 'WHERE'} s.end_time IS NOT NULL
            """, params)
            avg_duration = cursor.fetchone()[0] or 0
            
            # 最近一次训练时间
            cursor.execute(f"SELECT MAX(s.start_time) FROM uploaded_sessions s {where_clause}", params)
            last_training = cursor.fetchone()[0]
            
            return {
                "total_sessions": total_sessions,
                "total_squats": total_squats,
                "total_frames": total_frames,
                "avg_squats_per_session": round(avg_squats_per_session, 1),
                "avg_duration_seconds": round(avg_duration, 1),
                "weekly_sessions": weekly_sessions,
                "monthly_sessions": monthly_sessions,
                "last_training_time": last_training,
            }
        
        finally:
            conn.close()
    
    def get_trend_data(
        self,
        metric: str = "squats",
        period: str = "30d",
        client_id: Optional[int] = None,
        exercise_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取趋势数据
        
        Args:
            metric: 指标类型 ('squats', 'sessions', 'duration')
            period: 时间范围 ('7d', '30d', '90d', 'all')
            client_id: 可选，指定客户端ID
            exercise_type: 可选，运动类型过滤
            
        Returns:
            dict: 趋势数据 {"labels": [...], "values": [...]}
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if period == "7d":
                start_date = datetime.now() - timedelta(days=7)
            elif period == "30d":
                start_date = datetime.now() - timedelta(days=30)
            elif period == "90d":
                start_date = datetime.now() - timedelta(days=90)
            else:
                start_date = datetime(2020, 1, 1)
            
            where_conditions = ["s.start_time >= ?"]
            params = [start_date.isoformat()]
            
            if client_id:
                where_conditions.append("s.client_id = ?")
                params.append(client_id)
            
            if exercise_type:
                where_conditions.append("s.exercise_type = ?")
                params.append(exercise_type)
            
            where_clause = " AND ".join(where_conditions)
            
            # 按日期聚合数据
            if metric == "squats":
                cursor.execute(f"""
                    SELECT DATE(s.start_time) as date, SUM(s.total_squats) as value
                    FROM uploaded_sessions s
                    WHERE {where_clause}
                    GROUP BY DATE(s.start_time)
                    ORDER BY date
                """, params)
            elif metric == "sessions":
                cursor.execute(f"""
                    SELECT DATE(s.start_time) as date, COUNT(*) as value
                    FROM uploaded_sessions s
                    WHERE {where_clause}
                    GROUP BY DATE(s.start_time)
                    ORDER BY date
                """, params)
            elif metric == "duration":
                cursor.execute(f"""
                    SELECT DATE(s.start_time) as date,
                           SUM(CAST((julianday(s.end_time) - julianday(s.start_time)) * 86400 AS REAL)) as value
                    FROM uploaded_sessions s
                    WHERE {where_clause} AND s.end_time IS NOT NULL
                    GROUP BY DATE(s.start_time)
                    ORDER BY date
                """, params)
            else:
                return {"labels": [], "values": [], "error": f"Unknown metric: {metric}"}
            
            rows = cursor.fetchall()
            
            return {
                "labels": [row[0] for row in rows],
                "values": [row[1] for row in rows],
                "metric": metric,
                "period": period,
            }
        
        finally:
            conn.close()
    
    def get_distribution_data(
        self,
        metric: str = "depth",
        session_id: Optional[int] = None,
        client_id: Optional[int] = None,
        exercise_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取分布数据
        
        Args:
            metric: 分布类型 ('depth', 'state', 'time_of_day')
            session_id: 可选，指定会话ID
            client_id: 可选，指定客户端ID
            exercise_type: 可选，运动类型过滤
            
        Returns:
            dict: 分布数据 {"labels": [...], "values": [...]}
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if metric == "depth":
                if session_id:
                    cursor.execute("""
                        SELECT 
                            CASE
                                WHEN avg_angle < 90 THEN '深度 (<90°)'
                                WHEN avg_angle < 120 THEN '标准 (90-120°)'
                                WHEN avg_angle < 150 THEN '浅蹲 (120-150°)'
                                ELSE '站立 (>150°)'
                            END as depth_range,
                            COUNT(*) as count
                        FROM uploaded_records
                        WHERE session_id = ? AND state = 'SQUATTING'
                        GROUP BY depth_range
                    """, (session_id,))
                else:
                    where_conditions = ["r.state = 'SQUATTING'"]
                    params = []
                    
                    if exercise_type:
                        where_conditions.append("s.exercise_type = ?")
                        params.append(exercise_type)
                    
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                    
                    cursor.execute(f"""
                        SELECT 
                            CASE
                                WHEN r.avg_angle < 90 THEN '深度 (<90°)'
                                WHEN r.avg_angle < 120 THEN '标准 (90-120°)'
                                WHEN r.avg_angle < 150 THEN '浅蹲 (120-150°)'
                                ELSE '站立 (>150°)'
                            END as depth_range,
                            COUNT(*) as count
                        FROM uploaded_records r
                        JOIN uploaded_sessions s ON r.session_id = s.id
                        {where_clause}
                        GROUP BY depth_range
                    """, params)
                
                rows = cursor.fetchall()
                return {
                    "labels": [row[0] for row in rows],
                    "values": [row[1] for row in rows],
                    "metric": "depth",
                }
            
            elif metric == "state":
                # 状态分布：站立/下蹲占比
                if session_id:
                    cursor.execute("""
                        SELECT state, COUNT(*) as count
                        FROM uploaded_records
                        WHERE session_id = ?
                        GROUP BY state
                    """, (session_id,))
                else:
                    cursor.execute("""
                        SELECT r.state, COUNT(*) as count
                        FROM uploaded_records r
                        GROUP BY r.state
                    """)
                
                rows = cursor.fetchall()
                return {
                    "labels": [row[0] for row in rows],
                    "values": [row[1] for row in rows],
                    "metric": "state",
                }
            
            elif metric == "time_of_day":
                # 时段分布：按小时统计训练次数
                cursor.execute("""
                    SELECT 
                        CAST(strftime('%H', start_time) AS INTEGER) as hour,
                        COUNT(*) as count
                    FROM uploaded_sessions
                    GROUP BY hour
                    ORDER BY hour
                """)
                
                rows = cursor.fetchall()
                # 填充缺失的小时
                hours = {row[0]: row[1] for row in rows}
                labels = [f"{h:02d}:00" for h in range(24)]
                values = [hours.get(h, 0) for h in range(24)]
                
                return {
                    "labels": labels,
                    "values": values,
                    "metric": "time_of_day",
                }
            
            else:
                return {"labels": [], "values": [], "error": f"Unknown metric: {metric}"}
        
        finally:
            conn.close()
    
    def get_heatmap_data(
        self,
        period: str = "90d",
        client_id: Optional[int] = None,
        exercise_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取热力图数据（每日训练强度）
        
        Args:
            period: 时间范围 ('30d', '90d', '180d', 'all')
            client_id: 可选，指定客户端ID
            exercise_type: 可选，运动类型过滤
            
        Returns:
            dict: 热力图数据 {"data": [{"date": "...", "value": N}, ...]}
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if period == "30d":
                start_date = datetime.now() - timedelta(days=30)
            elif period == "90d":
                start_date = datetime.now() - timedelta(days=90)
            elif period == "180d":
                start_date = datetime.now() - timedelta(days=180)
            else:
                start_date = datetime(2020, 1, 1)
            
            where_conditions = ["start_time >= ?"]
            params = [start_date.isoformat()]
            
            if client_id:
                where_conditions.append("client_id = ?")
                params.append(client_id)
            
            if exercise_type:
                where_conditions.append("exercise_type = ?")
                params.append(exercise_type)
            
            where_clause = " AND ".join(where_conditions)
            
            # 按日期统计训练次数和深蹲数
            cursor.execute(f"""
                SELECT 
                    DATE(start_time) as date,
                    COUNT(*) as session_count,
                    COALESCE(SUM(total_squats), 0) as squat_count
                FROM uploaded_sessions
                WHERE {where_clause}
                GROUP BY DATE(start_time)
                ORDER BY date
            """, params)
            
            rows = cursor.fetchall()
            
            # 计算强度值（使用深蹲数作为强度指标）
            data = []
            for row in rows:
                data.append({
                    "date": row[0],
                    "sessions": row[1],
                    "squats": row[2],
                    "intensity": min(row[2] / 10, 5),  # 归一化到 0-5
                })
            
            return {
                "data": data,
                "period": period,
            }
        
        finally:
            conn.close()
    
    def get_radar_data(self, client_id: Optional[int] = None, exercise_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取雷达图数据（多维度能力评估）
        
        维度说明：
        - 深度：下蹲深度得分
        - 对称性：左右膝盖角度对称性
        - 节奏：动作节奏一致性
        - 稳定性：角度波动稳定性
        - 频率：训练规律性
        
        Args:
            client_id: 可选，指定客户端ID
            exercise_type: 可选，运动类型过滤
            
        Returns:
            dict: 雷达图数据
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            where_conditions = []
            params = []
            if client_id:
                where_conditions.append("s.client_id = ?")
                params.append(client_id)
            
            if exercise_type:
                where_conditions.append("s.exercise_type = ?")
                params.append(exercise_type)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # 获取最近10个会话的记录
            cursor.execute(f"""
                SELECT r.session_id, r.avg_angle, r.left_angle, r.right_angle, r.state
                FROM uploaded_records r
                JOIN uploaded_sessions s ON r.session_id = s.id
                {where_clause}
                ORDER BY r.session_id DESC, r.id
                LIMIT 5000
            """, params)
            
            records = cursor.fetchall()
            
            if not records:
                return {
                    "dimensions": ["深度", "对称性", "节奏", "稳定性", "频率"],
                    "values": [0, 0, 0, 0, 0],
                }
            
            # 计算各维度得分
            angles = [r[1] for r in records if r[1] is not None]
            left_angles = [r[2] for r in records if r[2] is not None]
            right_angles = [r[3] for r in records if r[3] is not None]
            
            # 深度得分：下蹲时角度越小越好
            squatting_angles = [r[1] for r in records if r[4] == "SQUATTING" and r[1] is not None]
            if squatting_angles:
                avg_squat_angle = sum(squatting_angles) / len(squatting_angles)
                depth_score = max(0, min(100, (120 - avg_squat_angle) / 30 * 100))
            else:
                depth_score = 50
            
            # 对称性得分：左右角度差异越小越好
            if left_angles and right_angles:
                asymmetry = sum(abs(l - r) for l, r in zip(left_angles, right_angles)) / len(left_angles)
                symmetry_score = max(0, min(100, 100 - asymmetry * 5))
            else:
                symmetry_score = 50
            
            # 节奏得分：角度变化的标准差
            if len(angles) > 1:
                mean_angle = sum(angles) / len(angles)
                variance = sum((a - mean_angle) ** 2 for a in angles) / len(angles)
                std_dev = variance ** 0.5
                rhythm_score = max(0, min(100, 100 - std_dev))
            else:
                rhythm_score = 50
            
            # 稳定性得分：连续帧角度变化的平滑度
            if len(angles) > 1:
                diffs = [abs(angles[i] - angles[i-1]) for i in range(1, len(angles))]
                avg_diff = sum(diffs) / len(diffs)
                stability_score = max(0, min(100, 100 - avg_diff * 2))
            else:
                stability_score = 50
            
            # 频率得分：训练规律性
            cursor.execute(f"""
                SELECT DATE(start_time) as date, COUNT(*) as count
                FROM uploaded_sessions
                {where_clause}
                GROUP BY DATE(start_time)
                ORDER BY date DESC
                LIMIT 30
            """, params)
            
            training_days = cursor.fetchall()
            if training_days:
                frequency_score = min(100, len(training_days) / 20 * 100)
            else:
                frequency_score = 0
            
            return {
                "dimensions": ["深度", "对称性", "节奏", "稳定性", "频率"],
                "values": [
                    round(depth_score, 1),
                    round(symmetry_score, 1),
                    round(rhythm_score, 1),
                    round(stability_score, 1),
                    round(frequency_score, 1),
                ],
            }
        
        finally:
            conn.close()
    
    def get_best_records(self, limit: int = 5, client_id: Optional[int] = None, exercise_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取最佳表现记录
        
        Args:
            limit: 返回数量限制
            client_id: 可选，指定客户端ID
            exercise_type: 可选，运动类型过滤
            
        Returns:
            list: 最佳记录列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            where_conditions = []
            params = []
            if client_id:
                where_conditions.append("s.client_id = ?")
                params.append(client_id)
            
            if exercise_type:
                where_conditions.append("s.exercise_type = ?")
                params.append(exercise_type)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # 按深蹲次数排序
            cursor.execute(f"""
                SELECT s.id, s.start_time, s.total_squats, s.total_frames, c.app_id
                FROM uploaded_sessions s
                JOIN clients c ON s.client_id = c.id
                {where_clause}
                ORDER BY s.total_squats DESC
                LIMIT ?
            """, params + [limit])
            
            rows = cursor.fetchall()
            
            return [
                {
                    "session_id": row[0],
                    "start_time": row[1],
                    "total_squats": row[2],
                    "total_frames": row[3],
                    "client_app_id": row[4],
                }
                for row in rows
            ]
        
        finally:
            conn.close()
    
    def get_recent_sessions(self, limit: int = 10, client_id: Optional[int] = None, exercise_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取最近的训练会话
        
        Args:
            limit: 返回数量限制
            client_id: 可选，指定客户端ID
            exercise_type: 可选，运动类型过滤
            
        Returns:
            list: 会话列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            where_conditions = []
            params = []
            if client_id:
                where_conditions.append("s.client_id = ?")
                params.append(client_id)
            
            if exercise_type:
                where_conditions.append("s.exercise_type = ?")
                params.append(exercise_type)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            cursor.execute(f"""
                SELECT s.id, s.client_session_id, s.start_time, s.end_time,
                       s.total_frames, s.total_squats, c.app_id
                FROM uploaded_sessions s
                JOIN clients c ON s.client_id = c.id
                {where_clause}
                ORDER BY s.id DESC
                LIMIT ?
            """, params + [limit])
            
            rows = cursor.fetchall()
            
            return [
                {
                    "server_session_id": row[0],
                    "client_session_id": row[1],
                    "start_time": row[2],
                    "end_time": row[3],
                    "total_frames": row[4],
                    "total_squats": row[5],
                    "client_app_id": row[6],
                }
                for row in rows
            ]
        
        finally:
            conn.close()


