# RK3566嵌入式部署优化方案

**目标平台**: RK3566 (4核Cortex-A55 @ 1.8GHz, 0.8 TOPS NPU, 2-4GB RAM)  
**性能目标**: 15-30 FPS 实时姿态检测  
**应用场景**: 健身姿态验证（深蹲计数与动作分析）

---

## 一、RK3566硬件限制分析

### 1.1 硬件规格

| 组件 | 规格 | 对算法的影响 |
|-----|------|-------------|
| CPU | 4× Cortex-A55 @ 1.8GHz | 纯CPU运行模型会很慢 |
| GPU | Mali-G52 | 不支持CUDA，OpenCL支持有限 |
| NPU | 0.8 TOPS | **关键加速器**，需RKNN格式 |
| RAM | 2-4GB LPDDR4 | 内存有限，需优化模型大小 |
| 存储 | eMMC/SD | 模型需量化压缩 |

### 1.2 性能基准参考

根据实测数据 (来源: YOLO11 on RK3566 NPU):

| 模式 | 延迟 | 能耗 | FPS |
|-----|------|------|-----|
| 纯CPU推理 | ~200ms | 3.60W | ~5 FPS |
| NPU加速 | ~12ms | 3.59W | ~80 FPS |
| **加速比** | **16.7×** | 相当 | **16×** |

**结论**: 必须使用NPU加速才能达到实时性能。

---

## 二、部署架构选择

### 2.1 三种部署方案对比

| 方案 | 优点 | 缺点 | FPS预期 |
|-----|------|------|--------|
| **A: MediaPipe + RKNN** | 保留现有代码，33关键点 | 需转换模型，复杂度高 | 20-30 FPS |
| **B: BlazePose-Lite + TFLite** | 官方轻量版，易部署 | 17关键点，功能减少 | 12-20 FPS |
| **C: RTMPose + RKNN** | 国产优化，NPU友好 | 需重写后处理 | 25-35 FPS |

### 2.2 推荐方案: **A: MediaPipe → RKNN转换**

**理由**:
1. 保留33关键点，支持膝盖内扣检测
2. 保留现有业务代码，改动最小
3. NPU加速可达20-30 FPS

---

## 三、核心改进方案（嵌入式优化版）

### 3.1 改进优先级（针对RK3566资源限制）

```
┌────────────────────────────────────────────────────────────┐
│              改进方案资源消耗矩阵                            │
├────────────────────────────────────────────────────────────┤
│                     计算开销        内存开销      推荐度     │
│  ─────────────────────────────────────────────────────     │
│  ① NPU模型转换        低             中          ⭐⭐⭐⭐⭐  │
│  ② INT8量化           低             低          ⭐⭐⭐⭐⭐  │
│  ③ 简化卡尔曼滤波     低             低          ⭐⭐⭐⭐☆  │
│  ④ 多帧验证(3帧)      低             低          ⭐⭐⭐⭐☆  │
│  ⑤ 3D坐标计算         中             低          ⭐⭐⭐☆☆  │
│  ⑥ 视角检测           低             低          ⭐⭐⭐☆☆  │
│  ⑦ ML辅助验证         高             高          ❌不推荐  │
│  ⑧ 多传感器融合       高             高          ❌不推荐  │
└────────────────────────────────────────────────────────────┘
```

### 3.2 必选改进：模型NPU加速

#### 步骤1: 提取TFLite模型

MediaPipe Pose Landmarker (.task) 包含多个子模型，需拆解：

```python
# pose_model_extractor.py
import struct
from pathlib import Path

def extract_tflite_from_task(task_path: str, output_dir: str):
    """
    从 .task 文件提取 TFLite 模型
    
    MediaPipe Pose Landmarker 包含:
    - pose_detection.tflite (人体检测)
    - pose_landmarks.tflite (关键点估计)
    """
    with open(task_path, 'rb') as f:
        data = f.read()
    
    # 搜索 TFLite 魔数
    tflite_magic = b'\x54\x46\x4c\x33'  # "TFL3"
    
    offset = 0
    model_count = 0
    
    while True:
        pos = data.find(tflite_magic, offset)
        if pos == -1:
            break
        
        # 提取模型大小
        size = struct.unpack('<I', data[pos-4:pos])[0]
        
        # 保存模型
        model_data = data[pos:pos+size]
        model_path = Path(output_dir) / f"model_{model_count}.tflite"
        model_path.write_bytes(model_data)
        
        print(f"Extracted: {model_path} ({size} bytes)")
        model_count += 1
        offset = pos + size
```

