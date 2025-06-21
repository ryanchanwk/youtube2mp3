import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
from moviepy.editor import AudioFileClip
import os
import threading
import re
import logging
import time
import subprocess
import sys
import ffmpeg
import glob

# 設置日誌
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YouTubeToMP3Converter:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube 轉 MP3 下載器")
        self.root.geometry("600x480")  # 增加高度以容納更多控件
        self.root.resizable(False, False)
        
        # 設置主題顏色
        self.bg_color = "#f0f0f0"
        self.button_color = "#4CAF50"
        self.root.configure(bg=self.bg_color)
        
        # 創建主框架
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # URL 輸入框
        self.url_label = ttk.Label(self.main_frame, text="YouTube 影片網址：", font=("Microsoft JhengHei", 10))
        self.url_label.pack(pady=(0, 5), anchor=tk.W)
        
        self.url_entry = ttk.Entry(self.main_frame, width=50, font=("Microsoft JhengHei", 10))
        self.url_entry.pack(pady=(0, 10), fill=tk.X)
        
        # 文件名輸入框
        self.filename_label = ttk.Label(self.main_frame, text="保存檔案名：", font=("Microsoft JhengHei", 10))
        self.filename_label.pack(pady=(0, 5), anchor=tk.W)
        
        self.filename_var = tk.StringVar()
        self.filename_entry = ttk.Entry(self.main_frame, textvariable=self.filename_var, width=50, font=("Microsoft JhengHei", 10))
        self.filename_entry.pack(pady=(0, 10), fill=tk.X)
        
        # 自動獲取標題按鈕
        self.get_title_button = ttk.Button(
            self.main_frame,
            text="獲取影片標題",
            command=self.get_video_title
        )
        self.get_title_button.pack(pady=(0, 10))
        
        # 下載路徑選擇
        self.path_frame = ttk.Frame(self.main_frame)
        self.path_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.path_label = ttk.Label(self.path_frame, text="下載路徑：", font=("Microsoft JhengHei", 10))
        self.path_label.pack(side=tk.LEFT)
        
        self.path_var = tk.StringVar()
        self.path_var.set(os.path.join(os.path.expanduser("~"), "Downloads"))
        
        self.path_entry = ttk.Entry(self.path_frame, textvariable=self.path_var, width=40, font=("Microsoft JhengHei", 10))
        self.path_entry.pack(side=tk.LEFT, padx=5)
        
        self.browse_button = ttk.Button(self.path_frame, text="瀏覽", command=self.browse_path)
        self.browse_button.pack(side=tk.LEFT)
        
        # 下載按鈕
        self.download_button = ttk.Button(
            self.main_frame,
            text="開始下載",
            command=self.start_download,
            style="Accent.TButton"
        )
        self.download_button.pack(pady=10)
        
        # 進度條
        self.progress = ttk.Progressbar(
            self.main_frame,
            orient=tk.HORIZONTAL,
            length=400,
            mode='determinate'
        )
        self.progress.pack(pady=10)
        
        # 狀態標籤
        self.status_label = ttk.Label(
            self.main_frame,
            text="",
            font=("Microsoft JhengHei", 10)
        )
        self.status_label.pack(pady=5)
        
        # 歷史記錄標籤
        self.history_label = ttk.Label(
            self.main_frame,
            text="最近下載：",
            font=("Microsoft JhengHei", 10)
        )
        self.history_label.pack(pady=(10,5), anchor=tk.W)
        
        # 歷史記錄文本框
        self.history_text = tk.Text(self.main_frame, height=3, width=50, font=("Microsoft JhengHei", 9), wrap=tk.WORD)
        self.history_text.pack(fill=tk.X, pady=(0,10))
        self.history_text.config(state=tk.DISABLED)
        
        # 設置樣式
        self.style = ttk.Style()
        self.style.configure("Accent.TButton", background=self.button_color)
        
        # 記錄下載開始時間
        self.download_start_time = 0
        
        # 下載歷史記錄
        self.download_history = []
        
    def add_to_history(self, message):
        """添加消息到歷史記錄"""
        self.download_history.append(message)
        if len(self.download_history) > 10:  # 只保留最近的10條記錄
            self.download_history = self.download_history[-10:]
            
        # 更新歷史記錄顯示
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        for msg in self.download_history:
            self.history_text.insert(tk.END, f"{msg}\n")
        self.history_text.config(state=tk.DISABLED)
        
        # 自動滾動到底部
        self.history_text.see(tk.END)
        
    def get_video_title(self):
        """從YouTube URL獲取視頻標題"""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showerror("錯誤", "請輸入 YouTube 影片網址")
            return
        
        if not self.is_valid_youtube_url(url):
            messagebox.showerror("錯誤", "請輸入有效的 YouTube 影片網址")
            return
            
        self.status_label.config(text="正在獲取影片信息...")
        self.get_title_button.config(state=tk.DISABLED)
        
        def fetch_title():
            try:
                # yt-dlp 配置
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True
                }
                
                # 使用 yt-dlp 獲取信息
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    video_title = info.get('title', '')
                    
                    # 更新UI (在主線程中)
                    self.root.after(0, lambda: self.update_title_ui(video_title))
                    
            except Exception as e:
                logger.error(f"獲取標題失敗: {str(e)}")
                # 更新UI (在主線程中)
                self.root.after(0, lambda: self.update_title_ui(None, str(e)))
                
        # 在新線程中獲取標題
        threading.Thread(target=fetch_title, daemon=True).start()
        
    def update_title_ui(self, title, error=None):
        """更新UI中的標題"""
        self.get_title_button.config(state=tk.NORMAL)
        
        if title:
            sanitized_title = self.sanitize_filename(title)
            self.filename_var.set(sanitized_title)
            self.status_label.config(text="已獲取影片標題")
        else:
            self.status_label.config(text=f"獲取標題失敗: {error}")
            messagebox.showerror("錯誤", f"獲取標題失敗：{error}")
            
    def browse_path(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)
    
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            # 計算下載進度百分比
            if 'total_bytes' in d and d['total_bytes'] > 0:
                percent = d['downloaded_bytes'] / d['total_bytes'] * 100
                self.progress['value'] = percent
                self.root.update_idletasks()
            elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                percent = d['downloaded_bytes'] / d['total_bytes_estimate'] * 100
                self.progress['value'] = percent
                self.root.update_idletasks()
        
        # 記錄文件名
        if d['status'] == 'finished':
            if 'filename' in d:
                logger.info(f"下載完成: {d['filename']}")
    
    def is_valid_youtube_url(self, url):
        youtube_regex = (
            r'(https?://)?(www\.)?'
            '(youtube|youtu|youtube-nocookie)\.(com|be)/'
            '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
        youtube_match = re.match(youtube_regex, url)
        return bool(youtube_match)
    
    def find_new_files(self, directory, since_time):
        """找出自從指定時間之後創建的文件"""
        new_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getmtime(file_path) > since_time:
                    new_files.append(file_path)
        return new_files
    
    def sanitize_filename(self, title):
        """移除文件名中的特殊字符"""
        return re.sub(r'[\\/*?:"<>|]', "", title)
    
    def convert_to_mp3(self, input_file, output_file):
        """使用 ffmpeg-python 將音頻文件轉換為 MP3"""
        try:
            # 使用 ffmpeg-python 進行轉換
            logger.info(f"使用 ffmpeg-python 開始轉換: {input_file} -> {output_file}")
            (
                ffmpeg
                .input(input_file)
                .output(output_file, acodec='libmp3lame', ab='192k')
                .run(quiet=True, overwrite_output=True)
            )
            
            # 檢查轉換後的文件是否存在
            if os.path.exists(output_file):
                logger.info(f"ffmpeg 轉換成功: {output_file}")
                # 刪除原始文件
                os.remove(input_file)
                return True
            else:
                logger.error(f"轉換失敗: 輸出文件不存在 {output_file}")
                return False
        except Exception as e:
            logger.error(f"ffmpeg 轉換失敗: {str(e)}")
            
            # 如果 ffmpeg-python 失敗，嘗試使用 moviepy
            try:
                logger.info(f"嘗試使用 moviepy 轉換: {input_file}")
                audio = AudioFileClip(input_file)
                audio.write_audiofile(output_file, verbose=False, logger=None)
                audio.close()
                os.remove(input_file)
                if os.path.exists(output_file):
                    logger.info(f"moviepy 轉換成功: {output_file}")
                    return True
                else:
                    logger.error(f"moviepy 轉換失敗: 輸出文件不存在 {output_file}")
                    return False
            except Exception as e2:
                logger.error(f"moviepy 轉換也失敗: {str(e2)}")
                return False
    
    def download_video(self):
        url = self.url_entry.get().strip()
        output_path = self.path_var.get()
        custom_filename = self.filename_var.get().strip()
        
        if not url:
            messagebox.showerror("錯誤", "請輸入 YouTube 影片網址")
            return
        
        if not self.is_valid_youtube_url(url):
            messagebox.showerror("錯誤", "請輸入有效的 YouTube 影片網址")
            return
        
        # 記錄下載開始時間
        self.download_start_time = time.time()
        
        try:
            logger.info(f"開始下載影片: {url}")
            self.status_label.config(text="正在下載影片...")
            
            # 創建唯一的輸出文件名前綴
            video_id = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url).group(1)
            timestamp = int(time.time())
            file_prefix = f'yt_{video_id}_{timestamp}'
            temp_file_path = os.path.join(output_path, file_prefix)
            
            # yt-dlp 配置 - 使用簡單配置
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_file_path + '.%(ext)s',
                'progress_hooks': [self.progress_hook],
                'noplaylist': True,
                'quiet': False,  # 顯示輸出以便調試
                'no_warnings': False
            }
            
            # 使用 yt-dlp 下載
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 先獲取影片信息
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title', 'Unknown')
                logger.info(f"影片標題: {video_title}")
                
                # 如果用戶沒有指定文件名，使用視頻標題
                if not custom_filename:
                    custom_filename = self.sanitize_filename(video_title)
                
                # 下載影片
                self.status_label.config(text="正在下載影片...")
                ydl.download([url])
                
                # 等待一些時間確保文件寫入完成
                time.sleep(2)
                
                # 查找下載的文件 - 使用通配符查找
                pattern = temp_file_path + '.*'
                downloaded_files = glob.glob(pattern)
                
                if not downloaded_files:
                    # 如果找不到使用唯一前綴的文件，嘗試查找下載期間創建的所有文件
                    logger.warning(f"找不到使用前綴的文件: {pattern}")
                    logger.info("嘗試查找所有新創建的文件...")
                    downloaded_files = self.find_new_files(output_path, self.download_start_time)
                
                logger.info(f"找到 {len(downloaded_files)} 個新文件: {downloaded_files}")
                
                if not downloaded_files:
                    logger.error("找不到下載的文件")
                    self.status_label.config(text="下載失敗")
                    messagebox.showerror("錯誤", "找不到下載的文件")
                    return False
                
                # 對於每個找到的文件
                for input_file in downloaded_files:
                    # 檢查是否已經是 MP3 文件
                    if input_file.endswith('.mp3'):
                        logger.info(f"文件已經是 MP3 格式: {input_file}")
                        
                        # 如果已經是 MP3，直接重命名為用戶指定的文件名
                        final_output = os.path.join(output_path, f"{custom_filename}.mp3")
                        try:
                            if os.path.exists(final_output) and os.path.normpath(input_file) != os.path.normpath(final_output):
                                os.remove(final_output)
                            if os.path.normpath(input_file) != os.path.normpath(final_output):
                                os.rename(input_file, final_output)
                                logger.info(f"重命名為: {final_output}")
                                input_file = final_output
                        except Exception as e:
                            logger.error(f"重命名失敗: {str(e)}")
                            # 繼續使用原始輸出文件
                        
                        self.status_label.config(text="下載完成！")
                        self.add_to_history(f"{time.strftime('%H:%M:%S')} - 下載完成: {os.path.basename(input_file)}")
                        messagebox.showinfo("成功", f"MP3 檔案已成功下載！\n\n{os.path.basename(input_file)}")
                        return True
                    
                    # 需要轉換為 MP3
                    self.status_label.config(text="正在轉換為 MP3...")
                    
                    # 創建 MP3 文件名
                    output_file = os.path.splitext(input_file)[0] + '.mp3'
                    
                    # 使用 ffmpeg-python 進行轉換
                    if self.convert_to_mp3(input_file, output_file):
                        logger.info(f"轉換成功: {output_file}")
                        
                        # 重命名為用戶指定的文件名
                        final_output = os.path.join(output_path, f"{custom_filename}.mp3")
                        try:
                            if os.path.exists(final_output) and os.path.normpath(output_file) != os.path.normpath(final_output):
                                os.remove(final_output)
                            if os.path.normpath(output_file) != os.path.normpath(final_output):
                                os.rename(output_file, final_output)
                                logger.info(f"重命名為: {final_output}")
                                output_file = final_output
                        except Exception as e:
                            logger.error(f"重命名失敗: {str(e)}")
                            # 繼續使用原始輸出文件
                        
                        self.status_label.config(text="下載完成！")
                        self.add_to_history(f"{time.strftime('%H:%M:%S')} - 下載完成: {os.path.basename(output_file)}")
                        messagebox.showinfo("成功", f"MP3 檔案已成功下載！\n\n{os.path.basename(output_file)}")
                        return True
                    else:
                        logger.error(f"轉換失敗: {input_file}")
                
                # 如果所有文件都轉換失敗
                self.status_label.config(text="轉換失敗")
                messagebox.showerror("錯誤", "所有文件轉換失敗")
                return False
            
        except Exception as e:
            logger.exception(f"下載失敗: {str(e)}")
            self.status_label.config(text="下載失敗")
            messagebox.showerror("錯誤", f"下載失敗：{str(e)}")
            return False
        
    def start_download(self):
        self.download_button.config(state=tk.DISABLED)
        self.progress['value'] = 0
        
        # 啟動下載線程
        def download_thread():
            result = self.download_video()
            # 無論下載成功或失敗，都重新啟用下載按鈕
            self.root.after(0, lambda: self.download_button.config(state=tk.NORMAL))
            # 重置進度條
            self.root.after(0, lambda: self.set_progress(0))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def set_progress(self, value):
        """設置進度條值"""
        self.progress['value'] = value

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeToMP3Converter(root)
    root.mainloop() 