let sessionId = null;
let currentSession = null;
let board = { known_stations: [], checkins: [] };
let expandedCheckinId = null;
let fccPreview = { callsign: '', status: 'idle', result: null, error: '' };
let fccPreviewTimer = null;
let fccPreviewSeq = 0;

const $ = (id) => document.getElementById(id);
function pageHas(id) { return $(id) !== null; }
const statusEl = $('status');

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) {
    const err = new Error(data.error || res.statusText);
    err.data = data;
    err.status = res.status;
    throw err;
  }
  return data;
}

function setStatus(text) { if (statusEl) statusEl.textContent = text; }
function esc(s) { return String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function place(station) { return [station.city, station.state].filter(Boolean).join(', '); }
function stationMeta(station) {
  return [station.name || '—', place(station), station.grid].filter(Boolean).join(' • ');
}
function sessionOpen() { return sessionId && (!currentSession || currentSession.status !== 'closed'); }
function closeExpandedCheckin() {
  expandedCheckinId = null;
  if (!document.querySelectorAll) return;
  document.querySelectorAll('[data-checkin-id] details[open]').forEach(details => { details.open = false; });
}
function handleDocumentClick(evt) {
  if (!expandedCheckinId) return;
  if (evt.target && evt.target.closest && evt.target.closest('[data-checkin-id]')) return;
  closeExpandedCheckin();
}
if (document.addEventListener) document.addEventListener('click', handleDocumentClick);
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
  $('cancelNetBtn').disabled = false;
  $('clearNetBtn').hidden = true;
  setStatus(`Session #${sessionId} open.`);
  await refreshAll();
}

async function stopSession() {
  if (!sessionId) return;
  const session = await api(`/api/sessions/${sessionId}/stop`, { method: 'POST' });
  currentSession = session;
  $('stopNetBtn').disabled = true;
  $('cancelNetBtn').disabled = true;
  $('clearNetBtn').hidden = false;
  setStatus(`Session #${sessionId} stopped. Records were already saved; this marks the net closed.`);
  await refreshAll();
}

async function cancelSession() {
  if (!sessionId) return;
  const canceledId = sessionId;
  if (!confirm('Cancel this net and discard its saved session/check-ins? Known station records will remain.')) return;
  await api(`/api/sessions/${canceledId}`, { method: 'DELETE' });
  sessionId = null;
  currentSession = null;
  $('stopNetBtn').disabled = true;
  $('cancelNetBtn').disabled = true;
  $('clearNetBtn').hidden = true;
  setStatus(`Session #${canceledId} canceled. Net session and check-ins were discarded.`);
  await loadBoard();
  await loadSessions();
  await loadMetrics();
}

async function clearNet() {
  sessionId = null;
  currentSession = null;
  $('stopNetBtn').disabled = true;
  $('cancelNetBtn').disabled = true;
  $('clearNetBtn').hidden = true;
  setStatus('Cleared the active board. The stopped net remains saved and exportable.');
  await loadBoard();
}