#### 步骤2: 转换为RKNN格式

```python
# convert_to_rknn.py
from rknn.api import RKNN

def convert_pose_to_rknn(tflite_path: str, rknn_path: str):
    """
    将 TFLite 模型转换为 RKNN 格式
    
    关键配置:
    - INT8 量化: 模型缩小4倍，速度提升2-3倍
    - 输入分辨率: 降采样到 256x256 (原版 256x256)
    """
    rknn = RKNN()
    
    # 配置
    rknn.config(
        mean_values=[[0, 0, 0]],
        std_values=[[255, 255, 255]],
        target_platform='rk3566',
        optimization_level=3,
        quantized_dtype='asymmetric_quantized-8',  # INT8量化
        quantized_algorithm='normal',  # 或 'mmse' 精度更高
    )
    
    # 加载 TFLite
    rknn.load_tflite(model=tflite_path)
    
    # 构建 RKNN
    rknn.build(do_quantization=True, dataset='quantization_dataset.txt')
    
    # 导出
    rknn.export_rknn(rknn_path)
    
    rknn.release()
    print(f"Converted: {rknn_path}")
```

#### 步骤3: RKNN推理封装

```python
# src/rknn_pose_detector.py
import numpy as np
import cv2
from rknn.api import RKNN

class RKNNPoseDetector:
    """
    RKNN加速的姿态检测器 (替代原MediaPipe)
    """
    
    def __init__(self, detection_model: str, landmark_model: str):
        self.detection_model = self._load_model(detection_model)
        self.landmark_model = self._load_model(landmark_model)
        
        # 输入尺寸
        self.input_size = (256, 256)
        
    def _load_model(self, path: str) -> RKNN:
        """加载RKNN模型"""
        rknn = RKNN()
        ret = rknn.load_rknn(path)
        if ret != 0:
            raise RuntimeError(f"Failed to load {path}")
        
        ret = rknn.init_runtime()
        if ret != 0:
            raise RuntimeError(f"Failed to init runtime for {path}")
        
        return rknn
    
    def detect(self, frame: np.ndarray) -> dict:
        """
        检测姿态关键点
        
        Args:
            frame: BGR图像 (OpenCV格式)
        
        Returns:
            dict: {
                'landmarks': 33个关键点坐标,
                'world_landmarks': 3D世界坐标,
                'scores': 置信度
            }
        """
        # 预处理
        input_img = cv2.resize(frame, self.input_size)
        input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)
        input_img = input_img.astype(np.float32) / 255.0
        input_img = np.expand_dims(input_img, 0)  # [1, H, W, C]
        
        # 人体检测
        detection = self.detection_model.inference(inputs=[input_img])
        
        if detection is None or len(detection) == 0:
            return None
        
        # 提取ROI并预测关键点
        # (简化版，实际需要根据检测结果裁剪ROI)
        landmarks = self.landmark_model.inference(inputs=[input_img])
        
        return self._postprocess(landmarks)
    
    def _postprocess(self, raw_output) -> dict:
        """后处理：解析RKNN输出"""
        # 解析33个关键点坐标
        # 格式取决于具体模型输出结构
        landmarks = raw_output[0].reshape(-1, 5)  # [33, 5] (x, y, z, visibility, presence)
        
        return {
            'landmarks': landmarks[:, :2],      # 2D坐标
            'world_landmarks': landmarks[:, :3], # 3D坐标
            'scores': landmarks[:, 3]            # 置信度
        }
    
    def close(self):
        """释放资源"""
        self.detection_model.release()
        self.landmark_model.release()
```

### 3.3 必选改进：轻量级时序平滑

**问题**: 卡尔曼滤波在嵌入式上有计算开销

**方案**: 简化移动平均 + 异常值过滤

