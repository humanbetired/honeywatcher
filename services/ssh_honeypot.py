import socket
import threading
import paramiko
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database import get_connection

HOST = "0.0.0.0"
PORT = 2222 

HOST_KEY = paramiko.RSAKey.generate(2048)


class FakeSSHServer(paramiko.ServerInterface):
    def __init__(self, client_ip, client_port):
        self.client_ip   = client_ip
        self.client_port = client_port
        self.event       = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        self._log_attempt(username, password)
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "password"

    def _log_attempt(self, username, password):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        from analyzer.geoip import lookup
        geo = lookup(self.client_ip)
        
        print(f"[SSH] {timestamp} | {self.client_ip} ({geo['country']}) | {username}:{password}")

        conn = get_connection()
        conn.execute("""
        INSERT INTO attack_log
        (timestamp, service, src_ip, src_port, country, city, lat, lon, username, password)
        VALUES (?, 'SSH', ?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, self.client_ip, self.client_port,
        geo["country"], geo["city"], geo["lat"], geo["lon"],
        username, password))
        conn.commit()
        conn.close()


def handle_client(client_socket, client_ip, client_port):
    transport = None
    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(HOST_KEY)
        transport.local_version = "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3"

        server = FakeSSHServer(client_ip, client_port)
        
        try:
            transport.start_server(server=server)
        except paramiko.SSHException:
            return

        chan = transport.accept(30)
        if chan:
            chan.close()

    except (ConnectionResetError, OSError):
        pass
    except Exception:
        pass
    finally:
        try:
            if transport:
                transport.close()
        except Exception:
            pass
        try:
            client_socket.close()
        except Exception:
            pass


def start():
    print(f"[SSH] Honeypot listening on port {PORT}...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(100)

    while True:
        try:
            client, addr = server_socket.accept()
            client_ip, client_port = addr
            print(f"[SSH] Connection from {client_ip}:{client_port}")
            t = threading.Thread(
                target=handle_client,
                args=(client, client_ip, client_port),
                daemon=True
            )
            t.start()
        except Exception as e:
            print(f"[SSH] Error: {e}")


if __name__ == "__main__":
    from database import init_db
    init_db()
    start()