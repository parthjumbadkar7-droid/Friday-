"""
FRIDAY Agent - Full Agentic Computer Control
Runs on your laptop. Controls everything. Reports heartbeat to backend.
"""

import subprocess
import threading
import time
import os
import json
import sys
import shutil
import random
import ctypes
import pyautogui
import webbrowser
import glob
import platform
import requests
try:
    import psutil
except ImportError:
    psutil = None
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None
try:
    import send2trash
except ImportError:
    send2trash = None
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'friday-backend', '.env'))

app = Flask(__name__)

BACKEND_URL = os.getenv('RENDER_BACKEND_URL', 'https://friday-lwx5.onrender.com')
AGENT_SECRET = os.getenv('AGENT_SECRET', 'friday-secret-2024')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
TUNNEL_URL = None

MEMORY_FILE = os.path.join(os.path.dirname(__file__), 'friday_memory.json')

# ── TTS Engine ────────────────────────────────────────────────────
tts_engine = None
if pyttsx3:
    try:
        tts_engine = pyttsx3.init()
        tts_engine.setProperty('rate', 175)
        tts_engine.setProperty('volume', 0.9)
        voices = tts_engine.getProperty('voices')
        for v in voices:
            if 'female' in v.name.lower() or 'zira' in v.name.lower():
                tts_engine.setProperty('voice', v.id)
                break
    except Exception:
        tts_engine = None

def speak(text):
    if tts_engine and len(text) < 200:
        threading.Thread(
            target=lambda: (tts_engine.say(text), tts_engine.runAndWait()),
            daemon=True
        ).start()

USERNAME = os.environ.get("USERNAME", "Parth")

# ─────────────────────────────────────────────
#  APP MAP  (Windows paths + UWP shell IDs)
# ─────────────────────────────────────────────
APP_MAP = {
    "telegram":      r"shell:AppsFolder\TelegramMessengerLLP.TelegramDesktop_t4vj0pshhgkwm!Telegram",
    "camera":        r"shell:AppsFolder\Microsoft.WindowsCamera_8wekyb3d8bbwe!App",
    "discord":       f"C:\\Users\\{USERNAME}\\AppData\\Local\\Discord\\Update.exe --processStart Discord.exe",
    "vs code":       f"C:\\Users\\{USERNAME}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
    "vscode":        f"C:\\Users\\{USERNAME}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
    "git bash":      r"C:\Program Files\Git\git-bash.exe",
    "vlc":           r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "steam":         r"C:\Program Files (x86)\Steam\Steam.exe",
}

WEBSITE_MAP = {
    "youtube":   "https://youtube.com",
    "github":    "https://github.com",
    "google":    "https://google.com",
    "gmail":     "https://mail.google.com",
    "reddit":    "https://reddit.com",
    "netflix":   "https://netflix.com",
    "twitter":   "https://twitter.com",
    "x":         "https://x.com",
    "instagram": "https://instagram.com",
    "linkedin":  "https://linkedin.com",
    "chatgpt":   "https://chat.openai.com",
    "claude":    "https://claude.ai",
    "spotify":   "https://open.spotify.com",
    "discord":   "https://discord.com/app",
    "notion":    "https://notion.so",
    "figma":     "https://figma.com",
    "vercel":    "https://vercel.com",
    "render":    "https://render.com",
    "supabase":  "https://supabase.com",
}



def resolve_path(path):
    return path.replace("{user}", USERNAME)


# ─────────────────────────────────────────────
#  MEMORY SYSTEM
# ─────────────────────────────────────────────

def load_memory():
    try:
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"last_session": None, "frequent_apps": {}, "frequent_commands": [], "last_worked_on": "unknown", "notes": []}

def save_memory(mem):
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(mem, f, indent=2)
    except Exception:
        pass

