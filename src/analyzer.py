"""
Training Data Analysis Module

Provides statistical analysis and visualization for training data.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure

from src.database import Database, Session, SquatRecord


@dataclass
class SquatRep:
    """Single squat repetition data"""
    rep_number: int
    start_time: str
    end_time: str
    duration_seconds: float
    min_angle: float
    max_angle: float
    angle_range: float


@dataclass
class SessionAnalysis:
    """Session analysis results"""
    session: Session
    total_records: int
    total_squats: int
    valid_count: int
    duration_seconds: float
    avg_angle: float
    min_angle: float
    max_angle: float
    angle_std: float
    standing_ratio: float
    squatting_ratio: float
    reps: List[SquatRep] = field(default_factory=list)
    quality_score: float = 0.0


class TrainingAnalyzer:
    """
    Training Data Analyzer
    
    Loads training data from database, generates statistics and visualizations.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize analyzer.
        
        Args:
            db_path: Database file path
        """
        self._db = Database(db_path)
    
    def get_session_list(self, limit: int = 10) -> List[Session]:
        """Get recent training sessions"""
        return self._db.get_recent_sessions(limit)
    
    def analyze_session(self, session_id: int) -> Optional[SessionAnalysis]:
        """
        Analyze training data for specified session.
        
        Args:
            session_id: Session ID
            
        Returns:
            SessionAnalysis: Analysis results, None if session not found
        """
        session = self._db.get_session(session_id)
        if not session:
            return None
        
        records = self._load_session_records(session_id)
        if not records:
            return None
        
        angles = [r.avg_angle for r in records]
        total_records = len(records)
        
        standing_count = sum(1 for r in records if r.state == "STANDING")
        squatting_count = sum(1 for r in records if r.state == "SQUATTING")
        
        reps = self._identify_reps(records)
        duration = self._calculate_duration(records)
        quality_score = self._calculate_quality_score(reps, angles)
        valid_count = self._calculate_valid_count(reps)
        
        return SessionAnalysis(
            session=session,
            total_records=total_records,
            total_squats=len(reps),
            valid_count=valid_count,
            duration_seconds=duration,
            avg_angle=sum(angles) / len(angles),
            min_angle=min(angles),
            max_angle=max(angles),
            angle_std=self._std_dev(angles),
            standing_ratio=standing_count / total_records,
            squatting_ratio=squatting_count / total_records,
            reps=reps,
            quality_score=quality_score,
        )
    
    def _load_session_records(self, session_id: int) -> List[SquatRecord]:
        """Load all records for a session"""
        import sqlite3
        conn = sqlite3.connect(self._db.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, session_id, timestamp, left_angle, right_angle, 
                   avg_angle, state, rep_count 
            FROM squat_records 
            WHERE session_id = ?
            ORDER BY id
            """,
            (session_id,)
        )
        records = [SquatRecord(*row) for row in cursor.fetchall()]
        conn.close()
        return records
    
    def _identify_reps(self, records: List[SquatRecord]) -> List[SquatRep]:
        """Identify individual squat repetitions from records"""
        reps = []
        rep_start = None
        rep_start_time = None
        min_angle_in_rep = 180.0
        max_angle_in_rep = 0.0
        
        for i, record in enumerate(records):
            if record.state == "SQUATTING" and rep_start is None:
                rep_start = i
                rep_start_time = record.timestamp
                min_angle_in_rep = record.avg_angle
                max_angle_in_rep = record.avg_angle
            
            if rep_start is not None:
                min_angle_in_rep = min(min_angle_in_rep, record.avg_angle)
                max_angle_in_rep = max(max_angle_in_rep, record.avg_angle)
            
            if record.state == "STANDING" and rep_start is not None and rep_start_time is not None:
                if record.rep_count > (reps[-1].rep_number if reps else 0):
                    start_dt = datetime.fromisoformat(rep_start_time)
                    end_dt = datetime.fromisoformat(record.timestamp)
                    duration = (end_dt - start_dt).total_seconds()
                    
                    reps.append(SquatRep(
                        rep_number=record.rep_count,
                        start_time=rep_start_time,
                        end_time=record.timestamp,
                        duration_seconds=duration,
                        min_angle=min_angle_in_rep,
                        max_angle=max_angle_in_rep,
                        angle_range=max_angle_in_rep - min_angle_in_rep,
                    ))
                
                rep_start = None
                min_angle_in_rep = 180.0
                max_angle_in_rep = 0.0
        
        return reps
    
    def _calculate_duration(self, records: List[SquatRecord]) -> float:
        """Calculate training duration in seconds"""
        if len(records) < 2:
            return 0.0
        
        start_dt = datetime.fromisoformat(records[0].timestamp)
        end_dt = datetime.fromisoformat(records[-1].timestamp)
        return (end_dt - start_dt).total_seconds()
    
    def _calculate_valid_count(self, reps: List[SquatRep]) -> int:
        """Calculate valid squat count based on depth threshold"""
        valid_threshold = 110.0
        return sum(1 for rep in reps if rep.min_angle <= valid_threshold)
    
    def _std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
    
    def _calculate_quality_score(
        self, 
        reps: List[SquatRep], 
        angles: List[float]
    ) -> float:
        """
        Calculate quality score (0-100)
        
        Scoring criteria:
        - Depth (30 pts): Minimum angle below 90 degrees
        - Consistency (30 pts): Standard deviation of angle ranges
        - Smoothness (20 pts): Angle variation smoothness
        - Reps (20 pts): Number of completed squats
        """
        if not reps:
            return 0.0
        
        score = 0.0
        
        # Depth scoring (30 pts)
        depth_scores = []
        for rep in reps:
            if rep.min_angle <= 70:
                depth_scores.append(1.0)
            elif rep.min_angle <= 90:
                depth_scores.append(0.8)
            elif rep.min_angle <= 110:
                depth_scores.append(0.5)
            else:
                depth_scores.append(0.3)
        score += 30 * (sum(depth_scores) / len(depth_scores))
        
        # Consistency scoring (30 pts)
        if len(reps) > 1:
            ranges = [rep.angle_range for rep in reps]
            range_std = self._std_dev(ranges)
            consistency = max(0, 1 - range_std / 50)
            score += 30 * consistency
        else:
            score += 15
        
        # Smoothness scoring (20 pts)
        angle_std = self._std_dev(angles)
        smoothness = max(0, 1 - angle_std / 60)
        score += 20 * smoothness
        
        # Reps scoring (20 pts)
        rep_score = min(1.0, len(reps) / 10)
        score += 20 * rep_score
        
        return min(100, score)
    
    def plot_session_analysis(
        self, 
        session_id: int, 
        save_path: Optional[Path] = None
    ) -> Optional[Figure]:
        """
        Generate session analysis chart.
        
        Args:
            session_id: Session ID
            save_path: Save path, None to not save
            
        Returns:
            Figure: matplotlib figure object
        """
        analysis = self.analyze_session(session_id)
        if not analysis:
            return None
        
        records = self._load_session_records(session_id)
        
        # Create figure
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        fig.suptitle(f'Training Analysis - Session {session_id}', fontsize=14)
        
        # Chart 1: Angle over time
        ax1 = axes[0]
        timestamps = [datetime.fromisoformat(r.timestamp) for r in records]
        left_angles = [r.left_angle for r in records]
        right_angles = [r.right_angle for r in records]
        avg_angles = [r.avg_angle for r in records]
        
        ax1.plot(timestamps, left_angles, 'b-', label='Left Knee', alpha=0.7)
        ax1.plot(timestamps, right_angles, 'g-', label='Right Knee', alpha=0.7)
        ax1.plot(timestamps, avg_angles, 'r-', label='Average', linewidth=2)
        ax1.axhline(y=90, color='orange', linestyle='--', label='Squat Threshold (90)')
        ax1.axhline(y=165, color='purple', linestyle='--', label='Stand Threshold (165)')
        ax1.set_ylabel('Angle (degrees)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        # Chart 2: State distribution
        ax2 = axes[1]
        states = [r.state for r in records]
        state_changes = []
        current_state = None
        for i, state in enumerate(states):
            if state != current_state:
                state_changes.append((i, state))
                current_state = state
        
        positions = [i for i, _ in state_changes]
        colors = [0 if s == 'STANDING' else 1 for _, s in state_changes]
        ax2.scatter(positions, [0] * len(positions), c=colors, 
                   cmap='Reds', s=100, marker='|', linewidths=2)
        ax2.set_yticks([0])
        ax2.set_yticklabels(['State'])
        ax2.set_xlabel('Frame')
        ax2.set_title('Pose State Changes (Red=Standing, Green=Squatting)')
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0, len(records))
        
        # Chart 3: Statistics
        ax3 = axes[2]
        ax3.axis('off')
        
        stats_text = f"""
Training Statistics
{'='*50}

Basic Info:
  - Duration: {analysis.duration_seconds:.1f} seconds
  - Total Frames: {analysis.total_records}
  - Squat Reps: {analysis.total_squats}

Angle Statistics:
  - Average: {analysis.avg_angle:.1f} deg
  - Minimum: {analysis.min_angle:.1f} deg
  - Maximum: {analysis.max_angle:.1f} deg
  - Std Dev: {analysis.angle_std:.2f}

State Distribution:
  - Standing: {analysis.standing_ratio*100:.1f}%
  - Squatting: {analysis.squatting_ratio*100:.1f}%

Quality Score: {analysis.quality_score:.1f} / 100
        """
        ax3.text(0.1, 0.5, stats_text, fontsize=10, verticalalignment='center',
                fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat'))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f'Chart saved to: {save_path}')
        
        return fig
