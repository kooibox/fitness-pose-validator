# 健身姿态验证算法改进方案摘要

**项目**: Fitness Pose Validator v2.4.0  
**目标**: 提升姿态检测精度、鲁棒性和用户体验

---

## 一、核心问题诊断

| 问题 | 影响 | 优先级 |
|-----|------|-------|
| 角度计算仅用2D坐标 | 侧向拍摄误差大，忽略深度信息 | 🔴 高 |
| 膝盖内扣检测视角依赖 | 与3D标准误差18-20° | 🔴 高 |
| 缺乏时序平滑处理 | 关键点抖动导致误判 | 🟡 中 |
| 状态机阈值固定 | 慢速动作可能重复计数 | 🟡 中 |
| 阈值缺乏生物力学依据 | 判断标准可能过严/过宽 | 🟢 低 |

---

## 二、改进方案总览

```
┌─────────────────────────────────────────────────────────────┐
│                    改进路线图                                 │
├─────────────────────────────────────────────────────────────┤
│  短期 (1-2周)          中期 (1-2月)          长期 (3-6月)   │
│  ─────────────         ─────────────         ─────────────  │
│  • 时序平滑处理        • 视角检测校正        • ML辅助验证   │
│  • 3D世界坐标支持      • 多帧验证机制        • 多传感器融合  │
│                        • 动态阈值配置        • 专业分析功能  │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、短期改进：时序平滑与3D坐标

### 3.1 时序平滑处理

**问题**: MediaPipe关键点存在抖动，导致角度波动和状态误触发

**方案**: 一维卡尔曼滤波

```python
# 实现文件: src/angle_smoother.py (新建)

import numpy as np
from filterpy.kalman import KalmanFilter

class AngleSmoother:
    """
    角度卡尔曼滤波器
    状态向量: [角度, 角速度]
    """
    def __init__(self, process_noise=0.1, measurement_noise=0.5):
        self.kf = KalmanFilter(dim_x=2, dim_z=1)
        
        # 状态转移矩阵 (匀速模型)
        self.kf.F = np.array([[1., 1.],
                              [0., 1.]])
        
        # 观测矩阵 (仅观测角度)
        self.kf.H = np.array([[1., 0.]])
        
        # 初始协方差
        self.kf.P *= 1000.
        
        # 过程噪声和观测噪声
        self.kf.Q = np.eye(2) * process_noise
        self.kf.R = measurement_noise
        
        self.initialized = False
    
    def update(self, measurement: float) -> float:
        """更新滤波器，返回平滑后的角度"""
        if not self.initialized:
            self.kf.x = np.array([measurement, 0.])
            self.initialized = True
            return measurement
        
        self.kf.predict()
        self.kf.update(np.array([measurement]))
        return self.kf.x[0]
    
    def reset(self):
        """重置滤波器状态"""
        self.initialized = False


# 集成到 squat_counter.py
class SquatCounter:
    def __init__(self, ...):
        # 添加平滑器
        self.left_knee_smoother = AngleSmoother()
        self.right_knee_smoother = AngleSmoother()
    
    def update(self, pose_landmarks):
        # 计算原始角度
        raw_left = self.calculate_angle(left_hip, left_knee, left_ankle)
        raw_right = self.calculate_angle(right_hip, right_knee, right_ankle)
        
        # 平滑处理
        self._left_knee_angle = self.left_knee_smoother.update(raw_left)
        self._right_knee_angle = self.right_knee_smoother.update(raw_right)
```

**效果预期**: 角度抖动减少60-80%，误触发率降低

---

### 3.2 3D世界坐标角度计算

**问题**: 当前仅使用归一化的2D坐标(x,y)，忽略z轴深度信息

**方案**: 使用MediaPipe世界坐标进行真3D角度计算

```python
# 修改文件: src/squat_counter.py

import numpy as np

