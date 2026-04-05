import requests

def lookup(ip):
    # Skip private/loopback IP
    if ip.startswith(("127.", "192.168.", "10.", "172.")):
        return {
            "country": "Local",
            "city":    "Localhost",
            "isp":     "Private Network",
            "lat":     0,
            "lon":     0,
        }
    try:
        res  = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = res.json()
        if data.get("status") == "success":
            return {
                "country": data.get("country", "Unknown"),
                "city":    data.get("city", "Unknown"),
                "isp":     data.get("isp", "Unknown"),
                "lat":     data.get("lat", 0),
                "lon":     data.get("lon", 0),
            }
    except Exception:
        pass
    return {
        "country": "Unknown",
        "city":    "Unknown",
        "isp":     "Unknown",
        "lat":     0,
        "lon":     0,
    }