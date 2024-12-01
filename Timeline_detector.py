import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from tkinterdnd2 import DND_FILES, TkinterDnD


class TimelineDetector:
    def __init__(self, file_path: str = None):
        self.file_path = file_path
        
    def is_scene_data(self, content_str: str) -> bool:
        """檢查是否為scene data"""
        return "KStudio" in content_str
        
    def check_timeline(self, content_str: str) -> tuple[str, float]:
        """檢查timeline類型並返回timeline狀態和duration"""
        # 檢查是否有任一種timeline
        if "Timeline" in content_str or "timeline" in content_str:
            # 檢查duration
            if "duration" in content_str:
                dur_pos = content_str.find("duration")
                search_pos = dur_pos + len("duration")
                
                while search_pos < len(content_str):
                    if content_str[search_pos].isdigit():
                        num_start = search_pos
                        num_end = num_start
                        while num_end < len(content_str) and (content_str[num_end].isdigit() or content_str[num_end] == '.'):
                            num_end += 1
                        try:
                            duration = float(content_str[num_start:num_end])
                            return "has_timeline", duration
                        except ValueError:
                            return "has_timeline", None
                    search_pos += 1
                return "has_timeline", None
            return "has_timeline", None
        return "no_timeline", None

class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Timeline Detector")
        self.geometry("400x500")  # 調整成更適合的高度
        self.configure(bg='white')
        self.setup_ui()
    def setup_ui(self):
        # Drop zone frame with border
        self.drop_frame = ttk.Frame(self)
        self.drop_frame.pack(fill="x", padx=20, pady=20)
        
        # Create a canvas for the drop zone with dashed border
        self.canvas = tk.Canvas(self.drop_frame, bg='white', bd=1, 
                              highlightthickness=1, height=100)
        self.canvas.pack(fill="x", padx=5, pady=5)
        
        # Update canvas size when window resizes
        def on_resize(event):
            # Redraw canvas content
            self.canvas.delete("all")  # Clear canvas
            # Draw dashed rectangle
            self.canvas.create_rectangle(2, 2, event.width-2, 98, 
                                       outline='gray', dash=(4, 2))
            # Center text (using actual canvas width)
            self.canvas.create_text(event.width/2, 50,
                                  text="Drag and Drop or Upload Scene Data here", 
                                  anchor="center")
            
        self.canvas.bind('<Configure>', on_resize)
        
        self.browse_button = ttk.Button(self.drop_frame, 
                                      text="Select File",
                                      command=self.browse_file)
        self.browse_button.pack(pady=10)
        
        # Results area
        self.result_frame = ttk.Frame(self)
        self.result_frame.pack(fill="both", expand=True, padx=20)
        
        # File info
        self.filename_label = ttk.Label(self.result_frame, text="")
        self.filename_label.pack(pady=5)
        
        # Image preview - 使用 tk.Label 而不是 ttk.Label 以便顯示圖片
        self.image_label = tk.Label(self.result_frame)
        self.image_label.pack(pady=10)
        
        # Timeline status
        self.timeline_label = ttk.Label(self.result_frame, text="")
        self.timeline_label.pack(pady=5)
        
        # Duration info
        self.duration_label = ttk.Label(self.result_frame, text="")
        self.duration_label.pack(pady=5)
        
        # Configure drop zone
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

    def show_preview(self, file_path):
        try:
            # 使用 tkinter 的 PhotoImage 直接載入 PNG
            photo = tk.PhotoImage(file=file_path)
            
            # 獲取圖片尺寸
            width = photo.width()
            height = photo.height()
            
            # 計算縮放比例，最大顯示尺寸為 300x300
            max_size = 300
            scale = min(max_size/width, max_size/height)
            
            if scale < 1:
                # 如果需要縮小，創建一個新的縮小版本
                new_width = int(width * scale)
                new_height = int(height * scale)
                photo = photo.subsample(int(1/scale))
            
            # 更新圖片顯示
            self.image_label.configure(image=photo)
            self.image_label.image = photo  # 保持引用以防止被垃圾回收
            
        except Exception as e:
            print(f"Error showing preview: {e}")
            self.image_label.configure(image="")  # 清除圖片


    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("PNG files", "*.png")]
        )
        if file_path:
            self.process_file(file_path)

    def handle_drop(self, event):
        file_paths = event.data
        # 將路徑字符串轉換為列表
        if '{' in file_paths:
            # Windows 風格的多個文件路徑會用空格分隔並用{}包圍
            paths = [p.strip('{}') for p in file_paths.split('} {')]
        else:
            # Unix 風格的多個文件路徑會用空格分隔
            paths = file_paths.split()
        
        # 檢查是否嘗試上傳多個文件
        if len(paths) > 1:
            messagebox.showerror("Error", "Please upload only one file at a time.")
            return
        
        file_path = paths[0]
        # 檢查是否為資料夾
        if os.path.isdir(file_path):
            messagebox.showerror("Error", "Please upload only one file at a time.")
            return
            
        # 檢查文件類型
        if file_path.endswith('.png'):
            self.process_file(file_path)
        else:
            messagebox.showerror("Error", "Please upload PNG files only.")

    def process_file(self, file_path):
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
                content_str = content.decode('utf-8', errors='ignore')
            
            detector = TimelineDetector(file_path)
            
            # Check if it's a scene data file
            if not detector.is_scene_data(content_str):
                messagebox.showerror("Error", "Please upload Scene Data only.")
                return  # 不清除之前的顯示內容
                
            # 只有在確認是scene data後才清除之前的顯示
            self.filename_label.configure(text="")
            self.timeline_label.configure(text="")
            self.duration_label.configure(text="")
            
            # Show filename
            filename = os.path.basename(file_path)
            self.filename_label.configure(text=filename)

            # Show preview
            self.show_preview(file_path)
            # Process timeline information
            timeline_status, duration = detector.check_timeline(content_str)
            
            if timeline_status == "has_timeline":
                self.timeline_label.configure(text="has timeline", 
                                           foreground="green")
                if duration is not None:
                    type_text = "GIF" if duration <= 10 else "movie"
                    self.duration_label.configure(
                        text=f"{type_text} (duration:{duration}s)")
            else:
                self.timeline_label.configure(text="no timeline", 
                                           foreground="red")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error processing file: {str(e)}")

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()