```python
# src/lightweight_smoother.py
from collections import deque
import numpy as np

class LightweightAngleSmoother:
    """
    轻量级角度平滑器 (适合嵌入式平台)
    
    原理: 指数加权移动平均 (EWMA) + 异常值剔除
    计算量: 仅几次乘法和加法
    内存: 仅存储上一帧值
    """
    
    def __init__(self, alpha: float = 0.3, threshold: float = 30.0):
        """
        Args:
            alpha: 平滑系数 (0-1), 越小越平滑
            threshold: 异常值阈值 (度), 超过则忽略
        """
        self.alpha = alpha
        self.threshold = threshold
        self.last_value = None
        self.history = deque(maxlen=5)  # 用于异常检测
    
    def update(self, value: float) -> float:
        """
        更新并返回平滑后的值
        
        计算复杂度: O(1)
        内存开销: 6个float
        """
        # 首帧初始化
        if self.last_value is None:
            self.last_value = value
            self.history.append(value)
            return value
        
        # 异常值检测
        if len(self.history) >= 3:
            mean = np.mean(self.history)
            if abs(value - mean) > self.threshold:
                # 视为异常，返回上一次的平滑值
                return self.last_value
        
        # 指数加权移动平均
        smoothed = self.alpha * value + (1 - self.alpha) * self.last_value
        
        self.last_value = smoothed
        self.history.append(value)
        
        return smoothed
    
    def reset(self):
        """重置状态"""
        self.last_value = None
        self.history.clear()


# 使用示例 (比卡尔曼滤波轻量100倍)
class EmbeddedSquatCounter:
    def __init__(self):
        self.left_knee_smoother = LightweightAngleSmoother(alpha=0.3)
        self.right_knee_smoother = LightweightAngleSmoother(alpha=0.3)
    
    def update(self, landmarks):
        # 计算原始角度
        raw_left = self.calculate_angle(...)
        raw_right = self.calculate_angle(...)
        
        # 轻量平滑
        self.left_knee_angle = self.left_knee_smoother.update(raw_left)
        self.right_knee_angle = self.right_knee_smoother.update(raw_right)
```

**性能对比**:

| 方法 | 计算复杂度 | 内存 | 平滑效果 |
|-----|----------|------|---------|
| 卡尔曼滤波 | O(n²) 矩阵运算 | ~1KB | 最佳 |
| **EWMA** | O(1) 乘法 | 24 bytes | 良好 |

### 3.4 必选改进：帧间确认机制

```python
# src/embedded_state_machine.py
from enum import Enum

class PoseState(Enum):
    STANDING = 0
    DESCENDING = 1      # 下蹲中
    SQUATTING = 2       # 最低点
    ASCENDING = 3       # 起身中

class EmbeddedSquatStateMachine:
    """
    嵌入式优化的深蹲状态机
    
    特点:
    - 4状态模型，更精确捕捉动作阶段
    - 2帧确认，平衡响应速度和稳定性
    - 无动态内存分配
    """
    
    def __init__(self,
                 standing_thresh: float = 165.0,
                 squat_thresh: float = 90.0,
                 confirm_frames: int = 2):
        self.standing_thresh = standing_thresh
        self.squat_thresh = squat_thresh
        self.confirm_frames = confirm_frames
        
        self.state = PoseState.STANDING
        self.confirm_count = 0
        self.count = 0
        self.min_angle = 180.0  # 记录最低角度
    
    def update(self, knee_angle: float) -> tuple:
        """
        更新状态
        
        Returns:
            (state, count, min_angle)
        """
        # 状态转换逻辑
        if self.state == PoseState.STANDING:
            if knee_angle < self.standing_thresh - 10:
                self._confirm_transition(PoseState.DESCENDING)
        
        elif self.state == PoseState.DESCENDING:
            self.min_angle = min(self.min_angle, knee_angle)
            if knee_angle < self.squat_thresh:
                self._confirm_transition(PoseState.SQUATTING)
            elif knee_angle > self.standing_thresh:
                self._confirm_transition(PoseState.STANDING)
        
        elif self.state == PoseState.SQUATTING:
            if knee_angle > self.squat_thresh + 20:
                self._confirm_transition(PoseState.ASCENDING)
        
        elif self.state == PoseState.ASCENDING:
            if knee_angle > self.standing_thresh:
                # 完成一次深蹲
                self.count += 1
                self._confirm_transition(PoseState.STANDING)
            elif knee_angle < self.squat_thresh:
                self._confirm_transition(PoseState.SQUATTING)
        
        return self.state, self.count, self.min_angle
    
    def _confirm_transition(self, new_state: PoseState):
        """帧间确认"""
        if self.confirm_count >= self.confirm_frames:
            self.state = new_state
            self.confirm_count = 0
            if new_state == PoseState.STANDING:
                self.min_angle = 180.0
        else:
            self.confirm_count += 1
    
    def reset(self):
        self.state = PoseState.STANDING
        self.confirm_count = 0
        self.count = 0
        self.min_angle = 180.0
```

