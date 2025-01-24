import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import typing
from tkinterdnd2 import DND_FILES, TkinterDnD


class TimelineDetector:

    _timeline_pattern = re.compile(rb'timeline.+?sceneInfo(?P<flag>.*?)(?P<data><root\b[^>]*?>.*?</root>)', re.DOTALL)
    _duration_pattern = re.compile(rb'duration="([\d\.]+)"')
    _animation_pattern = re.compile(rb'guideObjectPath="([^"]+)"')
    
    def __init__(self, file_path: str = None):
        self.file_path = file_path
        
    def is_scene_data(self, content: bytes) -> bool:
        """檢查是否為scene data"""
        return b"KStudio" in content
    
    def get_timeline_xml(self, content: bytes) -> typing.Optional[bytes]:
        match = self.timeline_regex.search(content)
        if match and b'</root>' in match.group("data"):
            return match.group("data")
        else:
            return None            
        
    def check_timeline(self, content_str: str) -> tuple[str, str, float]:
            """
            檢查timeline類型並返回timeline狀態和duration
            Returns: 
                tuple (timeline_status, image_type, duration)
                timeline_status: "has_timeline" 或 "no_timeline"
                image_type: "animation", "dynamic", "static" 或 None
                duration: float 或 None
            """
            timeline_xml = self.get_timeline_xml()
            if not timeline_xml :  # 沒有timeline :: Check if there is a timeline
                return "no_timeline", None, None
            elif b'Timeline' not in timeline_xml:
                return "has_timeline", "static", None
            elif match := re.search(self._duration_pattern, timeline_xml):
                if self._animation_pattern.search(timeline_xml):
                    # A timeline with a guideObject interpolable is most likely an animation.
                    return "has_timeline", "animation", float(match.group(1))
                else:
                    # Without a guideObject, it's most likely camera movement, sound effects or alpha/color changes.
                    return "has_timeline", "dynamic", float(match.group(1))
            else:
                return "has_timeline", "dynamic", None
            

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
        
        detector = TimelineDetector(file_path)
        
        if not detector.is_scene_data(content):
            messagebox.showerror("Error", "Please upload Scene Data only.")
            return
        
        self.filename_label.configure(text="")
        self.timeline_label.configure(text="")
        self.duration_label.configure(text="")
        
        filename = os.path.basename(file_path)
        self.filename_label.configure(text=filename)

        self.show_preview(file_path)
        
        timeline_status, image_type, duration = detector.check_timeline(content)
        
        if timeline_status == "has_timeline":
            self.timeline_label.configure(text="has timeline", 
                                       foreground="green")
            if image_type == "static":
                self.duration_label.configure(text="static image")
            elif image_type == "dynamic": 
                if duration is None:
                    self.duration_label.configure(text="dynamic image")
                else:
                    self.duration_label.configure(
                        text=f"dynamic scene (duration:{duration}s)")
            else: # animation
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