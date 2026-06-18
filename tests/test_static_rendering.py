import json
import subprocess


def _render_card(function_name, payload):
    script = f"""
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('src/net_logger/static/app.js', 'utf8');
const elements = new Map();
const makeElement = () => ({{
  textContent: '',
  innerHTML: '',
  value: '',
  disabled: false,
  hidden: false,
  addEventListener: () => {{}},
  classList: {{ add: () => {{}}, remove: () => {{}} }},
}});
const context = {{
  console,
  fetch: async () => ({{ status: 204 }}),
  document: {{
    getElementById: (id) => {{
      if (!elements.has(id)) elements.set(id, makeElement());
      return elements.get(id);
    }},
    querySelectorAll: () => [],
  }},
  sessionId: null,
  currentSession: null,
}};
vm.createContext(context);
vm.runInContext(code, context);
console.log(context[{json.dumps(function_name)}]({json.dumps(payload)}));
"""
    return subprocess.check_output(["node", "-e", script], text=True)


def _render_known_card(station):
    return _render_card("renderKnownCard", station)


def _render_checkin_card(checkin):
    return _render_card("renderCheckinCard", checkin)


def test_known_station_card_shows_grid_square_after_location():
    html = _render_known_card({
        "id": 1,
        "callsign": "K5SUB",
        "name": "Danny",
        "city": "Memphis",
        "state": "TN",
        "grid": "EM55AA",
    })

    assert "Danny • Memphis, TN • EM55AA" in html


def test_known_station_card_omits_grid_separator_when_grid_missing():
    html = _render_known_card({
        "id": 1,
        "callsign": "K5SUB",
        "name": "Danny",
        "city": "Memphis",
        "state": "TN",
        "grid": "",
    })

    assert "Danny • Memphis, TN" in html
    assert "Memphis, TN •</div>" not in html


def test_known_station_card_shows_last_heard_timestamp_under_heading():
    html = _render_known_card({
        "id": 1,
        "callsign": "K5SUB",
        "name": "Danny",
        "city": "Memphis",
        "state": "TN",
        "grid": "EM55AA",
        "last_heard_at": "2026-06-16 19:30:00",
    })

    assert "Last Heard" in html
    assert "06/16/2026" in html


def test_checkin_details_show_grid_square_after_location():
    html = _render_checkin_card({
        "id": 10,
        "sequence": 2,
        "checked_in_at": "2026-06-16 12:00:00",
        "traffic": False,
        "traffic_details": "",
        "notes": "",
        "station": {
            "id": 1,
            "callsign": "K5SUB",
            "name": "Danny",
            "city": "Memphis",
            "state": "TN",
            "grid": "EM55AA",
        },
    })

    assert "#2 Danny • Memphis, TN • EM55AA" in html


def test_known_station_card_includes_fcc_update_and_delete_buttons():
    html = _render_known_card({
        "id": 1,
        "callsign": "WD5EFY",
        "name": "",
        "city": "",
        "state": "",
        "grid": "",
    })

    assert 'onclick="refreshStationFromFcc(1)"' in html
    assert "Update details" in html
    assert 'onclick="deleteStation(1)"' in html
    assert "Delete" in html


def _run_station_action(action):
    script = f"""
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('src/net_logger/static/app.js', 'utf8');
const elements = new Map();
const calls = [];
const makeElement = () => ({{
  textContent: '',
  innerHTML: '',
  value: '',
  disabled: false,
  hidden: false,
  addEventListener: () => {{}},
  classList: {{ add: () => {{}}, remove: () => {{}} }},
}});
const context = {{
  console,
  calls,
  confirm: () => true,
  fetch: async () => ({{ status: 204 }}),
  document: {{
    getElementById: (id) => {{
      if (!elements.has(id)) elements.set(id, makeElement());
      return elements.get(id);
    }},
    querySelectorAll: () => [],
  }},
}};
vm.createContext(context);
vm.runInContext(code, context);
vm.runInContext(`
  api = async (path, options = {{}}) => {{
    calls.push([path, options.method || 'GET', options.body || '']);
    return {{ id: 1, callsign: 'WD5EFY', name: 'Updated Op' }};
  }};
  refreshAll = async () => {{ calls.push(['refreshAll', 'CALL', '']); }};
`, context);
context[{json.dumps(action)}](1).then(() => {{
  console.log(JSON.stringify({{ calls, status: elements.get('status').textContent }}));
}});
"""
    return json.loads(subprocess.check_output(["node", "-e", script], text=True))