def update_memory(app_name=None, command=None):
    mem = load_memory()
    mem["last_session"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if app_name:
        mem["frequent_apps"][app_name] = mem["frequent_apps"].get(app_name, 0) + 1
    if command:
        cmds = mem.get("frequent_commands", [])
        if command not in cmds:
            cmds.insert(0, command)
        mem["frequent_commands"] = cmds[:20]
    save_memory(mem)

def get_memory_context():
    mem = load_memory()
    top_apps = sorted(mem.get("frequent_apps", {}).items(), key=lambda x: -x[1])[:3]
    top_str = ", ".join(a for a, _ in top_apps) if top_apps else "none yet"
    return f"Parth's frequent apps: {top_str}. Last session: {mem.get('last_session','unknown')}. Last worked on: {mem.get('last_worked_on','unknown')}."


# ─────────────────────────────────────────────
#  FOLLOW-UP SUGGESTIONS (30% proactive)
# ─────────────────────────────────────────────

FOLLOW_UPS = {
    "spotify":      "Want me to also search for a specific playlist?",
    "vs code":      "Should I pull up your last project folder?",
    "vscode":       "Should I pull up your last project folder?",
    "youtube":      "Should I close other distracting tabs?",
    "screenshot":   "Want me to open it in Paint for editing?",
    "chrome":       "Want me to open a specific site?",
    "discord":      "Want me to mute notifications for focus time?",
}

def maybe_follow_up(action_type, app_name=""):
    if random.random() > 0.3:
        return None
    key = app_name.lower() if app_name else action_type
    return FOLLOW_UPS.get(key, None)


# ─────────────────────────────────────────────
#  SYSTEM EXTRAS
# ─────────────────────────────────────────────

def check_battery():
    if not psutil:
        return "psutil not installed — can't check battery."
    bat = psutil.battery()
    if bat is None:
        return "No battery detected (desktop PC)."
    status = "charging" if bat.power_plugged else "on battery"
    return f"✓ Battery: {bat.percent:.0f}% — {status}"

def get_current_time():
    return f"✓ Current time: {time.strftime('%I:%M %p, %A %d %B %Y')}"

def minimize_all():
    pyautogui.hotkey('win', 'd')
    return "✓ Minimized all windows"

def browser_control(action):
    action = action.lower().strip()
    if action == "new tab":
        pyautogui.hotkey('ctrl', 't')
    elif action == "close tab":
        pyautogui.hotkey('ctrl', 'w')
    elif action == "go back":
        pyautogui.hotkey('alt', 'left')
    elif action == "zoom in":
        pyautogui.hotkey('ctrl', '+')
    elif action == "zoom out":
        pyautogui.hotkey('ctrl', '-')
    elif action == "scroll down":
        pyautogui.scroll(-500)
    elif action == "scroll up":
        pyautogui.scroll(500)
    elif action == "refresh":
        pyautogui.press('f5')
    elif action == "incognito":
        pyautogui.hotkey('ctrl', 'shift', 'n')
    elif action == "copy":
        pyautogui.hotkey('ctrl', 'c')
    elif action == "paste":
        pyautogui.hotkey('ctrl', 'v')
    elif action == "select all":
        pyautogui.hotkey('ctrl', 'a')
    else:
        return f"✗ Unknown browser action: {action}"
    return f"✓ Browser: {action}"

def open_in_new_tab(url_or_name):
    from urllib.parse import quote as urlquote
    pyautogui.hotkey('ctrl', 't')
    time.sleep(0.5)
    if url_or_name.startswith("http"):
        url = url_or_name
    elif url_or_name in WEBSITE_MAP:
        url = WEBSITE_MAP[url_or_name]
    else:
        url = f"https://{url_or_name}"
    pyautogui.write(url, interval=0.03)
    pyautogui.press('enter')
    return f"✓ Opened {url} in new tab"

def find_file(filename):
    search_paths = [
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Pictures"),
    ]
    for sp in search_paths:
        matches = glob.glob(os.path.join(sp, "**", f"*{filename}*"), recursive=True)
        if matches:
            return matches[0]
    return None

def open_special_folder(name):
    folders = {
        "downloads": os.path.expanduser("~/Downloads"),
        "desktop":   os.path.expanduser("~/Desktop"),
        "documents": os.path.expanduser("~/Documents"),
        "pictures":  os.path.expanduser("~/Pictures"),
        "music":     os.path.expanduser("~/Music"),
    }
    path = folders.get(name.lower())
    if path:
        os.startfile(path)
        return f"✓ Opened {name} folder"
    return f"✗ Unknown folder: {name}"

def delete_file_safe(filename):
    path = find_file(filename)
    if path:
        if send2trash:
            send2trash.send2trash(path)
            return f"✓ Moved to Recycle Bin: {path}"
        os.remove(path)
        return f"✓ Deleted: {path}"
    return f"✗ File not found: {filename}"

def create_folder(name, location="desktop"):
    base = os.path.expanduser("~/Desktop") if location == "desktop" else os.path.expanduser(f"~/{location}")
    path = os.path.join(base, name)
    os.makedirs(path, exist_ok=True)
    return f"✓ Created folder: {path}"

def spotify_control(action):
    action = action.lower().strip()
    if action in ("pause", "play", "toggle"):
        pyautogui.press('playpause')
    elif action in ("next", "next song"):
        pyautogui.press('nexttrack')
    elif action in ("previous", "prev", "previous song"):
        pyautogui.press('prevtrack')
    else:
        return f"✗ Unknown Spotify action: {action}"
    return f"✓ Spotify: {action}"

def play_on_spotify(query):
    open_app("spotify")
    time.sleep(2.5)
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(0.3)
    pyautogui.write(query, interval=0.03)
    pyautogui.press('enter')
    return f"✓ Searched Spotify for: {query}"

def send_whatsapp_contact(contact, message):
    """Open WhatsApp desktop and send message to contact using Ctrl+F search."""
    open_app("whatsapp")
    time.sleep(3)
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.5)
    pyautogui.write(contact, interval=0.04)
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.write(message, interval=0.03)
    pyautogui.press('enter')
    return f"✓ Message sent to {contact}"




