import socket
import threading
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database import get_connection

HOST = "0.0.0.0"
PORT = 2121  # pakai 2121 bukan 21 karena butuh admin privileges


def handle_client(client_socket, client_ip, client_port):
    username = ""
    try:
        # Kirim banner FTP palsu
        client_socket.send(b"220 Microsoft FTP Service\r\n")

        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            command = data.decode("utf-8", errors="ignore").strip()

            if command.upper().startswith("USER"):
                username = command[5:].strip()
                client_socket.send(b"331 Password required\r\n")

            elif command.upper().startswith("PASS"):
                password  = command[5:].strip()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                from analyzer.geoip import lookup
                geo = lookup(client_ip)

                print(f"[FTP] {timestamp} | {client_ip} ({geo['country']}) | {username}:{password}")

                conn = get_connection()
                conn.execute("""
                INSERT INTO attack_log
                (timestamp, service, src_ip, src_port, country, city, lat, lon, username, password)
                VALUES (?, 'FTP', ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, client_ip, client_port,
                geo["country"], geo["city"], geo["lat"], geo["lon"],
                username, password))
                conn.commit()
                conn.close()

                # Selalu tolak login
                client_socket.send(b"530 Login incorrect\r\n")
                username = ""

            elif command.upper().startswith("QUIT"):
                client_socket.send(b"221 Goodbye\r\n")
                break

            else:
                client_socket.send(b"530 Please login with USER and PASS\r\n")

    except Exception as e:
        print(f"[FTP] Error: {e}")
    finally:
        client_socket.close()


def start():
    print(f"[FTP] Honeypot listening on port {PORT}...")
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
            print(f"[FTP] Error: {e}")


if __name__ == "__main__":
    from database import init_db
    init_db()
    start()