def test_refresh_station_from_fcc_calls_refresh_api_and_updates_board():
    result = _run_station_action("refreshStationFromFcc")

    assert result["calls"] == [["/api/stations/1/refresh-fcc", "POST", ""], ["refreshAll", "CALL", ""]]
    assert "Updated WD5EFY from FCC details" in result["status"]


def test_delete_station_calls_delete_api_and_updates_board():
    result = _run_station_action("deleteStation")

    assert result["calls"] == [["/api/stations/1", "DELETE", ""], ["refreshAll", "CALL", ""]]
    assert "Station deleted" in result["status"]


def test_cancel_net_calls_delete_session_api_and_clears_active_board():
    script = """
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('src/net_logger/static/app.js', 'utf8');
const elements = new Map();
const calls = [];
const makeElement = (id) => ({
  textContent: '',
  innerHTML: '',
  value: '',
  disabled: false,
  hidden: false,
  addEventListener: () => {},
  classList: { add: () => {}, remove: () => {} },
});
const context = {
  console,
  calls,
  confirm: () => true,
  fetch: async () => ({ status: 204 }),
  document: {
    getElementById: (id) => {
      if (!elements.has(id)) elements.set(id, makeElement(id));
      return elements.get(id);
    },
    querySelectorAll: () => [],
  },
};
vm.createContext(context);
vm.runInContext(code, context);
vm.runInContext(`
  sessionId = 12;
  currentSession = { id: 12, status: 'open' };
  api = async (path, options = {}) => {
    calls.push([path, options.method || 'GET', options.body || '']);
    return null;
  };
  loadBoard = async () => { calls.push(['loadBoard', 'CALL', '']); };
  loadSessions = async () => { calls.push(['loadSessions', 'CALL', '']); };
  loadMetrics = async () => { calls.push(['loadMetrics', 'CALL', '']); };
`, context);
context.cancelSession().then(() => {
  console.log(JSON.stringify({
    calls,
    status: elements.get('status').textContent,
    stopDisabled: elements.get('stopNetBtn').disabled,
    cancelDisabled: elements.get('cancelNetBtn').disabled,
    clearHidden: elements.get('clearNetBtn').hidden,
    sessionId: vm.runInContext('sessionId', context),
    currentSession: vm.runInContext('currentSession', context),
  }));
});
"""
    result = json.loads(subprocess.check_output(["node", "-e", script], text=True))

    assert result["calls"] == [["/api/sessions/12", "DELETE", ""], ["loadBoard", "CALL", ""], ["loadSessions", "CALL", ""], ["loadMetrics", "CALL", ""]]
    assert "Session #12 canceled" in result["status"]
    assert result["stopDisabled"] is True
    assert result["cancelDisabled"] is True
    assert result["clearHidden"] is True
    assert result["sessionId"] is None
    assert result["currentSession"] is None


def test_load_sessions_populates_metrics_net_name_filter_with_unique_net_names():
    script = """
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('src/net_logger/static/app.js', 'utf8');
const elements = new Map();
const calls = [];
const makeElement = () => ({
  textContent: '',
  innerHTML: '',
  value: '',
  disabled: false,
  hidden: false,
  addEventListener: () => {},
  classList: { add: () => {}, remove: () => {} },
});
const context = {
  console,
  calls,
  fetch: async () => ({ status: 204 }),
  document: {
    getElementById: (id) => {
      if (!elements.has(id)) elements.set(id, makeElement());
      return elements.get(id);
    },
    querySelectorAll: () => [],
  },
};
vm.createContext(context);
vm.runInContext(code, context);
vm.runInContext(`
  api = async (path) => {
    calls.push(path);
    return [
      { id: 1, name: 'Weekly Net', status: 'closed', started_at: '2026-01-01 19:00:00', checkin_count: 1, traffic_count: 0 },
      { id: 2, name: 'Skywarn Net', status: 'closed', started_at: '2026-01-02 19:00:00', checkin_count: 1, traffic_count: 0 },
      { id: 3, name: 'Weekly Net', status: 'closed', started_at: '2026-01-03 19:00:00', checkin_count: 1, traffic_count: 0 },
    ];
  };
`, context);
context.loadSessions().then(() => {
  console.log(JSON.stringify({ options: elements.get('metricsNetName').innerHTML }));
});
"""
    result = json.loads(subprocess.check_output(["node", "-e", script], text=True))

    assert '<option value="">All nets</option>' in result["options"]
    assert result["options"].count('<option value="Weekly Net">Weekly Net</option>') == 1
    assert "Skywarn Net" in result["options"]