async function loadBoard() {
  if (!pageHas('knownStations') || !pageHas('checkins')) return;
  const lookup = pageHas('stationLookup') ? $('stationLookup').value : '';
  if (!sessionId) {
    const stations = await api('/api/stations?q=' + encodeURIComponent(lookup));
    board = { known_stations: stations, checkins: [] };
  } else {
    board = await api(`/api/sessions/${sessionId}/board`);
    currentSession = board.session;
    $('stopNetBtn').disabled = currentSession.status === 'closed';
    $('cancelNetBtn').disabled = currentSession.status === 'closed';
    $('clearNetBtn').hidden = currentSession.status !== 'closed';
    const q = lookup.trim().toUpperCase();
    if (q) board.known_stations = board.known_stations.filter(s => s.callsign.includes(q) || (s.name || '').toUpperCase().includes(q));
  }
  renderBoard();
  updateStationLookupAssist();
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
    const details = el.querySelector ? el.querySelector('details') : null;
    if (details) {
      details.addEventListener('toggle', () => {
        const id = Number(el.dataset.checkinId);
        if (details.open) expandedCheckinId = id;
        else if (expandedCheckinId === id) expandedCheckinId = null;
      });
    }
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
  const open = expandedCheckinId === c.id ? ' open' : '';
  return `<article class="card checkin-card compact" draggable="true" data-checkin-id="${c.id}">
    <details${open}>
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

function stationCandidates() {
  const byCallsign = new Map();
  [...(board.known_stations || []), ...(board.checkins || []).map(c => c.station)].filter(Boolean).forEach(station => {
    const call = (station.callsign || '').toUpperCase();
    if (call && !byCallsign.has(call)) byCallsign.set(call, station);
  });
  return Array.from(byCallsign.values()).sort((a, b) => (a.callsign || '').localeCompare(b.callsign || ''));
}

function findKnownStation(query) {
  const q = query.trim().toUpperCase();
  if (!q) return null;
  return stationCandidates().find(s => (s.callsign || '').toUpperCase() === q) || null;
}

function renderStationSuggestions(stations) {
  return stations.map(s => `<option value="${esc(s.callsign)}" label="${esc(stationMeta(s))}"></option>`).join('');
}

function looksLikeCallsign(value) {
  return /^[A-Z0-9/]{3,}$/.test(value) && /\d/.test(value);
}

function resetFccPreview() {
  if (fccPreviewTimer && typeof clearTimeout === 'function') clearTimeout(fccPreviewTimer);
  fccPreviewTimer = null;
  fccPreviewSeq += 1;
  fccPreview = { callsign: '', status: 'idle', result: null, error: '' };
}

function renderNewStationPreview(result, q) {
  const station = result || { callsign: q };
  return `New station: <strong>${esc(station.callsign || q)}</strong> — ${esc(stationMeta(station))}. ${sessionOpen() ? 'Press Enter to add/check in this station.' : 'Press Enter to add this station.'}`;
}

function renderUnknownStationPreview(q, unavailable = false) {
  const reason = unavailable ? ' FCC database unavailable;' : '';
  return `Unknown station: <strong>${esc(q)}</strong>.${reason} ${sessionOpen() ? 'Press Enter to add as callsign-only/check in.' : 'Press Enter to add as callsign-only.'}`;
}

function scheduleFccPreview(q) {
  if (!q || findKnownStation(q) || !looksLikeCallsign(q)) {
    resetFccPreview();
    return;
  }
  if (fccPreview.callsign === q && ['loading', 'found', 'unknown', 'error'].includes(fccPreview.status)) return;

  if (fccPreviewTimer && typeof clearTimeout === 'function') clearTimeout(fccPreviewTimer);
  const seq = ++fccPreviewSeq;
  fccPreview = { callsign: q, status: 'loading', result: null, error: '' };

  const runLookup = async () => {
    try {
      const result = await api('/api/lookup?callsign=' + encodeURIComponent(q));
      if (seq !== fccPreviewSeq || normalizedLookupValue() !== q) return;
      if (result.found && result.result) {
        fccPreview = { callsign: q, status: 'found', result: result.result, error: '' };
      } else {
        fccPreview = { callsign: result.callsign || q, status: 'unknown', result: null, error: '' };
      }
    } catch (err) {
      if (seq !== fccPreviewSeq || normalizedLookupValue() !== q) return;
      fccPreview = { callsign: q, status: 'error', result: null, error: err.message || 'FCC lookup failed' };
    }
    const hint = pageHas('stationLookupHint') ? $('stationLookupHint') : null;
    if (hint) hint.innerHTML = renderStationLookupHint($('stationLookup').value);
  };

  if (typeof setTimeout === 'function') fccPreviewTimer = setTimeout(runLookup, 350);
  else runLookup();
}

function renderStationLookupHint(query) {
  const q = query.trim().toUpperCase();
  if (!q) return 'Known station details appear here as you type.';
  const exact = findKnownStation(q);
  if (exact) {
    return `Known station: <strong>${esc(exact.callsign)}</strong> — ${esc(stationMeta(exact))}. ${sessionOpen() ? 'Press Enter to check in this station.' : 'Press Enter to select this station.'}`;
  }
  if (fccPreview.callsign === q && fccPreview.status === 'loading') {
    return `No known station match for ${esc(q)}. Searching local FCC database…`;
  }
  if (fccPreview.callsign === q && fccPreview.status === 'found') {
    return renderNewStationPreview(fccPreview.result, q);
  }
  if (fccPreview.callsign === q && fccPreview.status === 'unknown') {
    return renderUnknownStationPreview(q);
  }
  if (fccPreview.callsign === q && fccPreview.status === 'error') {
    return renderUnknownStationPreview(q, true);
  }
  const matches = stationCandidates().filter(s => (s.callsign || '').toUpperCase().includes(q) || (s.name || '').toUpperCase().includes(q));
  if (matches.length) return `${matches.length} known station match${matches.length === 1 ? '' : 'es'} available. Choose a suggestion or press Enter to add/search FCC.`;
  return `No known station match for ${esc(q)}. Press Enter to search the local FCC database and add it.`;
}

function updateStationLookupAssist() {
  if (!pageHas('stationLookup')) return;
  const suggestions = $('stationSuggestions');
  const hint = $('stationLookupHint');
  const query = $('stationLookup').value;
  const q = query.trim().toUpperCase();
  if (suggestions) suggestions.innerHTML = renderStationSuggestions(stationCandidates());
  scheduleFccPreview(q);
  if (hint) hint.innerHTML = renderStationLookupHint(query);
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

function prefillSessionFormFromLastSession(sessions) {
  if (!pageHas('netName') || !pageHas('frequency')) return;
  if (!sessions.length || $('netName').value || $('frequency').value) return;
  const latest = sessions[0];
  if (latest.name) $('netName').value = latest.name;
  if (latest.frequency) $('frequency').value = latest.frequency;
}

function renderSessionRow(s) {
  const pushed = Boolean(s.wordpress_pushed_at);
  const wordpressButton = pushed
    ? `<button type="button" class="secondary" disabled>Sent to WordPress</button>`
    : `<button type="button" class="secondary" onclick="sendSessionToWordPress(${s.id})">Send to WordPress</button>`;
  return `<div class="session-row">
      <div><div class="title">${esc(s.name || 'Untitled net')} #${s.id}</div>
      <div class="details">${esc(s.status)} • ${formatDateTime(s.started_at)} • check-ins: ${s.checkin_count} • traffic: ${s.traffic_count}${pushed ? ` • WordPress: sent ${formatDateTime(s.wordpress_pushed_at)}` : ''}</div></div>
      <div class="session-actions"><a class="button-link secondary" href="/api/export.csv?session_id=${s.id}">Export CSV</a>${wordpressButton}</div>
    </div>`;
}

async function loadSessions() {
  if (!pageHas('sessionsList')) return;
  const sessions = await api('/api/sessions');
  $('sessionsList').innerHTML = sessions.length ? sessions.map(renderSessionRow).join('') : '<div class="empty">No saved nets yet.</div>';
  prefillSessionFormFromLastSession(sessions);
  populateMetricsNetFilter(sessions);
}

async function getWordPressConfig() {
  return api('/api/wordpress/config');
}

function wordPressConfigPayload() {
  return {
    endpoint: $('wordpressEndpoint').value.trim(),
    username: $('wordpressUsername').value.trim(),
    application_password: $('wordpressApplicationPassword').value.trim(),
    timeout: Number($('wordpressTimeout').value || 20),
  };
}

async function openWordPressConfigDialog(message = '') {
  const dialog = $('wordpressConfigDialog');
  if (!dialog) return false;
  const status = $('wordpressConfigStatus');
  try {
    const config = await getWordPressConfig();
    $('wordpressEndpoint').value = config.endpoint || '';
    $('wordpressUsername').value = config.username || '';
    $('wordpressApplicationPassword').value = '';
    $('wordpressTimeout').value = config.timeout || 20;
    status.textContent = message || (config.configured ? 'WordPress export is configured. Enter a new Application Password only if you want to replace it.' : 'WordPress export is not configured yet. Fill in the required settings.');
  } catch (err) {
    status.textContent = err.message;
  }
  if (typeof dialog.showModal === 'function') dialog.showModal();
  else dialog.setAttribute('open', 'open');
  return true;
}

function closeWordPressConfigDialog() {
  const dialog = $('wordpressConfigDialog');
  if (!dialog) return;
  if (typeof dialog.close === 'function') dialog.close();
  else dialog.removeAttribute('open');
}

async function testWordPressConfigOnly() {
  const status = $('wordpressConfigStatus');
  status.textContent = 'Testing WordPress connection…';
  try {
    const result = await api('/api/wordpress/config/test', { method: 'POST', body: JSON.stringify(wordPressConfigPayload()) });
    status.textContent = result.message || 'WordPress connection and authentication succeeded.';
  } catch (err) {
    status.textContent = err.message;
  }
}

async function saveWordPressConfig(evt) {
  evt.preventDefault();
  const status = $('wordpressConfigStatus');
  status.textContent = 'Testing and saving WordPress settings…';
  try {
    const result = await api('/api/wordpress/config', { method: 'POST', body: JSON.stringify(wordPressConfigPayload()) });
    status.textContent = result.message || 'WordPress configuration saved.';
    setStatus('WordPress configuration saved. You can now send saved nets to WordPress.');
    closeWordPressConfigDialog();
  } catch (err) {
    status.textContent = err.message;
  }
}

async function sendSessionToWordPress(sessionIdToSend) {
  if (!confirm('Send this saved net to WordPress? This can only be done once from Net Logger.')) return;
  try {
    const result = await api(`/api/sessions/${sessionIdToSend}/send-wordpress`, { method: 'POST' });
    const eventId = result.wordpress && result.wordpress.event_id ? ` Event #${result.wordpress.event_id}.` : '';
    setStatus(`Saved net sent to WordPress.${eventId}`);
    await loadSessions();
  } catch (err) {
    if (err.data && err.data.setup_required) {
      await openWordPressConfigDialog('WordPress export is not configured yet. Enter the endpoint, username, and Application Password, then test and save.');
      return;
    }
    setStatus(err.message);
  }
}

