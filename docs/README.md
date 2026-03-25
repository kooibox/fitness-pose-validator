# Fitness Pose Validator - Documentation

## 文档目录结构

```
docs/
├── README.md                          # 本文档（文档目录说明）
│
├── algorithm/                         # 算法相关文档
│   ├── ALGORITHM_EVALUATION_REPORT.md       # 算法评估报告
│   ├── ALGORITHM_IMPROVEMENT_SUMMARY.md     # 算法改进摘要
│   ├── FAST_SQUAT_DETECTION_IMPROVEMENT.md  # 快速深蹲检测优化
│   ├── VALID_COUNT_IMPROVEMENT.md           # 有效计数改进方案
│   └── VALIDITY_REVIEW_REPORT.md            # 多智能体有效性评审
│
├── architecture/                      # 架构设计文档
│   ├── AGENT.md                           # AI代理配置指南
│   ├── DATA_UPLOAD_DESIGN.md              # 数据上传功能设计
│   └── pyqt6_design_proposal.md           # PyQt6界面设计方案
│
├── testing/                           # 测试文档
│   ├── TEST_GUIDE.md                      # 算法精准度测试指南
│   └── TEST_METHODS.md                    # 算法测试方法
│
└── deployment/                        # 部署构建文档
    ├── FASTAPI_CLIENT_MIGRATION_GUIDE.md  # FastAPI迁移指南
    ├── RK3566_DEPLOYMENT_GUIDE.md         # RK3566嵌入式部署
    ├── WINDOWS_BUILD_GUIDE.md             # Windows打包指南
    └── WINDOWS_OPTIMIZATION_GUIDE.md      # Windows平台优化
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行训练程序

```bash
# Windows
fitness-pose-validator\venv\Scripts\activate
python main.py

# Linux/macOS
source venv/bin/activate
python main.py
```

### 3. 启动GUI

```bash
python run_gui.py
```

---

## 算法核心配置

编辑 `src/config.py` 自定义阈值：

```python
STANDING_ANGLE_THRESHOLD = 165.0  # 站立角度阈值
SQUAT_ANGLE_THRESHOLD = 90.0      # 下蹲角度阈值

CAMERA_RESOLUTION = (1280, 720)   # 摄像头分辨率
CAMERA_FPS = 30                    # 帧率
```

---

## 关键参考

### MediaPipe姿态关键点

- 左侧: HIP=23, KNEE=25, ANKLE=27
- 右侧: HIP=24, KNEE=26, ANKLE=28

文档: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker

### 角度计算

```python
def calculate_angle(a, b, c):
    """计算三点夹角（b为顶点）"""
    radians = math.atan2(c.y - b.y, c.x - b.x) - math.atan2(a.y - b.y, a.x - b.x)
    angle = abs(radians * 180.0 / math.pi)
    if angle > 180.0:
        angle = 360.0 - angle
    return angle
```

---

## 常见问题

### Q: 图表显示方块而非中文
**A**: 字体问题，确保系统安装了标准字体。

### Q: 质量得分低
**A**: 
- 蹲得更深（膝角<90°）
- 保持每蹲姿势一致
- 完成更多蹲数（目标10+）

### Q: 导出原始数据
**A**: 使用SQLite工具查询：
```sql
SELECT * FROM squat_records WHERE session_id = 3;
```