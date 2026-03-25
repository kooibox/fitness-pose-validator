# 算法测试方法

## 一、单元测试

### 1. 峰值检测测试
```powershell
# 离线测试（使用已有CSV数据）
python test/test_peak_detection.py
```

测试场景：
- 站立不动 → 计数保持不变
- 单次完整深蹲 → 计数+1
- 快速连续深蹲（不完全站立） → 计数正确累加
- 保持半蹲再蹲 → 每次下蹲到谷值时计数+1

### 2. 角度计算测试

```python
# 测试3D角度计算
from src.squat_counter import SquatCounter

counter = SquatCounter()

# 模拟关键点
class MockLandmark:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

# 直腿：角度应接近180°
angle = counter.calculate_angle_3d(
    MockLandmark(0, 0, 0),  # 髋
    MockLandmark(0, 1, 0),  # 膝
    MockLandmark(0, 2, 0)   # 踝
)
assert 175 < angle < 185, f"直腿角度错误: {angle}"

# 弯腿：角度应接近90°
angle = counter.calculate_angle_3d(
    MockLandmark(0, 0, 0),   # 髋
    MockLandmark(0, 1, 0),   # 膝
    MockLandmark(1, 1, 0)    # 踝（侧向）
)
assert 85 < angle < 95, f"弯腿角度错误: {angle}"
```

### 3. 自适应阈值测试

```python
from src.adaptive_threshold import AdaptiveThresholdManager
from src.squat_counter import PoseState

manager = AdaptiveThresholdManager()

# 模拟角度数据
for _ in range(50):
    manager.add_sample(160.0, PoseState.STANDING)
    manager.add_sample(70.0, PoseState.SQUATTING)

result = manager.calibrate()
assert result is not None, "校准失败"
assert 140 < result.standing_threshold < 175
assert 70 < result.squat_threshold < 110
```

---

## 二、集成测试

### 1. 完整流程测试
```powershell
# 启动GUI进行手动测试
python run_gui.py
```

测试清单：
- [ ] 摄像头正常打开
- [ ] 姿态骨架正确显示
- [ ] 深蹲计数准确
- [ ] 峰值检测计数显示（调试模式）
- [ ] 反馈信息正确（深度、膝盖内扣、背部弯曲）
- [ ] 严格程度切换生效

### 2. 性能测试
```powershell
# 运行30秒，检查帧率和内存
python -c "
import time
import psutil
import os

# 启动检测后监控
pid = os.getpid()
start = time.time()
while time.time() - start < 30:
    process = psutil.Process(pid)
    cpu = process.cpu_percent()
    mem = process.memory_info().rss / 1024 / 1024
    print(f'CPU: {cpu}%, Memory: {mem:.1f}MB')
    time.sleep(2)
"
```

预期结果：
- CPU: < 50%
- Memory: < 500MB

---

## 三、回归测试

### 运行所有测试
```powershell
# 激活虚拟环境
venv\Scripts\activate

# 运行测试
python -m pytest test/ -v
```

### 覆盖率报告
```powershell
pip install pytest-cov
python -m pytest test/ --cov=src --cov-report=html
```

---

## 四、测试数据

### 测试CSV数据格式
```csv
frame_id,timestamp,avg_angle,state,rep_count
1,0.033,165.2,STANDING,0
2,0.066,164.8,STANDING,0
...
```

### 生成测试数据
```python
import csv
import math

with open('test_data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['frame_id', 'timestamp', 'avg_angle', 'state', 'rep_count'])
    
    for i in range(500):
        t = i * 0.033
        angle = 160 - 80 * math.sin(i * 0.1)  # 模拟深蹲曲线
        state = 'SQUATTING' if angle < 100 else 'STANDING'
        count = int(i * 0.1 / (2 * math.pi))
        writer.writerow([i, f'{t:.3f}', f'{angle:.1f}', state, count])
```

---

## 五、问题诊断

### 深蹲漏检诊断
```powershell
# 导出当前会话数据
python analyze.py --session <session_id> --export debug_records.csv

# 使用峰值检测算法验证
python test/test_peak_detection.py
```

### 自适应阈值诊断
在 `detection_worker.py` 中启用日志：
```python
if result and result.confidence > 0.7:
    print(f"[校准] 站立={result.standing_threshold:.0f}, "
          f"下蹲={result.squat_threshold:.0f}, "
          f"置信度={result.confidence:.2f}")
```