# ─────────────────────────────────────────────
#  CORE EXECUTORS
# ─────────────────────────────────────────────

def open_app(app_name):
    name = app_name.lower().strip()
    
    # Special cases first
    if name in ("whatsapp",):
        subprocess.run('start whatsapp:', shell=True)
        return f"✓ Opened {app_name}"
    
    if name in ("spotify",):
        subprocess.run('start spotify:', shell=True)
        return f"✓ Opened {app_name}"
    
    if name in ("cs2", "counter strike", "counter-strike"):
        webbrowser.open("steam://rungameid/730")
        return f"✓ Launching CS2 via Steam"
    
    if name in ("settings",):
        subprocess.Popen(["explorer.exe", "ms-settings:"])
        return f"✓ Opened Settings"

    # Method 1: Check APP_MAP for known paths
    if name in APP_MAP:
        target = resolve_path(APP_MAP[name])
        if target.startswith("shell:") or target.startswith("ms-"):
            subprocess.Popen(["explorer.exe", target])
            return f"✓ Opened {app_name}"
        if target.startswith("steam://"):
            webbrowser.open(target)
            return f"✓ Launched {app_name} via Steam"
        exe = target.split()[0]
        if os.path.exists(exe):
            subprocess.Popen(target, shell=True)
            return f"✓ Opened {app_name}"

    # Method 2: Windows START command (works for most installed apps by name)
    result = subprocess.run(f'start "" "{app_name}"', shell=True, capture_output=True)
    if result.returncode == 0:
        return f"✓ Opened {app_name}"

    # Method 3: Search Program Files and AppData for matching exe
    search_dirs = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        os.path.expanduser(r"~\AppData\Local"),
        os.path.expanduser(r"~\AppData\Roaming"),
    ]
    for d in search_dirs:
        try:
            matches = glob.glob(os.path.join(d, "**", f"{name}*.exe"), recursive=True)
            if matches:
                subprocess.Popen(matches[0], shell=True)
                return f"✓ Found and opened {app_name}"
        except Exception:
            continue

    # Method 4: PowerShell fuzzy search
    ps_cmd = f'powershell -command "Get-StartApps | Where-Object {{{{$_.Name -like \'*{name}*\'}}}} | Select-Object -First 1 | ForEach-Object {{{{ Start-Process $_.AppID }}}}"'
    subprocess.run(ps_cmd, shell=True)
    return f"✓ Attempted to open {app_name}"


