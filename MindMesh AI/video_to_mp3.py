# Converts the videos to mp3 
import os 
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.telegram_helper import send_notification

files = os.listdir("videos") 
for file in files: 
    tutorial_number = file.split(" [")[0].split(" #")[1]
    file_name = file.split(" ｜ ")[0]
    print( tutorial_number,  file_name)
    subprocess.run(["ffmpeg", "-i", f"videos/{file}", f"audios/{tutorial_number}_{file_name}.mp3"])
    send_notification(f"✅ <b>Video Uploaded & Extracted</b>\n\nCourse: {file_name}")