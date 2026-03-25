# Fitness Pose Validator - AI Context Guide

## Project Overview
Real-time fitness pose detection system using MediaPipe Pose Landmarker. Supports squat counting, data persistence, and training quality analysis.

## Quick Start
```bash
# Activate venv
fitness-pose-validator\venv\Scripts\activate

# Run training
python main.py

# View analysis
python analyze.py --list          # List sessions
python analyze.py --session 3     # Analyze session
python analyze.py -s 3 --save     # Analyze & save chart
```

## Directory Structure
```
fitness-pose-validator/
├── src/                       # Source modules
│   ├── config.py             # Config constants
│   ├── database.py           # SQLite DB
│   ├── pose_detector.py      # MediaPipe wrapper
│   ├── squat_counter.py      # Counting logic
│   ├── visualizer.py         # Rendering
│   └── analyzer.py           # Data analysis
├── models/pose_landmarker.task
├── data/
│   ├── fitness_data.db
│   └── analysis/             # Charts
├── docs/                     # Documentation
├── main.py                   # Entry point
└── analyze.py                # Analysis CLI
```

## Core Config (src/config.py)
```python
STANDING_ANGLE_THRESHOLD = 165.0  # Standing threshold
SQUAT_ANGLE_THRESHOLD = 90.0      # Squat threshold
RECORD_BUFFER_SIZE = 100          # Batch write size
```

## Key Indices (MediaPipe Pose)
- Left: HIP=23, KNEE=25, ANKLE=27
- Right: HIP=24, KNEE=26, ANKLE=28

## Counting Logic
State machine: STANDING (>165 deg) <-> SQUATTING (<90 deg)
- Stand->Squat: avg_angle < 90
- Squat->Stand: avg_angle > 165, count++

## Database Tables
- sessions: training sessions (id, start_time, end_time, total_frames, total_squats)
- squat_records: per-frame records (session_id, timestamp, angles, state, rep_count)

## Quality Score Algorithm
```
score = depth(30) + consistency(30) + smoothness(20) + reps(20)

- Depth: min_angle <= 70 = full points
- Consistency: low std dev of angle ranges
- Smoothness: low overall angle variation
- Reps: 10+ = full points
```

## Known Issues
- LSP import errors: venv not configured for LSP, doesn't affect runtime
- Camera rotation: cv2.ROTATE_90_CLOCKWISE for portrait mode
- MediaPipe warnings: inference_feedback_manager warnings are harmless

## Testing
1. Run: python main.py (do squats, check REPS count)
2. Analyze: python analyze.py --session <id> --save
3. Check chart in data/analysis/

---

## Git-Based Project Management

### Core Rule: Code Changes Must Update Git

**MANDATORY**: When modifying code, you MUST update git with the changes.

#### Git Workflow:

1. **Before Making Changes**:
   - Run `git status` to check current state
   - Ensure you're on the correct branch
   - Pull latest changes if working with remote

2. **After Making Changes**:
   - Stage changes: `git add <changed-files>`
   - Write meaningful commit messages
   - Commit changes: `git commit -m "descriptive message"`
   - Push to remote if applicable: `git push`

3. **Commit Message Format**:
   ```
   <type>(<scope>): <subject>
   
   [optional body]
   
   [optional footer]
   ```
   
   Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

4. **Verification**:
   - After commit, run `git status` to verify clean state
   - Ensure no unintended files are staged
   - Run tests/build if applicable before committing

### Git Safety Protocol

- NEVER update git config without explicit request
- NEVER run destructive commands (`push --force`, `reset --hard`) unless explicitly requested
- NEVER skip hooks (`--no-verify`, `--no-gpg-sign`) unless explicitly requested
- NEVER run force push to main/master - warn user if requested
- Avoid `git commit --amend` - only use when ALL conditions are met:
  1. User explicitly requested amend, OR commit SUCCEEDED but pre-commit hook auto-modified files
  2. HEAD commit was created in current session
  3. Commit has NOT been pushed to remote
- If commit FAILED or was REJECTED by hook: fix issue and create NEW commit (do NOT amend)
- If already pushed to remote: NEVER amend unless user explicitly requests (requires force push)
- NEVER commit changes unless user explicitly asks - it's VERY IMPORTANT to only commit when explicitly requested

### Git Management Commands

```bash
# Check status
git status

# Add files
git add <file-pattern>

# Commit with message
git commit -m "type(scope): descriptive message"

# View recent commits
git log --oneline -5

# Check diff before commit
git diff

# Push to remote
git push origin <branch-name>
```

### Branch Management

- `main`/`master`: Protected production branch
- Create feature branches: `git checkout -b feature/feature-name`
- Naming conventions:
  - `feature/xxx`: New features
  - `fix/xxx`: Bug fixes
  - `docs/xxx`: Documentation
  - `refactor/xxx`: Code refactoring

### Code Change Evidence

When making code changes, provide evidence:
- `git diff` showing changes
- `git log -1` showing latest commit
- Confirmation that git status is clean (or shows expected uncommitted changes)