def open_website(url_or_name):
    name = url_or_name.lower().strip()
    if name in WEBSITE_MAP:
        url = WEBSITE_MAP[name]
    elif url_or_name.startswith("http"):
        url = url_or_name
    else:
        url = f"https://{url_or_name}"
    
    webbrowser.open(url)
    return f"✓ Opened {url}"


def search_web(query):
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
    webbrowser.open(url)
    return f"✓ Searched Google for: {query}"


def open_file_or_folder(path):
    expanded = os.path.expanduser(path)
    if os.path.exists(expanded):
        os.startfile(expanded)
        return f"✓ Opened: {expanded}"
    
    # Try searching common locations
    search_paths = [
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Pictures"),
    ]
    filename = os.path.basename(path)
    for sp in search_paths:
        matches = glob.glob(os.path.join(sp, "**", filename), recursive=True)
        if matches:
            os.startfile(matches[0])
            return f"✓ Found and opened: {matches[0]}"
    
    return f"✗ File not found: {path}"


def take_screenshot(save_path=None):
    if not save_path:
        save_path = os.path.join(os.path.expanduser("~"), "Desktop", f"friday_screenshot_{int(time.time())}.png")
    screenshot = pyautogui.screenshot()
    screenshot.save(save_path)
    return f"✓ Screenshot saved to: {save_path}"


def system_control(action):
    action = action.lower()
    if action == "shutdown":
        subprocess.run(["shutdown", "/s", "/t", "30"])
        return "✓ Shutting down in 30 seconds (run 'shutdown /a' to cancel)"
    elif action == "restart":
        subprocess.run(["shutdown", "/r", "/t", "30"])
        return "✓ Restarting in 30 seconds"
    elif action == "lock":
        ctypes.windll.user32.LockWorkStation()
        return "✓ Screen locked"
    elif action == "sleep":
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
        return "✓ Going to sleep"
    elif action == "volume up":
        for _ in range(5):
            pyautogui.press("volumeup")
        return "✓ Volume increased"
    elif action == "volume down":
        for _ in range(5):
            pyautogui.press("volumedown")
        return "✓ Volume decreased"
    elif action == "mute":
        pyautogui.press("volumemute")
        return "✓ Toggled mute"
    return f"✗ Unknown system action: {action}"


def type_and_send(app_context, message):
    """Type text into whatever is focused. Works in WhatsApp, Telegram, etc."""
    time.sleep(1)
    pyautogui.typewrite(message, interval=0.03)
    time.sleep(0.3)
    pyautogui.press("enter")
    return f"✓ Typed and sent: {message}"


