import os
import subprocess
import webbrowser
import pathlib
from flask import Flask, request, jsonify
import pyautogui
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

app = Flask(__name__)

def execute_action(command):
    cmd = command.lower().strip()
    
    try:
        # --- OPEN WEBSITES ---
        if cmd.startswith("open "):
            target = cmd[5:].strip()
            
            # Apps first
            if target in ["cs2", "counter strike"]:
                os.startfile("steam://rungameid/730")
                return True, "Opened Counter Strike 2"
            elif target == "spotify":
                subprocess.Popen("spotify") # Assumes in PATH or standard start
                return True, "Opened Spotify"
            elif target in ["vs code", "vscode", "code"]:
                subprocess.Popen("code")
                return True, "Opened VS Code"
            elif target == "chrome":
                subprocess.Popen("chrome")
                return True, "Opened Chrome"
            elif target == "discord":
                # Assuming discord is typically installed in localappdata
                discord_path = os.path.join(os.getenv('LOCALAPPDATA'), "Discord", "Update.exe")
                subprocess.Popen(f'"{discord_path}" --processStart Discord.exe', shell=True)
                return True, "Opened Discord"
            elif target in ["file explorer", "explorer"]:
                subprocess.Popen("explorer")
                return True, "Opened File Explorer"
            elif target == "notepad":
                subprocess.Popen("notepad")
                return True, "Opened Notepad"
            elif target == "calculator":
                subprocess.Popen("calc")
                return True, "Opened Calculator"
            elif target == "task manager":
                subprocess.Popen("taskmgr")
                return True, "Opened Task Manager"
            
            # File Explorer specific folders
            elif target == "downloads":
                os.startfile(os.path.join(os.path.expanduser('~'), 'Downloads'))
                return True, "Opened Downloads"
            elif target == "documents":
                os.startfile(os.path.join(os.path.expanduser('~'), 'Documents'))
                return True, "Opened Documents"
            elif target == "desktop":
                os.startfile(os.path.join(os.path.expanduser('~'), 'Desktop'))
                return True, "Opened Desktop"
            
            # Websites
            elif target == "youtube":
                webbrowser.open("https://youtube.com")
                return True, "Opened YouTube"
            elif target == "github":
                webbrowser.open("https://github.com")
                return True, "Opened GitHub"
            elif target == "google":
                webbrowser.open("https://google.com")
                return True, "Opened Google"
            elif target == "netflix":
                webbrowser.open("https://netflix.com")
                return True, "Opened Netflix"
            elif target == "spotify web":
                webbrowser.open("https://open.spotify.com")
                return True, "Opened Spotify Web"
            else:
                # Fallback to general website
                webbrowser.open(f"https://{target.replace(' ', '')}.com")
                return True, f"Trying to open {target}.com"

        # --- SYSTEM CONTROLS ---
        elif cmd == "shutdown":
            os.system("shutdown /s /t 0")
            return True, "Shutting down system"
        elif cmd == "restart":
            os.system("shutdown /r /t 0")
            return True, "Restarting system"
        elif cmd == "sleep":
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return True, "Sleeping system"
        elif cmd == "lock screen":
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return True, "Locked screen"
        
        # --- AUDIO CONTROLS ---
        elif cmd in ["volume up", "volume down", "mute"]:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            if cmd == "mute":
                is_muted = volume.GetMute()
                volume.SetMute(int(not is_muted), None)
                return True, f"System {'unmuted' if is_muted else 'muted'}"
            else:
                current_vol = volume.GetMasterVolumeLevelScalar()
                new_vol = min(1.0, current_vol + 0.1) if cmd == "volume up" else max(0.0, current_vol - 0.1)
                volume.SetMasterVolumeLevelScalar(new_vol, None)
                return True, f"Volume changed to {int(new_vol * 100)}%"
        
        # --- FILE OPERATIONS ---
        elif cmd.startswith("create note "):
            note_name = cmd[12:].strip()
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            note_path = os.path.join(desktop, f"{note_name}.txt")
            with open(note_path, "w") as f:
                f.write("")
            os.startfile(note_path)
            return True, f"Created note {note_name} on Desktop"
            
        elif cmd == "take screenshot":
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            ss_path = os.path.join(desktop, "screenshot.png")
            screenshot = pyautogui.screenshot()
            screenshot.save(ss_path)
            return True, "Saved screenshot to Desktop"
            
        return False, "Command not recognized"
        
    except Exception as e:
        return False, f"Error executing command: {str(e)}"

@app.route('/execute', methods=['POST'])
def execute():
    data = request.json
    if not data or 'command' not in data:
        return jsonify({"success": False, "message": "No command provided"}), 400
        
    command = data['command']
    success, message = execute_action(command)
    
    return jsonify({
        "success": success,
        "message": message
    })

if __name__ == '__main__':
    print("FRIDAY Local Agent running on port 5001...")
    app.run(port=5001, host='127.0.0.1')
