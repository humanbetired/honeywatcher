import socket
import threading
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database import get_connection

HOST = "0.0.0.0"
PORT = 8080

FAKE_RESPONSE = b"""HTTP/1.1 200 OK\r\nServer: Apache/2.4.41 (Ubuntu)\r\nContent-Type: text/html\r\nX-Powered-By: PHP/7.4.3\r\nX-Frame-Options: SAMEORIGIN\r\n\r\n<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Company Internal Portal &mdash; Login</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f0f2f5; min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
  }
  .container {
    background: white; border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.1);
    padding: 40px; width: 100%; max-width: 400px;
  }
  .logo {
    text-align: center; margin-bottom: 28px;
  }
  .logo-icon {
    width: 56px; height: 56px; background: #1a56db;
    border-radius: 12px; display: inline-flex;
    align-items: center; justify-content: center;
    margin-bottom: 12px;
  }
  .logo-icon svg { width: 32px; height: 32px; fill: white; }
  .logo h1 { font-size: 20px; font-weight: 700; color: #111; }
  .logo p { font-size: 13px; color: #6b7280; margin-top: 4px; }
  .form-group { margin-bottom: 16px; }
  label { display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px; }
  input {
    width: 100%; padding: 10px 14px; border: 1px solid #d1d5db;
    border-radius: 6px; font-size: 14px; color: #111;
    outline: none; transition: border 0.2s;
  }
  input:focus { border-color: #1a56db; box-shadow: 0 0 0 3px rgba(26,86,219,0.1); }
  .btn {
    width: 100%; padding: 11px; background: #1a56db;
    color: white; border: none; border-radius: 6px;
    font-size: 14px; font-weight: 600; cursor: pointer;
    margin-top: 8px; transition: background 0.2s;
  }
  .btn:hover { background: #1447b2; }
  .divider { text-align: center; margin: 20px 0; color: #9ca3af; font-size: 12px; position: relative; }
  .divider::before, .divider::after {
    content: ''; position: absolute; top: 50%;
    width: 42%; height: 1px; background: #e5e7eb;
  }
  .divider::before { left: 0; }
  .divider::after { right: 0; }
  .sso-btn {
    width: 100%; padding: 10px; border: 1px solid #d1d5db;
    border-radius: 6px; background: white; font-size: 13px;
    font-weight: 500; cursor: pointer; display: flex;
    align-items: center; justify-content: center; gap: 8px;
    color: #374151; transition: background 0.2s;
  }
  .sso-btn:hover { background: #f9fafb; }
  .footer-links { text-align: center; margin-top: 20px; font-size: 12px; color: #6b7280; }
  .footer-links a { color: #1a56db; text-decoration: none; }
  .notice {
    background: #eff6ff; border: 1px solid #bfdbfe;
    border-radius: 6px; padding: 10px 14px;
    font-size: 12px; color: #1e40af; margin-bottom: 20px;
    display: flex; align-items: flex-start; gap: 8px;
  }
</style>
</head>
<body>
<div class="container">
  <div class="logo">
    <div class="logo-icon">
      <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
    </div>
    <h1>Acme Corp</h1>
    <p>Internal Employee Portal</p>
  </div>

  <div class="notice">
    &#x26A0;&#xFE0F; For authorized personnel only. All access is monitored and logged.
  </div>

  <form method="POST" action="/auth/login">
    <div class="form-group">
      <label>Corporate Email</label>
      <input type="email" name="email" placeholder="you@acmecorp.com" autocomplete="email">
    </div>
    <div class="form-group">
      <label>Password</label>
      <input type="password" name="password" placeholder="Enter your password" autocomplete="current-password">
    </div>
    <button type="submit" class="btn">Sign In</button>
  </form>

  <div class="divider">or continue with</div>

  <button class="sso-btn">
    <svg width="16" height="16" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
    Sign in with Google SSO
  </button>

  <div class="footer-links">
    <a href="/forgot-password">Forgot password?</a> &bull;
    <a href="/help">IT Support</a> &bull;
    <a href="/privacy">Privacy Policy</a>
  </div>
</div>
</body>
</html>"""


def get_real_ip(data, fallback_ip):
    try:
        lines = data.decode("utf-8", errors="ignore").split("\r\n")
        for line in lines:
            if line.lower().startswith("x-forwarded-for:"):
                ip = line.split(":", 1)[1].strip().split(",")[0].strip()
                return ip
    except Exception:
        pass
    return fallback_ip


def parse_request(data):
    try:
        lines      = data.decode("utf-8", errors="ignore").split("\r\n")
        first_line = lines[0].split(" ")
        method     = first_line[0] if len(first_line) > 0 else ""
        path       = first_line[1] if len(first_line) > 1 else ""
        user_agent = ""
        payload    = ""

        for line in lines[1:]:
            if line.lower().startswith("user-agent:"):
                user_agent = line.split(":", 1)[1].strip()
            if not line.startswith(("GET","POST","HTTP","Host",
                                    "User","Accept","Content",
                                    "Connection","Cache")):
                if line.strip():
                    payload += line + " "

        return method, path, user_agent, payload.strip()
    except Exception:
        return "", "", "", ""


def handle_client(client_socket, client_ip, client_port):
    try:
        data = client_socket.recv(4096)
        if not data:
            return

        real_ip = get_real_ip(data, client_ip)
        method, path, user_agent, payload = parse_request(data)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        from analyzer.geoip import lookup
        geo = lookup(real_ip)

        print(f"[HTTP] {timestamp} | {real_ip} ({geo['country']}) | {method} {path} | {user_agent[:50]}")

        conn = get_connection()
        conn.execute("""
            INSERT INTO attack_log
            (timestamp, service, src_ip, src_port, country, city, lat, lon,
             method, path, user_agent, payload, raw_data)
            VALUES (?, 'HTTP', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, real_ip, client_port,
              geo["country"], geo["city"], geo["lat"], geo["lon"],
              method, path, user_agent, payload,
              data.decode("utf-8", errors="ignore")[:500]))
        conn.commit()
        conn.close()

        client_socket.send(FAKE_RESPONSE)

    except Exception as e:
        print(f"[HTTP] Error: {e}")
    finally:
        client_socket.close()


def start():
    print(f"[HTTP] Honeypot listening on port {PORT}...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(100)

    while True:
        try:
            client, addr = server_socket.accept()
            client_ip, client_port = addr
            t = threading.Thread(
                target=handle_client,
                args=(client, client_ip, client_port),
                daemon=True
            )
            t.start()
        except Exception as e:
            print(f"[HTTP] Error: {e}")


if __name__ == "__main__":
    from database import init_db
    init_db()
    start()