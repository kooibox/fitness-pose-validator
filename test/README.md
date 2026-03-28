# 测试目录结构

## 目录组织

```
test/
├── algorithm/              # 算法测试
│   ├── peak_detection.py       # 深蹲峰值检测测试
│   ├── offline_comparison.py   # 深蹲离线算法对比
│   ├── debug_evaluation.py     # 深蹲调试评估测试
│   ├── tune_peak_detector.py   # 深蹲峰值检测调参
│   └── jumping_jack_test.py    # 开合跳算法测试
│
├── evaluation/             # 评估测试
│   ├── generate_test_report.py # 生成测试报告
│   ├── accuracy_evaluation.py  # 精准度评估
│   ├── proper_evaluation.py    # 深蹲实时/视频测试
│   └── video_to_csv.py         # 视频转CSV工具
│
├── gui/                    # GUI测试
│   ├── test_upload.py          # 上传功能测试
│   ├── test_gui_upload.py      # GUI上传测试
│   ├── test_export.py          # 导出功能测试
│   └── test_export_simple.py   # 简单导出测试
│
└── data/                   # 测试数据
    ├── samples/                # 样本数据
    │   ├── squat/                  # 深蹲测试数据
    │   │   └── debug_records.csv   # 深蹲调试记录
    │   └── jumping_jack/           # 开合跳测试数据
    │       └── (待添加)
    ├── videos/                 # 测试视频
    │   └── test*.mp4
    └── reports/                # 测试报告
        ├── test_report.md
        └── test_report.json
```

## 测试命令

### 深蹲测试

```powershell
# 峰值检测测试
python test/algorithm/peak_detection.py

# 实时测试
python test/evaluation/proper_evaluation.py --realtime --duration 60

# 视频测试
python test/evaluation/proper_evaluation.py --video test/data/videos/test.mp4 --ground-truth 10

# 调试评估
python test/algorithm/debug_evaluation.py --duration 60

# 离线算法对比
python test/algorithm/offline_comparison.py
```

### 开合跳测试

```powershell
# 实时测试
python test/algorithm/jumping_jack_test.py --realtime --duration 60

# 视频测试
python test/algorithm/jumping_jack_test.py --video your_video.mp4 --ground-truth 20

# 离线测试
python test/algorithm/jumping_jack_test.py --csv test/data/samples/jumping_jack/records.csv --actual-count 15

# 阈值分析
python test/algorithm/jumping_jack_test.py --analyze
```

## 测试数据

### 深蹲数据

| 文件 | 说明 |
|------|------|
| `samples/squat/debug_records.csv` | 调试记录，592帧，实际33次深蹲 |
| `samples/squat/test3_records.csv` | 测试记录3 |
| `samples/squat/test4_records.csv` | 测试记录4 |
| `samples/squat/test5_records.csv` | 测试记录5 |
| `samples/squat/test6_records.csv` | 测试记录6 |

### 开合跳数据

| 文件 | 说明 |
|------|------|
| `samples/jumping_jack/` | 待添加测试数据 |

### 视频数据

| 文件 | 说明 |
|------|------|
| `videos/test.mp4` | 深蹲测试视频 |
| `videos/test(2).mp4` - `test(6).mp4` | 其他测试视频 |

## 生成新数据

### 深蹲数据

```powershell
# 运行调试评估生成CSV
python test/algorithm/debug_evaluation.py --duration 60
# 数据保存到: test/data/samples/squat/debug_records.csv
```

### 开合跳数据

```powershell
# 运行实时测试生成CSV
python test/algorithm/jumping_jack_test.py --realtime --duration 60
# 数据保存到: test/data/samples/jumping_jack/jumping_jack_realtime_*.csv
```

## 测试指标

### 深蹲指标

| 测试项 | 期望值 |
|-------|-------|
| 峰值检测准确率 | ≥ 85% |
| EMA平滑抖动减少 | ≥ 40% |
| 状态机准确率 | ≥ 80% |
| 自适应阈值置信度 | ≥ 70% |

### 开合跳指标

| 测试项 | 期望值 |
|-------|-------|
| 状态机准确率 | ≥ 80% |
| 峰值检测准确率 | ≥ 85% |
| 髋角检测稳定性 | 波动 < 10° |
| 肩角检测稳定性 | 波动 < 15° |