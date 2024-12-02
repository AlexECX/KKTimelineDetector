from js import document, File, window, FileReader, Uint8Array, URL
from pyodide.ffi import create_proxy
import base64

class TimelineDetector:
    def __init__(self):
        self.file_content = None
        
    def is_scene_data(self, content_str: str) -> bool:
        """檢查是否為scene data"""
        try:
            return b"KStudio" in content_str
        except:
            return False
        
    def check_timeline(self, content) -> tuple[str, str, float]:
        """
        檢查timeline類型並返回timeline狀態和duration
        """
        try:
            content_str = str(content)
            if b"timeline" in content:  # 先檢查是否有timeline
                # 檢查是否為static (沒有Timeline就是static)
                if b"Timeline" not in content:
                    return "has_timeline", "static", None
                else:
                    # 是dynamic，檢查duration
                    if b"duration" in content:
                        content_str = content.decode('utf-8', errors='ignore')
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
        except Exception as e:
            print(f"Error in check_timeline: {str(e)}")
            return "no_timeline", None, None

detector = TimelineDetector()

def update_ui(filename, timeline_status, duration_text):
    # Update filename
    filename_elem = document.getElementById("filename")
    filename_elem.innerText = filename
    
    # Update timeline status
    status_elem = document.getElementById("timelineStatus")
    status_elem.innerText = timeline_status
    status_elem.style.color = "#34a853" if timeline_status == "has_timeline" else "#ea4335"
    
    # Update duration info
    duration_elem = document.getElementById("durationInfo")
    duration_elem.innerText = duration_text

def process_file(event):
    try:
        # 1. 檢查是否為拖放事件
        if hasattr(event, 'dataTransfer'):
            # === 拖放事件處理 ===
            files = event.dataTransfer.files
            
            # 1.1 檢查是否為資料夾
            first_file = files.item(0)
            if not first_file.type:
                window.alert("Please do not upload folders. upload only one file at a time.")
                return
            
            # if not hasattr(first_file, 'type') or not first_file.type:  # 沒有 type 或 type 為空
            #     if hasattr(first_file, 'webkitRelativePath') and first_file.webkitRelativePath:
            #         # 通過 webkitRelativePath 判斷是否為資料夾
            #         if '/' in first_file.webkitRelativePath:
            #             window.alert("Folder detected. Please upload individual files.")
            #             return
            #     else:
            #         window.alert("File type or path indicates a folder. Please do not upload folders.")
            #         return
                
            # 1.2 檢查檔案數量
            if files.length > 1:
                window.alert("Please upload only one file at a time.")
                return
                
            file = first_file
        else:
            # === 一般檔案上傳處理 ===
            files = event.target.files
            
            # 2.1 檢查檔案數量
            if files.length > 1:
                window.alert("Please upload only one file at a time.")
                return
                
            file = files.item(0)
        
        # === 共同的檢查 ===
        # 檢查是否為 .png 檔案
        if not str(file.name).lower().endswith('.png'):
            window.alert("Please upload .png files only.")
            return
            
        def handle_load(event):
            try:
                # 處理檔案內容
                array_buffer = event.target.result
                uint8_array = Uint8Array.new(array_buffer)
                content = bytes(uint8_array.to_py())
                
                # 檢查是否為 scene data
                if not detector.is_scene_data(content):
                    window.alert("Please upload Scene Data only.")
                    return
                    
                # Timeline 處理
                timeline_status, image_type, duration = detector.check_timeline(content)
                
                # 更新預覽圖片
                preview = document.getElementById("preview")
                preview.src = URL.createObjectURL(file)
                preview.style.display = "block"
                
                # 準備 UI 更新資訊
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
                    
                # 更新 UI
                update_ui(file.name, timeline_status, duration_text)
                
            except Exception as e:
                print(f"Error in handle_load: {str(e)}")
                window.alert(f"Error processing file: {str(e)}")
                
        reader = FileReader.new()
        reader.onload = create_proxy(handle_load)
        reader.readAsArrayBuffer(file)
    except Exception as e:
        print(f"Error in process_file: {str(e)}")
        window.alert(f"Error in process_file: {str(e)}")

def handle_drag_over(event):
    event.preventDefault()
    document.body.classList.add("dragover")

def handle_drag_leave(event):
    event.preventDefault()
    document.body.classList.remove("dragover")

def handle_drop(event):
    event.preventDefault()
    document.body.classList.remove("dragover")
    
    try:
        process_file(event)
    except Exception as e:
        print(f"Error in handle_drop: {str(e)}")
        window.alert(f"Error in handle_drop: {str(e)}")

# Set up event listeners
file_input = document.getElementById("fileInput")
file_input.addEventListener("change", create_proxy(process_file))

# 設置整個視窗作為拖放區域
document.body.addEventListener("dragover", create_proxy(handle_drag_over))
document.body.addEventListener("dragleave", create_proxy(handle_drag_leave))
document.body.addEventListener("drop", create_proxy(handle_drop))