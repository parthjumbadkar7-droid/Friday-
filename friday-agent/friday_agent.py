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
                if target in ["cs2", "counter strike"]:
                    os.startfile('steam://rungameid/730')
                    return True, "Opened Counter Strike 2"
                elif target == "spotify" or target == "spotify app":
                    os.startfile('spotify:')
                    return True, "Opened Spotify"
                elif target in ["vs code", "vscode", "code"]:
                    try:
                        os.startfile('code.cmd') # VS Code often registers this
                    except:
                        subprocess.Popen(['code'], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    return True, "Opened VS Code"
                elif target == "chrome":
                    try:
                        os.startfile('chrome.exe')
                    except:
                        chrome_paths = [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]
                        for p in chrome_paths:
                            if os.path.exists(p):
                                os.startfile(p)
                                return True, "Opened Chrome"
                        return False, "Could not find Chrome"
                    return True, "Opened Chrome"
                elif target == "opera":
                    try:
                        os.startfile('opera.exe')
                    except:
                        opera_paths = [os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera\opera.exe"), r"C:\Program Files\Opera\opera.exe"]
                        for p in opera_paths:
                            if os.path.exists(p):
                                os.startfile(p)
                                return True, "Opened Opera"
                        return False, "Could not find Opera"
                    return True, "Opened Opera"
                elif target == "discord":
                    discord_path = os.path.join(os.getenv('LOCALAPPDATA'), "Discord", "Update.exe")
                    if os.path.exists(discord_path):
                        subprocess.Popen([discord_path, '--processStart', 'Discord.exe'], creationflags=subprocess.CREATE_NO_WINDOW)
                    else:
                        os.startfile('discord:')
                    return True, "Opened Discord"
                elif target in ["file explorer", "explorer"]:
                    os.startfile('explorer.exe')
                    return True, "Opened File Explorer"
                elif target == "notepad":
                    os.startfile('notepad.exe')
                    return True, "Opened Notepad"
                elif target == "calculator":
                    os.startfile('calc.exe')
                    return True, "Opened Calculator"
                elif target == "task manager":
                    os.startfile('taskmgr.exe')
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
                
                else:
                    # Fallback for unrecognized apps using Windows smart start
                    # Also checking if it could be a website
                    if '.' in target:
                        webbrowser.open(f"https://{target}")
                    else:
                        os.startfile(target)
                    return True, f"Trying to open {target}"
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