### 3.5 可选改进：简化视角检测

```python
# src/embedded_view_check.py

def check_front_view(landmarks) -> bool:
    """
    简单的正面视角检查
    
    计算复杂度: O(1)
    仅用于提示用户，不影响主流程
    """
    # 肩宽/髋宽比例
    shoulder_width = abs(landmarks[12].x - landmarks[11].x)
    hip_width = abs(landmarks[24].x - landmarks[23].x)
    
    if hip_width < 0.01:
        return False
    
    ratio = shoulder_width / hip_width
    
    # 正面: 比例接近1
    return ratio > 0.7


def get_view_warning(landmarks) -> str:
    """获取视角警告信息"""
    if not check_front_view(landmarks):
        return "请正对摄像头以获得最佳检测效果"
    return ""
```

---

## 四、不建议的改进（嵌入式不适用）

| 改进项 | 原因 | 替代方案 |
|-------|------|---------|
| 3D世界坐标角度 | RKNN输出可能不包含世界坐标 | 使用2D坐标+视角校正 |
| 完整卡尔曼滤波 | 计算开销较大 | EWMA指数平滑 |
| ML辅助验证 | 需要额外模型，内存不足 | 简化规则判断 |
| 多传感器融合 | 硬件不支持 | 单摄像头优化 |
| 深度学习姿态校正 | 计算量大 | 固定阈值+动态调整 |

---

## 五、部署架构

### 5.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    RK3566 部署架构                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   摄像头     │───→│  NPU推理     │───→│  后处理      │  │
│  │  (USB/CSI)   │    │  (RKNN)      │    │  (CPU)       │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                    │          │
│         │            ┌──────┴──────┐             │          │
│         │            │             │             │          │
│         │     ┌──────┴──────┐ ┌────┴────┐        │          │
│         │     │pose_detect  │ │pose_    │        │          │
│         │     │.rknn        │ │landmark │        │          │
│         │     │             │ │.rknn    │        │          │
│         │     └─────────────┘ └─────────┘        │          │
│         │                                        │          │
│         └────────────────────────────────────────┘          │
│                           │                                 │
│                    ┌──────┴──────┐                          │
│                    │  状态机     │                          │
│                    │  计数逻辑   │                          │
│                    │  姿态验证   │                          │
│                    └──────┬──────┘                          │
│                           │                                 │
│                    ┌──────┴──────┐                          │
│                    │  UI显示     │                          │
│                    │  (Qt/SDL)   │                          │
│                    └─────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 线程模型

```python
# main_embedded.py
import threading
import queue

class EmbeddedFitnessApp:
    """
    嵌入式多线程应用
    
    线程分配:
    - 主线程: UI渲染
    - 采集线程: 摄像头读取
    - 推理线程: NPU推理 (绑定大核)
    - 处理线程: 后处理+计数
    """
    
    def __init__(self):
        self.frame_queue = queue.Queue(maxsize=2)  # 限制内存
        self.result_queue = queue.Queue(maxsize=2)
        
        self.running = False
        
        # 绑定大核优化 (RK3566: 核心2,3是大核)
        self.bind_cores = [2, 3]
    
    def run(self):
        self.running = True
        
        # 启动线程
        capture_thread = threading.Thread(target=self._capture_loop)
        inference_thread = threading.Thread(target=self._inference_loop)
        process_thread = threading.Thread(target=self._process_loop)
        
        capture_thread.start()
        inference_thread.start()
        process_thread.start()
        
        # 主线程: UI
        self._ui_loop()
        
        # 等待退出
        self.running = False
        capture_thread.join()
        inference_thread.join()
        process_thread.join()
    
    def _capture_loop(self):
        """摄像头采集线程"""
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        while self.running:
            ret, frame = cap.read()
            if ret:
                # 非阻塞放入队列
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    pass  # 丢弃旧帧
        
        cap.release()
    
    def _inference_loop(self):
        """NPU推理线程"""
        detector = RKNNPoseDetector(...)
        
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=0.1)
                result = detector.detect(frame)
                self.result_queue.put(result)
            except queue.Empty:
                continue
        
        detector.close()
```