def run_shell_command(cmd):
    try:
        result = subprocess.run(
            cmd, shell=True,
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout or result.stderr or "(no output)"
        return f"✓ Command executed:\n{output[:1000]}"
    except subprocess.TimeoutExpired:
        return "✗ Command timed out after 30s"
    except Exception as e:
        return f"✗ Error: {e}"


def download_file(url, dest_folder=None):
    if not dest_folder:
        dest_folder = os.path.expanduser("~/Downloads")
    
    filename = url.split("/")[-1].split("?")[0] or "friday_download"
    save_path = os.path.join(dest_folder, filename)
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        os.startfile(dest_folder)  # open Downloads folder
        return f"✓ Downloaded to: {save_path}"
    except Exception as e:
        return f"✗ Download failed: {e}"


def close_app(app_name):
    name = app_name.lower().strip()
    
    PROCESS_MAP = {
        "whatsapp": ["WhatsApp.exe", "whatsapp.exe"],
        "spotify": ["Spotify.exe"],
        "chrome": ["chrome.exe"],
        "firefox": ["firefox.exe"],
        "edge": ["msedge.exe"],
        "discord": ["Discord.exe"],
        "telegram": ["Telegram.exe"],
        "vs code": ["Code.exe"],
        "vscode": ["Code.exe"],
        "notepad": ["notepad.exe"],
        "vlc": ["vlc.exe"],
        "steam": ["steam.exe"],
        "youtube": ["chrome.exe"],
    }
    
    processes = PROCESS_MAP.get(name, [f"{name}.exe"])
    killed = False
    
    for process in processes:
        result = subprocess.run(
            f'taskkill /F /IM "{process}" /T',
            shell=True, capture_output=True, text=True
        )
        if "SUCCESS" in result.stdout or result.returncode == 0:
            killed = True
    
    if killed:
        return f"✓ Closed {app_name}"
    
    # Last resort: use PowerShell to find and kill by window title
    ps_cmd = f'powershell -command "Get-Process | Where-Object {{$_.MainWindowTitle -like \'*{name}*\'}} | Stop-Process -Force"'
    subprocess.run(ps_cmd, shell=True)
    return f"✓ Attempted to close {app_name}"


def send_whatsapp_message(contact, message):
    """Open WhatsApp web with a pre-filled message to a contact."""
    encoded = requests.utils.quote(message)
    # WhatsApp Web deep link (works if already logged in)
    url = f"https://web.whatsapp.com/send?phone={contact}&text={encoded}"
    webbrowser.open(url)
    time.sleep(5)
    pyautogui.press("enter")
    return f"✓ Sent WhatsApp message to {contact}"


# ─────────────────────────────────────────────
#  AGENTIC AI LOOP  (Groq decides what to do)
# ─────────────────────────────────────────────

def build_system_prompt():
    mem_ctx = get_memory_context()
    return f"""You are FRIDAY, a personal AI assistant running on Parth's laptop.
You can control Parth's computer by outputting JSON commands.
{mem_ctx}

Your response MUST always be valid JSON with this structure:
{{
  "reply": "What you say to Parth (friendly, concise)",
  "actions": [
    {{"type": "action_type", "params": {{...}}}}
  ]
}}

Available action types:
- open_app:       {{"app": "spotify"}}
- close_app:      {{"app": "whatsapp"}}
- open_website:   {{"url": "youtube"}}
- new_tab:        {{"url": "github.com"}}
- browser:        {{"action": "new tab|close tab|go back|refresh|scroll down|scroll up|zoom in|zoom out|incognito|copy|paste|select all"}}
- search_web:     {{"query": "python tutorials"}}
- open_file:      {{"path": "~/Desktop/report.pdf"}}
- open_folder:    {{"name": "downloads|desktop|documents"}}
- find_file:      {{"name": "report.pdf"}}
- delete_file:    {{"name": "old_file.txt"}}
- create_folder:  {{"name": "MyProject", "location": "desktop"}}
- screenshot:     {{}}
- system:         {{"action": "lock|shutdown|restart|sleep|volume up|volume down|mute|minimize all|battery|time"}}
- spotify:        {{"action": "pause|next|previous"}}
- play_spotify:   {{"query": "lo-fi hip hop"}}
- shell:          {{"cmd": "dir C:\\\\"}}
- type_send:      {{"message": "Hello!"}}
- download:       {{"url": "https://...", "folder": "~/Downloads"}}
- whatsapp_msg:   {{"contact": "Parth", "message": "Hey!"}}
- wait:           {{"seconds": 2}}

Rules:
- Always respond in JSON. Never plain text.
- If nothing to do, actions = []
- Chain multiple actions for complex tasks with wait between steps
- Be proactive: if user says "play music", open Spotify AND play_spotify
- User is Parth, a hardware engineering student in Amravati, India.
"""

def ask_groq(user_message, conversation_history=None):
    if not GROQ_API_KEY:
        return {"reply": "Groq API key not configured.", "actions": []}
    
    messages = []
    if conversation_history:
        messages.extend(conversation_history[-6:])
    messages.append({"role": "user", "content": user_message})
    
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": build_system_prompt()}] + messages,
                "temperature": 0.4,
                "max_tokens": 1024,
            },
            timeout=15
        )
        content = res.json()["choices"][0]["message"]["content"]
        
        # Strip markdown fences if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        parsed = json.loads(content)
        
        # If reply is a dict, extract text
        reply_val = parsed.get("reply")
        if isinstance(reply_val, dict):
            parsed["reply"] = reply_val.get("reply", reply_val.get("text", str(reply_val)))
        elif not isinstance(reply_val, str):
            parsed["reply"] = str(reply_val)
            
        return parsed
    
    except json.JSONDecodeError:
        return {"reply": content, "actions": []}
    except Exception as e:
        return {"reply": f"AI error: {e}", "actions": []}


