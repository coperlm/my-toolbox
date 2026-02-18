import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import threading
import pyperclip
from tkinter.font import Font
import sys
import platform

class B3SumGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("B3sum 验证工具")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # 设置窗口图标（如果在Windows上）
        if platform.system() == "Windows":
            try:
                self.root.iconbitmap(default="")  # 如果有图标文件，可以放在这里
            except:
                pass
                
        # 创建自定义字体
        self.header_font = Font(family="Segoe UI" if platform.system() == "Windows" else "Helvetica", 
                               size=11, weight="bold")
        self.normal_font = Font(family="Segoe UI" if platform.system() == "Windows" else "Helvetica", 
                               size=10)
        self.mono_font = Font(family="Consolas" if platform.system() == "Windows" else "Courier", 
                             size=10)
                
        # 设置主题颜色
        self.primary_color = "#2196f3"  # 蓝色
        self.accent_color = "#ff9800"   # 橙色
        self.bg_color = "#f5f5f5"       # 浅灰色背景
        self.text_color = "#212121"     # 深灰色文本
        
        # 设置界面样式
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", font=self.normal_font)
        self.style.configure("Accent.TButton", background=self.accent_color)
        self.style.configure("TLabel", padding=5, font=self.normal_font)
        self.style.configure("Header.TLabel", font=self.header_font)
        self.style.configure("TFrame", padding=10, background=self.bg_color)
        self.style.configure("TLabelframe", padding=10, background=self.bg_color)
        self.style.configure("TLabelframe.Label", font=self.header_font)
        
        # 设置根窗口背景色
        self.root.configure(background=self.bg_color)
        
        # 创建标题
        self.header_frame = ttk.Frame(self.root)
        self.header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        self.title_label = ttk.Label(self.header_frame, text="B3sum 文件哈希验证工具", 
                                    font=Font(family="Segoe UI" if platform.system() == "Windows" else "Helvetica", 
                                             size=14, weight="bold"))
        self.title_label.pack(side=tk.LEFT)
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # 文件选择部分 - 使用更现代的布局
        self.file_frame = ttk.LabelFrame(self.main_frame, text="文件选择")
        self.file_frame.pack(fill=tk.X, pady=10, padx=5)
        
        self.file_inner_frame = ttk.Frame(self.file_frame)
        self.file_inner_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.file_path = tk.StringVar()
        self.file_entry = ttk.Entry(self.file_inner_frame, textvariable=self.file_path, width=50, font=self.normal_font)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.browse_button = ttk.Button(self.file_inner_frame, text="浏览文件", command=self.browse_file)
        self.browse_button.pack(side=tk.RIGHT, padx=(10, 0))
          # 计算按钮 - 使用更现代的按钮布局
        self.action_frame = ttk.Frame(self.main_frame)
        self.action_frame.pack(fill=tk.X, pady=10)
        
        # 添加状态提示文本
        self.status_text = ttk.Label(self.action_frame, text="", foreground=self.primary_color)
        self.status_text.pack(side=tk.LEFT, padx=(10, 0))
        
        # 右侧放置计算按钮
        self.calculate_button = ttk.Button(self.action_frame, text="计算 B3sum", 
                                         command=self.calculate_b3sum, 
                                         style="Accent.TButton",
                                         width=15)  # 固定宽度使按钮更美观
        self.calculate_button.pack(side=tk.RIGHT)
        
        # 哈希长度选择区域
        self.length_frame = ttk.Frame(self.action_frame)
        self.length_frame.pack(side=tk.LEFT, padx=(20, 0))
        
        # 长度提示标签
        self.length_label = ttk.Label(self.length_frame, text="哈希值长度:")
        self.length_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # 长度选择下拉菜单
        self.hash_length = tk.StringVar()
        self.hash_length.set("完整")  # 默认显示完整哈希
        hash_lengths = ["完整", "16位", "32位", "64位", "自定义"]
        self.length_combobox = ttk.Combobox(self.length_frame, 
                                          textvariable=self.hash_length,
                                          values=hash_lengths,
                                          width=8,
                                          state="readonly")
        self.length_combobox.pack(side=tk.LEFT)
        self.length_combobox.bind("<<ComboboxSelected>>", self.on_length_changed)
        
        # 自定义长度输入框(初始隐藏)
        self.custom_length = tk.StringVar()
        self.custom_length.set("32")  # 默认值
        self.custom_length_entry = ttk.Entry(self.length_frame, 
                                           textvariable=self.custom_length,
                                           width=5)
        # 只有选择"自定义"时才显示
        self.custom_length_entry.pack(side=tk.LEFT, padx=(5, 0))
        self.custom_length_entry.pack_forget()  # 初始隐藏
        
        # 结果区域 - 使用更现代的样式
        self.result_frame = ttk.LabelFrame(self.main_frame, text="哈希结果")
        self.result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 添加结果文本框和滚动条
        self.result_text_frame = ttk.Frame(self.result_frame)
        self.result_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.result_scrollbar = ttk.Scrollbar(self.result_text_frame)
        self.result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text = tk.Text(self.result_text_frame, 
                                 height=5, 
                                 width=50, 
                                 wrap=tk.WORD, 
                                 font=self.mono_font,
                                 yscrollcommand=self.result_scrollbar.set,
                                 bg="#ffffff",
                                 fg=self.text_color,
                                 selectbackground=self.primary_color,
                                 padx=10,
                                 pady=10,
                                 relief="flat",
                                 borderwidth=1)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        self.result_scrollbar.config(command=self.result_text.yview)
        self.result_text.config(state=tk.DISABLED)
        
        # 底部按钮区域
        self.button_frame = ttk.Frame(self.result_frame)
        self.button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 复制按钮 - 更现代的样式
        self.copy_button = ttk.Button(self.button_frame, 
                                     text="复制到剪贴板", 
                                     command=self.copy_to_clipboard,
                                     style="TButton")
        self.copy_button.pack(side=tk.RIGHT)
        
        # 验证区域 - 添加一个验证哈希的区域
        self.verify_frame = ttk.LabelFrame(self.main_frame, text="哈希验证")
        self.verify_frame.pack(fill=tk.X, pady=(5, 10), padx=5)
        
        # 验证输入框架
        self.verify_inner_frame = ttk.Frame(self.verify_frame)
        self.verify_inner_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # 验证标签
        self.verify_label = ttk.Label(self.verify_inner_frame, text="输入哈希值进行验证:")
        self.verify_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 验证输入框
        self.verify_hash = tk.StringVar()
        self.verify_entry = ttk.Entry(self.verify_inner_frame, textvariable=self.verify_hash, width=50, font=self.mono_font)
        self.verify_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 验证按钮
        self.verify_button = ttk.Button(self.verify_inner_frame, text="验证", 
                                      command=self.verify_hash_value)
        self.verify_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("准备就绪")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    def browse_file(self):
        file_path = filedialog.askopenfilename(title="选择文件")
        if file_path:
            self.file_path.set(file_path)
            self.status_var.set(f"已选择文件: {os.path.basename(file_path)}")
    def calculate_b3sum(self, silent=False):
        file_path = self.file_path.get()
        if not file_path:
            if not silent:
                messagebox.showerror("错误", "请先选择一个文件")
            return
        
        if not os.path.exists(file_path):
            if not silent:
                messagebox.showerror("错误", "选择的文件不存在")
            return
        
        # 禁用按钮，更新状态
        self.calculate_button.config(state=tk.DISABLED)
        self.status_text.config(text="计算中...")
        self.status_var.set("计算中...")
        
        # 在新线程中执行计算以避免UI冻结
        threading.Thread(target=self._run_b3sum, args=(file_path,), daemon=True).start()
        
    def _run_b3sum(self, file_path):
        try:
            # 调用b3sum命令，不使用text=True，改为手动处理bytes
            result = subprocess.run(['b3sum', file_path], capture_output=True)
            if result.returncode == 0:
                # 使用utf-8解码输出（通常是"哈希值 文件名"格式）
                output = result.stdout.decode('utf-8', errors='replace').strip()
                hash_value = output.split()[0] if ' ' in output else output
                
                # 处理哈希值长度
                selected_length = self.hash_length.get()
                if selected_length != "完整":
                    original_length = len(hash_value)
                    if selected_length == "16位":
                        hash_value = hash_value[:16]
                    elif selected_length == "32位":
                        hash_value = hash_value[:32]
                    elif selected_length == "64位":
                        hash_value = hash_value[:64]
                    elif selected_length == "自定义":
                        try:
                            custom_len = int(self.custom_length.get().strip())
                            if custom_len > 0 and custom_len <= original_length:
                                hash_value = hash_value[:custom_len]
                            else:
                                # 如果自定义长度无效，添加警告信息
                                hash_value += f"\n(注意: 自定义长度 {custom_len} 无效，需在1-{original_length}之间)"
                        except ValueError:
                            # 如果输入的不是数字，添加警告信息
                            hash_value += "\n(注意: 自定义长度必须是数字)"
                
                # 更新UI (必须在主线程中)
                self.root.after(0, self._update_result, hash_value, True)
            else:
                # 使用utf-8解码错误信息
                error_msg = result.stderr.decode('utf-8', errors='replace').strip()
                self.root.after(0, self._update_result, f"错误: {error_msg}", False)
        except Exception as e:
            self.root.after(0, self._update_result, f"异常: {str(e)}", False)
    
    def _update_result(self, text, success):
        # 启用按钮
        self.calculate_button.config(state=tk.NORMAL)
        self.status_text.config(text="")
        
        # 更新结果文本
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)
        
        # 更新状态
        if success:
            self.status_var.set("计算完成")
        else:
            self.status_var.set("计算失败")
    
    def copy_to_clipboard(self):
        result = self.result_text.get(1.0, tk.END).strip()
        if result:
            pyperclip.copy(result)
            self.status_var.set("已复制到剪贴板")
        else:
            self.status_var.set("没有可复制的内容")
    
    def verify_hash_value(self):
        # 获取用户输入的哈希值
        user_hash = self.verify_hash.get().strip().lower()
        
        # 获取计算出的哈希值
        calculated_hash = self.result_text.get(1.0, tk.END).strip().lower()
        
        if not user_hash:
            messagebox.showerror("错误", "请输入要验证的哈希值")
            return
            
        if not calculated_hash:
            messagebox.showerror("错误", "请先计算文件哈希值")
            return
          # 如果结果中包含文件名（格式为"哈希值 文件名"），则只比较哈希部分
        if ' ' in calculated_hash:
            calculated_hash = calculated_hash.split()[0]
            
        # 如果结果中包含注意事项（自定义长度错误警告），则去除
        if "\n" in calculated_hash:
            calculated_hash = calculated_hash.split("\n")[0]
            
        # 智能比较哈希值 - 处理不同长度的情况
        # 取两个哈希值中较短的一个长度进行比较
        min_length = min(len(user_hash), len(calculated_hash))
        if user_hash[:min_length] == calculated_hash[:min_length]:
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"{calculated_hash}\n\n")
            self.result_text.insert(tk.END, "✓ 验证成功！哈希值匹配。", "success")
            # 配置成功标签为绿色
            self.result_text.tag_configure("success", foreground="#4CAF50", font=self.header_font)
            self.result_text.config(state=tk.DISABLED)
            self.status_var.set("哈希值匹配")
        else:
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"输入: {user_hash}\n计算: {calculated_hash}\n\n")
            self.result_text.insert(tk.END, "✗ 验证失败！哈希值不匹配。", "error")
            # 配置错误标签为红色
            self.result_text.tag_configure("error", foreground="#F44336", font=self.header_font)
            self.result_text.config(state=tk.DISABLED)
            self.status_var.set("哈希值不匹配")
    
    def on_length_changed(self, event):
        selected_length = self.hash_length.get()
        if selected_length == "自定义":
            self.custom_length_entry.pack(side=tk.LEFT, padx=(5, 0))
        else:
            self.custom_length_entry.pack_forget()
            
        # 如果已经有计算结果，则根据新选择的长度重新格式化显示
        result_text = self.result_text.get(1.0, tk.END).strip()
        if result_text and not result_text.startswith("错误:") and not result_text.startswith("异常:"):
            # 重新计算当前文件的哈希值（如果有选定文件）
            if self.file_path.get():
                # 使用silent=True参数调用计算函数，避免弹出错误消息
                self.calculate_b3sum(True)

if __name__ == "__main__":
    root = tk.Tk()
    app = B3SumGUI(root)
    root.mainloop()
