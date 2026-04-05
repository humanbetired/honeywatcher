## README.md untuk HoneyWatch

```markdown
# HoneyWatch

Multi-service honeypot intelligence system with AI-powered attacker profiling and real-time dashboard.

---

## Overview

HoneyWatch is a blue team portfolio project designed to simulate vulnerable services, capture attacker behavior, and generate actionable intelligence using AI analysis. It is not a production security tool — it is built to demonstrate threat detection concepts and attacker profiling workflows.

---

## Features

- **Multi-service honeypot** — Simulates SSH, HTTP, and FTP services simultaneously
- **GeoIP enrichment** — Resolves attacker IP to country, city, and coordinates
- **AI attacker profiling** — Uses Claude API to classify attacker type, behavior pattern, and threat level
- **Real-time dashboard** — Flask-based web UI with attack log, charts, and attacker profiles
- **World map visualization** — Plots attacker origin on an interactive map using Leaflet.js
- **Credential tracking** — Aggregates most-attempted usernames and passwords
- **Dashboard authentication** — Basic auth protection for the web interface
- **Ngrok-ready** — Supports X-Forwarded-For header to capture real IPs behind tunnels

---

## Architecture

```
Attacker
   │
   ├── SSH (port 2222)   → ssh_honeypot.py
   ├── HTTP (port 8080)  → http_honeypot.py
   └── FTP (port 2121)   → ftp_honeypot.py
          │
          ▼
     SQLite Database
          │
          ├── GeoIP Lookup (ip-api.com)
          ├── AI Profiler (Claude API)
          └── Dashboard (Flask :5001)
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Honeypot services | socket, paramiko |
| Dashboard | Flask |
| Database | SQLite |
| AI Analysis | Anthropic Claude API |
| GeoIP | ip-api.com (free tier) |
| Map | Leaflet.js |
| Charts | Chart.js |
| Tunneling | Ngrok |

---

## Project Structure

```
honeywatcher/
├── main.py                  # Entry point — launches all services
├── database.py              # DB init and connection helper
├── requirements.txt
├── .env.example
├── services/
│   ├── ssh_honeypot.py      # Fake SSH server
│   ├── http_honeypot.py     # Fake HTTP server
│   └── ftp_honeypot.py      # Fake FTP server
├── analyzer/
│   ├── geoip.py             # IP geolocation lookup
│   └── ai_profiler.py       # Claude API attacker profiling
└── dashboard/
    ├── app.py               # Flask routes and API
    ├── templates/
    │   └── index.html
    └── static/
        ├── style.css
        └── app.js
```

---

## Installation

```bash
git clone https://github.com/yourusername/honeywatcher.git
cd honeywatcher
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

---

## Configuration

```env
ANTHROPIC_API_KEY=your_claude_api_key
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=your_secure_password
```

---

## Usage

```bash
# Run all services + dashboard
python main.py

# Run AI profiler manually
python analyzer/ai_profiler.py
```

Dashboard available at: `http://localhost:5001`

| Service | Port |
|---|---|
| Dashboard | 5001 |
| SSH Honeypot | 2222 |
| HTTP Honeypot | 8080 |
| FTP Honeypot | 2121 |

---

## Security Concepts Demonstrated

- Deception-based defense (honeypot deployment)
- Attacker behavior analysis and classification
- Threat intelligence enrichment (GeoIP, AI profiling)
- Credential harvesting detection
- Intelligence dissemination via dashboard

---

## Disclaimer

This project is intended for educational and portfolio purposes only. Deploy only on networks and systems you own or have explicit permission to monitor. The author is not responsible for any misuse.

---

## Author

Dibuat oleh Saya
```

---