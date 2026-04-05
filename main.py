import threading
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database import init_db

def start_ssh():
    from services.ssh_honeypot import start
    start()

def start_http():
    from services.http_honeypot import start
    start()

def start_ftp():
    from services.ftp_honeypot import start
    start()

def start_dashboard():
    from dashboard.app import app
    from database import init_db
    init_db()
    app.run(debug=False, port=5001, use_reloader=False)

if __name__ == "__main__":
    print("""
    ██╗  ██╗ ██████╗ ███╗   ██╗███████╗██╗   ██╗
    ██║  ██║██╔═══██╗████╗  ██║██╔════╝╚██╗ ██╔╝
    ███████║██║   ██║██╔██╗ ██║█████╗   ╚████╔╝ 
    ██╔══██║██║   ██║██║╚██╗██║██╔══╝    ╚██╔╝  
    ██║  ██║╚██████╔╝██║ ╚████║███████╗   ██║   
    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝   ╚═╝   
    HoneyWatch — Multi-Service Honeypot
    """)

    init_db()

    services = [
        ("SSH Honeypot",  start_ssh),
        ("HTTP Honeypot", start_http),
        ("FTP Honeypot",  start_ftp),
        ("Dashboard",     start_dashboard),
    ]

    threads = []
    for name, target in services:
        t = threading.Thread(target=target, name=name, daemon=True)
        t.start()
        threads.append(t)
        print(f"[+] {name} started")

    print("\n[HoneyWatch] All services running. Press Ctrl+C to stop.\n")

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[HoneyWatch] Shutting down...")
        sys.exit(0)