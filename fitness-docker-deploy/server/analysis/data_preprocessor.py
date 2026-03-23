"""
数据预处理模块

将数据库中的训练数据转换为 LLM 可理解的格式。
"""

import sqlite3
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .llm_analyzer import AnalysisType


class DataPreprocessor:
    """数据预处理器"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化预处理器
        
        Args:
            db_path: 数据库路径
        """
        import os
        if db_path:
            self.db_path = db_path
        else:
            env_path = os.environ.get("SERVER_DB_PATH")
            self.db_path = Path(env_path) if env_path else Path("server_data.db")
    
    def prepare(
        self,
        session_ids: List[int],
        analysis_type: AnalysisType,
    ) -> str:
        """
        准备训练数据
        
        Args:
            session_ids: 会话 ID 列表
            analysis_type: 分析类型
            
        Returns:
            str: 格式化后的训练数据文本
        """
        if analysis_type == AnalysisType.SESSION:
            return self._prepare_session_data(session_ids)
        elif analysis_type == AnalysisType.TREND:
            return self._prepare_trend_data(session_ids)
        elif analysis_type == AnalysisType.COMPARISON:
            return self._prepare_comparison_data(session_ids)
        elif analysis_type == AnalysisType.ADVICE:
            return self._prepare_advice_data(session_ids)
        elif analysis_type == AnalysisType.GOAL:
            return self._prepare_goal_data(session_ids)
        else:
            raise ValueError(f"未知的分析类型: {analysis_type}")
    
    def _prepare_session_data(self, session_ids: List[int]) -> str:
        """准备单次训练数据"""
        sessions_text = []
        
        for sid in session_ids:
            session = self._get_session(sid)
            records = self._get_records(sid)
            
            if not session or not records:
                continue
            
            # 计算统计指标
            stats = self._calculate_statistics(records)
            
            sessions_text.append(f"""
训练会话 #{sid}:
- 时间: {session['start_time']} 至 {session['end_time']}
- 总深蹲次数: {session['total_squats']}
- 总帧数: {session['total_frames']}
- 平均下蹲角度: {stats['avg_angle']:.1f}°
- 角度范围: {stats['min_angle']:.1f}° ~ {stats['max_angle']:.1f}°
- 角度标准差: {stats['angle_std']:.2f} (越低越稳定)
- 左右对称性评分: {stats['symmetry_score']:.1f}分
- 训练时长: {stats['duration_seconds']:.0f}秒
""")
        
        return "\n".join(sessions_text)
    
    def _prepare_trend_data(self, session_ids: List[int]) -> str:
        """准备趋势数据"""
        sessions_data = []
        
        for sid in sorted(session_ids):
            session = self._get_session(sid)
            records = self._get_records(sid)
            
            if session and records:
                stats = self._calculate_statistics(records)
                sessions_data.append({
                    "date": session['start_time'][:10],
                    "squats": session['total_squats'],
                    "avg_angle": stats['avg_angle'],
                    "symmetry": stats['symmetry_score'],
                })
        
        # 按日期排序
        sessions_data.sort(key=lambda x: x['date'])
        
        # 格式化为文本
        lines = ["训练趋势数据 (按时间顺序):"]
        for i, data in enumerate(sessions_data):
            lines.append(
                f"{i+1}. {data['date']}: "
                f"深蹲{data['squats']}次, "
                f"角度{data['avg_angle']:.1f}°, "
                f"对称性{data['symmetry']:.0f}分"
            )
        
        return "\n".join(lines)
    
    def _prepare_comparison_data(self, session_ids: List[int]) -> str:
        """准备对比数据"""
        if len(session_ids) < 2:
            return "对比分析需要至少2个训练会话"
        
        sessions_text = []
        for i, sid in enumerate(session_ids[:2]):  # 最多对比2个
            session = self._get_session(sid)
            records = self._get_records(sid)
            
            if session and records:
                stats = self._calculate_statistics(records)
                label = "本次训练" if i == 0 else "上次训练"
                sessions_text.append(f"""
{label} (会话 #{sid}):
- 时间: {session['start_time']}
- 深蹲次数: {session['total_squats']}
- 平均角度: {stats['avg_angle']:.1f}°
- 对称性: {stats['symmetry_score']:.1f}分
- 稳定性: {stats['angle_std']:.2f}
""")
        
        return "\n".join(sessions_text)
    
    def _prepare_advice_data(self, session_ids: List[int]) -> str:
        """准备个性化建议数据 (最近10个会话)"""
        recent_ids = sorted(session_ids)[-10:]  # 最近10个
        
        all_stats = []
        for sid in recent_ids:
            session = self._get_session(sid)
            records = self._get_records(sid)
            
            if session and records:
                stats = self._calculate_statistics(records)
                stats['date'] = session['start_time'][:10]
                stats['squats'] = session['total_squats']
                all_stats.append(stats)
        
        if not all_stats:
            return "暂无训练数据"
        
        # 计算整体统计
        avg_squats = statistics.mean([s['squats'] for s in all_stats])
        avg_angle = statistics.mean([s['avg_angle'] for s in all_stats])
        avg_symmetry = statistics.mean([s['symmetry_score'] for s in all_stats])
        
        return f"""
用户训练历史摘要 (最近{len(all_stats)}次训练):
- 平均每次深蹲: {avg_squats:.0f}次
- 平均下蹲角度: {avg_angle:.1f}° (标准值: 90°)
- 平均对称性: {avg_symmetry:.1f}分
- 训练频率: {len(all_stats)}次

详细记录:
{chr(10).join(f"- {s['date']}: {s['squats']}次, 角度{s['avg_angle']:.1f}°" for s in all_stats)}
"""
    
    def _prepare_goal_data(self, session_ids: List[int]) -> str:
        """准备目标设定数据"""
        # 复用 advice 数据准备逻辑
        return self._prepare_advice_data(session_ids)
    
    def _get_session(self, session_id: int) -> Optional[Dict]:
        """获取会话信息"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM uploaded_sessions WHERE id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def _get_records(self, session_id: int) -> List[Dict]:
        """获取训练记录"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM uploaded_records WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def _calculate_statistics(self, records: List[Dict]) -> Dict[str, Any]:
        """计算统计指标"""
        angles = [r['avg_angle'] for r in records if r['avg_angle'] is not None]
        left_angles = [r['left_angle'] for r in records if r['left_angle'] is not None]
        right_angles = [r['right_angle'] for r in records if r['right_angle'] is not None]
        
        if not angles:
            return {
                "avg_angle": 0,
                "min_angle": 0,
                "max_angle": 0,
                "angle_std": 0,
                "symmetry_score": 0,
                "duration_seconds": 0,
            }
        
        # 计算左右对称性 (角度差的平均值)
        if left_angles and right_angles:
            angle_diffs = [abs(l - r) for l, r in zip(left_angles, right_angles)]
            avg_diff = statistics.mean(angle_diffs)
            symmetry_score = max(0, 100 - avg_diff * 2)  # 差异越小分数越高
        else:
            symmetry_score = 0
        
        # 计算时长
        if len(records) >= 2:
            try:
                start = datetime.fromisoformat(records[0]['timestamp'])
                end = datetime.fromisoformat(records[-1]['timestamp'])
                duration = (end - start).total_seconds()
            except:
                duration = 0
        else:
            duration = 0
        
        return {
            "avg_angle": statistics.mean(angles),
            "min_angle": min(angles),
            "max_angle": max(angles),
            "angle_std": statistics.stdev(angles) if len(angles) > 1 else 0,
            "symmetry_score": symmetry_score,
            "duration_seconds": duration,
        }