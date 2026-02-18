# b3sum-validator-V2
跨平台 BLAKE3 哈希文件重命名工具

## 功能介绍
计算文件的 BLAKE3 哈希值，并将前16位添加到文件名：`原文件名(BLAKE3：哈希值前16位).扩展名`

**支持平台**：Windows、Linux、macOS

## 快速开始

### Windows 用户（推荐）

#### 方式一：使用可执行文件（无需安装 Python）
1. 从 [Releases](https://github.com/coperlm/b3sum-validator-V2/releases) 下载最新的 `b3sum_rename.exe`
2. 双击运行，点击"注册到右键菜单"
3. 右键点击任意文件，选择"使用BLAKE3计算哈希并重命名"即可

**卸载**：双击运行 exe，点击"从右键菜单移除"

#### 方式二：使用 Python 脚本
1. 安装依赖：`pip install -r requirements.txt`
2. 以管理员身份运行 `start_tool.bat`，点击"注册到右键菜单"

### Linux 用户

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **使用方式**

   **命令行重命名文件**：
   ```bash
   python b3sum_rename.py <文件路径>
   ```

   **注册右键菜单**（需要 root 权限）：
   ```bash
   sudo python b3sum_rename.py --register
   ```
   注册后，在 Nautilus 文件管理器中右键文件可看到"BLAKE3-Rename"选项
   
   **移除右键菜单**：
   ```bash
   python b3sum_rename.py --unregister
   ```

### macOS 用户

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **使用方式**

   **命令行重命名文件**：
   ```bash
   python b3sum_rename.py <文件路径>
   ```

   > 注：macOS 暂不支持右键菜单集成

## 命令行参数

```bash
python b3sum_rename.py                    # 打开GUI（仅Windows）
python b3sum_rename.py --register         # 注册右键菜单
python b3sum_rename.py --unregister       # 移除右键菜单
python b3sum_rename.py <文件路径>         # 重命名文件
```

## 自动发布

本项目使用 GitHub Actions 自动构建和发布：
- 每次推送到 `main` 分支会自动创建新版本
- 版本号自动递增（v1.0.0 → v1.0.1 → v1.0.2...）
- 自动生成 Windows 可执行文件并发布到 Releases

## 开发

### 本地构建可执行文件

```bash
pip install pyinstaller
pyinstaller --onefile --name b3sum_rename b3sum_rename.py
```

生成的可执行文件在 `dist/` 目录中