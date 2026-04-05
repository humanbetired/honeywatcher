import os
import sys
import anthropic
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database import get_connection

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


def get_attack_data(ip):
    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row

    attempts = conn.execute("""
        SELECT service, username, password, path, method,
               user_agent, payload, timestamp
        FROM attack_log
        WHERE src_ip = ?
        ORDER BY timestamp DESC
        LIMIT 50
    """, (ip,)).fetchall()

    stats = conn.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT service) as services,
            MIN(timestamp) as first_seen,
            MAX(timestamp) as last_seen,
            GROUP_CONCAT(DISTINCT service) as services_hit
        FROM attack_log
        WHERE src_ip = ?
    """, (ip,)).fetchone()

    conn.close()
    return [dict(a) for a in attempts], dict(stats)


def profile(ip):
    print(f"[AI Profiler] Analyzing {ip}...")
    attempts, stats = get_attack_data(ip)

    if not attempts:
        print(f"[AI Profiler] No data for {ip}")
        return

    # Format data untuk prompt
    attempt_summary = "\n".join([
        f"- [{a['service']}] {a['timestamp']} | "
        f"user:{a['username'] or '-'} pass:{a['password'] or '-'} "
        f"path:{a['path'] or '-'} method:{a['method'] or '-'}"
        for a in attempts[:20]
    ])

    prompt = f"""
You are a cybersecurity threat intelligence analyst.
Analyze the following honeypot attack data and profile the attacker.

ATTACKER IP: {ip}
FIRST SEEN: {stats['first_seen']}
LAST SEEN: {stats['last_seen']}
TOTAL ATTEMPTS: {stats['total']}
SERVICES TARGETED: {stats['services_hit']}

ATTACK LOG (latest 20):
{attempt_summary}

Based on this data, provide:
1. ATTACKER TYPE: (one of: Automated Scanner, Script Kiddie, Credential Stuffing Bot, Targeted Attacker, Unknown)
2. CONFIDENCE: (High / Medium / Low)
3. BEHAVIOR SUMMARY: (2-3 sentences describing the attack pattern)
4. THREAT LEVEL: (Critical / High / Medium / Low)
5. RECOMMENDATION: (1-2 sentences on what to do)

Respond in this exact JSON format:
{{
    "attacker_type": "...",
    "confidence": "...",
    "behavior_summary": "...",
    "threat_level": "...",
    "recommendation": "..."
}}
"""

    client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    raw  = message.content[0].text
    # Clean JSON
    raw  = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    data = json.loads(raw)

    # Simpan ke database
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO attacker_profile
        (src_ip, first_seen, last_seen, total_attempts, services_hit,
         profile_type, confidence, ai_summary, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ip,
        stats["first_seen"],
        stats["last_seen"],
        stats["total"],
        stats["services_hit"],
        data["attacker_type"],
        data["confidence"],
        f"{data['behavior_summary']} | Threat: {data['threat_level']} | {data['recommendation']}",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

    print(f"[AI Profiler] {ip} → {data['attacker_type']} ({data['confidence']} confidence)")
    print(f"[AI Profiler] Threat Level: {data['threat_level']}")
    print(f"[AI Profiler] {data['behavior_summary']}")
    return data


def profile_all():
    """Profile semua IP yang ada di attack_log"""
    conn = get_connection()
    ips  = conn.execute(
        "SELECT DISTINCT src_ip FROM attack_log"
    ).fetchall()
    conn.close()

    print(f"[AI Profiler] Found {len(ips)} unique IPs to profile")
    for row in ips:
        profile(row[0])


if __name__ == "__main__":
    profile_all()