def calculate_angle_3d(landmarks, idx_a: int, idx_b: int, idx_c: int) -> float:
    """
    使用3D世界坐标计算角度
    
    Args:
        landmarks: MediaPipe姿态地标
        idx_a, idx_b, idx_c: 三个关键点的索引，b为顶点
    
    Returns:
        角度值 (0-180度)
    """
    # 提取3D世界坐标 (单位: 米)
    # 注意: 需要使用 PoseLandmarkerResult.pose_world_landmarks
    a = np.array([
        landmarks[idx_a].x,
        landmarks[idx_a].y,
        landmarks[idx_a].z
    ])
    b = np.array([
        landmarks[idx_b].x,
        landmarks[idx_b].y,
        landmarks[idx_b].z
    ])
    c = np.array([
        landmarks[idx_c].x,
        landmarks[idx_c].y,
        landmarks[idx_c].z
    ])
    
    # 计算向量
    ba = a - b
    bc = c - b
    
    # 余弦定理计算角度
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    
    angle = np.degrees(np.arccos(cosine_angle))
    return angle


# 修改 pose_detector.py 返回世界坐标
class PoseDetector:
    def detect(self, frame, timestamp_ms: int):
        # ... 现有代码 ...
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)
        
        if result.pose_landmarks and result.pose_world_landmarks:
            return {
                'normalized': result.pose_landmarks,      # 归一化坐标
                'world': result.pose_world_landmarks      # 世界坐标 (米)
            }
        return None
```

**效果预期**: 
- 侧向拍摄误差减少40-50%
- 角度精度提升至与专业系统差距 < 10°

---

## 四、中期改进：视角校正与多帧验证

### 4.1 视角检测与校正

**问题**: 膝盖内扣检测依赖正面视角，斜向/侧面误差大

**方案**: 自动检测视角并调整算法

```python
# 实现文件: src/view_detector.py (新建)

from enum import Enum
from dataclasses import dataclass

class ViewAngle(Enum):
    FRONT = "front"         # 正面 (最佳)
    OBLIQUE_LEFT = "oblique_left"   # 左斜
    OBLIQUE_RIGHT = "oblique_right" # 右斜
    SIDE_LEFT = "side_left"         # 左侧
    SIDE_RIGHT = "side_right"       # 右侧


@dataclass
class ViewInfo:
    angle: ViewAngle
    confidence: float
    rotation_degrees: float  # 建议的校正角度


class ViewDetector:
    """
    基于身体比例检测用户相对摄像头的朝向
    """
    
    def detect(self, landmarks) -> ViewInfo:
        """
        检测当前视角
        
        算法原理:
        - 正面: 肩宽 ≈ 髋宽，双眼可见
        - 侧面: 肩宽 << 髋宽，单眼可见
        - 斜向: 介于两者之间
        """
        # 提取关键点
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        left_hip = landmarks[23]
        right_hip = landmarks[24]
        left_eye = landmarks[2]
        right_eye = landmarks[5]
        
        # 计算比例
        shoulder_width = abs(right_shoulder.x - left_shoulder.x)
        hip_width = abs(right_hip.x - left_hip.x)
        eye_distance = abs(right_eye.x - left_eye.x)
        
        # 避免除零
        if hip_width < 0.01:
            hip_width = 0.01
        
        # 视角判断
        shoulder_hip_ratio = shoulder_width / hip_width
        eye_visible = eye_distance > 0.02  # 双眼可见阈值
        
        if shoulder_hip_ratio > 0.8 and eye_visible:
            return ViewInfo(ViewAngle.FRONT, 0.9, 0.0)
        elif shoulder_hip_ratio < 0.3:
            side = ViewAngle.SIDE_LEFT if left_shoulder.x < right_shoulder.x else ViewAngle.SIDE_RIGHT
            return ViewInfo(side, 0.7, 90.0 if side == ViewAngle.SIDE_LEFT else -90.0)
        else:
            oblique = ViewAngle.OBLIQUE_LEFT if left_shoulder.x < right_shoulder.x else ViewAngle.OBLIQUE_RIGHT
            return ViewInfo(oblique, 0.6, shoulder_hip_ratio * 45)