---

## 六、性能预期

### 6.1 FPS估算

| 阶段 | CPU耗时 | NPU耗时 | 优化后耗时 |
|-----|--------|--------|----------|
| 图像采集 | 5ms | - | 5ms |
| 预处理 | 10ms | - | 5ms (降采样) |
| 人体检测 | 100ms | 8ms | **8ms** |
| 关键点估计 | 150ms | 15ms | **15ms** |
| 后处理 | 5ms | - | 3ms |
| 状态机+验证 | 2ms | - | 2ms |
| **总计** | **~270ms** | - | **~38ms** |
| **FPS** | **~4 FPS** | - | **~26 FPS** |

### 6.2 内存估算

| 组件 | 内存占用 |
|-----|---------|
| pose_detection.rknn (INT8) | ~3MB |
| pose_landmarks.rknn (INT8) | ~5MB |
| 运行时缓冲 | ~10MB |
| 应用程序 | ~20MB |
| **总计** | **~40MB** |

---

## 七、实施路线图

### 阶段1: 模型转换 (1周)

```
Day 1-2: 提取TFLite模型
Day 3-4: RKNN转换 + INT8量化
Day 5-7: 推理验证 + 精度对比测试
```

### 阶段2: 代码移植 (1周)

```
Day 1-2: RKNN推理封装
Day 3-4: 轻量级平滑器实现
Day 5-7: 状态机优化 + 多线程架构
```

### 阶段3: 部署优化 (1周)

```
Day 1-2: 交叉编译 + 部署测试
Day 3-4: 性能调优 (绑核、内存)
Day 5-7: 现场测试 + 问题修复
```

---

## 八、关键代码清单

### 新增文件

```
src/
├── rknn_pose_detector.py      # RKNN推理封装
├── lightweight_smoother.py    # 轻量级平滑器
├── embedded_state_machine.py  # 嵌入式状态机
└── embedded_view_check.py     # 视角检查

tools/
├── extract_tflite.py          # TFLite提取
└── convert_to_rknn.py         # RKNN转换

models/
├── pose_detection.rknn        # 检测模型 (INT8)
└── pose_landmarks.rknn        # 关键点模型 (INT8)
```

### 修改文件

```
requirements.txt        # 移除mediapipe, 添加rknn-toolkit2
src/config.py          # 添加RKNN配置
main.py → main_embedded.py  # 嵌入式入口
```

---

## 九、风险与应对

| 风险 | 可能性 | 影响 | 应对措施 |
|-----|-------|------|---------|
| RKNN转换失败 | 中 | 高 | 使用官方转换工具，参考手势识别案例 |
| INT8精度下降 | 中 | 中 | 使用MMSE量化算法，准备校准数据集 |
| NPU利用率低 | 低 | 中 | 合并预处理到模型中 |
| 内存不足 | 低 | 高 | 降低输入分辨率，减少队列深度 |

---

## 十、总结

### 核心优化措施

| 优先级 | 措施 | 收益 |
|-------|------|------|
| ⭐⭐⭐⭐⭐ | MediaPipe → RKNN | FPS从4提升到26 |
| ⭐⭐⭐⭐⭐ | INT8量化 | 模型缩小4倍，速度提升2-3倍 |
| ⭐⭐⭐⭐ | 轻量级EWMA平滑 | 消除抖动，开销可忽略 |
| ⭐⭐⭐⭐ | 多帧状态确认 | 消除误计数 |
| ⭐⭐⭐ | 简化视角检测 | 改善用户体验 |

### 最终性能预期

- **FPS**: 20-30 FPS (满足实时需求)
- **内存**: ~40MB (2GB RAM完全够用)
- **功耗**: <5W (适合嵌入式长时间运行)
- **精度**: 与PC版本相比损失 < 3%

---

**文档版本**: v1.0  
**适用平台**: RK3566 / RK3568  
**创建日期**: 2026年3月24日