def test_load_sessions_populates_session_suggestions_and_autofills_latest_frequency():
    script = """
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('src/net_logger/static/app.js', 'utf8');
const elements = new Map();
const listeners = new Map();
const makeElement = (id) => ({
  textContent: '',
  innerHTML: '',
  value: '',
  disabled: false,
  hidden: false,
  addEventListener: (event, handler) => { listeners.set(`${id}:${event}`, handler); },
  classList: { add: () => {}, remove: () => {} },
});
const context = {
  console,
  fetch: async () => ({ status: 204 }),
  document: {
    getElementById: (id) => {
      if (!elements.has(id)) elements.set(id, makeElement(id));
      return elements.get(id);
    },
    querySelectorAll: () => [],
  },
};
vm.createContext(context);
vm.runInContext(code, context);
vm.runInContext(`
  api = async (path) => {
    return [
      { id: 3, name: 'Weekly Net', frequency: '147.240 MHz', status: 'closed', started_at: '2026-01-03 19:00:00', checkin_count: 1, traffic_count: 0 },
      { id: 2, name: 'Skywarn Net', frequency: '146.940 MHz', status: 'closed', started_at: '2026-01-02 19:00:00', checkin_count: 1, traffic_count: 0 },
      { id: 1, name: 'Weekly Net', frequency: '146.520 MHz', status: 'closed', started_at: '2026-01-01 19:00:00', checkin_count: 1, traffic_count: 0 },
    ];
  };
`, context);
context.loadSessions().then(() => {
  elements.get('netName').value = 'Weekly Net';
  listeners.get('netName:change')();
  const weeklyFrequency = elements.get('frequency').value;
  elements.get('netName').value = 'Skywarn Net';
  listeners.get('netName:input')();
  const typedSkywarnFrequency = elements.get('frequency').value;
  elements.get('netNamePreset').value = 'Weekly Net';
  listeners.get('netNamePreset:change')();
  const presetName = elements.get('netName').value;
  const presetFrequency = elements.get('frequency').value;
  elements.get('frequencyPreset').value = '146.940 MHz';
  listeners.get('frequencyPreset:change')();
  console.log(JSON.stringify({
    names: elements.get('netNameSuggestions').innerHTML,
    frequencies: elements.get('frequencySuggestions').innerHTML,
    namePreset: elements.get('netNamePreset').innerHTML,
    frequencyPreset: elements.get('frequencyPreset').innerHTML,
    weeklyFrequency,
    typedSkywarnFrequency,
    presetName,
    presetFrequency,
    frequencyAfterPreset: elements.get('frequency').value,
    skywarnFrequency: elements.get('frequency').value,
  }));
});
"""
    result = json.loads(subprocess.check_output(["node", "-e", script], text=True))

    assert result["names"].count('<option value="Weekly Net">') == 1
    assert '<option value="Skywarn Net">' in result["names"]
    assert '<option value="147.240 MHz">' in result["frequencies"]
    assert '<option value="146.940 MHz">' in result["frequencies"]
    assert '<option value="Weekly Net">Weekly Net</option>' in result["namePreset"]
    assert '<option value="146.940 MHz">146.940 MHz</option>' in result["frequencyPreset"]
    assert result["weeklyFrequency"] == "147.240 MHz"
    assert result["typedSkywarnFrequency"] == "146.940 MHz"
    assert result["presetName"] == "Weekly Net"
    assert result["presetFrequency"] == "147.240 MHz"
    assert result["frequencyAfterPreset"] == "146.940 MHz"
    assert result["skywarnFrequency"] == "146.940 MHz"


