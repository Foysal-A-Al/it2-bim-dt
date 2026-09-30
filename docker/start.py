"""Start the models, checker and optional demo tunnel in one container."""
import os
import signal
import subprocess
import sys
import time
import urllib.request

children = []

def stop(signum, frame):
    raise SystemExit(0)

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
try:
    subprocess.run([sys.executable, 'data/download.py'], check=True)
    app = subprocess.Popen(sys.argv[1:])
    children.append(app)
    for attempt in range(90):
        if app.poll() is not None:
            raise RuntimeError('Streamlit exited during startup')
        try:
            urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=2).close()
            break
        except OSError:
            time.sleep(1)
    else:
        raise RuntimeError('Streamlit did not become healthy')
    print('IT2 READY — open http://127.0.0.1:8501 on the Docker host', flush=True)
    if os.environ.get('IT2_SHARE') == '1':
        tunnel = subprocess.Popen(['cloudflared', 'tunnel', '--no-autoupdate', '--url', 'http://127.0.0.1:8501'])
        children.append(tunnel)
        print('Public HTTPS demo URL will appear below in these Docker logs.', flush=True)
    while all(p.poll() is None for p in children):
        time.sleep(1)
    raise RuntimeError('A container service stopped; Docker will restart the container')
finally:
    for p in children:
        if p.poll() is None:
            p.terminate()
    for p in children:
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()