function populateMetricsNetFilter(sessions) {
  const select = $('metricsNetName');
  if (!select) return;
  const selected = select.value;
  const names = Array.from(new Set(sessions.map(s => s.name || 'Untitled net'))).sort((a, b) => a.localeCompare(b));
  select.innerHTML = '<option value="">All nets</option>' + names.map(name => `<option value="${esc(name)}">${esc(name)}</option>`).join('');
  if (names.includes(selected)) select.value = selected;
}

async function loadMetrics() {
  if (!pageHas('metricsSeriesByNet')) return;
  const period = $('metricsPeriod') ? $('metricsPeriod').value : 'month';
  const netName = $('metricsNetName') ? $('metricsNetName').value : '';
  const params = ['period=' + encodeURIComponent(period)];
  if (netName) params.push('net_name=' + encodeURIComponent(netName));
  const metrics = await api('/api/metrics?' + params.join('&'));
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
  await refreshPage();
}

async function refreshPage() {
  if (pageHas('knownStations')) await loadBoard();
  if (pageHas('sessionsList')) await loadSessions();
  if (pageHas('metricsSeriesByNet')) await loadMetrics();
  if (pageHas('fccStatus')) await loadFccStatus();
}

if (pageHas('sessionForm')) $('sessionForm').addEventListener('submit', startSession);
if (pageHas('stopNetBtn')) $('stopNetBtn').addEventListener('click', stopSession);
if (pageHas('cancelNetBtn')) $('cancelNetBtn').addEventListener('click', cancelSession);
if (pageHas('clearNetBtn')) $('clearNetBtn').addEventListener('click', clearNet);
if (pageHas('stationLookupForm')) $('stationLookupForm').addEventListener('submit', handleStationLookup);
if (pageHas('updateFccBtn')) $('updateFccBtn').addEventListener('click', () => updateFccDatabase().catch(err => setStatus(err.message)));
if (pageHas('refreshMetricsBtn')) $('refreshMetricsBtn').addEventListener('click', () => refreshAll().catch(err => setStatus(err.message)));
if (pageHas('metricsPeriod')) $('metricsPeriod').addEventListener('change', () => loadMetrics().catch(err => setStatus(err.message)));
if (pageHas('metricsNetName')) $('metricsNetName').addEventListener('change', () => loadMetrics().catch(err => setStatus(err.message)));
if (pageHas('stationLookup')) $('stationLookup').addEventListener('input', () => loadBoard().catch(err => setStatus(err.message)));
if (pageHas('openWordPressConfigBtn')) $('openWordPressConfigBtn').addEventListener('click', () => openWordPressConfigDialog('View or edit the WordPress export settings. Leave Application Password blank to keep the saved password.').catch(err => setStatus(err.message)));
if (pageHas('wordpressConfigForm')) $('wordpressConfigForm').addEventListener('submit', saveWordPressConfig);
if (pageHas('testWordPressConfigBtn')) $('testWordPressConfigBtn').addEventListener('click', () => testWordPressConfigOnly().catch(err => $('wordpressConfigStatus').textContent = err.message));
if (pageHas('cancelWordPressConfigBtn')) $('cancelWordPressConfigBtn').addEventListener('click', closeWordPressConfigDialog);

const checkedDrop = $('checkedInDropZone');
if (checkedDrop) {
  checkedDrop.addEventListener('dragover', e => { if (sessionOpen()) { e.preventDefault(); checkedDrop.classList.add('dragover'); } });
  checkedDrop.addEventListener('dragleave', () => checkedDrop.classList.remove('dragover'));
  checkedDrop.addEventListener('drop', async e => {
    e.preventDefault(); checkedDrop.classList.remove('dragover');
    const id = e.dataTransfer.getData('application/x-station-id');
    if (id) await checkIn(Number(id));
  });
}

const knownDrop = $('knownDropZone');
if (knownDrop) {
  knownDrop.addEventListener('dragover', e => {
    if (e.dataTransfer.types.includes('application/x-checkin-id')) { e.preventDefault(); knownDrop.classList.add('dragover'); }
  });
  knownDrop.addEventListener('dragleave', () => knownDrop.classList.remove('dragover'));
  knownDrop.addEventListener('drop', async e => {
    e.preventDefault(); knownDrop.classList.remove('dragover');
    const id = e.dataTransfer.getData('application/x-checkin-id');
    if (id) await removeCheckin(Number(id));
  });
}

refreshPage().catch(err => setStatus(err.message));
