"""
start_friday.py — FRIDAY Startup Orchestrator
Starts agent → waits for it → starts tunnel → registers URL with backend
"""

import subprocess
import threading
import time
import re
import os
import signal
import sys
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'friday-backend', '.env'))

RENDER_API_KEY      = os.getenv('RENDER_API_KEY')
RENDER_SERVICE_ID   = os.getenv('RENDER_SERVICE_ID')
BACKEND_URL         = os.getenv('RENDER_BACKEND_URL', 'https://friday-lwx5.onrender.com')
AGENT_SECRET        = os.getenv('AGENT_SECRET', 'friday-secret-2024')

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.join(BASE_DIR, 'friday-agent')

agent_process  = None
tunnel_process = None


# ─────────────────────────────────────────────
#  INTERNET CHECK
# ─────────────────────────────────────────────

def wait_for_internet(max_wait=120):
    """Block until internet is available, up to max_wait seconds."""
    print("Checking internet connection...")
    start = time.time()
    while time.time() - start < max_wait:
        try:
            requests.get('https://google.com', timeout=5)
            print("✓ Internet connected!")
            return True
        except:
            remaining = int(max_wait - (time.time() - start))
            print(f"  No internet yet. Retrying... ({remaining}s remaining)")
            time.sleep(8)
    print("✗ No internet after waiting. FRIDAY may not work properly.")
    return False


# ─────────────────────────────────────────────
#  AGENT STARTUP
# ─────────────────────────────────────────────

def start_agent():
    global agent_process
    print("\nStarting FRIDAY agent...")
    agent_path = os.path.join(AGENT_DIR, 'friday_agent.py')
    agent_process = subprocess.Popen(
        ['python', agent_path],
        cwd=AGENT_DIR,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    # Wait for agent to be ready
    print("Waiting for agent to come online...")
    for i in range(20):
        time.sleep(2)
        try:
            res = requests.get('http://localhost:5001/health', timeout=3)
            if res.status_code == 200:
                print("✓ Agent is running on port 5001!")
                return True
        except:
            print(f"  Agent starting... ({(i+1)*2}s)")
    
    print("⚠ Agent may not have started correctly. Check the agent window.")
    return False


# ─────────────────────────────────────────────
#  RENDER URL UPDATE
# ─────────────────────────────────────────────

def update_render_url(url):
    print(f"\nUpdating Render env var with tunnel URL...")
    
    if not RENDER_API_KEY or not RENDER_SERVICE_ID:
        print("⚠ RENDER_API_KEY or RENDER_SERVICE_ID missing — skipping Render update")
        return

    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    try:
        res = requests.get(
            f'https://api.render.com/v1/services/{RENDER_SERVICE_ID}/env-vars',
            headers=headers, timeout=15
        )
        if res.status_code != 200:
            print(f"✗ Could not fetch Render env vars: {res.status_code}")
            return

        env_vars = res.json()
        updated_vars = []
        found = False
        for var in env_vars:
            key   = var.get('envVar', {}).get('key')   or var.get('key', '')
            value = var.get('envVar', {}).get('value') or var.get('value', '')
            if key == 'LOCAL_AGENT_URL':
                updated_vars.append({'key': 'LOCAL_AGENT_URL', 'value': url})
                found = True
            else:
                updated_vars.append({'key': key, 'value': value})
        
        if not found:
            updated_vars.append({'key': 'LOCAL_AGENT_URL', 'value': url})

        put_res = requests.put(
            f'https://api.render.com/v1/services/{RENDER_SERVICE_ID}/env-vars',
            headers=headers, json=updated_vars, timeout=15
        )
        if put_res.status_code in [200, 201]:
            print("✓ Render env var updated!")
        else:
            print(f"✗ Render update failed: {put_res.text}")

    except Exception as e:
        print(f"✗ Render update error: {e}")


# ─────────────────────────────────────────────
#  BACKEND REGISTRATION
#  THIS is what makes the frontend show "Agent online"
# ─────────────────────────────────────────────

def register_with_backend(tunnel_url, retries=5):
    """Tell the Render backend about the new tunnel URL."""
    print(f"\nRegistering agent with backend: {BACKEND_URL}")
    
    for attempt in range(1, retries + 1):
        try:
            res = requests.post(
                f"{BACKEND_URL}/api/agent/register",
                json={"url": tunnel_url, "secret": AGENT_SECRET},
                timeout=10
            )
            if res.status_code == 200:
                print(f"✓ Agent registered with backend! (attempt {attempt})")
                return True
            else:
                print(f"  Backend returned {res.status_code}, retrying...")
        except requests.exceptions.ConnectionError:
            print(f"  Backend unreachable (attempt {attempt}/{retries}), retrying in 10s...")
        except Exception as e:
            print(f"  Registration error: {e}")
        
        time.sleep(10)
    
    print("✗ Could not register with backend after all attempts.")
    return False


# ─────────────────────────────────────────────
#  TUNNEL
# ─────────────────────────────────────────────

def start_tunnel():
    global tunnel_process
    print("\nStarting Cloudflare tunnel...")
    
    while True:
        tunnel_process = subprocess.Popen(
            ['cloudflared', 'tunnel', '--url', 'http://localhost:5001'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        url_found = False
        try:
            for line in tunnel_process.stdout:
                print(line.strip())
                if not url_found:
                    match = re.search(r'https://[a-z0-9\-]+\.trycloudflare\.com', line)
                    if match:
                        tunnel_url = match.group(0)
                        url_found = True
                        print(f"\n{'='*50}")
                        print(f"  ✨ TUNNEL ONLINE: {tunnel_url}")
                        print(f"{'='*50}\n")
                        
                        # Run registrations in background so tunnel keeps reading
                        def register_all(url=tunnel_url):
                            # Tell the local agent its own URL
                            try:
                                requests.post('http://localhost:5001/api/set-url', json={'url': url}, timeout=5)
                            except: pass
                            
                            update_render_url(url)
                            register_with_backend(url)
                            print("\n✅ FRIDAY is fully online!")
                            print(f"   Open: friday-git-main-parthjumbadkar7-5293s-projects.vercel.app\n")
                        
                        threading.Thread(target=register_all, daemon=True).start()
            
            print("\nTunnel disconnected. Restarting in 5s...")
        except Exception as e:
            print(f"Tunnel error: {e}")
        
        if tunnel_process:
            tunnel_process.terminate()
        
        time.sleep(5)
        
        # Re-check internet before restarting
        if not wait_for_internet(max_wait=60):
            print("Still no internet. Will keep trying...")


# ─────────────────────────────────────────────
#  SHUTDOWN
# ─────────────────────────────────────────────

def shutdown(sig=None, frame=None):
    print("\nShutting down FRIDAY...")
    if agent_process:
        agent_process.terminate()
    if tunnel_process:
        tunnel_process.terminate()
    print("FRIDAY stopped. Goodbye!")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 50)
    print("  FRIDAY — Starting Up")
    print("=" * 50)
    print(f"  Render API Key:  {'✓' if RENDER_API_KEY else '✗ MISSING'}")
    print(f"  Render Svc ID:   {'✓' if RENDER_SERVICE_ID else '✗ MISSING'}")
    print(f"  Backend URL:     {BACKEND_URL}")
    print("=" * 50)

    # Step 1: Wait for internet (handles slow boot)
    wait_for_internet(max_wait=120)

    # Step 2: Start the agent
    start_agent()

    # Step 3: Start the tunnel (loops forever, re-registers on reconnect)
    tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
    tunnel_thread.start()

    print("\nFRIDAY is starting... Wait for the ✅ message above.\n")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()