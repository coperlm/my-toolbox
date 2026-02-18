import os
import sys
from datetime import datetime
import re
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import winreg
import ctypes

def is_admin():
    """检查程序是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_date_prefix():
    """获取当前日期前缀，格式为[YYMMDD]"""
    now = datetime.now()
    # 年份取后两位，月日补零到两位
    year = now.year % 100  # 获取后两位年份
    month = now.month
    day = now.day
    return f"[{year:02d}{month:02d}{day:02d}]"

def rename_file(file_path):
    """添加日期前缀并重命名文件"""
    # 检查文件是否存在
    if not os.path.isfile(file_path):
        return f"错误: 文件不存在: {file_path}"
    
    try:
        # 获取日期前缀
        date_prefix = get_date_prefix()
        
        # 解析文件路径
        path_obj = Path(file_path)
        directory = path_obj.parent
        original_filename = path_obj.name
        
        # 检查文件名是否已经包含日期前缀
        pattern = r'^\[\d{6}\]'
        if re.match(pattern, original_filename):
            # 移除旧的日期前缀
            original_filename = re.sub(pattern, '', original_filename)
        
        # 创建新文件名
        new_filename = f"{date_prefix}{original_filename}"
        new_path = directory / new_filename
        
        # 检查新文件名是否已存在
        if new_path.exists():
            return f"错误: 目标文件名已存在: {new_filename}"
        
        # 重命名文件
        os.rename(file_path, new_path)
        
        return f"已成功重命名文件:\n{path_obj.name} → {new_filename}"
    
    except Exception as e:
        return f"重命名时出错: {str(e)}"

def register_context_menu():
    """注册右键菜单"""
    if not is_admin():
        # 如果不是以管理员身份运行，重新以管理员身份启动
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        return
    
    try:
        script_path = os.path.abspath(sys.argv[0])
        
        # 为所有文件创建右键菜单
        key_path = r'*\\shell\\DateRename'
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "添加日期前缀并重命名")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, sys.executable)
        
        # 添加命令
        command_key_path = f'{key_path}\\command'
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_key_path) as key:
            command = f'"{sys.executable}" "{script_path}" "%1"'
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
        
        return "成功注册到右键菜单！"
    except Exception as e:
        return f"注册右键菜单时出错: {str(e)}"

def unregister_context_menu():
    """移除右键菜单"""
    if not is_admin():
        # 如果不是以管理员身份运行，重新以管理员身份启动
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        return
    
    try:
        key_path = r'*\\shell\\DateRename'
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, f'{key_path}\\command')
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path)
        return "成功移除右键菜单！"
    except Exception as e:
        return f"移除右键菜单时出错: {str(e)}"

def show_gui():
    """显示简单的GUI界面用于注册/移除右键菜单"""
    root = tk.Tk()
    root.title("日期前缀重命名工具")
    root.geometry("400x300")
    root.resizable(False, False)
    
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    title = tk.Label(frame, text="日期前缀文件重命名工具", font=("Arial", 14, "bold"))
    title.pack(pady=10)
    
    # 显示当前日期前缀示例
    current_prefix = get_date_prefix()
    example_label = tk.Label(frame, text=f"当前日期前缀: {current_prefix}", font=("Arial", 10))
    example_label.pack(pady=5)
    
    example_label2 = tk.Label(frame, text=f"示例: test.cpp → {current_prefix}test.cpp", font=("Arial", 10), fg="gray")
    example_label2.pack(pady=5)
    
    register_btn = tk.Button(frame, text="注册到右键菜单", width=20, height=2,
                           command=lambda: messagebox.showinfo("结果", register_context_menu()))
    register_btn.pack(pady=10)
    
    unregister_btn = tk.Button(frame, text="从右键菜单移除", width=20, height=2,
                             command=lambda: messagebox.showinfo("结果", unregister_context_menu()))
    unregister_btn.pack(pady=5)
    
    # 测试功能
    test_btn = tk.Button(frame, text="测试重命名功能", width=20, height=1,
                        command=test_rename)
    test_btn.pack(pady=5)
    
    root.mainloop()

def test_rename():
    """测试重命名功能"""
    from tkinter import filedialog
    file_path = filedialog.askopenfilename(title="选择要重命名的文件")
    if file_path:
        result = rename_file(file_path)
        messagebox.showinfo("重命名结果", result)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        show_gui()
    elif len(sys.argv) == 2:
        file_path = sys.argv[1]
        # 直接重命名，不显示任何弹窗
        result = rename_file(file_path)
        # 可选：如果需要显示结果，取消下面的注释
        # messagebox.showinfo("重命名结果", result)
    else:
        print("用法: date_rename.py [文件路径]")
