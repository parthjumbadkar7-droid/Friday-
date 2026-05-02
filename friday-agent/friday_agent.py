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
import ctypes
import pyautogui
import webbrowser
import glob
import platform
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', 'friday-backend', '.env'))

app = Flask(__name__)

BACKEND_URL = os.getenv('RENDER_BACKEND_URL', 'https://friday-lwx5.onrender.com')
AGENT_SECRET = os.getenv('AGENT_SECRET', 'friday-secret-2024')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
TUNNEL_URL = None  # Updated by start_friday.py when tunnel opens

# ─────────────────────────────────────────────
#  APP MAP  (Windows paths + UWP shell IDs)
# ─────────────────────────────────────────────
APP_MAP = {
    # Only keep these — they NEED special handling
    "whatsapp":      f"C:\\Users\\{USERNAME}\\AppData\\Local\\WhatsApp\\WhatsApp.exe",
    "spotify":       f"C:\\Users\\{USERNAME}\\AppData\\Roaming\\Spotify\\Spotify.exe",
    "telegram":      r"shell:AppsFolder\TelegramMessengerLLP.TelegramDesktop_t4vj0pshhgkwm!Telegram",
    "camera":        r"shell:AppsFolder\Microsoft.WindowsCamera_8wekyb3d8bbwe!App",
    "settings":      "ms-settings:",
    "cs2":           "steam://rungameid/730",
    "counter strike":"steam://rungameid/730",
    "discord":       f"C:\\Users\\{USERNAME}\\AppData\\Local\\Discord\\Update.exe --processStart Discord.exe",
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
    "whatsapp":  "https://web.whatsapp.com",
    "discord":   "https://discord.com/app",
    "notion":    "https://notion.so",
    "figma":     "https://figma.com",
    "vercel":    "https://vercel.com",
    "render":    "https://render.com",
    "supabase":  "https://supabase.com",
}

USERNAME = os.environ.get("USERNAME", "Parth")

def resolve_path(path):
    return path.replace("{user}", USERNAME)


# ─────────────────────────────────────────────
#  CORE EXECUTORS
# ─────────────────────────────────────────────

def open_app(app_name):
    name = app_name.lower().strip()
    
    # Method 1: Check APP_MAP first (for known UWP/special apps)
    if name in APP_MAP:
        target = resolve_path(APP_MAP[name])
        if target.startswith("shell:") or target.startswith("ms-"):
            try:
                os.startfile(target)
            except Exception:
                subprocess.Popen(f'explorer "{target}"', shell=True)
            return f"✓ Opened {app_name}"
        if target.startswith("steam://"):
            webbrowser.open(target)
            return f"✓ Launched {app_name} via Steam"
        exe = target.split()[0]
        if os.path.exists(exe):
            subprocess.Popen(target, shell=True)
            return f"✓ Opened {app_name}"

    # Method 2: Try Windows START command (works for most installed apps)
    try:
        subprocess.Popen(f'start "" "{app_name}"', shell=True)
        time.sleep(1)
        return f"✓ Opened {app_name}"
    except Exception:
        pass

    # Method 3: Search for exe in common install locations
    search_dirs = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        f"C:\\Users\\{USERNAME}\\AppData\\Local",
        f"C:\\Users\\{USERNAME}\\AppData\\Roaming",
    ]
    for d in search_dirs:
        try:
            matches = glob.glob(os.path.join(d, "**", f"{app_name}*.exe"), recursive=True)
            if matches:
                subprocess.Popen(f'"{matches[0]}"', shell=True)
                return f"✓ Found and opened {app_name}"
        except Exception:
            continue

    # Method 4: Try Windows Search via shell
    try:
        subprocess.Popen(f'explorer shell:AppsFolder', shell=True)
        time.sleep(0.5)
        subprocess.Popen(f'start "" "{app_name}"', shell=True)
        return f"✓ Attempted to open {app_name}"
    except Exception:
        pass

    # Method 5: Ask user for exact name
    return f"✗ Could not find {app_name}. Try saying the exact app name."


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

SYSTEM_PROMPT = f"""You are FRIDAY, a personal AI assistant running on Parth's laptop.
You can control Parth's computer by outputting JSON commands.

Your response MUST always be valid JSON with this structure:
{{
  "reply": "What you say to Parth (friendly, concise)",
  "actions": [
    {{"type": "action_type", "params": {{...}}}}
  ]
}}

Available action types and their params:
- open_app:       {{"app": "spotify"}}
- open_website:   {{"url": "youtube"}}
- search_web:     {{"query": "python tutorials"}}
- open_file:      {{"path": "~/Desktop/report.pdf"}}
- screenshot:     {{}}
- system:         {{"action": "lock|shutdown|restart|sleep|volume up|volume down|mute"}}
- shell:          {{"cmd": "dir C:\\"}}
- type_send:      {{"message": "Hello!"}}
- download:       {{"url": "https://...", "folder": "~/Downloads"}}
- whatsapp:       {{"contact": "+919999999999", "message": "Hey!"}}

Rules:
- Always respond in JSON. Never plain text.
- If nothing to do, actions = []
- Chain multiple actions for complex tasks
- Be proactive: if user says "play music", open Spotify AND search for the song
- User is Parth, a hardware engineering student in Amravati, India.
"""

def ask_groq(user_message, conversation_history=None):
    if not GROQ_API_KEY:
        return {"reply": "Groq API key not configured.", "actions": []}
    
    messages = []
    if conversation_history:
        messages.extend(conversation_history[-6:])  # last 3 turns
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
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                "temperature": 0.4,
                "max_tokens": 1024,
            },
            timeout=15
        )
        content = res.json()["choices"][0]["message"]["content"]
        
        # Strip markdown fences if present
        content = content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(content)
    
    except json.JSONDecodeError:
        return {"reply": content, "actions": []}
    except Exception as e:
        return {"reply": f"AI error: {e}", "actions": []}


def execute_actions(actions):
    results = []
    for action in actions:
        action_type = action.get("type")
        params = action.get("params", {})
        
        try:
            if action_type == "open_app":
                results.append(open_app(params.get("app", "")))
            elif action_type == "open_website":
                results.append(open_website(params.get("url", "")))
            elif action_type == "search_web":
                results.append(search_web(params.get("query", "")))
            elif action_type == "open_file":
                results.append(open_file_or_folder(params.get("path", "")))
            elif action_type == "screenshot":
                results.append(take_screenshot())
            elif action_type == "system":
                results.append(system_control(params.get("action", "")))
            elif action_type == "shell":
                results.append(run_shell_command(params.get("cmd", "")))
            elif action_type == "type_send":
                results.append(type_and_send("", params.get("message", "")))
            elif action_type == "download":
                results.append(download_file(params.get("url", ""), params.get("folder")))
            elif action_type == "whatsapp":
                results.append(send_whatsapp_message(params.get("contact", ""), params.get("message", "")))
            else:
                results.append(f"✗ Unknown action: {action_type}")
        except Exception as e:
            results.append(f"✗ Action failed ({action_type}): {e}")
    
    return results


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
    actions = ai_response.get("actions", [])
    
    # Execute the actions
    action_results = execute_actions(actions)
    
    return jsonify({
        "reply": ai_response.get("reply", "Done!"),
        "actions": actions,
        "results": action_results,
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
    results = execute_actions(actions)
    return jsonify({"results": results, "status": "ok"})


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
