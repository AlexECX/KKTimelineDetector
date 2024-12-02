from js import document, File, window, FileReader
from pyodide.ffi import create_proxy, to_js
import base64

class TimelineDetector:
    def __init__(self):
        self.file_content = None
        
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

detector = TimelineDetector()

def update_ui(filename, timeline_status, duration_text):
    # Update filename
    filename_elem = document.getElementById("filename")
    filename_elem.innerText = filename
    
    # Update timeline status
    status_elem = document.getElementById("timelineStatus")
    status_elem.innerText = timeline_status
    if timeline_status == "has timeline":
        status_elem.style.color = "green"
    else:
        status_elem.style.color = "red"
    
    # Update duration info
    duration_elem = document.getElementById("durationInfo")
    duration_elem.innerText = duration_text

def process_file(event):
    file = event.target.files[0]
    if not file:
        return
        
    if not file.name.lower().endswith('.png'):
        window.alert("Please upload .png files only.")
        return
        
    def handle_load(event):
        content = event.target.result
        try:
            # Convert ArrayBuffer to string
            content_str = bytes(content).decode('utf-8', errors='ignore')
            
            if not detector.is_scene_data(content_str):
                window.alert("Please upload Scene Data only.")
                return
                
            # Process timeline information
            timeline_status, image_type, duration = detector.check_timeline(content_str)
            
            # Update preview image
            preview = document.getElementById("preview")
            preview.src = URL.createObjectURL(file)
            preview.style.display = "block"
            
            # Prepare UI update information
            if timeline_status == "has_timeline":
                if image_type == "static":
                    duration_text = "static image"
                else:  # dynamic
                    if duration is not None:
                        type_text = "GIF" if duration <= 10 else "movie"
                        duration_text = f"{type_text} (duration:{duration}s)"
                    else:
                        duration_text = ""
            else:  # no timeline
                duration_text = ""
                
            # Update UI
            update_ui(file.name, timeline_status, duration_text)
            
        except Exception as e:
            window.alert(f"Error processing file: {str(e)}")
            
    reader = FileReader.new()
    reader.onload = create_proxy(handle_load)
    reader.readAsArrayBuffer(file)

def handle_drag_over(event):
    event.preventDefault()
    drop_zone = document.getElementById("dropZone")
    drop_zone.classList.add("dragover")

def handle_drag_leave(event):
    event.preventDefault()
    drop_zone = document.getElementById("dropZone")
    drop_zone.classList.remove("dragover")

def handle_drop(event):
    event.preventDefault()
    drop_zone = document.getElementById("dropZone")
    drop_zone.classList.remove("dragover")
    
    # Get the dropped file
    file = event.dataTransfer.files[0]
    if file:
        # Update the file input
        file_input = document.getElementById("fileInput")
        file_input.files = event.dataTransfer.files
        # Trigger the file processing
        process_file(to_js({"target": {"files": [file]}}))

# Set up event listeners
file_input = document.getElementById("fileInput")
file_input.addEventListener("change", create_proxy(process_file))

drop_zone = document.getElementById("dropZone")
drop_zone.addEventListener("dragover", create_proxy(handle_drag_over))
drop_zone.addEventListener("dragleave", create_proxy(handle_drag_leave))
drop_zone.addEventListener("drop", create_proxy(handle_drop))