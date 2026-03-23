# 🏋️ Fitness Pose Validator

[![Version](https://img.shields.io/badge/version-v2.4.0-blue.svg)](https://github.com/kooibox/fitness-pose-validator)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

基于 **MediaPipe** 的实时健身动作检测与分析系统，支持深蹲计数、姿态评估、数据可视化和智能分析。

## ✨ 功能特性

### 🎯 实时检测
- **姿态识别**: 基于 MediaPipe Pose Landmarker，实时追踪 33 个人体关键点
- **深蹲计数**: 智能状态机算法，准确识别深蹲动作并自动计数
- **动作分析**: 实时检测膝盖内扣、背部弯曲、下蹲深度等姿态问题
- **即时反馈**: 视觉和文字提示，指导用户纠正动作

### 📊 数据大屏
- **概览面板**: 核心 KPI 指标卡片、趋势折线图、能力雷达图
- **趋势分析**: 多维度数据分析，时段分布、深度分布可视化
- **训练详情**: 单次训练报告、膝关节角度曲线、AI 智能分析
- **能力评估**: 五维能力雷达图、综合评分、训练目标管理

### 🖥️ 多端支持
- **桌面 GUI**: PyQt6 原生界面，流畅的用户体验
- **Web 大屏**: 深色科技主题，响应式设计
- **服务器**: 轻量级 HTTP 服务，支持数据上传和 API 查询

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 摄像头（USB 或内置）
- 推荐 8GB+ 内存

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/kooibox/fitness-pose-validator.git
cd fitness-pose-validator

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 运行程序

```bash
# 启动 GUI 界面
python run_gui.py

# 或启动命令行版本
python main.py
```

### 启动数据大屏

```bash
# 方式 1: 直接打开 HTML
open dashboard/index.html

# 方式 2: 使用 HTTP 服务器
cd dashboard && python -m http.server 8080
```

### 启动数据服务器

```bash
cd fitness-docker-deploy/server
# 开发模式
uvicorn main:app --reload --host 0.0.0.0 --port 8081

# 或使用 Docker Compose
cd fitness-docker-deploy
docker-compose up -d
```

### API 文档

服务启动后访问：
- Swagger UI: http://localhost:8081/docs
- ReDoc: http://localhost:8081/redoc

## 📁 项目结构

```
fitness-pose-validator/
├── main.py                    # 命令行入口
├── run_gui.py                 # GUI 入口
├── requirements.txt           # Python 依赖
│
├── src/                       # 核心模块
│   ├── config.py              # 配置管理
│   ├── pose_detector.py       # MediaPipe 姿态检测
│   ├── squat_counter.py       # 深蹲计数状态机
│   ├── form_analyzer.py       # 动作姿态分析
│   ├── analyzer.py            # 训练数据分析
│   ├── database.py            # SQLite 数据存储
│   ├── visualizer.py          # OpenCV 可视化
│   └── data_exporter.py       # 数据导出
│
├── gui/                       # PyQt6 桌面界面
│   ├── main_window.py         # 主窗口
│   ├── pages/                 # 页面组件
│   │   ├── training_page.py   # 训练页面
│   │   ├── history_page.py    # 历史记录
│   │   └── settings_page.py   # 设置页面
│   ├── widgets/               # 自定义控件
│   │   ├── video_widget.py    # 视频显示
│   │   ├── stats_panel.py     # 统计面板
│   │   └── angle_chart.py     # 角度图表
│   └── workers/               # 后台线程
│       └── detection_worker.py
│
├── fitness-docker-deploy/     # Docker 部署
│   ├── server/                # FastAPI 服务器
│   │   ├── main.py            # FastAPI 入口
│   │   ├── auth.py            # JWT 认证模块
│   │   ├── database.py        # 数据库初始化
│   │   ├── models.py          # Pydantic 模型
│   │   ├── routers/           # API 路由
│   │   │   ├── auth.py        # 认证接口
│   │   │   ├── sessions.py    # 训练数据接口
│   │   │   ├── dashboard.py   # 大屏数据接口
│   │   │   └── llm.py         # LLM 分析接口
│   │   └── analysis/          # 数据分析模块
│   ├── dashboard/             # Web 前端
│   └── docker-compose.yml     # Docker 编排
│
├── dashboard/                 # Web 数据大屏（独立版）
│   ├── index.html             # 主页面
│   ├── css/
│   │   └── styles.css         # 深色主题样式
│   └── js/
│       ├── api.js             # API 接口
│       ├── charts.js          # ECharts 配置
│       └── app.js             # 应用逻辑
│
└── data/                      # 数据存储
    ├── training_history.db    # 训练历史数据库
    └── exports/               # 导出文件
```

## 🔧 技术栈

### 核心技术

| 技术 | 版本 | 用途 |
|------|------|------|
| **MediaPipe** | 0.10+ | 人体姿态检测与关键点追踪 |
| **OpenCV** | 4.x | 图像处理与视频捕获 |
| **PyQt6** | 6.x | 桌面 GUI 框架 |
| **FastAPI** | 0.100+ | 高性能 Web 框架 |
| **SQLite** | 3.x | 本地数据存储 |
| **Matplotlib** | 3.x | 数据可视化 |

### 前端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| **ECharts** | 5.4 | 数据图表可视化 |
| **CSS Grid** | - | 响应式布局 |
| **Fetch API** | - | HTTP 请求 |

### 算法原理

```
┌─────────────────────────────────────────────────────────────┐
│                     深蹲检测算法流程                          │
└─────────────────────────────────────────────────────────────┘

摄像头 → MediaPipe Pose → 关键点提取
                            ↓
                    计算膝关节角度
                            ↓
                    ┌───────┴───────┐
                    ↓               ↓
              角度 < 90°        角度 > 165°
              (下蹲中)          (站立中)
                    ↓               ↓
                    └───────┬───────┘
                            ↓
                    状态机状态转换
                    (STANDING ↔ SQUATTING)
                            ↓
                    深蹲计数 +1
```

## 📡 API 文档

### 认证 API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/auth/login` | POST | 用户登录，获取 JWT Token |
| `/api/v1/auth/me` | GET | 获取当前用户信息（需认证） |

### 训练数据 API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/sessions/upload` | POST | 上传训练数据（需认证） |
| `/api/v1/sessions/` | GET | 获取训练会话列表 |
| `/api/v1/sessions/{id}` | GET | 获取单个会话详情 |

### Dashboard API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/dashboard/overview` | GET | 概览统计 |
| `/api/v1/dashboard/trend` | GET | 趋势数据 |
| `/api/v1/dashboard/distribution` | GET | 分布数据 |
| `/api/v1/dashboard/heatmap` | GET | 热力图数据 |
| `/api/v1/dashboard/radar` | GET | 雷达图数据 |
| `/api/v1/dashboard/best-records` | GET | 最佳记录 |
| `/api/v1/dashboard/recent-sessions` | GET | 最近会话 |

### LLM Analysis API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/llm/analyze` | POST | 提交分析请求 |
| `/api/v1/llm/status/{id}` | GET | 查询分析状态 |
| `/api/v1/llm/types` | GET | 获取分析类型 |

### 请求示例

```bash
# 用户登录
curl -X POST http://localhost:8081/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test123"}'

# 上传训练数据（需 Token）
curl -X POST http://localhost:8081/api/v1/sessions/upload \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"version": "2.4.0", "session": {...}, "records": [...]}'

# 获取概览统计
curl http://localhost:8081/api/v1/dashboard/overview

# LLM 分析
curl -X POST http://localhost:8081/api/v1/llm/analyze \
  -H "Content-Type: application/json" \
  -d '{"session_ids": [1, 2], "analysis_type": "session"}'
```

## ⚙️ 配置说明

主要配置项位于 `src/config.py`：

```python
# 姿态检测配置
DETECTION_CONFIDENCE = 0.5    # 检测置信度阈值
TRACKING_CONFIDENCE = 0.5     # 追踪置信度阈值

# 深蹲检测配置
STANDING_ANGLE = 165          # 站立角度阈值
SQUATTING_ANGLE = 90          # 下蹲角度阈值

# 动作分析配置
STRICTNESS_LEVEL = "standard" # 严格程度 (loose/standard/strict)
```

## 🎨 界面预览

### 桌面 GUI

- 实时视频显示 + 姿态骨架
- 膝关节角度实时曲线
- 深蹲计数和状态指示
- 动作反馈提示

### Web 数据大屏

- 深色科技主题
- KPI 卡片 + 趋势图表
- 能力雷达图
- 训练历史记录

## 🛠️ 开发指南

### 运行测试

```bash
python -m pytest tests/
```

### 代码规范

- 遵循 PEP 8 规范
- 使用类型注解
- 添加文档字符串

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📝 更新日志

### v2.4.0 (2026-03-23)

#### 🚀 重大更新：服务器端 FastAPI 迁移

##### 新增
- **FastAPI 框架**: 使用 FastAPI 替代 http.server，提供更好的性能和自动 API 文档
- **JWT 认证模块**: 支持用户登录和 Token 认证，预置测试账号
- **数据库初始化模块**: 自动创建用户表和训练数据表
- **Pydantic 数据模型**: 完整的请求/响应模型定义
- **路由模块化设计**:
  - `routers/auth.py`: 登录接口
  - `routers/sessions.py`: 训练数据上传/查询
  - `routers/dashboard.py`: Dashboard 数据接口 (7个端点)
  - `routers/llm.py`: LLM 分析接口 (3个端点)
- **环境变量配置**: `.env.example` 支持灵活配置

##### 优化
- 更新 Dockerfile 使用 uvicorn 启动
- 简化 docker-compose.yml 配置
- 存档旧 http.server 实现到 `_archive_http_server/`

##### 技术栈更新
- 新增依赖: FastAPI, uvicorn, python-jose, passlib, python-multipart

### v2.3.0 (2026-03-21)

#### 新增
- 设置页面重构：双栏布局设计，分类导航（摄像头、检测参数、界面、存储、服务器）
- 历史记录页面重构：下拉栏模式，卡片式信息展示
- 服务器连接配置：默认服务器地址和 API Key 预配置
- Docker 部署支持：Dockerfile 和 docker-compose 配置

#### 优化
- QSS 主题样式增强：QCheckBox、输入控件样式完善
- 组件样式统一：按钮、卡片风格一致化
- 代码结构简化：移除冗余嵌套容器

### v2.2.0 (2026-03-20)

#### 新增
- 服务器端数据分析 API（Dashboard Analyzer）
- LLM 分析接口（预留 stub，支持 5 种分析类型）
- REST API 端点（Dashboard 7个 + LLM 3个）
- Web 数据大屏前端（深色科技主题，4个功能页面）

#### 优化
- 扩展服务器路由支持
- 完善 API 响应格式

### v2.1.1 (2026-03-15)

- 修复已知问题
- 性能优化

### v2.1.0 (2026-03-10)

- 添加数据上传功能
- GUI 界面优化

## ❓ 常见问题

### Q: 摄像头无法打开？

A: 检查摄像头是否被其他程序占用，或尝试修改 `config.py` 中的摄像头索引。

### Q: MediaPipe 模型下载失败？

A: 程序会自动下载模型，如下载失败可手动下载 `pose_landmarker_heavy.task` 放入 `models/` 目录。

### Q: 数据大屏无法连接服务器？

A: 确保服务器已启动（`python server/run_server.py`），并检查端口是否被占用。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👥 作者

- **kooibox** - [GitHub](https://github.com/kooibox)

## 🙏 致谢

- [MediaPipe](https://google.github.io/mediapipe/) - 人体姿态检测
- [OpenCV](https://opencv.org/) - 计算机视觉库
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI 框架
- [ECharts](https://echarts.apache.org/) - 数据可视化

---

**如果这个项目对你有帮助，请给一个 ⭐ Star！**
