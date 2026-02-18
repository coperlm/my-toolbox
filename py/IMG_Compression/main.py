"""
图片批量压缩工具 - GUI版本
单文件版本,带有图形界面
只在文件大小超过阈值时才进行压缩
"""

import os
import io
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image
import threading
from datetime import datetime


class ImageCompressor:
    """图片压缩器类"""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
    
    def __init__(self, target_size_kb: float = 200, threshold_kb: float = 300, 
                 quality_range: Tuple[int, int] = (20, 95)):
        """
        初始化压缩器
        
        Args:
            target_size_kb: 目标文件大小(KB)
            threshold_kb: 阈值大小(KB),只有超过这个大小的文件才会被压缩
            quality_range: 质量范围 (最小质量, 最大质量)
        """
        self.target_size_kb = target_size_kb
        self.target_size_bytes = target_size_kb * 1024
        self.threshold_kb = threshold_kb
        self.threshold_bytes = threshold_kb * 1024
        self.min_quality = quality_range[0]
        self.max_quality = quality_range[1]
    
    def get_file_size(self, img: Image.Image, quality: int, format: str = 'JPEG') -> int:
        """获取指定质量下的图片文件大小"""
        buffer = io.BytesIO()
        save_kwargs = {'quality': quality, 'optimize': True}
        
        if format == 'PNG':
            compress_level = int((100 - quality) / 100 * 9)
            save_kwargs = {'compress_level': compress_level, 'optimize': True}
        
        img.save(buffer, format=format, **save_kwargs)
        size = buffer.tell()
        buffer.close()
        return size
    
    def compress_image(self, img: Image.Image, output_format: str = 'JPEG') -> Tuple[Image.Image, int]:
        """压缩图片到目标大小"""
        if output_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        low, high = self.min_quality, self.max_quality
        best_quality = high
        
        size_at_max = self.get_file_size(img, high, output_format)
        if size_at_max <= self.target_size_bytes:
            return img, high
        
        size_at_min = self.get_file_size(img, low, output_format)
        if size_at_min > self.target_size_bytes:
            scale_factor = (self.target_size_bytes / size_at_min) ** 0.5
            new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            return img, low
        
        while low <= high:
            mid = (low + high) // 2
            current_size = self.get_file_size(img, mid, output_format)
            
            if self.target_size_bytes * 0.95 <= current_size <= self.target_size_bytes * 1.05:
                best_quality = mid
                break
            elif current_size > self.target_size_bytes:
                high = mid - 1
                best_quality = mid
            else:
                low = mid + 1
                if current_size <= self.target_size_bytes:
                    best_quality = mid
        
        return img, best_quality
    
    def compress_file(self, input_path: str, output_path: Optional[str] = None, 
                     output_format: Optional[str] = None) -> dict:
        """压缩单个图片文件"""
        try:
            original_size = os.path.getsize(input_path)
            
            # 检查是否需要压缩
            if original_size <= self.threshold_bytes:
                return {
                    'success': True,
                    'skipped': True,
                    'input_path': input_path,
                    'output_path': output_path or input_path,
                    'original_size': original_size,
                    'compressed_size': original_size,
                    'compression_ratio': 0,
                    'quality': 100,
                    'message': f'文件大小 {original_size/1024:.1f}KB 未超过阈值 {self.threshold_kb}KB，跳过'
                }
            
            img = Image.open(input_path)
            
            if output_format is None:
                output_format = img.format if img.format else 'JPEG'
            
            if output_path is None:
                output_path = input_path
            
            compressed_img, quality = self.compress_image(img, output_format)
            
            save_kwargs = {'quality': quality, 'optimize': True}
            if output_format == 'PNG':
                compress_level = int((100 - quality) / 100 * 9)
                save_kwargs = {'compress_level': compress_level, 'optimize': True}
            
            compressed_img.save(output_path, format=output_format, **save_kwargs)
            compressed_size = os.path.getsize(output_path)
            
            return {
                'success': True,
                'skipped': False,
                'input_path': input_path,
                'output_path': output_path,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': (1 - compressed_size / original_size) * 100,
                'quality': quality,
                'message': f'{original_size/1024:.1f}KB → {compressed_size/1024:.1f}KB (压缩 {(1 - compressed_size / original_size) * 100:.1f}%, 质量 {quality})'
            }
        
        except Exception as e:
            return {
                'success': False,
                'skipped': False,
                'input_path': input_path,
                'error': str(e),
                'message': f'错误: {str(e)}'
            }
    
    def compress_folder(self, input_folder: str, output_folder: Optional[str] = None,
                       recursive: bool = True, output_format: Optional[str] = None,
                       progress_callback=None) -> List[dict]:
        """批量压缩文件夹内的图片"""
        input_path = Path(input_folder)
        if not input_path.exists():
            raise ValueError(f"输入文件夹不存在: {input_folder}")
        
        if output_folder:
            output_path = Path(output_folder)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = None
        
        results = []
        pattern = '**/*' if recursive else '*'
        
        # 先收集所有文件
        all_files = [f for f in input_path.glob(pattern) 
                     if f.is_file() and f.suffix.lower() in self.SUPPORTED_FORMATS]
        
        total_files = len(all_files)
        
        for index, file_path in enumerate(all_files, 1):
            if output_path:
                relative_path = file_path.relative_to(input_path)
                out_file = output_path / relative_path
                out_file.parent.mkdir(parents=True, exist_ok=True)
                
                if output_format:
                    ext = '.' + output_format.lower()
                    if ext == '.jpeg':
                        ext = '.jpg'
                    out_file = out_file.with_suffix(ext)
                
                out_file_str = str(out_file)
            else:
                out_file_str = str(file_path)
            
            result = self.compress_file(str(file_path), out_file_str, output_format)
            results.append(result)
            
            if progress_callback:
                progress_callback(index, total_files, file_path.name, result)
        
        return results


