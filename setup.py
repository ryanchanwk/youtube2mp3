import os
import sys
import subprocess
from pathlib import Path

def main():
    print("YouTube 轉 MP3 下載器安裝程序")
    print("="*50)
    print("此程序將安裝所需的所有 Python 套件")
    print("="*50)
    
    # 安裝 Python 依賴項
    print("正在安裝 Python 依賴項...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Python 依賴項安裝完成!")
    except Exception as e:
        print(f"安裝 Python 依賴項時出錯: {str(e)}")
        input("按 Enter 鍵退出...")
        return
    
    # 創建桌面快捷方式
    if sys.platform.startswith('win'):
        try:
            # 創建桌面快捷方式
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop_path, "YouTube 轉 MP3 下載器.bat")
            
            with open(shortcut_path, 'w') as f:
                script_path = os.path.abspath("youtube_to_mp3.py")
                f.write(f'@echo off\n')
                f.write(f'echo 正在啟動 YouTube 轉 MP3 下載器...\n')
                f.write(f'python "{script_path}"\n')
                f.write(f'pause\n')
                
            print(f"桌面快捷方式已創建: {shortcut_path}")
        except Exception as e:
            print(f"創建桌面快捷方式時出錯: {str(e)}")
    
    print("="*50)
    print("安裝完成!")
    print("您現在可以運行 youtube_to_mp3.py 或使用桌面上的快捷方式啟動應用程序。")
    print("="*50)
    
    input("按 Enter 鍵退出...")

if __name__ == "__main__":
    main() 