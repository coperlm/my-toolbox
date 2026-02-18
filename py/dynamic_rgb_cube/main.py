import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import to_rgb

class RGBCubeApp:
    def __init__(self, master):
        self.master = master
        master.title("动态 RGB 颜色立方体")
        master.geometry("900x900") # 调整窗口大小以容纳更多控件

        self.fig = plt.Figure(figsize=(7, 7), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # 添加导航工具栏，包含缩放等功能
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.master)
        self.toolbar.update()
        
        # 启用鼠标交互功能
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

        self.setup_cube()
        
        # 初始选中的颜色点，用于更新
        self.selected_point = self.ax.scatter([], [], [], color='black', s=200, marker='o', edgecolors='white', linewidth=2)
        
        self.setup_controls()

    def setup_cube(self):
        # 绘制立方体边缘
        # 定义立方体的8个顶点 (0,0,0) 到 (1,1,1)
        verts = [[0,0,0], [1,0,0], [1,1,0], [0,1,0], [0,0,1], [1,0,1], [1,1,1], [0,1,1]]
        # 定义连接顶点的边
        edges = [[0,1], [1,2], [2,3], [3,0], # Bottom square
                 [4,5], [5,6], [6,7], [7,4], # Top square
                 [0,4], [1,5], [2,6], [3,7]] # Vertical edges

        for edge in edges:
            x = [verts[edge[0]][0], verts[edge[1]][0]]
            y = [verts[edge[0]][1], verts[edge[1]][1]]
            z = [verts[edge[0]][2], verts[edge[1]][2]]
            self.ax.plot(x, y, z, color='gray', linestyle='--', linewidth=0.5)

        # 生成 RGB 颜色空间中的采样点
        # 我们可以增加采样密度，但为了性能，仍不建议达到1670万
        # 这里使用 16x16x16 = 4096 个点
        r_sample = np.linspace(0, 1, 16)
        g_sample = np.linspace(0, 1, 16)
        b_sample = np.linspace(0, 1, 16)

        R_grid, G_grid, B_grid = np.meshgrid(r_sample, g_sample, b_sample)
        points = np.vstack([R_grid.ravel(), G_grid.ravel(), B_grid.ravel()]).T
        colors = points # 颜色就是点本身的 RGB 值

        self.ax.scatter(points[:, 0], points[:, 1], points[:, 2], c=colors, marker='o', s=10, alpha=0.6)

        # 设置中文字体以避免警告
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        self.ax.set_xlabel('Red (R)')
        self.ax.set_ylabel('Green (G)')
        self.ax.set_zlabel('Blue (B)')
        self.ax.set_title('RGB Color Cube')

        self.ax.set_xlim([0, 1])
        self.ax.set_ylim([0, 1])
        self.ax.set_zlim([0, 1])

        self.ax.set_xticks(np.linspace(0,1,5)) # 设置刻度，更清晰
        self.ax.set_yticks(np.linspace(0,1,5))
        self.ax.set_zticks(np.linspace(0,1,5))

        self.ax.grid(False) # 移除网格线，让颜色更突出
        self.fig.tight_layout() # 调整布局，防止标签重叠

    def setup_controls(self):
        control_frame = ttk.Frame(self.master, padding="10 10 10 10")
        control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 配置滑块样式，增加高度
        style = ttk.Style()
        style.configure("Thick.Horizontal.TScale", sliderlength=30, sliderrelief="raised")

        # 红光滑块
        ttk.Label(control_frame, text="红色 (R):").grid(row=0, column=0, sticky="w", pady=5)
        self.r_var = tk.DoubleVar(value=0.0)
        self.r_slider = ttk.Scale(control_frame, from_=0.0, to=1.0, orient="horizontal",
                                  variable=self.r_var, command=self.update_color, 
                                  style="Thick.Horizontal.TScale", length=300)
        self.r_slider.grid(row=0, column=1, sticky="ew", padx=5, pady=3, ipady=5)
        # 绑定点击事件 - 使用多个事件来确保兼容性
        self.r_slider.bind("<Button-1>", lambda e: self.slider_click(e, self.r_var, self.r_slider))
        self.r_slider.bind("<ButtonRelease-1>", lambda e: self.slider_click(e, self.r_var, self.r_slider))
        self.r_label = ttk.Label(control_frame, text="0.000")
        self.r_label.grid(row=0, column=2, sticky="w")

        # 绿光滑块
        ttk.Label(control_frame, text="绿色 (G):").grid(row=1, column=0, sticky="w", pady=5)
        self.g_var = tk.DoubleVar(value=0.0)
        self.g_slider = ttk.Scale(control_frame, from_=0.0, to=1.0, orient="horizontal",
                                  variable=self.g_var, command=self.update_color,
                                  style="Thick.Horizontal.TScale", length=300)
        self.g_slider.grid(row=1, column=1, sticky="ew", padx=5, pady=3, ipady=5)
        # 绑定点击事件 - 使用多个事件来确保兼容性
        self.g_slider.bind("<Button-1>", lambda e: self.slider_click(e, self.g_var, self.g_slider))
        self.g_slider.bind("<ButtonRelease-1>", lambda e: self.slider_click(e, self.g_var, self.g_slider))
        self.g_label = ttk.Label(control_frame, text="0.000")
        self.g_label.grid(row=1, column=2, sticky="w")

        # 蓝光滑块
        ttk.Label(control_frame, text="蓝色 (B):").grid(row=2, column=0, sticky="w", pady=5)
        self.b_var = tk.DoubleVar(value=0.0)
        self.b_slider = ttk.Scale(control_frame, from_=0.0, to=1.0, orient="horizontal",
                                  variable=self.b_var, command=self.update_color,
                                  style="Thick.Horizontal.TScale", length=300)
        self.b_slider.grid(row=2, column=1, sticky="ew", padx=5, pady=3, ipady=5)
        # 绑定点击事件 - 使用多个事件来确保兼容性
        self.b_slider.bind("<Button-1>", lambda e: self.slider_click(e, self.b_var, self.b_slider))
        self.b_slider.bind("<ButtonRelease-1>", lambda e: self.slider_click(e, self.b_var, self.b_slider))
        self.b_label = ttk.Label(control_frame, text="0.000")
        self.b_label.grid(row=2, column=2, sticky="w")

        # 当前颜色显示框
        self.color_display_frame = ttk.Frame(control_frame, relief="solid", borderwidth=2, width=80, height=40)
        self.color_display_frame.grid(row=0, column=3, rowspan=3, padx=10, sticky="nsew")
        self.color_display_frame.grid_propagate(False) # 防止内部控件改变帧大小

        # RGB 值文本显示（同时显示浮点数和整数值）
        self.rgb_text_label = ttk.Label(control_frame, text="RGB: (0.000, 0.000, 0.000) | (0, 0, 0)")
        self.rgb_text_label.grid(row=3, column=0, columnspan=3, pady=5, sticky="w")
        
        # 添加重置视图按钮
        self.reset_view_button = ttk.Button(control_frame, text="重置视图", command=self.reset_view)
        self.reset_view_button.grid(row=3, column=3, pady=5, padx=5, sticky="e")

        # 配置列权重，使滑块可以扩展
        control_frame.grid_columnconfigure(1, weight=1)

        # 初始更新颜色显示
        self.update_color()

    def update_color(self, *args):
        r = self.r_var.get()
        g = self.g_var.get()
        b = self.b_var.get()

        # 显示浮点数值（保留3位小数）
        self.r_label.config(text=f"{r:.3f}")
        self.g_label.config(text=f"{g:.3f}")
        self.b_label.config(text=f"{b:.3f}")

        # 转换为0-255整数值用于颜色显示
        r_int = int(r * 255)
        g_int = int(g * 255)
        b_int = int(b * 255)

        hex_color = f"#{r_int:02x}{g_int:02x}{b_int:02x}"
        
        # 更新颜色显示框背景
        try:
            style = ttk.Style()
            style.configure("Color.TFrame", background=hex_color)
            self.color_display_frame.configure(style="Color.TFrame")
        except:
            pass  # 如果样式设置失败，忽略错误

        # 更新选中颜色点的位置（使用浮点数值）
        self.selected_point._offsets3d = ([r], [g], [b])
        self.selected_point.set_color([r, g, b])  # 直接使用浮点RGB值
        self.canvas.draw_idle()  # 重新绘制画布

        # 显示浮点数和整数值
        self.rgb_text_label.config(text=f"RGB: ({r:.3f}, {g:.3f}, {b:.3f}) | ({r_int}, {g_int}, {b_int})")

    def slider_click(self, event, var, slider):
        """处理滑块点击事件，允许直接点击跳转到指定位置"""
        try:
            # 获取滑块的几何信息
            slider_width = slider.winfo_width()
            click_x = event.x
            
            # 计算点击位置相对于滑块的比例
            if slider_width > 0:
                # 对于ttk.Scale，边距可能不同，使用更保守的计算
                margin = 15  # ttk滑块的边距可能更大
                effective_width = slider_width - 2 * margin
                effective_x = click_x - margin
                
                # 确保点击位置在有效范围内
                effective_x = max(0, min(effective_x, effective_width))
                
                # 计算对应的值（浮点数，范围0.0-1.0）
                if effective_width > 0:
                    ratio = effective_x / effective_width
                    # 限制在0-1范围内
                    ratio = max(0.0, min(1.0, ratio))
                    new_value = round(ratio, 3)  # 保留3位小数
                    
                    # 设置新值
                    var.set(new_value)
                    
                    # 立即更新颜色显示
                    self.master.after_idle(self.update_color)
        except Exception as e:
            # 如果出现任何错误，静默忽略，不影响程序运行
            print(f"Slider click error: {e}")  # 调试信息

    def on_scroll(self, event):
        """处理鼠标滚轮事件，实现缩放功能"""
        if event.inaxes != self.ax:
            return
        
        # 获取当前的坐标轴范围
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        zlim = self.ax.get_zlim()
        
        # 计算当前范围的中心点
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        z_center = (zlim[0] + zlim[1]) / 2
        
        # 计算当前范围的大小
        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]
        z_range = zlim[1] - zlim[0]
        
        # 设置缩放因子
        scale_factor = 1.1 if event.button == 'down' else 0.9
        
        # 计算新的范围
        new_x_range = x_range * scale_factor
        new_y_range = y_range * scale_factor
        new_z_range = z_range * scale_factor
        
        # 设置新的坐标轴范围，保持中心不变
        self.ax.set_xlim(x_center - new_x_range/2, x_center + new_x_range/2)
        self.ax.set_ylim(y_center - new_y_range/2, y_center + new_y_range/2)
        self.ax.set_zlim(z_center - new_z_range/2, z_center + new_z_range/2)
        
        # 重新绘制
        self.canvas.draw_idle()

    def reset_view(self):
        """重置3D视图到初始状态"""
        self.ax.set_xlim([0, 1])
        self.ax.set_ylim([0, 1]) 
        self.ax.set_zlim([0, 1])
        self.canvas.draw_idle()

# 主程序入口
if __name__ == "__main__":
    root = tk.Tk()
    app = RGBCubeApp(root)
    root.mainloop()