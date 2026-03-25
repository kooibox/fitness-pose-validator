# Fitness Pose Validator - Windows 打包指南

## 前置条件

### 1. Python 环境
- Python 3.8 或更高版本
- 已安装 pip

### 2. 创建虚拟环境
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖
```cmd
pip install -r requirements.txt
pip install pyinstaller
```

## 打包方式

### 方式一：单文件打包（推荐）

**优点**：
- 生成单个 exe 文件，便于分发
- 用户使用简单

**缺点**：
- 启动稍慢（需要解压）
- 文件体积较大（约 200-300MB）

**执行命令**：
```cmd
build_single_exe.bat
```

**输出文件**：`dist\FitnessPoseValidator.exe`

### 方式二：目录打包

**优点**：
- 启动速度快
- 文件体积较小

**缺点**：
- 需要整个目录
- 分发不便

**执行命令**：
```cmd
build_windows.bat
```

**输出目录**：`dist\FitnessPoseValidator\`

## 打包配置说明

### fitness-pose-validator.spec

```python
# 入口文件
'run_gui.py'  # GUI 入口

# 需要打包的数据文件
('models/pose_landmarker.task', 'models')  # MediaPipe 模型
('gui/resources', 'gui/resources')         # GUI 资源

# 隐藏导入的模块
'PyQt6', 'cv2', 'mediapipe', 'numpy', 'matplotlib', 'PIL'
```

## 常见问题

### Q1: 打包失败，提示找不到模块

**解决方案**：
```cmd
# 确保所有依赖已安装
pip install -r requirements.txt

# 手动添加隐藏导入
pyinstaller --hidden-import <模块名> ...
```

### Q2: 打包后运行闪退

**解决方案**：
1. 使用命令行运行 exe 查看错误信息：
   ```cmd
   cd dist\FitnessPoseValidator
   FitnessPoseValidator.exe
   ```

2. 检查模型文件是否正确打包：
   - 确保 `models/pose_landmarker.task` 存在
   - 检查 `--add-data` 参数格式

### Q3: 文件体积过大

**优化方案**：
1. 使用 `--exclude-module` 排除不需要的模块：
   ```cmd
   pyinstaller --exclude-module tkinter --exclude-module test ...
   ```

2. 使用 UPX 压缩：
   ```cmd
   pyinstaller --upx-dir=C:\upx ...
   ```

### Q4: 启动速度慢

**优化方案**：
1. 使用目录打包（非单文件）
2. 减少隐藏导入数量
3. 优化模型加载逻辑

## 打包后测试

### 功能测试清单

- [ ] 程序能正常启动
- [ ] 摄像头能正常打开
- [ ] 姿态检测正常工作
- [ ] 深蹲计数准确
- [ ] 历史记录能正常显示
- [ ] 设置能正常保存
- [ ] 截图功能正常
- [ ] 删除功能正常

### 性能测试

- [ ] 启动时间 < 10秒
- [ ] 帧率 > 20 FPS
- [ ] 内存占用 < 500MB
- [ ] CPU 占用 < 30%

## 分发指南

### 单文件分发

直接发送 `dist\FitnessPoseValidator.exe` 即可。

### 目录分发

压缩整个 `dist\FitnessPoseValidator\` 目录：
```cmd
cd dist
tar -a -c -f FitnessPoseValidator.zip FitnessPoseValidator
```

### 系统要求

- Windows 10 或更高版本
- 摄像头（内置或外接）
- 至少 4GB 内存
- 至少 500MB 磁盘空间

## 版本信息

- 版本号：2.0.0
- 构建工具：PyInstaller 6.x
- Python 版本：3.8+
- 支持平台：Windows 10/11
