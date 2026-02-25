import subprocess
import time
import socket
import os

def check_port(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('127.0.0.1', port))
        s.close()
        return True
    except:
        return False

log_file = "boot_diag.log"
with open(log_file, "w") as log:
    log.write(f"Bootstrapper started at {time.ctime()}\n")
    try:
        python_exe = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
        if not os.path.exists(python_exe):
            python_exe = "python" # fallback
        
        log.write(f"Starting server with: {python_exe} app.py\n")
        # Run in a way that doesn't wait
        proc = subprocess.Popen([python_exe, "app.py"], stdout=log, stderr=log)
        log.write(f"Process started. PID: {proc.pid}\n")
        
        for i in range(15):
            time.sleep(1)
            is_up = check_port(5000)
            log.write(f"[{i}s] Port 5000 up: {is_up}\n")
            if is_up:
                log.write("Server is confirmed UP!\n")
                break
            # Check if process died
            if proc.poll() is not None:
                log.write(f"Process died with exit code: {proc.poll()}\n")
                break
        else:
            log.write("Server timed out waiting for port 5000\n")
            
    except Exception as e:
        log.write(f"Startup Exception: {e}\n")
