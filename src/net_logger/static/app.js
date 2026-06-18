let sessionId = null;
let currentSession = null;
let board = { known_stations: [], checkins: [] };

const $ = (id) => document.getElementById(id);
const statusEl = $('status');

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

function setStatus(text) { statusEl.textContent = text; }
function esc(s) { return String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function place(station) { return [station.city, station.state].filter(Boolean).join(', '); }
function stationMeta(station) {
  return [station.name || '—', place(station), station.grid].filter(Boolean).join(' • ');
}
function sessionOpen() { return sessionId && (!currentSession || currentSession.status !== 'closed'); }
function formatDateTime(value) {
  if (!value) return '';
  const iso = value.includes('T') ? value : value.replace(' ', 'T') + 'Z';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString([], { year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' });
}

function renderFccStatus(status) {
  if (!status || !status.available) return 'FCC database: unavailable';
  const age = status.age_days === 0 ? 'updated today' : `${status.age_days} day${status.age_days === 1 ? '' : 's'} old`;
  return `FCC database: ${age}`;
}

async function loadFccStatus() {
  const status = await api('/api/fcc/status');
  $('fccStatus').textContent = renderFccStatus(status);
}

async function updateFccDatabase() {
  const btn = $('updateFccBtn');
  btn.disabled = true;
  $('fccStatus').textContent = 'FCC database: updating…';
  setStatus('Downloading FCC data and rebuilding the local index. This may take a few minutes.');
  try {
    const result = await api('/api/fcc/update', { method: 'POST' });
    $('fccStatus').textContent = renderFccStatus(result.status);
    setStatus(`FCC database updated. Indexed ${result.indexed_count.toLocaleString()} active call signs.`);
  } finally {
    btn.disabled = false;
  }
}

async function startSession(evt) {
  evt.preventDefault();
  const session = await api('/api/sessions/start', {
    method: 'POST',
    body: JSON.stringify({ name: $('netName').value, frequency: $('frequency').value, net_control: $('netControl').value })
  });
  sessionId = session.id;
  currentSession = session;
  $('stopNetBtn').disabled = false;
  $('clearNetBtn').hidden = true;
  setStatus(`Session #${sessionId} open.`);
  await refreshAll();
}

async function stopSession() {
  if (!sessionId) return;
  const session = await api(`/api/sessions/${sessionId}/stop`, { method: 'POST' });
  currentSession = session;
  $('stopNetBtn').disabled = true;
  $('clearNetBtn').hidden = false;
  setStatus(`Session #${sessionId} stopped. Records were already saved; this marks the net closed.`);
  await refreshAll();
}

async function clearNet() {
  sessionId = null;
  currentSession = null;
  $('stopNetBtn').disabled = true;
  $('clearNetBtn').hidden = true;
  setStatus('Cleared the active board. The stopped net remains saved and exportable.');
  await loadBoard();
}

async function loadBoard() {
  if (!sessionId) {
    const stations = await api('/api/stations?q=' + encodeURIComponent($('stationLookup').value));
    board = { known_stations: stations, checkins: [] };
  } else {
    board = await api(`/api/sessions/${sessionId}/board`);
    currentSession = board.session;
    $('stopNetBtn').disabled = currentSession.status === 'closed';
    $('clearNetBtn').hidden = currentSession.status !== 'closed';
    const q = $('stationLookup').value.trim().toUpperCase();
    if (q) board.known_stations = board.known_stations.filter(s => s.callsign.includes(q) || (s.name || '').toUpperCase().includes(q));
  }
  renderBoard();
}

function renderBoard() {
  $('knownCount').textContent = board.known_stations.length;
  $('checkinCount').textContent = board.checkins.length;
  $('knownStations').innerHTML = board.known_stations.length ? board.known_stations.map(renderKnownCard).join('') : '<div class="empty">No matching known stations.</div>';
  $('checkins').innerHTML = board.checkins.length ? board.checkins.map(renderCheckinCard).join('') : '<div class="empty">Drag or add stations here as they check in.</div>';
  document.querySelectorAll('[data-station-id]').forEach(el => {
    el.addEventListener('dragstart', e => { e.dataTransfer.setData('application/x-station-id', el.dataset.stationId); el.classList.add('dragging'); });
    el.addEventListener('dragend', () => el.classList.remove('dragging'));
  });
  document.querySelectorAll('[data-checkin-id]').forEach(el => {
    el.addEventListener('dragstart', e => { e.dataTransfer.setData('application/x-checkin-id', el.dataset.checkinId); el.classList.add('dragging'); });
    el.addEventListener('dragend', () => el.classList.remove('dragging'));
  });
}

function renderKnownCard(s) {
  const disabled = sessionOpen() ? '' : 'disabled';
  return `<article class="card" draggable="${sessionOpen()}" data-station-id="${s.id}">
    <div class="card-head"><div><div class="call">${esc(s.callsign)}</div><div class="meta">${esc(stationMeta(s))}</div></div>${s.last_heard_at ? `<div class="last-heard"><div class="last-heard-label">Last Heard</div><div class="last-heard-time">${esc(formatDateTime(s.last_heard_at))}</div></div>` : ''}</div>
    <div class="card-actions"><button ${disabled} onclick="checkIn(${s.id})">Check in</button><button class="secondary" onclick="refreshStationFromFcc(${s.id})">Update details</button><button class="secondary danger" onclick="deleteStation(${s.id})">Delete</button></div>
  </article>`;
}

function renderCheckinCard(c) {
  const s = c.station;
  return `<article class="card checkin-card compact" draggable="true" data-checkin-id="${c.id}">
    <details>
      <summary class="compact-summary" title="Click to expand check-in details">
        <span class="compact-main"><span class="call">${esc(s.callsign)}</span><span class="meta time">${formatDateTime(c.checked_in_at)}</span></span>
        <span class="expand-hint">Details</span>
      </summary>
      <div class="expanded-details">
        <div class="meta">#${c.sequence} ${esc(stationMeta(s))}</div>
        <div class="checkin-fields">
          <label><input type="checkbox" ${c.traffic ? 'checked' : ''} onchange="updateCheckin(${c.id}, {traffic:this.checked})"> Traffic</label>
          <textarea placeholder="Traffic details" onblur="updateCheckin(${c.id}, {traffic_details:this.value})">${esc(c.traffic_details)}</textarea>
          <textarea placeholder="Notes" onblur="updateCheckin(${c.id}, {notes:this.value})">${esc(c.notes)}</textarea>
        </div>
        <div class="card-actions"><button class="secondary danger" onclick="removeCheckin(${c.id})">Move back to Known</button></div>
      </div>
    </details>
  </article>`;
}

async function checkIn(stationId) {
  if (!sessionOpen()) {
    setStatus(sessionId ? 'This net is stopped; start a new net before checking in stations.' : 'Start a net session before checking in stations.');
    return;
  }
  await api(`/api/sessions/${sessionId}/checkins`, { method: 'POST', body: JSON.stringify({ station_id: stationId }) });
  await refreshAll();
}

async function removeCheckin(id) {
  await api(`/api/checkins/${id}`, { method: 'DELETE' });
  setStatus('Check-in removed; station moved back to Known Stations.');
  await refreshAll();
}

async function updateCheckin(id, patch) {
  await api(`/api/checkins/${id}`, { method: 'PATCH', body: JSON.stringify(patch) });
  await loadBoard();
}

async function refreshStationFromFcc(id) {
  const station = await api(`/api/stations/${id}/refresh-fcc`, { method: 'POST' });
  setStatus(`Updated ${station.callsign} from FCC details.`);
  await refreshAll();
}

async function deleteStation(id) {
  if (!confirm('Delete this station and any saved check-ins for it?')) return;
  await api(`/api/stations/${id}`, { method: 'DELETE' });
  setStatus('Station deleted.');
  await refreshAll();
}

function normalizedLookupValue() {
  return $('stationLookup').value.trim().toUpperCase();
}

function findKnownStation(query) {
  const q = query.trim().toUpperCase();
  if (!q) return null;
  const candidates = [...(board.known_stations || []), ...(board.checkins || []).map(c => c.station)].filter(Boolean);
  return candidates.find(s => (s.callsign || '').toUpperCase() === q) || null;
}

function payloadFromFccResult(result, fallbackCallsign) {
  if (!result) return { callsign: fallbackCallsign };
  return {
    callsign: result.callsign || fallbackCallsign,
    name: result.name || '',
    city: result.city || '',
    state: result.state || '',
    grid: result.grid || '',
    lat: result.lat,
    lon: result.lon,
    source: 'fcc',
  };
}

async function handleStationLookup(evt) {
  evt.preventDefault();
  const query = normalizedLookupValue();
  if (!query) return;

  const known = findKnownStation(query);
  if (known) {
    setStatus(`Known station ${known.callsign} found${sessionOpen() ? '; checking in.' : '.'}`);
    $('stationLookup').value = '';
    if (sessionOpen()) await checkIn(known.id);
    else await loadBoard();
    return;
  }

  setStatus(`No known station for ${query}; searching local FCC database…`);
  const result = await api('/api/lookup?callsign=' + encodeURIComponent(query));
  const payload = result.found && result.result ? payloadFromFccResult(result.result, query) : { callsign: result.callsign || query };
  const station = await api('/api/stations', { method: 'POST', body: JSON.stringify(payload) });
  $('stationLookup').value = '';

  if (result.found && result.result) {
    const where = place(result.result) ? ` (${place(result.result)})` : '';
    setStatus(`FCC lookup found ${station.callsign}${where}; station saved${sessionOpen() ? ' and checked in.' : '.'}`);
  } else {
    setStatus(`No local FCC result for ${payload.callsign}; callsign-only station saved${sessionOpen() ? ' and checked in.' : '.'}`);
  }

  if (sessionOpen()) await checkIn(station.id);
  else await refreshAll();
}

async function loadSessions() {
  const sessions = await api('/api/sessions');
  $('sessionsList').innerHTML = sessions.length ? sessions.map(s => `
    <div class="session-row">
      <div><div class="title">${esc(s.name || 'Untitled net')} #${s.id}</div>
      <div class="details">${esc(s.status)} • ${formatDateTime(s.started_at)} • check-ins: ${s.checkin_count} • traffic: ${s.traffic_count}</div></div>
      <a class="button-link secondary" href="/api/export.csv?session_id=${s.id}">Export CSV</a>
    </div>`).join('') : '<div class="empty">No saved nets yet.</div>';
}

async function loadMetrics() {
  const period = $('metricsPeriod') ? $('metricsPeriod').value : 'month';
  const metrics = await api('/api/metrics?period=' + encodeURIComponent(period));
  renderNetSeriesCharts('metricsSeriesByNet', metrics.series_by_net || []);
}

function renderNetSeriesCharts(id, seriesByNet) {
  if (!seriesByNet.length) {
    $(id).innerHTML = '<div class="empty">No check-in data yet.</div>';
    return;
  }
  $(id).innerHTML = seriesByNet.map(series => renderColumnChart(series)).join('');
}

function renderColumnChart(series) {
  const points = series.points || [];
  const max = Math.max(...points.map(p => p.checkin_count), 1);
  const bars = points.map(point => {
    const height = Math.max(8, Math.round((point.checkin_count / max) * 140));
    return `<div class="column-bar-wrap">
      <div class="column-value">${point.checkin_count}</div>
      <div class="column-bar" style="height:${height}px" title="${esc(point.bucket)}: ${point.checkin_count}"></div>
      <div class="column-label">${esc(point.bucket)}</div>
    </div>`;
  }).join('');
  return `<section class="net-chart">
    <h4>${esc(series.net_name || 'Untitled net')}</h4>
    <div class="column-chart" role="img" aria-label="Check-ins for ${esc(series.net_name || 'Untitled net')}">${bars}</div>
  </section>`;
}

function renderChart(id, rows, labelKey) {
  if (!rows.length) {
    $(id).innerHTML = '<div class="empty">No check-in data yet.</div>';
    return;
  }
  const max = Math.max(...rows.map(r => r.checkin_count), 1);
  $(id).innerHTML = rows.map(r => {
    const pct = Math.round((r.checkin_count / max) * 100);
    return `<div class="bar-row"><div class="bar-label">${esc(r[labelKey] || 'Unknown')}</div><div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div><div class="bar-value">${r.checkin_count}</div></div>`;
  }).join('');
}

async function refreshAll() {
  await loadBoard();
  await loadSessions();
  await loadMetrics();
  await loadFccStatus();
}

$('sessionForm').addEventListener('submit', startSession);
$('stopNetBtn').addEventListener('click', stopSession);
$('clearNetBtn').addEventListener('click', clearNet);
$('stationLookupForm').addEventListener('submit', handleStationLookup);
$('updateFccBtn').addEventListener('click', () => updateFccDatabase().catch(err => setStatus(err.message)));
$('refreshMetricsBtn').addEventListener('click', () => refreshAll().catch(err => setStatus(err.message)));
$('metricsPeriod').addEventListener('change', () => loadMetrics().catch(err => setStatus(err.message)));
$('stationLookup').addEventListener('input', () => loadBoard().catch(err => setStatus(err.message)));

const checkedDrop = $('checkedInDropZone');
checkedDrop.addEventListener('dragover', e => { if (sessionOpen()) { e.preventDefault(); checkedDrop.classList.add('dragover'); } });
checkedDrop.addEventListener('dragleave', () => checkedDrop.classList.remove('dragover'));
checkedDrop.addEventListener('drop', async e => {
  e.preventDefault(); checkedDrop.classList.remove('dragover');
  const id = e.dataTransfer.getData('application/x-station-id');
  if (id) await checkIn(Number(id));
});

const knownDrop = $('knownDropZone');
knownDrop.addEventListener('dragover', e => {
  if (e.dataTransfer.types.includes('application/x-checkin-id')) { e.preventDefault(); knownDrop.classList.add('dragover'); }
});
knownDrop.addEventListener('dragleave', () => knownDrop.classList.remove('dragover'));
knownDrop.addEventListener('drop', async e => {
  e.preventDefault(); knownDrop.classList.remove('dragover');
  const id = e.dataTransfer.getData('application/x-checkin-id');
  if (id) await removeCheckin(Number(id));
});

refreshAll().catch(err => setStatus(err.message));
