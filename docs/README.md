# Fitness Pose Validator - Documentation

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Training Program

```bash
fitness-pose-validator\venv\Scripts\activate
python main.py
```

### 3. View Analysis

```bash
# List all sessions
python analyze.py --list

# Analyze specific session
python analyze.py --session 3

# Analyze and save chart
python analyze.py --session 3 --save
```

## Project Structure

```
fitness-pose-validator/
├── src/                       # Source code
│   ├── __init__.py
│   ├── config.py             # Configuration constants
│   ├── database.py           # SQLite database operations
│   ├── pose_detector.py      # MediaPipe wrapper
│   ├── squat_counter.py      # Squat counting logic
│   ├── visualizer.py         # Visualization rendering
│   └── analyzer.py           # Training data analysis
├── models/                    # Model files
│   └── pose_landmarker.task
├── data/                      # Data storage
│   ├── fitness_data.db       # SQLite database
│   └── analysis/             # Analysis charts
├── main.py                    # Main entry point
├── analyze.py                 # Analysis CLI tool
├── requirements.txt           # Python dependencies
├── run.bat                    # Windows launcher
└── docs/                      # Documentation
    ├── AGENT.md              # AI context guide
    └── ANALYSIS_GUIDE.md     # Analysis guide
```

## Configuration

Edit `src/config.py` to customize:

```python
# Squat thresholds
STANDING_ANGLE_THRESHOLD = 165.0  # Standing angle threshold
SQUAT_ANGLE_THRESHOLD = 90.0      # Squat angle threshold

# Camera settings
CAMERA_RESOLUTION = (1280, 720)
CAMERA_FPS = 30
```

## Database Schema

### sessions Table

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER | Session ID |
| start_time | TEXT | Start timestamp |
| end_time | TEXT | End timestamp |
| total_frames | INTEGER | Total frames |
| total_squats | INTEGER | Total squats |

### squat_records Table

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER | Record ID |
| session_id | INTEGER | Session ID (FK) |
| timestamp | TEXT | Timestamp |
| left_angle | REAL | Left knee angle |
| right_angle | REAL | Right knee angle |
| avg_angle | REAL | Average angle |
| state | TEXT | State (STANDING/SQUATTING) |
| rep_count | INTEGER | Rep count |

## Quality Score

Scored 0-100 based on:

| Metric | Weight | Criteria |
|--------|--------|----------|
| Depth | 30 pts | Min angle ≤70° = full points |
| Consistency | 30 pts | Low std dev of angle ranges |
| Smoothness | 20 pts | Low overall angle variation |
| Reps | 20 pts | 10+ reps = full points |

## Reference

### MediaPipe Pose Landmarks

Key landmark indices:
- Left: HIP=23, KNEE=25, ANKLE=27
- Right: HIP=24, KNEE=26, ANKLE=28

Documentation: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker

### Angle Calculation

```python
def calculate_angle(a, b, c):
    """Calculate angle at point b formed by points a-b-c"""
    radians = math.atan2(c.y - b.y, c.x - b.x) - math.atan2(a.y - b.y, a.x - b.x)
    angle = abs(radians * 180.0 / math.pi)
    if angle > 180.0:
        angle = 360.0 - angle
    return angle
```

## Troubleshooting

### Q: Chart shows square boxes instead of characters
**A**: This is a font issue. The analysis module uses system fonts. Ensure your system has standard fonts installed.

### Q: Low quality score
**A**: 
- Squat deeper (knee angle < 90°)
- Maintain consistent form across reps
- Complete more reps (aim for 10+)

### Q: Export raw data
**A**: Use SQLite tools to query `data/fitness_data.db`:
```sql
SELECT * FROM squat_records WHERE session_id = 3;
```
