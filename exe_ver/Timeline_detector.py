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
        
    def check_timeline(self, content_str: str) -> tuple[str, str, float]:
            """
            檢查timeline類型並返回timeline狀態和duration
            Returns: 
                tuple (timeline_status, image_type, duration)
                timeline_status: "has_timeline" 或 "no_timeline"
                image_type: "dynamic", "static" 或 None
                duration: float 或 None
            """
            if "timeline" in content_str:  # 先檢查是否有timeline
                # 檢查是否為static (沒有Timeline就是static)
                if "Timeline" not in content_str:
                    return "has_timeline", "static", None
                else:
                    # 是dynamic，檢查duration
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
                                    return "has_timeline", "dynamic", duration
                                except ValueError:
                                    return "has_timeline", "dynamic", None
                            search_pos += 1
                    return "has_timeline", "dynamic", None
            return "no_timeline", None, None
class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Timeline Detector")
        self.geometry("400x500")
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
        
        # Image preview
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
            photo = tk.PhotoImage(file=file_path)
            
            width = photo.width()
            height = photo.height()
            
            max_size = 300
            scale = min(max_size/width, max_size/height)
            
            if scale < 1:
                new_width = int(width * scale)
                new_height = int(height * scale)
                photo = photo.subsample(int(1/scale))
            
            self.image_label.configure(image=photo)
            self.image_label.image = photo
            
        except:
            self.image_label.configure(image="")

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[(".png files", "*.png *.PNG")]
        )
        if file_path:
            self.process_file(file_path)

    def handle_drop(self, event, *args):
        """
        Handle the drag-and-drop event.
        Ensure that the input is a single .png file and not a folder.
        """
        file_paths = event.data
        # Parse file paths from the event
        if '{' in file_paths:
            paths = [p.strip('{}') for p in file_paths.split('} {')]
        else:
            paths = file_paths.split()

        # Check if multiple files or folders are provided
        if len(paths) > 1:
            for path in paths:
                if os.path.isdir(path):
                    messagebox.showerror("Error", "Please do not upload folders. Upload one .png file at a time.")
                    return
            messagebox.showerror("Error", "Please upload only one .png file at a time.")
            return

        # Validate single file path
        file_path = paths[0]
        if os.path.isdir(file_path):
            messagebox.showerror("Error", "Please do not upload folders. Upload one .png file at a time.")
            return

        if not file_path.lower().endswith('.png'):
            messagebox.showerror("Error", "Please upload .png files only.")
            return
        
        self.process_file(file_path)





    def process_file(self, file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
            content_str = content.decode('utf-8', errors='ignore')
        
        detector = TimelineDetector(file_path)
        
        if not detector.is_scene_data(content_str):
            messagebox.showerror("Error", "Please upload Scene Data only.")
            return
        
        self.filename_label.configure(text="")
        self.timeline_label.configure(text="")
        self.duration_label.configure(text="")
        
        filename = os.path.basename(file_path)
        self.filename_label.configure(text=filename)

        self.show_preview(file_path)
        
        timeline_status, image_type, duration = detector.check_timeline(content_str)
        
        if timeline_status == "has_timeline":
            self.timeline_label.configure(text="has timeline", 
                                       foreground="green")
            if image_type == "static":
                self.duration_label.configure(text="static image")
            else:  # dynamic
                if duration is not None:
                    type_text = "GIF" if duration <= 10 else "movie"
                    self.duration_label.configure(
                        text=f"{type_text} (duration:{duration}s)")
        else:  # no timeline
            self.timeline_label.configure(text="no timeline", 
                                       foreground="red")
            self.duration_label.configure(text="")
def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()