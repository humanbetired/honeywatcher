let attackData    = [];
let attackFilter  = 'ALL';
let chartService, chartTrend, chartIPs;

// ── Sections ─────────────────────────────────────────────────────────────────

function showSection(name, el) {
  ['overview','attacks','profiles','credentials','map'].forEach(s => {
    document.getElementById('section-' + s).style.display = s === name ? '' : 'none';
  });
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  if (el) el.classList.add('active');

  if (name === 'attacks')     loadAttacks();
  if (name === 'profiles')    loadProfiles();
  if (name === 'credentials') loadCredentials();
  if (name === 'map')         loadMap();
}

// ── Stats & Charts ───────────────────────────────────────────────────────────

async function loadDashboard() {
  const stats = await fetch('/api/stats').then(r => r.json());
  document.getElementById('m-total').textContent    = stats.total;
  document.getElementById('m-ips').textContent      = stats.unique_ips;
  document.getElementById('m-ssh').textContent      = stats.ssh;
  document.getElementById('m-http').textContent     = stats.http;
  document.getElementById('m-ftp').textContent      = stats.ftp;
  document.getElementById('m-profiled').textContent = stats.profiled;

  const clr = {
    critical: '#e8453c', high: '#f59e0b', medium: '#3b82f6',
    low: '#10b981', accent: '#6366f1', muted: '#6b7280', text: '#e2e6ef'
  };
  const chartBase = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } };

  if (chartService) { chartService.destroy(); chartService = null; }
  if (chartTrend)   { chartTrend.destroy();   chartTrend   = null; }
  if (chartIPs)     { chartIPs.destroy();     chartIPs     = null; }

  // Service donut
  const svcData = await fetch('/api/service-distribution').then(r => r.json());
  const svcColors = { SSH: clr.critical, HTTP: clr.high, FTP: clr.medium };
  chartService = new Chart(document.getElementById('chart-service'), {
    type: 'doughnut',
    data: {
      labels: svcData.map(d => d.service),
      datasets: [{ data: svcData.map(d => d.count),
        backgroundColor: svcData.map(d => svcColors[d.service] || clr.accent),
        borderWidth: 0, hoverOffset: 6 }]
    },
    options: { ...chartBase, cutout: '68%',
      plugins: { legend: { display: true, position: 'right',
        labels: { color: clr.muted, font: { size: 12 }, boxWidth: 12, padding: 12 } } } }
  });

  // Trend line
  const trend = await fetch('/api/trend').then(r => r.json());
  chartTrend = new Chart(document.getElementById('chart-trend'), {
    type: 'line',
    data: {
      labels: trend.map(d => d.hour),
      datasets: [{ data: trend.map(d => d.count),
        borderColor: clr.accent, backgroundColor: 'rgba(99,102,241,0.08)',
        pointBackgroundColor: clr.accent, pointRadius: 3,
        tension: 0.4, fill: true, borderWidth: 2 }]
    },
    options: { ...chartBase, scales: {
      x: { ticks: { color: clr.muted, font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
      y: { ticks: { color: clr.muted, font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.04)' } }
    }}
  });

  // Top IPs bar
  const ips = await fetch('/api/top-ips').then(r => r.json());
  chartIPs = new Chart(document.getElementById('chart-ips'), {
    type: 'bar',
    data: {
      labels: ips.map(d => d.src_ip),
      datasets: [{ data: ips.map(d => d.attempts),
        backgroundColor: 'rgba(232,69,60,0.75)', borderRadius: 4, borderSkipped: false }]
    },
    options: { ...chartBase, indexAxis: 'y', scales: {
      x: { ticks: { color: clr.muted, font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
      y: { ticks: { color: clr.text, font: { size: 11 } }, grid: { display: false } }
    }}
  });
}

// ── Attack Log ────────────────────────────────────────────────────────────────

async function loadAttacks() {
  const res  = await fetch('/api/attacks');
  attackData = await res.json();
  renderAttacks();
}

function setAttackFilter(filter, btn) {
  attackFilter = filter;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderAttacks();
}

function renderAttacks() {
  const q = document.getElementById('attack-search').value.toLowerCase();
  const filtered = attackData.filter(r => {
    const matchFilter = attackFilter === 'ALL' || r.service === attackFilter;
    const matchSearch = !q || [r.src_ip, r.username, r.password, r.path, r.country]
      .some(v => v && v.toLowerCase().includes(q));
    return matchFilter && matchSearch;
  });

  document.getElementById('attack-footer').textContent =
    `Showing ${filtered.length} of ${attackData.length} attacks`;

  const tbody = document.getElementById('attack-tbody');
  if (!filtered.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="loading-row">No results found</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.map(r => {
    const detail = r.service === 'HTTP'
      ? `<span class="mono">${r.method || ''} ${r.path || ''}</span>`
      : `<span class="mono">${r.password || '--'}</span>`;

    return `<tr>
      <td class="mono" style="font-size:11px;white-space:nowrap">${r.timestamp}</td>
      <td><span class="service-badge service-${r.service}">${r.service}</span></td>
      <td class="mono">${r.src_ip}</td>
      <td style="font-size:12px;color:var(--muted)">${r.country || '--'}, ${r.city || ''}</td>
      <td class="mono">${r.username || '--'}</td>
      <td class="truncate">${detail}</td>
    </tr>`;
  }).join('');
}

// ── Attacker Profiles ─────────────────────────────────────────────────────────

async function loadProfiles() {
  const grid  = document.getElementById('profiles-grid');
  grid.innerHTML = '<div class="loading-row">Loading...</div>';

  const data = await fetch('/api/profiles').then(r => r.json());

  if (!data.length) {
    grid.innerHTML = '<div class="loading-row">No profiles yet. Run AI Profiler first.</div>';
    return;
  }

  grid.innerHTML = data.map(p => {
    const summary  = p.ai_summary || '';
    const parts    = summary.split(' | ');
    const behavior = parts[0] || '';
    const threat   = parts[1]?.replace('Threat: ', '') || 'Unknown';
    const rec      = parts[2] || '';

    return `
      <div class="profile-card">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
          <span class="profile-ip">${p.src_ip}</span>
          <span class="service-badge threat-${threat}">${threat} Threat</span>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <span class="profile-type">${p.profile_type || 'Unknown'}</span>
          <span class="profile-type" style="background:rgba(16,185,129,0.1);color:var(--low)">
            ${p.confidence} Confidence
          </span>
        </div>
        <div class="profile-summary">${behavior}</div>
        <div class="profile-summary" style="color:var(--high)">→ ${rec}</div>
        <div class="profile-meta">
          <span>First seen: ${p.first_seen || '--'}</span>
          <span>Last seen: ${p.last_seen || '--'}</span>
          <span>Attempts: ${p.total_attempts}</span>
          <span>Services: ${p.services_hit || '--'}</span>
        </div>
      </div>`;
  }).join('');
}

// ── Credentials ───────────────────────────────────────────────────────────────

async function loadCredentials() {
  const [usernames, passwords] = await Promise.all([
    fetch('/api/top-usernames').then(r => r.json()),
    fetch('/api/top-passwords').then(r => r.json()),
  ]);

  document.getElementById('username-tbody').innerHTML = usernames.map(r => `
    <tr>
      <td class="mono">${r.username}</td>
      <td class="mono" style="color:var(--critical)">${r.count}</td>
    </tr>`).join('');

  document.getElementById('password-tbody').innerHTML = passwords.map(r => `
    <tr>
      <td class="mono">${r.password}</td>
      <td class="mono" style="color:var(--critical)">${r.count}</td>
    </tr>`).join('');
}

// ── AI Profiler ───────────────────────────────────────────────────────────────

async function profileNow() {
  const res  = await fetch('/api/profile-now', { method: 'POST' });
  const data = await res.json();
  if (data.error) {
    alert('Error: ' + data.error);
    return;
  }
  alert('AI Profiler started! Refresh profiles in a few seconds.');
}

// ── Auto refresh ──────────────────────────────────────────────────────────────

function startAutoRefresh() {
  setInterval(() => {
    loadDashboard();
  }, 30000); // refresh setiap 30 detik
}

// ── Init ──────────────────────────────────────────────────────────────────────

window.onload = () => {
  document.getElementById('footer-date').textContent = new Date().toISOString().slice(0,10);
  loadDashboard();
  startAutoRefresh();
};

// ── World Map ─────────────────────────────────────────────────────────────────

let map         = null;
let mapLoaded   = false;

async function loadMap() {
  const data = await fetch('/api/attackers-geo').then(r => r.json());

  // Init map sekali saja
  if (!map) {
    map = L.map('map', {
      center: [20, 0],
      zoom: 2,
      zoomControl: true,
      scrollWheelZoom: true,
    });

    // Dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '© OpenStreetMap © CARTO',
      subdomains: 'abcd',
      maxZoom: 19
    }).addTo(map);
  } else {
    // Clear existing markers
    map.eachLayer(layer => {
      if (layer instanceof L.CircleMarker) map.removeLayer(layer);
    });
  }

  if (!data.length) {
    document.getElementById('m-countries').textContent  = '0';
    document.getElementById('m-top-country').textContent = '--';
    document.getElementById('m-mapped').textContent     = '0';
    return;
  }

  // Fetch koordinat per IP dari GeoIP cache
  const geoRes  = await fetch('/api/attackers-geo-coords').then(r => r.json());
  const coordMap = {};
  geoRes.forEach(g => { coordMap[g.src_ip] = g; });

  let mapped   = 0;
  let countries = new Set();
  let topCountry = '';
  let topCount   = 0;

  data.forEach(attacker => {
    const geo = coordMap[attacker.src_ip];
    if (!geo || !geo.lat || !geo.lon) return;

    countries.add(attacker.country);
    if (attacker.attempts > topCount) {
      topCount   = attacker.attempts;
      topCountry = attacker.country;
    }

    const radius = Math.min(6 + attacker.attempts * 0.5, 20);

    const circle = L.circleMarker([geo.lat, geo.lon], {
      radius:      radius,
      fillColor:   '#e8453c',
      color:       '#ff6b6b',
      weight:      1,
      opacity:     0.9,
      fillOpacity: 0.7,
    }).addTo(map);

    circle.bindPopup(`
      <div class="attack-popup">
        <strong>${attacker.src_ip}</strong><br>
        ${attacker.country}, ${attacker.city || ''}<br>
        Attempts: ${attacker.attempts}<br>
        Services: ${attacker.services}<br>
        Last seen: ${attacker.last_seen}
      </div>
    `);

    mapped++;
  });

  document.getElementById('m-countries').textContent   = countries.size;
  document.getElementById('m-top-country').textContent = topCountry || '--';
  document.getElementById('m-mapped').textContent      = mapped;
}