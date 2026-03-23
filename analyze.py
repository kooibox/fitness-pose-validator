#!/usr/bin/env python3
"""
Training Data Analysis Tool

Usage:
    python analyze.py                     # Analyze most recent session
    python analyze.py --session 3         # Analyze session 3
    python analyze.py --list              # List all sessions
    python analyze.py --session 3 --save  # Analyze and save chart
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.analyzer import TrainingAnalyzer
from src.database import Database


def list_sessions(db: Database, limit: int = 10) -> None:
    """List training sessions"""
    sessions = db.get_recent_sessions(limit)
    
    if not sessions:
        print("No training records found")
        return
    
    print("\n" + "=" * 80)
    print("Training Sessions")
    print("=" * 80)
    print(f"{'ID':<8} {'Start Time':<26} {'Duration(s)':<12} {'Squats':<10}")
    print("-" * 80)
    
    for session in sessions:
        duration = "N/A"
        if session.end_time:
            from datetime import datetime
            start = datetime.fromisoformat(session.start_time)
            end = datetime.fromisoformat(session.end_time)
            duration = f"{(end - start).total_seconds():.1f}"
        
        print(f"{session.id:<8} {session.start_time:<26} {duration:<12} {session.total_squats:<10}")
    
    print("=" * 80)


def analyze_session(analyzer: TrainingAnalyzer, session_id: int, save: bool = False) -> None:
    """Analyze specified session"""
    print(f"\nAnalyzing session {session_id}...")
    
    analysis = analyzer.analyze_session(session_id)
    if not analysis:
        print(f"Error: Session {session_id} not found")
        return
    
    print("\n" + "=" * 60)
    print(f"Session {session_id} Analysis")
    print("=" * 60)
    
    print(f"\n[Basic Info]")
    print(f"  Duration: {analysis.duration_seconds:.1f} seconds")
    print(f"  Total Frames: {analysis.total_records}")
    print(f"  Squat Reps: {analysis.total_squats}")
    
    print(f"\n[Angle Statistics]")
    print(f"  Average: {analysis.avg_angle:.1f} deg")
    print(f"  Minimum: {analysis.min_angle:.1f} deg")
    print(f"  Maximum: {analysis.max_angle:.1f} deg")
    print(f"  Std Dev: {analysis.angle_std:.2f}")
    
    print(f"\n[State Distribution]")
    print(f"  Standing: {analysis.standing_ratio*100:.1f}%")
    print(f"  Squatting: {analysis.squatting_ratio*100:.1f}%")
    
    print(f"\n[Quality Score]")
    print(f"  Score: {analysis.quality_score:.1f} / 100")
    
    if analysis.reps:
        print(f"\n[Rep Details]")
        print(f"{'Rep':<8} {'Duration(s)':<12} {'Min Angle':<12} {'Range':<10}")
        print("-" * 45)
        for rep in analysis.reps:
            print(f"{rep.rep_number:<8} {rep.duration_seconds:<12.2f} {rep.min_angle:<12.1f} {rep.angle_range:<10.1f}")
    
    if save:
        output_dir = Path(__file__).parent / "data" / "analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        save_path = output_dir / f"session_{session_id}_analysis.png"
        analyzer.plot_session_analysis(session_id, save_path)
        print(f"\nChart saved to: {save_path}")
    else:
        analyzer.plot_session_analysis(session_id)
        plt = __import__('matplotlib.pyplot')
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Fitness Training Data Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze.py --list           List all training sessions
  python analyze.py --session 3      Analyze session 3
  python analyze.py -s 3 --save      Analyze and save chart
        """
    )
    
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List recent training sessions"
    )
    
    parser.add_argument(
        "-s", "--session",
        type=int,
        metavar="ID",
        help="Analyze specified session ID"
    )
    
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save analysis chart to file"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of sessions to list (default: 10)"
    )
    
    args = parser.parse_args()
    
    db = Database()
    analyzer = TrainingAnalyzer()
    
    if args.list:
        list_sessions(db, args.limit)
    elif args.session:
        analyze_session(analyzer, args.session, args.save)
    else:
        sessions = db.get_recent_sessions(1)
        if sessions:
            print(f"No session specified, analyzing most recent (ID: {sessions[0].id})")
            analyze_session(analyzer, sessions[0].id, args.save)
        else:
            print("No training records found. Please run training program first.")
            sys.exit(1)


if __name__ == "__main__":
    main()