# 集成到 form_analyzer.py
class FormAnalyzer:
    def __init__(self, ...):
        self.view_detector = ViewDetector()
        self.current_view = ViewAngle.FRONT
    
    def analyze(self, landmarks, ...):
        # 检测视角
        view_info = self.view_detector.detect(landmarks[0])
        self.current_view = view_info.angle
        
        # 根据视角调整阈值
        if view_info.angle == ViewAngle.FRONT:
            # 正面: 使用标准阈值
            knee_valgus_threshold = self._config["knee_valgus_error"]
        elif view_info.angle in [ViewAngle.SIDE_LEFT, ViewAngle.SIDE_RIGHT]:
            # 侧面: 禁用膝盖内扣检测或大幅放宽阈值
            knee_valgus_threshold = 1.0  # 实际禁用
        else:
            # 斜向: 适度放宽
            knee_valgus_threshold = self._config["knee_valgus_error"] * 1.5
        
        # 执行检测...
```

**效果预期**: 减少非正面视角的误报率50%以上

---

### 4.2 多帧验证机制

**问题**: 单帧状态转换可能因抖动误触发

**方案**: 连续N帧确认才触发状态转换

```python
# 修改文件: src/squat_counter.py

from collections import deque

class RobustSquatCounter:
    """
    带多帧验证的深蹲计数器
    """
    
    def __init__(self, confirm_frames: int = 3, ...):
        self.confirm_frames = confirm_frames
        self._state_buffer = deque(maxlen=confirm_frames)
        self._pending_state = None
        self._pending_count = 0
        
        # ... 其他初始化 ...
    
    def _update_state(self) -> None:
        """带确认的状态更新"""
        # 判断目标状态
        if self._avg_knee_angle < self.squat_threshold:
            target_state = PoseState.SQUATTING
        elif self._avg_knee_angle > self.standing_threshold:
            target_state = PoseState.STANDING
        else:
            return  # 在过渡区，不改变状态
        
        # 状态缓冲
        self._state_buffer.append(target_state)
        
        # 连续N帧确认才切换
        if len(self._state_buffer) == self.confirm_frames:
            if all(s == target_state for s in self._state_buffer):
                if self._state == PoseState.SQUATTING and target_state == PoseState.STANDING:
                    self._count += 1  # 完成一次深蹲
                self._state = target_state
                self._state_buffer.clear()
    
    def reset(self):
        """重置状态"""
        super().reset()
        self._state_buffer.clear()
```

**效果预期**: 消除快速抖动导致的误计数

---

### 4.3 动态阈值配置

**问题**: 固定阈值不适合不同体型/柔韧性的用户

**方案**: 基于用户特征的动态阈值

```python
# 实现文件: src/adaptive_config.py (新建)

from dataclasses import dataclass

@dataclass
class UserProfile:
    """用户体测数据"""
    height: float          # 身高 (cm)
    leg_length: float      # 腿长 (cm)
    flexibility: str       # 柔韧性: "low", "medium", "high"
    experience: str        # 经验: "beginner", "intermediate", "advanced"


