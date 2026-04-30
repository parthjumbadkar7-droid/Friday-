import subprocess
import threading
import time
import re
import os
import signal
import sys
from dotenv import load_dotenv
import requests

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'friday-backend', '.env'))

RENDER_API_KEY = os.getenv('RENDER_API_KEY')
RENDER_SERVICE_ID = os.getenv('RENDER_SERVICE_ID')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.join(BASE_DIR, 'friday-agent')

agent_process = None
tunnel_process = None

def start_agent():
    global agent_process
    print("Starting Friday agent...")
    agent_process = subprocess.Popen(
        ['python', 'friday_agent.py'],
        cwd=AGENT_DIR,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    print("Agent started!")

def update_render_url(url):
    print(f"Updating Render with new tunnel URL: {url}")
    
    if not RENDER_API_KEY or not RENDER_SERVICE_ID:
        print("ERROR: RENDER_API_KEY or RENDER_SERVICE_ID missing from .env file!")
        return

    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    try:
        # Get all env vars
        res = requests.get(
            f'https://api.render.com/v1/services/{RENDER_SERVICE_ID}/env-vars',
            headers=headers,
            timeout=15
        )
        
        print(f"GET status: {res.status_code}")
        
        if res.status_code == 401:
            print("ERROR: Invalid Render API key. Check your .env file.")
            return
        
        if res.status_code != 200:
            print(f"Failed to get env vars: {res.text}")
            return

        env_vars = res.json()
        
        # Build updated list
        updated_vars = []
        found = False
        for var in env_vars:
            key = var.get('envVar', {}).get('key') or var.get('key', '')
            value = var.get('envVar', {}).get('value') or var.get('value', '')
            if key == 'LOCAL_AGENT_URL':
                updated_vars.append({'key': 'LOCAL_AGENT_URL', 'value': url})
                found = True
            else:
                updated_vars.append({'key': key, 'value': value})
        
        if not found:
            updated_vars.append({'key': 'LOCAL_AGENT_URL', 'value': url})

        # Update env vars
        put_res = requests.put(
            f'https://api.render.com/v1/services/{RENDER_SERVICE_ID}/env-vars',
            headers=headers,
            json=updated_vars,
            timeout=15
        )

        print(f"PUT status: {put_res.status_code}")
        
        if put_res.status_code in [200, 201]:
            print(f"\n✓ Render updated successfully!")
            print(f"✓ Friday can now control your laptop!")
            print(f"✓ Tunnel URL: {url}\n")
        else:
            print(f"Failed to update Render: {put_res.text}")

    except requests.exceptions.Timeout:
        print("Request timed out. Check your internet connection.")
    except Exception as e:
        print(f"Error: {e}")

def start_tunnel():
    global tunnel_process
    print("Starting Cloudflare tunnel...")
    tunnel_process = subprocess.Popen(
        ['cloudflared', 'tunnel', '--url', 'http://localhost:5001'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    url_found = False
    for line in tunnel_process.stdout:
        print(line.strip())
        if not url_found:
            match = re.search(r'https://[a-z0-9\-]+\.trycloudflare\.com', line)
            if match:
                tunnel_url = match.group(0)
                url_found = True
                update_render_url(tunnel_url)

def shutdown(sig=None, frame=None):
    print("\nShutting down Friday...")
    if agent_process:
        agent_process.terminate()
    if tunnel_process:
        tunnel_process.terminate()
    print("Friday stopped. Goodbye!")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)

if __name__ == '__main__':
    print("=" * 50)
    print("  FRIDAY - Starting up...")
    print("=" * 50)

    print(f"API Key loaded: {'YES' if RENDER_API_KEY else 'NO - CHECK .env FILE'}")
    print(f"Service ID loaded: {'YES' if RENDER_SERVICE_ID else 'NO - CHECK .env FILE'}")

    start_agent()
    time.sleep(3)

    tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
    tunnel_thread.start()

    print("\nFriday is starting! Wait for success message...")
    print("Press Ctrl+C to stop everything.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()