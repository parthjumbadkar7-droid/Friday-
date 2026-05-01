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
            
            # Websites (always webbrowser)
            if target in ["youtube", "github", "google", "netflix", "spotify web"]:
                url = f"https://{target.replace(' ', '')}.com"
                if target == "spotify web": url = "https://open.spotify.com"
                webbrowser.open(url)
                return True, f"Opened {target.title()}"
                
            # Apps
            try:
                # --- SMART APP/FILE RESOLVER ---
                # 1. Broad Friendly Mapping
                friendly_map = {
                    "whatsapp": "whatsapp:",
                    "telegram": "tg:",
                    "file manager": "explorer.exe",
                    "file explorer": "explorer.exe",
                    "this pc": "explorer.exe",
                    "my computer": "explorer.exe",
                    "cs2": "steam://rungameid/730",
                    "counter strike": "steam://rungameid/730",
                    "settings": "ms-settings:",
                    "control panel": "control",
                    "task manager": "taskmgr.exe",
                    "browser": "opera",
                    "web": "opera",
                    "terminal": "wt.exe",
                    "cmd": "cmd.exe",
                    "powershell": "powershell.exe",
                    "calculator": "calc.exe",
                    "notepad": "notepad.exe",
                    "paint": "mspaint.exe",
                    "camera": "microsoft.windows.camera:",
                    "photos": "ms-photos:",
                    "store": "ms-windows-store:",
                    "mail": "outlookmail:",
                    "calendar": "outlookcal:",
                    "maps": "bingmaps:",
                    "weather": "bingweather:"
                }
                
                resolved_target = friendly_map.get(target.lower())
                if resolved_target:
                    try:
                        os.startfile(resolved_target)
                        return True, f"Opened {target}"
                    except: pass

                # 2. Try direct os.startfile (handles protocols and registered exes)
                try:
                    os.startfile(target)
                    return True, f"Opened {target}"
                except: pass

                # 3. Try with .exe
                try:
                    os.startfile(f"{target}.exe")
                    return True, f"Opened {target}"
                except: pass

                # 4. Search deep roots including AppData
                search_roots = [
                    os.path.join(os.environ["ProgramFiles"]),
                    os.path.join(os.environ["ProgramFiles(x86)"]),
                    os.path.join(os.environ["LOCALAPPDATA"]), # Crucial for WhatsApp/Discord
                    os.path.join(os.environ["APPDATA"]),
                    os.path.join(os.path.expanduser("~"), "Desktop")
                ]
                
                for root in search_roots:
                    if not os.path.exists(root): continue
                    for dirpath, _, filenames in os.walk(root):
                        # Limit depth for speed
                        if dirpath.count(os.sep) - root.count(os.sep) > 2:
                            continue
                        for f in filenames:
                            if target.lower() in f.lower() and f.endswith(".exe"):
                                full_path = os.path.join(dirpath, f)
                                os.startfile(full_path)
                                return True, f"Found and opened: {f}"
                
                # 5. Try 'start' via shell for protocols or registered aliases
                try:
                    subprocess.Popen(f'start {target}', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    return True, f"Triggered system start for {target}"
                except: pass

                return False, f"I searched everywhere but couldn't find '{target}'. Try saying the full app name or checking if it's installed."
            except Exception as e:
                return False, f"Failed to launch {target}: {str(e)}"

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
            
        elif cmd.startswith("close "):
            target = cmd[6:].strip()
            # Map common names to process names
            process_map = {
                "chrome": "chrome.exe",
                "opera": "opera.exe",
                "vs code": "code.exe",
                "vscode": "code.exe",
                "code": "code.exe",
                "spotify": "Spotify.exe",
                "discord": "Discord.exe",
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "task manager": "taskmgr.exe",
                "file manager": "explorer.exe",
                "explorer": "explorer.exe",
                "cs2": "cs2.exe"
            }
            
            pname = process_map.get(target.lower(), f"{target}.exe")
            try:
                # Try killing by process name (with and without .exe)
                subprocess.run(['taskkill', '/F', '/IM', pname], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(['taskkill', '/F', '/IM', target], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                # Also try killing by window title wildcard
                subprocess.run(['taskkill', '/F', '/FI', f"WINDOWTITLE eq {target}*"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                return True, f"Closed {target}"
            except Exception as e:
                return False, f"Failed to close {target}: {str(e)}"
                
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
