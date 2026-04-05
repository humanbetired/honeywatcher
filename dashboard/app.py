import sys
import os
import threading
from datetime import datetime
import pytz
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
from functools import wraps
from flask import request, Response

load_dotenv()

DASH_USER = os.getenv("DASHBOARD_USERNAME", "admin")
DASH_PASS = os.getenv("DASHBOARD_PASSWORD", "honeywatcher")

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != DASH_USER or auth.password != DASH_PASS:
            return Response(
                "Authentication required.",
                401,
                {"WWW-Authenticate": 'Basic realm="HoneyWatch Dashboard"'}
            )
        return f(*args, **kwargs)
    return decorated
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database import get_connection, init_db

jakarta_tz = pytz.timezone("Asia/Jakarta")

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
    template_folder=os.path.join(DASHBOARD_DIR, "templates"),
    static_folder=os.path.join(DASHBOARD_DIR, "static")
)


def query(sql, params=()):
    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def scalar(sql, params=()):
    conn = get_connection()
    r = conn.execute(sql, params).fetchone()
    conn.close()
    return r[0] if r else 0


# ── API: Stats ───────────────────────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    return jsonify({
        "total":        scalar("SELECT COUNT(*) FROM attack_log"),
        "unique_ips":   scalar("SELECT COUNT(DISTINCT src_ip) FROM attack_log"),
        "ssh":          scalar("SELECT COUNT(*) FROM attack_log WHERE service='SSH'"),
        "http":         scalar("SELECT COUNT(*) FROM attack_log WHERE service='HTTP'"),
        "ftp":          scalar("SELECT COUNT(*) FROM attack_log WHERE service='FTP'"),
        "profiled":     scalar("SELECT COUNT(*) FROM attacker_profile"),
        "last_attack":  scalar("SELECT timestamp FROM attack_log ORDER BY timestamp DESC LIMIT 1"),
    })

@app.route("/api/attacks")
def api_attacks():
    return jsonify(query("""
        SELECT timestamp, service, src_ip, country, city,
               username, password, method, path, user_agent
        FROM attack_log
        ORDER BY timestamp DESC
        LIMIT 100
    """))

@app.route("/api/profiles")
def api_profiles():
    return jsonify(query("""
        SELECT src_ip, first_seen, last_seen, total_attempts,
               services_hit, profile_type, confidence, ai_summary, updated_at
        FROM attacker_profile
        ORDER BY total_attempts DESC
    """))

@app.route("/api/top-ips")
def api_top_ips():
    return jsonify(query("""
        SELECT src_ip, country, COUNT(*) as attempts
        FROM attack_log
        GROUP BY src_ip
        ORDER BY attempts DESC
        LIMIT 10
    """))

@app.route("/api/attackers-geo")
def api_attackers_geo():
    return jsonify(query("""
        SELECT src_ip, country, city,
               COUNT(*) as attempts,
               GROUP_CONCAT(DISTINCT service) as services,
               MAX(timestamp) as last_seen
        FROM attack_log
        WHERE country != 'Local' AND country != 'Unknown'
        GROUP BY src_ip
        ORDER BY attempts DESC
    """))

@app.route("/api/attackers-geo-coords")
def api_attackers_geo_coords():
    return jsonify(query("""
        SELECT src_ip, AVG(lat) as lat, AVG(lon) as lon
        FROM attack_log
        WHERE lat IS NOT NULL AND lon IS NOT NULL
        GROUP BY src_ip
    """))

@app.route("/api/service-distribution")
def api_service_dist():
    return jsonify(query("""
        SELECT service, COUNT(*) as count
        FROM attack_log
        GROUP BY service
    """))

@app.route("/api/trend")
def api_trend():
    rows = query("""
        SELECT substr(timestamp,1,13) as hour, COUNT(*) as count
        FROM attack_log
        GROUP BY hour
        ORDER BY hour DESC
        LIMIT 24
    """)
    rows.reverse()
    return jsonify(rows)

@app.route("/api/profile-now", methods=["POST"])
def api_profile_now():
    try:
        from analyzer.ai_profiler import profile_all
        t = threading.Thread(target=profile_all, daemon=True)
        t.start()
        return jsonify({"message": "Profiling started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/top-passwords")
def api_top_passwords():
    return jsonify(query("""
        SELECT password, COUNT(*) as count
        FROM attack_log
        WHERE password IS NOT NULL AND password != ''
        GROUP BY password
        ORDER BY count DESC
        LIMIT 10
    """))

@app.route("/api/top-usernames")
def api_top_usernames():
    return jsonify(query("""
        SELECT username, COUNT(*) as count
        FROM attack_log
        WHERE username IS NOT NULL AND username != ''
        GROUP BY username
        ORDER BY count DESC
        LIMIT 10
    """))


# ── Main ─────────────────────────────────────────────────────────────────────

@app.route("/")
@require_auth
def index():
    return render_template("index.html")


if __name__ == "__main__":
    init_db()
    print("[HoneyWatch] Dashboard running at http://127.0.0.1:5001")
    app.run(debug=False, port=5001)