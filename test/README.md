# 测试目录结构

## 目录组织

```
test/
├── algorithm/          # 算法测试
│   ├── peak_detection.py    # 峰值检测测试
│   ├── offline_comparison.py# 离线算法对比
│   └── debug_evaluation.py  # 调试评估测试
│
├── evaluation/         # 评估测试
│   ├── generate_test_report.py  # 生成测试报告
│   ├── accuracy_evaluation.py   # 精准度评估
│   └── proper_evaluation.py     # 实时/视频测试
│
├── gui/                # GUI测试
│   ├── test_upload.py         # 上传功能测试
│   ├── test_gui_upload.py     # GUI上传测试
│   ├── test_export.py         # 导出功能测试
│   └── test_export_simple.py  # 简单导出测试
│
└── data/               # 测试数据
    ├── samples/           # 样本数据
    │   └── debug_records.csv
    └── reports/           # 测试报告
        ├── test_report.md
        └── test_report.json
```

## 测试命令

### 峰值检测测试

```powershell
cd test
python algorithm\peak_detection.py
```

### 生成测试报告

```powershell
cd test
python evaluation\generate_test_report.py
```

### 实时测试

```powershell
cd test
python evaluation\proper_evaluation.py --realtime --duration 60
```

### 视频测试

```powershell
cd test
python evaluation\proper_evaluation.py --video your_video.mp4 --ground-truth 10
```

### 离线算法对比

```powershell
cd test
python algorithm\offline_comparison.py
```

## 测试数据

### 已有数据

`data/samples/debug_records.csv` - 包含592帧数据，用户实际做33次深蹲

### 生成新数据

1. 运行调试评估：

```powershell
python algorithm\debug_evaluation.py --duration 60
```

2. 生成的CSV文件会保存到 `data/samples/` 目录

## 测试指标

| 测试项 | 期望值 |
|-------|-------|
| 峰值检测准确率 | ≥ 85% |
| EMA平滑抖动减少 | ≥ 40% |
| 状态机准确率 | ≥ 80% |
| 自适应阈值置信度 | ≥ 70% |