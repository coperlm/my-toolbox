import time
import pyautogui
import re

def read_and_input_data(file_path):
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 使用正则表达式按照"数字+)"的格式划分内容
        # 匹配模式：数字后面跟着")"，会捕获这个分隔符之后的所有内容，直到下一个分隔符
        pattern = r'(\d+\s*\))(.*?)(?=\d+\s*\)|$)'
        matches = re.findall(pattern, content, re.DOTALL)
          # 提取每个项目的内容并去除首尾空白
        # 如果项目中包含逗号，只取逗号前的第一个选项
        items = []
        for match in matches:
            item = match[1].strip()
            # 如果有逗号，只取第一部分
            if ',' in item:
                item = item.split(',')[0]
            items.append(item)
        
        print(f"已读取{len(items)}个项目，5秒后开始输入...")
        # 等待5秒，让用户切换到目标窗口
        for i in range(5, 0, -1):
            print(f"{i}...")
            time.sleep(1)
        
        # 对每个项目进行处理
        for i, item in enumerate(items):
            # 输入文本
            pyautogui.write(item)
            print(f"已输入第{i+1}项: {item}")
            
            # 按Tab键
            pyautogui.press('tab')
            print("已按Tab键")
              # 如果不是最后一项，等待0.1秒
            if i < len(items) - 1:
                # print("等待0.1秒...")
                time.sleep(0.1)
        
        print("所有数据输入完成！")
    
    except FileNotFoundError:
        print(f"错误：找不到文件 {file_path}")
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    # 确保pyautogui已安装
    try:
        import pyautogui
    except ImportError:
        print("请先安装pyautogui库:")
        print("pip install pyautogui")
        exit(1)
        
    file_path = "input.txt"
    read_and_input_data(file_path)