class AdaptiveThresholds:
    """
    基于用户特征动态计算阈值
    参考: ACSM健身指南, NSCA训练标准
    """
    
    # 生物力学基准值
    BASE_STANDING_ANGLE = 170.0
    BASE_SQUAT_ANGLE = 85.0
    BASE_DEPTH_ERROR = 110.0
    
    def __init__(self, profile: UserProfile):
        self.profile = profile
        self._calculate_thresholds()
    
    def _calculate_thresholds(self):
        """计算个性化阈值"""
        # 身高修正: 高个子阈值略宽
        height_factor = (self.profile.height - 170) / 100 * 5
        
        # 腿长比例修正
        leg_ratio = self.profile.leg_length / self.profile.height
        leg_factor = (leg_ratio - 0.5) * 10
        
        # 柔韧性修正
        flexibility_adjust = {
            "low": 10,      # 柔韧性差 -> 阈值放宽
            "medium": 0,
            "high": -5      # 柔韧性好 -> 阈值收紧
        }
        flex_factor = flexibility_adjust.get(self.profile.flexibility, 0)
        
        # 经验修正
        experience_adjust = {
            "beginner": 10,
            "intermediate": 0,
            "advanced": -5
        }
        exp_factor = experience_adjust.get(self.profile.experience, 0)
        
        # 综合修正
        total_adjust = height_factor + leg_factor + flex_factor + exp_factor
        
        # 计算最终阈值
        self.standing_angle = self.BASE_STANDING_ANGLE + total_adjust
        self.squat_angle = self.BASE_SQUAT_ANGLE + total_adjust * 0.5
        self.depth_error = self.BASE_DEPTH_ERROR + total_adjust
        
        # 限制范围
        self.standing_angle = max(160, min(175, self.standing_angle))
        self.squat_angle = max(80, min(95, self.squat_angle))
    
    def get_thresholds(self) -> dict:
        return {
            "standing_angle": self.standing_angle,
            "squat_angle": self.squat_angle,
            "depth_error": self.depth_error
        }


# 使用示例
profile = UserProfile(
    height=180,
    leg_length=95,
    flexibility="medium",
    experience="intermediate"
)
thresholds = AdaptiveThresholds(profile)

counter = SquatCounter(
    standing_threshold=thresholds.standing_angle,
    squat_threshold=thresholds.squat_angle
)
```

---

## 五、膝盖内扣检测改进

### 5.1 问题分析

当前实现基于2D投影的髋宽比:

```python
# 当前方法的问题
ratio = knee_distance / hip_width  # 仅考虑x方向
```

**误差来源**:
1. 仅考虑x轴投影，忽略y和z
2. 正面视角检测较准，侧面完全失效
3. 与3D动捕系统误差18-20° (Asaeda 2024)

### 5.2 改进方案: 3D向量法

```python
# 修改文件: src/form_analyzer.py

def _check_knee_valgus_3d(self, world_landmarks) -> dict:
    """
    使用3D世界坐标检测膝盖内扣
    
    原理: 计算股骨-胫骨在冠状面的夹角
    """
    # 提取3D世界坐标
    left_hip = np.array([world_landmarks[23].x, world_landmarks[23].y, world_landmarks[23].z])
    right_hip = np.array([world_landmarks[24].x, world_landmarks[24].y, world_landmarks[24].z])
    left_knee = np.array([world_landmarks[25].x, world_landmarks[25].y, world_landmarks[25].z])
    right_knee = np.array([world_landmarks[26].x, world_landmarks[26].y, world_landmarks[26].z])
    left_ankle = np.array([world_landmarks[27].x, world_landmarks[27].y, world_landmarks[27].z])
    right_ankle = np.array([world_landmarks[28].x, world_landmarks[28].y, world_landmarks[28].z])
    
    # 计算大腿向量 (髋->膝)
    left_thigh = left_knee - left_hip
    right_thigh = right_knee - right_hip
    
    # 计算小腿向量 (膝->踝)
    left_shin = left_ankle - left_knee
    right_shin = right_ankle - right_knee
    
    # 计算膝关节角度 (冠状面投影)
    def coronal_plane_angle(thigh, shin):
        """计算冠状面(XZ平面)上的膝盖内外翻角度"""
        # 投影到冠状面 (忽略Y轴)
        thigh_xz = np.array([thigh[0], thigh[2]])
        shin_xz = np.array([shin[0], shin[2]])
        
        # 计算夹角
        dot = np.dot(thigh_xz, shin_xz)
        norm = np.linalg.norm(thigh_xz) * np.linalg.norm(shin_xz) + 1e-8
        
        cosine = np.clip(dot / norm, -1, 1)
        return np.degrees(np.arccos(cosine))
    
    left_knee_angle = coronal_plane_angle(left_thigh, left_shin)
    right_knee_angle = coronal_plane_angle(right_thigh, right_shin)
    
    # 内扣判断: 角度偏离180° (直线) 的程度
    # 正常应该接近180°，内扣时角度减小
    left_valgus = 180 - left_knee_angle
    right_valgus = 180 - right_knee_angle
    
    # 计算内扣评分 (0-1)
    def valgus_score(angle_deviation):
        """将角度偏差转换为0-1评分"""
        # 参考值: 10°以内正常, 20°以上严重内扣
        if angle_deviation < 10:
            return 0.0
        elif angle_deviation > 20:
            return 1.0
        else:
            return (angle_deviation - 10) / 10
    
    return {
        "left_knee_valgus_deg": left_valgus,
        "right_knee_valgus_deg": right_valgus,
        "left_valgus_score": valgus_score(abs(left_valgus)),
        "right_valgus_score": valgus_score(abs(right_valgus)),
        "method": "3d_coronal_plane"
    }