def execute_actions(actions, user_message=""):
    results = []
    follow_up = None

    for i, action in enumerate(actions):
        action_type = action.get("type")
        params = action.get("params", {})

        # Sequential delay between chained actions
        if i > 0:
            time.sleep(1)

        try:
            if action_type == "wait":
                time.sleep(float(params.get("seconds", 1)))
                results.append(f"✓ Waited {params.get('seconds', 1)}s")

            elif action_type == "open_app":
                app = params.get("app", "")
                r = open_app(app)
                results.append(r)
                update_memory(app_name=app, command=user_message)
                if not follow_up:
                    follow_up = maybe_follow_up("open_app", app)

            elif action_type == "close_app":
                results.append(close_app(params.get("app", "")))

            elif action_type == "open_website":
                results.append(open_website(params.get("url", "")))
                update_memory(command=user_message)

            elif action_type == "new_tab":
                results.append(open_in_new_tab(params.get("url", "")))

            elif action_type == "browser":
                results.append(browser_control(params.get("action", "")))

            elif action_type == "search_web":
                results.append(search_web(params.get("query", "")))

            elif action_type == "open_file":
                results.append(open_file_or_folder(params.get("path", "")))

            elif action_type == "open_folder":
                results.append(open_special_folder(params.get("name", "")))

            elif action_type == "find_file":
                path = find_file(params.get("name", ""))
                if path:
                    os.startfile(path)
                    results.append(f"✓ Opened: {path}")
                else:
                    results.append(f"✗ File not found: {params.get('name', '')}")

            elif action_type == "delete_file":
                results.append(delete_file_safe(params.get("name", "")))

            elif action_type == "create_folder":
                results.append(create_folder(params.get("name", ""), params.get("location", "desktop")))

            elif action_type == "screenshot":
                r = take_screenshot()
                results.append(r)
                if not follow_up:
                    follow_up = maybe_follow_up("screenshot")

            elif action_type == "system":
                act = params.get("action", "")
                if act == "battery":
                    results.append(check_battery())
                elif act == "time":
                    results.append(get_current_time())
                elif act == "minimize all":
                    results.append(minimize_all())
                else:
                    results.append(system_control(act))

            elif action_type == "spotify":
                results.append(spotify_control(params.get("action", "")))

            elif action_type == "play_spotify":
                results.append(play_on_spotify(params.get("query", "")))
                update_memory(app_name="spotify", command=user_message)
                if not follow_up:
                    follow_up = maybe_follow_up("open_app", "spotify")

            elif action_type == "shell":
                results.append(run_shell_command(params.get("cmd", "")))

            elif action_type == "type_send":
                results.append(type_and_send("", params.get("message", "")))

            elif action_type == "download":
                results.append(download_file(params.get("url", ""), params.get("folder")))

            elif action_type == "whatsapp":
                results.append(send_whatsapp_message(params.get("contact", ""), params.get("message", "")))

            elif action_type == "whatsapp_msg":
                results.append(send_whatsapp_contact(params.get("contact", ""), params.get("message", "")))

            else:
                results.append(f"✗ Unknown action: {action_type}")

        except Exception as e:
            results.append(f"✗ Action failed ({action_type}): {e}")

    return results, follow_up


