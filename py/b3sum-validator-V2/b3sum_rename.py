import os
import sys
import hashlib
import re
from pathlib import Path
import platform

# 根据平台导入不同的模块
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'
IS_MAC = platform.system() == 'Darwin'

if IS_WINDOWS:
    import winreg
    import ctypes
    try:
        import tkinter as tk
        from tkinter import messagebox
        HAS_GUI = True
    except:
        HAS_GUI = False
else:
    HAS_GUI = False

try:
    import blake3
except ImportError:
    print("安装 blake3 库...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "blake3"])
    import blake3

def is_admin():
    """检查程序是否以管理员/root权限运行"""
    if IS_WINDOWS:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        # Linux/Mac: 检查是否为root用户
        return os.geteuid() == 0

def calculate_hash(file_path):
    """计算文件的BLAKE3哈希值"""
    hasher = blake3.blake3()
    with open(file_path, 'rb') as f:
        chunk = f.read(8192)
        while chunk:
            hasher.update(chunk)
            chunk = f.read(8192)
    return hasher.hexdigest()

def rename_file(file_path):
    """计算哈希值并重命名文件"""
    # 检查文件是否存在
    if not os.path.isfile(file_path):
        return f"错误: 文件不存在: {file_path}"
    
    try:
        # 计算BLAKE3哈希值
        hash_value = calculate_hash(file_path)
        hash_prefix = hash_value[:16]  # 获取前16位
        
        # 解析文件路径
        path_obj = Path(file_path)
        directory = path_obj.parent
        name = path_obj.stem
        extension = path_obj.suffix
        
        # 检查文件名是否已经包含哈希值
        pattern = r'\(BLANK3：[a-f0-9]{16}\)'
        if re.search(pattern, name):
            # 移除旧的哈希值标记
            name = re.sub(pattern, '', name).strip()
        
        # 创建新文件名
        new_name = f"{name}(BLANK3：{hash_prefix}){extension}"
        new_path = directory / new_name
        
        # 重命名文件
        os.rename(file_path, new_path)
        
        return f"已成功重命名文件:\n{os.path.basename(file_path)} → {new_name}"
    
    except Exception as e:
        return f"重命名时出错: {str(e)}"

def register_context_menu():
    """注册右键菜单"""
    if IS_WINDOWS:
        return register_context_menu_windows()
    elif IS_LINUX:
        return register_context_menu_linux()
    elif IS_MAC:
        return "macOS暂不支持自动注册右键菜单，请使用命令行方式：python b3sum_rename.py <文件路径>"
    else:
        return "不支持的操作系统"

def unregister_context_menu():
    """移除右键菜单"""
    if IS_WINDOWS:
        return unregister_context_menu_windows()
    elif IS_LINUX:
        return unregister_context_menu_linux()
    elif IS_MAC:
        return "macOS不需要卸载右键菜单"
    else:
        return "不支持的操作系统"

def register_context_menu_windows():
    """Windows平台注册右键菜单"""
    if not is_admin():
        return "需要管理员权限！请右键点击程序选择'以管理员身份运行'"
    
    try:
        script_path = os.path.abspath(sys.argv[0])
        
        # 为所有文件创建右键菜单
        key_path = r'*\shell\B3SumRename'
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "使用BLAKE3计算哈希并重命名")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, sys.executable)
        
        # 添加命令
        command_key_path = f'{key_path}\\command'
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_key_path) as key:
            command = f'"{sys.executable}" "{script_path}" "%1"'
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
        
        return "成功注册到右键菜单！"
    except Exception as e:
        return f"注册右键菜单时出错: {str(e)}"

def unregister_context_menu_windows():
    """Windows平台移除右键菜单"""
    if not is_admin():
        return "需要管理员权限！请右键点击程序选择'以管理员身份运行'"
    
    try:
        key_path = r'*\shell\B3SumRename'
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, f'{key_path}\\command')
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path)
        return "成功移除右键菜单！"
    except Exception as e:
        return f"移除右键菜单时出错: {str(e)}"

def register_context_menu_linux():
    """Linux平台注册右键菜单（Nautilus文件管理器）"""
    if not is_admin():
        return "需要root权限！请使用 sudo 运行此程序"
    
    try:
        script_path = os.path.abspath(sys.argv[0])
        
        # 创建Nautilus脚本目录
        script_dir = os.path.expanduser('~/.local/share/nautilus/scripts')
        os.makedirs(script_dir, exist_ok=True)
        
        # 创建脚本文件
        script_file = os.path.join(script_dir, 'BLAKE3-Rename')
        with open(script_file, 'w') as f:
            f.write(f'''#!/bin/bash
# Nautilus script for BLAKE3 renaming
{sys.executable} "{script_path}" "$1"
''')
        
        # 设置可执行权限
        os.chmod(script_file, 0o755)
        
        return "成功注册到右键菜单！\n重启文件管理器后生效。"
    except Exception as e:
        return f"注册右键菜单时出错: {str(e)}"

def unregister_context_menu_linux():
    """Linux平台移除右键菜单"""
    try:
        script_dir = os.path.expanduser('~/.local/share/nautilus/scripts')
        script_file = os.path.join(script_dir, 'BLAKE3-Rename')
        
        if os.path.exists(script_file):
            os.remove(script_file)
            return "成功移除右键菜单！"
        else:
            return "右键菜单未注册"
    except Exception as e:
        return f"移除右键菜单时出错: {str(e)}"

def show_gui():
    """显示简单的GUI界面用于注册/移除右键菜单"""
    if not HAS_GUI:
        print("当前环境不支持图形界面")
        print("使用方法:")
        print("  注册右键菜单: python b3sum_rename.py --register")
        print("  移除右键菜单: python b3sum_rename.py --unregister")
        print("  重命名文件: python b3sum_rename.py <文件路径>")
        return
    
    root = tk.Tk()
    root.title("BLAKE3 哈希重命名工具")
    root.geometry("400x250")
    root.resizable(False, False)
    
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    title = tk.Label(frame, text="BLAKE3 文件哈希重命名工具", font=("Arial", 14, "bold"))
    title.pack(pady=10)
    
    # 显示当前操作系统
    os_name = platform.system()
    os_label = tk.Label(frame, text=f"当前系统: {os_name}", font=("Arial", 10))
    os_label.pack(pady=5)
    
    if IS_MAC:
        info_label = tk.Label(frame, text="macOS请使用命令行:\npython b3sum_rename.py <文件路径>", 
                            font=("Arial", 10), fg="blue")
        info_label.pack(pady=10)
    else:
        register_btn = tk.Button(frame, text="注册到右键菜单", width=20, height=2,
                               command=lambda: messagebox.showinfo("结果", register_context_menu()))
        register_btn.pack(pady=5)
        
        unregister_btn = tk.Button(frame, text="从右键菜单移除", width=20, height=2,
                                 command=lambda: messagebox.showinfo("结果", unregister_context_menu()))
        unregister_btn.pack(pady=5)
    
    root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        show_gui()
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg == "--register":
            result = register_context_menu()
            print(result)
        elif arg == "--unregister":
            result = unregister_context_menu()
            print(result)
        else:
            # 文件路径，重命名文件
            file_path = arg
            result = rename_file(file_path)
            print(result)
    else:
        print("用法:")
        print("  python b3sum_rename.py                    # 打开GUI（仅Windows）")
        print("  python b3sum_rename.py --register         # 注册右键菜单")
        print("  python b3sum_rename.py --unregister       # 移除右键菜单")
        print("  python b3sum_rename.py <文件路径>         # 重命名文件")