```

**效果预期**: 将视角依赖误差从18-20°降低到8-10°

---

## 六、配置参数优化建议

### 6.1 基于文献的阈值调整

| 参数 | 当前值 | 建议值 | 文献依据 |
|-----|-------|-------|---------|
| 站立阈值 | 165° | 170° | Straub 2024 |
| 下蹲阈值 | 90° | 85° | Deep Squat定义 |
| 深度错误(NORMAL) | 115° | 110° | Half Squat标准 |
| 深度错误(STRICT) | 100° | 95° | ACSM指南 |
| 膝盖内扣错误 | 0.4 | 0.3 | Asaeda 2024归一化建议 |
| 背部弯曲错误 | 25° | 30° | 生物力学躯干角38°±6° |

### 6.2 检测置信度优化

```python
# 当前配置
min_pose_detection_confidence = 0.5
min_tracking_confidence = 0.5

# 建议配置 (平衡精度和稳定性)
min_pose_detection_confidence = 0.6   # 提高初始检测精度
min_tracking_confidence = 0.7         # 提高跟踪稳定性
```

---

## 七、实施优先级矩阵

```
         影响程度
           ↑
    高     │  ①3D坐标  ④多帧验证
           │     ┌───────┐
           │     │  高   │
           │     │ 优先  │
    中     │  ②时序平滑  ⑤视角校正
           │     ├───────┤
           │     │  中   │
           │     │ 优先  │
    低     │  ③动态阈值  ⑥阈值优化
           │     └───────┘
           └──────────────────→ 实施难度
                低      中      高
```

### 建议实施顺序

| 阶段 | 任务 | 工作量 | 收益 |
|-----|------|-------|------|
| **第1周** | 3D世界坐标支持 | 2天 | 精度提升40% |
| **第1周** | 时序平滑处理 | 1天 | 稳定性提升60% |
| **第2周** | 多帧验证机制 | 1天 | 消除误计数 |
| **第2周** | 阈值参数优化 | 0.5天 | 符合学术标准 |
| **第3-4周** | 视角检测校正 | 3天 | 减少误报50% |
| **第3-4周** | 动态阈值配置 | 2天 | 个性化适配 |

---

## 八、预期改进效果

| 指标 | 改进前 | 改进后 | 提升幅度 |
|-----|-------|-------|---------|
| 角度计算精度 | ±15° | ±8° | 47%↑ |
| 膝盖内扣检测误差 | 18-20° | 8-10° | 50%↑ |
| 误计数率 | ~5% | <1% | 80%↑ |
| 关键点抖动 | 明显 | 轻微 | 60%↓ |
| 非正面视角误报 | 高 | 低 | 50%↓ |

---

**文档版本**: v1.0  
**创建日期**: 2026年3月24日