# ─────────────────────────────────────────────
#  FLASK ROUTES
# ─────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "online", "agent": "FRIDAY", "timestamp": time.time()})


@app.route('/api/command', methods=['POST'])
def handle_command():
    data = request.json or {}
    secret = data.get("secret") or request.headers.get("X-Agent-Secret")
    
    if secret != AGENT_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_message = data.get("message", "")
    history = data.get("history", [])
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    # Let Groq decide what to do
    ai_response = ask_groq(user_message, history)
    
    if isinstance(ai_response, str):
        try:
            ai_response = json.loads(ai_response)
        except:
            ai_response = {"reply": ai_response, "actions": []}
            
    actions = ai_response.get("actions", [])
    reply = ai_response.get("reply", "Done!")
    
    if not isinstance(reply, str):
        reply = str(reply)
        
    # Execute the actions
    action_results, follow_up = execute_actions(actions, user_message)
    
    # Speak the reply on laptop
    speak(reply)
    
    return jsonify({
        "reply": reply,
        "actions": actions,
        "results": action_results,
        "follow_up": follow_up,
        "status": "ok"
    })


@app.route('/api/execute', methods=['POST'])
def execute_direct():
    """Direct command execution without AI (for backend to call specific actions)."""
    data = request.json or {}
    secret = data.get("secret") or request.headers.get("X-Agent-Secret")
    
    if secret != AGENT_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    
    actions = data.get("actions", [])
    results, _ = execute_actions(actions)
    return jsonify({"results": results, "status": "ok"})


@app.route('/api/memory', methods=['GET'])
def get_memory():
    return jsonify(load_memory())


@app.route('/api/memory/note', methods=['POST'])
def add_note():
    data = request.json or {}
    note = data.get("note", "")
    if note:
        mem = load_memory()
        mem.setdefault("notes", []).append({"text": note, "time": time.strftime("%Y-%m-%dT%H:%M:%S")})
        save_memory(mem)
    return jsonify({"ok": True})


@app.route('/api/speak', methods=['POST'])
def speak_route():
    data = request.json or {}
    text = data.get("text", "")
    if text:
        speak(text)
    return jsonify({"ok": True})


@app.route('/api/set-url', methods=['POST'])
def set_url():
    global TUNNEL_URL
    data = request.json
    TUNNEL_URL = data.get('url')
    print(f"✨ Agent URL updated: {TUNNEL_URL}")
    return jsonify({"success": True})

# ─────────────────────────────────────────────
#  HEARTBEAT  (keeps agent "online" in frontend)
# ─────────────────────────────────────────────

def heartbeat_loop():
    print("Starting heartbeat loop...")
    while True:
        try:
            res = requests.post(
                f"{BACKEND_URL}/api/agent/heartbeat",
                json={
                    "secret": AGENT_SECRET, 
                    "status": "online",
                    "url": TUNNEL_URL
                },
                timeout=8
            )
            if res.status_code == 200:
                print(f"[{time.strftime('%H:%M:%S')}] ♥ Heartbeat OK")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] ⚠ Heartbeat returned {res.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"[{time.strftime('%H:%M:%S')}] ✗ Backend unreachable, retrying in 15s...")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ✗ Heartbeat error: {e}")
        time.sleep(15)


# ─────────────────────────────────────────────
#  STARTUP
# ─────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 50)
    print("  FRIDAY Agent — Agentic Mode")
    print("=" * 50)
    print(f"  Backend: {BACKEND_URL}")
    print(f"  Groq: {'✓ Ready' if GROQ_API_KEY else '✗ No API key!'}")
    print("=" * 50)
    
    # Start heartbeat in background
    hb_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    hb_thread.start()
    
    # Start Flask
    app.run(host='0.0.0.0', port=5001, debug=False)