class ImageCompressorGUI:
    """图片压缩工具GUI界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("图片批量压缩工具 - Image Compressor")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)
        
        # 设置窗口图标颜色
        self.root.configure(bg='#f5f6fa')
        
        # 现代化配色方案 - 高对比度版本
        self.colors = {
            'primary': '#6c5ce7',      # 主色调 - 明亮紫色
            'secondary': '#00cec9',    # 次要色 - 明亮青色
            'success': '#00b894',      # 成功 - 明亮绿色
            'warning': '#fdcb6e',      # 警告 - 明亮橙色
            'danger': '#d63031',       # 危险 - 明亮红色
            'info': '#0984e3',         # 信息 - 明亮蓝色
            'light': '#f5f6fa',        # 浅色背景
            'dark': '#2d3436',         # 深色文字
            'gray': '#636e72',         # 灰色
            'white': '#ffffff'         # 白色
        }
        
        # 设置现代化样式
        self.setup_styles()
        self.setup_ui()
        self.is_processing = False
    
    def setup_styles(self):
        """设置现代化样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置整体背景
        style.configure('.', background=self.colors['light'], 
                       foreground=self.colors['dark'])
        
        # 标题样式
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 20, 'bold'),
                       foreground=self.colors['primary'],
                       background=self.colors['light'])
        
        # 副标题样式
        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 10),
                       foreground=self.colors['gray'],
                       background=self.colors['light'])
        
        # 标签样式
        style.configure('Modern.TLabel',
                       font=('Segoe UI', 10),
                       background=self.colors['light'],
                       foreground=self.colors['dark'])
        
        # 输入框样式
        style.configure('Modern.TEntry',
                       fieldbackground=self.colors['white'],
                       borderwidth=2,
                       relief='flat')
        
        # 按钮样式
        style.configure('Primary.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        style.map('Primary.TButton',
                 background=[('active', self.colors['primary']), 
                           ('!active', self.colors['primary'])],
                 foreground=[('active', self.colors['white']), 
                           ('!active', self.colors['white'])])
        
        style.configure('Success.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        style.map('Success.TButton',
                 background=[('active', self.colors['success']), 
                           ('!active', self.colors['success'])],
                 foreground=[('active', self.colors['white']), 
                           ('!active', self.colors['white'])])
        
        style.configure('Danger.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        style.map('Danger.TButton',
                 background=[('active', self.colors['danger']), 
                           ('!active', self.colors['danger'])],
                 foreground=[('active', self.colors['white']), 
                           ('!active', self.colors['white'])])
        
        style.configure('Secondary.TButton',
                       font=('Segoe UI', 9),
                       borderwidth=0,
                       padding=(15, 8))
        style.map('Secondary.TButton',
                 background=[('active', self.colors['info']), 
                           ('!active', self.colors['secondary'])],
                 foreground=[('active', self.colors['white']), 
                           ('!active', self.colors['white'])])
        
        # LabelFrame样式
        style.configure('Modern.TLabelframe',
                       background=self.colors['white'],
                       borderwidth=2,
                       relief='flat')
        style.configure('Modern.TLabelframe.Label',
                       font=('Segoe UI', 11, 'bold'),
                       foreground=self.colors['primary'],
                       background=self.colors['white'])
        
        # 进度条样式
        style.configure('Modern.Horizontal.TProgressbar',
                       troughcolor=self.colors['light'],
                       background=self.colors['success'],
                       borderwidth=0,
                       thickness=25)
        
    def setup_ui(self):
        """设置UI界面"""
        # 主容器框架
        container = tk.Frame(self.root, bg=self.colors['light'])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题区域
        header_frame = tk.Frame(container, bg=self.colors['white'], 
                               relief='flat', bd=0)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 标题和图标
        title_container = tk.Frame(header_frame, bg=self.colors['white'])
        title_container.pack(pady=20)
        
        # 主标题
        title_label = tk.Label(title_container, 
                              text="🖼️ 图片批量压缩工具", 
                              font=('Segoe UI', 22, 'bold'),
                              fg=self.colors['primary'],
                              bg=self.colors['white'])
        title_label.pack()
        
        # 副标题
        subtitle_label = tk.Label(title_container,
                                 text="智能压缩 · 精确控制 · 批量处理",
                                 font=('Segoe UI', 10),
                                 fg='#636e72',
                                 bg=self.colors['white'])
        subtitle_label.pack(pady=(5, 0))
        
        # 主内容框架
        main_frame = tk.Frame(container, bg=self.colors['light'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件夹选择区域
        folder_frame = tk.Frame(main_frame, bg=self.colors['white'], 
                               relief='flat', bd=0)
        folder_frame.pack(fill=tk.X, pady=(0, 15))
        folder_frame.columnconfigure(1, weight=1)
        
        # 内边距
        folder_content = tk.Frame(folder_frame, bg=self.colors['white'])
        folder_content.pack(fill=tk.X, padx=20, pady=20)
        folder_content.columnconfigure(1, weight=1)
        
        # 输入文件夹
        input_label = tk.Label(folder_content, text="📁 输入文件夹", 
                              font=('Segoe UI', 10, 'bold'),
                              fg=self.colors['dark'],
                              bg=self.colors['white'])
        input_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        input_frame = tk.Frame(folder_content, bg=self.colors['white'])
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        input_frame.columnconfigure(0, weight=1)
        
        self.input_folder_var = tk.StringVar()
        input_entry = tk.Entry(input_frame, textvariable=self.input_folder_var,
                              font=('Segoe UI', 10),
                              relief='flat',
                              bg=self.colors['light'],
                              fg=self.colors['dark'],
                              insertbackground=self.colors['primary'])
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, 
                        ipady=8, padx=(0, 10))
        
        input_btn = tk.Button(input_frame, text="浏览", 
                             command=self.browse_input_folder,
                             font=('Segoe UI', 9, 'bold'),
                             bg=self.colors['secondary'],
                             fg=self.colors['white'],
                             relief='flat',
                             cursor='hand2',
                             padx=20, pady=8)
        input_btn.pack(side=tk.RIGHT)
        self.add_hover_effect(input_btn, self.colors['secondary'], self.colors['info'])
        
        # 输出文件夹
        output_label = tk.Label(folder_content, text="💾 输出文件夹", 
                               font=('Segoe UI', 10, 'bold'),
                               fg=self.colors['dark'],
                               bg=self.colors['white'])
        output_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 8))
        
        output_frame = tk.Frame(folder_content, bg=self.colors['white'])
        output_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)
        
        self.output_folder_var = tk.StringVar()
        output_entry = tk.Entry(output_frame, textvariable=self.output_folder_var,
                               font=('Segoe UI', 10),
                               relief='flat',
                               bg=self.colors['light'],
                               fg=self.colors['dark'],
                               insertbackground=self.colors['primary'])
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, 
                         ipady=8, padx=(0, 10))
        
        output_btn = tk.Button(output_frame, text="浏览",
                              command=self.browse_output_folder,
                              font=('Segoe UI', 9, 'bold'),
                              bg=self.colors['secondary'],
                              fg=self.colors['white'],
                              relief='flat',
                              cursor='hand2',
                              padx=20, pady=8)
        output_btn.pack(side=tk.RIGHT)
        self.add_hover_effect(output_btn, self.colors['secondary'], self.colors['info'])
        
        # 提示信息
        hint_label = tk.Label(folder_content, 
                             text="💡 提示: 如果不选择输出文件夹，将覆盖原文件", 
                             font=('Segoe UI', 9),
                             fg=self.colors['warning'],
                             bg=self.colors['white'])
        hint_label.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # 参数设置区域
        params_frame = tk.Frame(main_frame, bg=self.colors['white'], 
                               relief='flat', bd=0)
        params_frame.pack(fill=tk.X, pady=(0, 15))
        
        params_content = tk.Frame(params_frame, bg=self.colors['white'])
        params_content.pack(fill=tk.X, padx=20, pady=20)
        
        # 参数标题
        params_title = tk.Label(params_content, text="⚙️ 压缩参数设置",
                               font=('Segoe UI', 12, 'bold'),
                               fg=self.colors['primary'],
                               bg=self.colors['white'])
        params_title.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 15))
        
        # 参数网格布局
        params_content.columnconfigure(1, weight=1)
        params_content.columnconfigure(3, weight=1)
        
        # 阈值大小
        threshold_label = tk.Label(params_content, text="📏 阈值大小 (KB)", 
                                  font=('Segoe UI', 10),
                                  fg=self.colors['dark'],
                                  bg=self.colors['white'])
        threshold_label.grid(row=1, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        
        self.threshold_var = tk.StringVar(value="300")
        threshold_spinbox = tk.Spinbox(params_content, from_=1, to=10000, 
                                      textvariable=self.threshold_var,
                                      font=('Segoe UI', 10),
                                      relief='flat',
                                      bg=self.colors['light'],
                                      fg=self.colors['dark'],
                                      buttonbackground=self.colors['secondary'],
                                      width=12)
        threshold_spinbox.grid(row=1, column=1, sticky=tk.W, pady=8)
        
        threshold_hint = tk.Label(params_content, 
                                 text="只压缩超过此大小的图片", 
                                 font=('Segoe UI', 9),
                                 fg='#636e72',
                                 bg=self.colors['white'])
        threshold_hint.grid(row=1, column=2, sticky=tk.W, padx=15)
        
        # 目标大小
        target_label = tk.Label(params_content, text="🎯 目标大小 (KB)", 
                               font=('Segoe UI', 10),
                               fg=self.colors['dark'],
                               bg=self.colors['white'])
        target_label.grid(row=2, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        
        self.target_size_var = tk.StringVar(value="200")
        target_spinbox = tk.Spinbox(params_content, from_=10, to=10000, 
                                   textvariable=self.target_size_var,
                                   font=('Segoe UI', 10),
                                   relief='flat',
                                   bg=self.colors['light'],
                                   fg=self.colors['dark'],
                                   buttonbackground=self.colors['secondary'],
                                   width=12)
        target_spinbox.grid(row=2, column=1, sticky=tk.W, pady=8)
        
        target_hint = tk.Label(params_content, 
                              text="压缩后的目标大小", 
                              font=('Segoe UI', 9),
                              fg='#636e72',
                              bg=self.colors['white'])
        target_hint.grid(row=2, column=2, sticky=tk.W, padx=15)
        
        # 质量范围
        quality_label = tk.Label(params_content, text="✨ 质量范围", 
                                font=('Segoe UI', 10),
                                fg=self.colors['dark'],
                                bg=self.colors['white'])
        quality_label.grid(row=3, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        
        quality_frame = tk.Frame(params_content, bg=self.colors['white'])
        quality_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=8)
        
        tk.Label(quality_frame, text="最小:", 
                font=('Segoe UI', 9),
                fg=self.colors['dark'],
                bg=self.colors['white']).pack(side=tk.LEFT, padx=(0, 5))
        
        self.min_quality_var = tk.StringVar(value="20")
        min_quality_spin = tk.Spinbox(quality_frame, from_=1, to=100, 
                                     textvariable=self.min_quality_var,
                                     font=('Segoe UI', 10),
                                     relief='flat',
                                     bg=self.colors['light'],
                                     fg=self.colors['dark'],
                                     buttonbackground=self.colors['secondary'],
                                     width=8)
        min_quality_spin.pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Label(quality_frame, text="最大:", 
                font=('Segoe UI', 9),
                fg=self.colors['dark'],
                bg=self.colors['white']).pack(side=tk.LEFT, padx=(0, 5))
        
        self.max_quality_var = tk.StringVar(value="95")
        max_quality_spin = tk.Spinbox(quality_frame, from_=1, to=100, 
                                     textvariable=self.max_quality_var,
                                     font=('Segoe UI', 10),
                                     relief='flat',
                                     bg=self.colors['light'],
                                     fg=self.colors['dark'],
                                     buttonbackground=self.colors['secondary'],
                                     width=8)
        max_quality_spin.pack(side=tk.LEFT)
        
        # 选项区域
        options_frame = tk.Frame(params_content, bg=self.colors['white'])
        options_frame.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(15, 0))
        
        # 递归处理
        self.recursive_var = tk.BooleanVar(value=True)
        recursive_check = tk.Checkbutton(options_frame, 
                                        text="🔄 递归处理子文件夹",
                                        variable=self.recursive_var,
                                        font=('Segoe UI', 10),
                                        fg=self.colors['dark'],
                                        bg=self.colors['white'],
                                        selectcolor=self.colors['light'],
                                        activebackground=self.colors['white'],
                                        activeforeground=self.colors['primary'])
        recursive_check.pack(side=tk.LEFT, padx=(0, 30))
        
        # 输出格式
        tk.Label(options_frame, text="📄 输出格式:", 
                font=('Segoe UI', 10),
                fg=self.colors['dark'],
                bg=self.colors['white']).pack(side=tk.LEFT, padx=(0, 10))
        
        self.format_var = tk.StringVar(value="保持原格式")
        format_combo = ttk.Combobox(options_frame, textvariable=self.format_var, 
                                   values=["保持原格式", "JPEG", "PNG", "WEBP"], 
                                   font=('Segoe UI', 10),
                                   width=12, state='readonly')
        format_combo.pack(side=tk.LEFT)
        
        # 按钮区域
        button_frame = tk.Frame(main_frame, bg=self.colors['light'])
        button_frame.pack(fill=tk.X, pady=15)
        
        button_container = tk.Frame(button_frame, bg=self.colors['light'])
        button_container.pack()
        
        # 开始按钮
        self.start_button = tk.Button(button_container, 
                                      text="▶ 开始压缩",
                                      command=self.start_compression,
                                      font=('Segoe UI', 11, 'bold'),
                                      bg='#00b894',
                                      fg=self.colors['white'],
                                      relief='flat',
                                      cursor='hand2',
                                      padx=30, pady=12)
        self.start_button.pack(side=tk.LEFT, padx=8)
        self.add_hover_effect(self.start_button, '#00b894', '#00a383')
        
        # 停止按钮
        self.stop_button = tk.Button(button_container, 
                                     text="⏸ 停止",
                                     command=self.stop_compression,
                                     font=('Segoe UI', 11, 'bold'),
                                     bg='#d63031',
                                     fg=self.colors['white'],
                                     relief='flat',
                                     cursor='hand2',
                                     state='disabled',
                                     padx=30, pady=12)
        self.stop_button.pack(side=tk.LEFT, padx=8)
        self.add_hover_effect(self.stop_button, '#d63031', '#c0281f')
        
        # 清空日志按钮
        clear_button = tk.Button(button_container, 
                                text="🗑 清空日志",
                                command=self.clear_log,
                                font=('Segoe UI', 10),
                                bg='#636e72',
                                fg=self.colors['white'],
                                relief='flat',
                                cursor='hand2',
                                padx=25, pady=12)
        clear_button.pack(side=tk.LEFT, padx=8)
        self.add_hover_effect(clear_button, '#636e72', '#4a5055')
        
        # 进度区域
        progress_frame = tk.Frame(main_frame, bg=self.colors['white'])
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        progress_content = tk.Frame(progress_frame, bg=self.colors['white'])
        progress_content.pack(fill=tk.X, padx=20, pady=15)
        
        # 状态标签
        self.status_var = tk.StringVar(value="🟢 就绪 - 请选择文件夹并开始压缩")
        status_label = tk.Label(progress_content, 
                               textvariable=self.status_var,
                               font=('Segoe UI', 10, 'bold'),
                               fg=self.colors['primary'],
                               bg=self.colors['white'])
        status_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        progress_container = tk.Frame(progress_content, bg=self.colors['light'], 
                                     relief='flat', bd=0)
        progress_container.pack(fill=tk.X)
        
        self.progress_bar = ttk.Progressbar(progress_container, 
                                           variable=self.progress_var,
                                           maximum=100,
                                           mode='determinate',
                                           style='Modern.Horizontal.TProgressbar')
        self.progress_bar.pack(fill=tk.X, padx=2, pady=2)
        
        # 日志区域
        log_frame = tk.Frame(main_frame, bg=self.colors['white'])
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        log_content = tk.Frame(log_frame, bg=self.colors['white'])
        log_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(15, 20))
        
        log_title = tk.Label(log_content, text="📋 处理日志",
                            font=('Segoe UI', 11, 'bold'),
                            fg=self.colors['primary'],
                            bg=self.colors['white'])
        log_title.pack(anchor=tk.W, pady=(0, 10))
        
        # 日志文本框
        log_container = tk.Frame(log_content, bg=self.colors['light'], 
                                relief='flat', bd=0)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_container, 
                                                  height=12,
                                                  wrap=tk.WORD,
                                                  font=('Consolas', 9),
                                                  bg=self.colors['white'],
                                                  fg=self.colors['dark'],
                                                  relief='flat',
                                                  padx=10, pady=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 配置日志文本标签颜色 - 高对比度
        self.log_text.tag_config('success', foreground='#00b894', 
                                font=('Consolas', 9, 'bold'))
        self.log_text.tag_config('skip', foreground='#0984e3')
        self.log_text.tag_config('error', foreground='#d63031', 
                                font=('Consolas', 9, 'bold'))
        self.log_text.tag_config('info', foreground='#2d3436')
        self.log_text.tag_config('summary', foreground='#6c5ce7', 
                                font=('Consolas', 10, 'bold'))
        
        # 添加初始欢迎信息
        self.log("🎉 欢迎使用图片批量压缩工具!", 'summary')
        self.log("📝 请选择输入文件夹，配置参数，然后点击\"开始压缩\"", 'info')
        self.log("─" * 80, 'info')
    
    def add_hover_effect(self, button, normal_color, hover_color):
        """为按钮添加悬停效果"""
        def on_enter(e):
            if button['state'] != 'disabled':
                button['background'] = hover_color
        
        def on_leave(e):
            if button['state'] != 'disabled':
                button['background'] = normal_color
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def browse_input_folder(self):
        """浏览输入文件夹"""
        folder = filedialog.askdirectory(title="选择输入文件夹")
        if folder:
            self.input_folder_var.set(folder)
    
    def browse_output_folder(self):
        """浏览输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder_var.set(folder)
    
    def log(self, message, tag='info'):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
        self.root.update()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        # 重新添加欢迎信息
        self.log("🎉 日志已清空!", 'summary')
        self.log("📝 准备开始新的压缩任务", 'info')
        self.log("─" * 80, 'info')
    
    def validate_inputs(self):
        """验证输入"""
        if not self.input_folder_var.get():
            messagebox.showerror("错误", "请选择输入文件夹!")
            return False
        
        if not os.path.exists(self.input_folder_var.get()):
            messagebox.showerror("错误", "输入文件夹不存在!")
            return False
        
        try:
            threshold = float(self.threshold_var.get())
            target = float(self.target_size_var.get())
            if threshold <= 0 or target <= 0:
                raise ValueError()
            if target >= threshold:
                response = messagebox.askyesno("警告", 
                    f"目标大小({target}KB)大于或等于阈值({threshold}KB)，\n"
                    "这意味着可能不会有文件被压缩。\n是否继续?")
                if not response:
                    return False
        except:
            messagebox.showerror("错误", "请输入有效的数字!")
            return False
        
        try:
            min_q = int(self.min_quality_var.get())
            max_q = int(self.max_quality_var.get())
            if min_q < 1 or max_q > 100 or min_q > max_q:
                raise ValueError()
        except:
            messagebox.showerror("错误", "质量范围必须在1-100之间，且最小值不能大于最大值!")
            return False
        
        output = self.output_folder_var.get()
        if not output:
            response = messagebox.askyesno("警告", 
                "未选择输出文件夹，将覆盖原文件!\n确定要继续吗?")
            if not response:
                return False
        
        return True
    
    def start_compression(self):
        """开始压缩"""
        if not self.validate_inputs():
            return
        
        self.is_processing = True
        self.start_button.config(state='disabled', bg='#636e72')
        self.stop_button.config(state='normal', bg='#d63031')
        self.progress_var.set(0)
        self.log_text.delete(1.0, tk.END)  # 清空日志
        
        # 在新线程中运行压缩
        thread = threading.Thread(target=self.run_compression)
        thread.daemon = True
        thread.start()
    
    def stop_compression(self):
        """停止压缩"""
        self.is_processing = False
        self.log("⏸️ 用户取消操作", 'info')
    
    def run_compression(self):
        """运行压缩任务"""
        try:
            # 获取参数
            input_folder = self.input_folder_var.get()
            output_folder = self.output_folder_var.get() or None
            threshold = float(self.threshold_var.get())
            target_size = float(self.target_size_var.get())
            min_quality = int(self.min_quality_var.get())
            max_quality = int(self.max_quality_var.get())
            recursive = self.recursive_var.get()
            output_format = None if self.format_var.get() == "保持原格式" else self.format_var.get()
            
            self.log(f"🚀 开始处理图片...", 'info')
            self.log(f"📁 输入文件夹: {input_folder}", 'info')
            self.log(f"📏 阈值大小: {threshold} KB (只压缩超过此大小的文件)", 'info')
            self.log(f"🎯 目标大小: {target_size} KB", 'info')
            self.log(f"✨ 质量范围: {min_quality}-{max_quality}", 'info')
            if output_folder:
                self.log(f"💾 输出文件夹: {output_folder}", 'info')
            else:
                self.log(f"⚠️ 模式: 覆盖原文件", 'info')
            self.log("─" * 80, 'info')
            
            # 创建压缩器
            compressor = ImageCompressor(
                target_size_kb=target_size,
                threshold_kb=threshold,
                quality_range=(min_quality, max_quality)
            )
            
            # 定义进度回调
            def progress_callback(current, total, filename, result):
                if not self.is_processing:
                    raise InterruptedError("用户取消操作")
                
                progress = (current / total) * 100
                self.progress_var.set(progress)
                self.status_var.set(f"🔄 处理中: {current}/{total} - {filename}")
                
                if result['success']:
                    if result.get('skipped', False):
                        self.log(f"⊙ {filename}: {result['message']}", 'skip')
                    else:
                        self.log(f"✓ {filename}: {result['message']}", 'success')
                else:
                    self.log(f"✗ {filename}: {result['message']}", 'error')
            
            # 执行压缩
            results = compressor.compress_folder(
                input_folder=input_folder,
                output_folder=output_folder,
                recursive=recursive,
                output_format=output_format,
                progress_callback=progress_callback
            )
            
            # 生成摘要
            self.log("─" * 80, 'info')
            self.log("🎉 处理完成!", 'summary')
            self.log("─" * 80, 'info')
            
            successful = [r for r in results if r['success'] and not r.get('skipped', False)]
            skipped = [r for r in results if r['success'] and r.get('skipped', False)]
            failed = [r for r in results if not r['success']]
            
            self.log(f"📊 总文件数: {len(results)}", 'summary')
            self.log(f"✅ 已压缩: {len(successful)}", 'summary')
            self.log(f"⊙ 已跳过: {len(skipped)}", 'summary')
            self.log(f"❌ 失败: {len(failed)}", 'summary')
            
            if successful:
                total_original = sum(r['original_size'] for r in successful)
                total_compressed = sum(r['compressed_size'] for r in successful)
                total_saved = total_original - total_compressed
                avg_ratio = sum(r['compression_ratio'] for r in successful) / len(successful)
                
                self.log(f"\n📈 压缩文件统计:", 'summary')
                self.log(f"📦 原始总大小: {total_original/1024/1024:.2f} MB", 'summary')
                self.log(f"📦 压缩后总大小: {total_compressed/1024/1024:.2f} MB", 'summary')
                self.log(f"💾 节省空间: {total_saved/1024/1024:.2f} MB", 'summary')
                self.log(f"📉 平均压缩率: {avg_ratio:.1f}%", 'summary')
            
            self.status_var.set("✅ 处理完成!")
            self.progress_var.set(100)
            messagebox.showinfo("🎉 完成", 
                              f"处理完成!\n\n"
                              f"✅ 已压缩: {len(successful)}\n"
                              f"⊙ 已跳过: {len(skipped)}\n"
                              f"❌ 失败: {len(failed)}")
            
        except InterruptedError:
            self.status_var.set("⏸️ 已取消")
            self.progress_var.set(0)
        except Exception as e:
            self.log(f"❌ 发生错误: {str(e)}", 'error')
            self.status_var.set("❌ 发生错误")
            messagebox.showerror("错误", f"处理过程中发生错误:\n{str(e)}")
        finally:
            self.is_processing = False
            self.start_button.config(state='normal', bg='#00b894')
            self.stop_button.config(state='disabled', bg='#636e72')


def main():
    """主函数"""
    root = tk.Tk()
    app = ImageCompressorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