def test_load_metrics_passes_selected_net_name_to_api():
    script = """
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('src/net_logger/static/app.js', 'utf8');
const elements = new Map();
const calls = [];
const makeElement = (id) => ({
  textContent: '',
  innerHTML: '',
  value: id === 'metricsPeriod' ? 'week' : id === 'metricsNetName' ? 'Skywarn Net' : '',
  disabled: false,
  hidden: false,
  addEventListener: () => {},
  classList: { add: () => {}, remove: () => {} },
});
const context = {
  console,
  calls,
  fetch: async () => ({ status: 204 }),
  document: {
    getElementById: (id) => {
      if (!elements.has(id)) elements.set(id, makeElement(id));
      return elements.get(id);
    },
    querySelectorAll: () => [],
  },
};
vm.createContext(context);
vm.runInContext(code, context);
vm.runInContext(`
  api = async (path) => { calls.push(path); return { series_by_net: [] }; };
`, context);
context.loadMetrics().then(() => {
  console.log(JSON.stringify({ calls }));
});
"""
    result = json.loads(subprocess.check_output(["node", "-e", script], text=True))

    assert result["calls"] == ["/api/metrics?period=week&net_name=Skywarn%20Net"]


def _run_station_lookup(board, query, session_open=True, fcc_found=False):
    session_json = json.dumps(12 if session_open else None)
    current_session_json = json.dumps({"status": "open"} if session_open else None)
    board_json = json.dumps(board)
    lookup_response_json = json.dumps(
        {
            "ok": True,
            "found": True,
            "result": {
                "callsign": "K5FCC",
                "name": "FCC OP",
                "city": "Lufkin",
                "state": "TX",
                "grid": "EM21AA",
                "lat": 31.0,
                "lon": -94.0,
            },
        }
        if fcc_found
        else {"ok": True, "found": False, "callsign": "K5FCC"}
    )
    script = f"""
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('src/net_logger/static/app.js', 'utf8');
const elements = new Map();
const calls = [];
const makeElement = (id) => ({{
  textContent: '',
  innerHTML: '',
  value: id === 'stationLookup' ? {json.dumps(query)} : '',
  disabled: false,
  hidden: false,
  addEventListener: () => {{}},
  classList: {{ add: () => {{}}, remove: () => {{}} }},
}});
const context = {{
  console,
  calls,
  fetch: async () => ({{ status: 204 }}),
  document: {{
    getElementById: (id) => {{
      if (!elements.has(id)) elements.set(id, makeElement(id));
      return elements.get(id);
    }},
    querySelectorAll: () => [],
  }},
}};
vm.createContext(context);
vm.runInContext(code, context);
vm.runInContext(`
  sessionId = {session_json};
  currentSession = {current_session_json};
  board = {board_json};
  api = async (path, options = {{}}) => {{
    calls.push([path, options.method || 'GET', options.body || '']);
    if (path.startsWith('/api/lookup')) {{
      return {lookup_response_json};
    }}
    if (path === '/api/stations') {{ return {{ id: 99, callsign: 'K5FCC' }}; }}
    return {{}};
  }};
  refreshAll = async () => {{ calls.push(['refreshAll', 'CALL', '']); }};
  checkIn = async (stationId) => {{ calls.push(['/api/sessions/12/checkins', 'POST', JSON.stringify({{ station_id: stationId }})]); }};
`, context);
context.handleStationLookup({{ preventDefault: () => {{}} }}).then(() => {{
  console.log(JSON.stringify({{ calls, status: elements.get('status').textContent, value: elements.get('stationLookup').value }}));
}});
"""
    return json.loads(subprocess.check_output(["node", "-e", script], text=True))


def test_station_lookup_checks_in_known_callsign_before_calling_fcc():
    result = _run_station_lookup({
        "known_stations": [{"id": 7, "callsign": "K5SUB", "name": "Danny"}],
        "checkins": [],
    }, "k5sub")

    assert result["calls"] == [['/api/sessions/12/checkins', 'POST', '{"station_id":7}']]
    assert "Known station K5SUB" in result["status"]


def test_station_lookup_searches_fcc_and_creates_station_when_not_known():
    result = _run_station_lookup({"known_stations": [], "checkins": []}, "K5FCC", fcc_found=True)

    assert result["calls"][0][0] == "/api/lookup?callsign=K5FCC"
    assert result["calls"][1][0] == "/api/stations"
    assert result["calls"][1][1] == "POST"
    assert '"source":"fcc"' in result["calls"][1][2]
    assert result["calls"][2] == ['/api/sessions/12/checkins', 'POST', '{"station_id":99}']
    assert result["value"] == ""
