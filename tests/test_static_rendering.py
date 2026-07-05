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


def test_expanded_checkin_card_stays_open_when_board_rerenders():
    script = """
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('src/net_logger/static/app.js', 'utf8');
const elements = new Map();
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
  fetch: async () => ({ status: 204 }),
  document: {
    getElementById: (id) => {
      if (!elements.has(id)) elements.set(id, makeElement());
      return elements.get(id);
    },
    querySelectorAll: () => [],
    addEventListener: () => {},
  },
};
vm.createContext(context);
vm.runInContext(code, context);
const checkin = {
  id: 10,
  sequence: 2,
  checked_in_at: '2026-06-16 12:00:00',
  traffic: true,
  traffic_details: 'Can relay',
  notes: 'Good signal',
  station: { id: 1, callsign: 'K5SUB', name: 'Danny', city: 'Memphis', state: 'TN', grid: 'EM55AA' },
};
vm.runInContext('expandedCheckinId = 10', context);
console.log(context.renderCheckinCard(checkin));
"""
    html = subprocess.check_output(["node", "-e", script], text=True)

    assert '<details open>' in html


def test_clicking_away_from_checkin_card_collapses_expanded_card():
    script = """
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('src/net_logger/static/app.js', 'utf8');
let documentClickHandler = null;
const openDetails = { open: true };
const context = {
  console,
  fetch: async () => ({ status: 204 }),
  document: {
    getElementById: () => null,
    querySelectorAll: (selector) => selector === '[data-checkin-id] details[open]' ? [openDetails] : [],
    addEventListener: (event, handler) => {
      if (event === 'click') documentClickHandler = handler;
    },
  },
};
vm.createContext(context);
vm.runInContext(code, context);
vm.runInContext('expandedCheckinId = 10', context);
documentClickHandler({ target: { closest: () => null } });
console.log(JSON.stringify({
  expandedCheckinId: vm.runInContext('expandedCheckinId', context),
  open: openDetails.open,
}));
"""
    result = json.loads(subprocess.check_output(["node", "-e", script], text=True))

    assert result == {"expandedCheckinId": None, "open": False}


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


def test_load_sessions_prefills_form_with_most_recent_saved_net_without_extra_selectors():
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
  console.log(JSON.stringify({
    netName: elements.get('netName').value,
    frequency: elements.get('frequency').value,
    hasNetNameChangeListener: listeners.has('netName:change'),
    hasNetPresetChangeListener: listeners.has('netNamePreset:change'),
    hasFrequencyPresetChangeListener: listeners.has('frequencyPreset:change'),
  }));
});
"""
    result = json.loads(subprocess.check_output(["node", "-e", script], text=True))

    assert result["netName"] == "Weekly Net"
    assert result["frequency"] == "147.240 MHz"
    assert result["hasNetNameChangeListener"] is False
    assert result["hasNetPresetChangeListener"] is False
    assert result["hasFrequencyPresetChangeListener"] is False


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


def test_station_suggestions_include_callsign_name_and_location_for_reuse():
    script = """
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('src/net_logger/static/app.js', 'utf8');
const elements = new Map();
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
  board = {
    known_stations: [
      { id: 7, callsign: 'K5SUB', name: 'Danny', city: 'Memphis', state: 'TN', grid: 'EM55AA' },
      { id: 8, callsign: 'W5XYZ', name: '', city: '', state: '', grid: '' },
    ],
    checkins: [
      { station: { id: 9, callsign: 'N5ABC', name: 'Checked Op', city: 'Dallas', state: 'TX', grid: '' } },
    ],
  };
  updateStationLookupAssist();
`, context);
console.log(JSON.stringify({ suggestions: elements.get('stationSuggestions').innerHTML }));
"""
    result = json.loads(subprocess.check_output(["node", "-e", script], text=True))

    assert '<option value="K5SUB" label="Danny • Memphis, TN • EM55AA"></option>' in result["suggestions"]
    assert '<option value="W5XYZ" label="—"></option>' in result["suggestions"]
    assert '<option value="N5ABC" label="Checked Op • Dallas, TX"></option>' in result["suggestions"]


def test_station_lookup_hint_shows_exact_known_station_and_enter_action():
    script = """
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('src/net_logger/static/app.js', 'utf8');
const elements = new Map();
const makeElement = (id) => ({
  textContent: '',
  innerHTML: '',
  value: id === 'stationLookup' ? 'k5sub' : '',
  disabled: false,
  hidden: false,
  addEventListener: () => {},
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
  sessionId = 12;
  currentSession = { status: 'open' };
  board = {
    known_stations: [{ id: 7, callsign: 'K5SUB', name: 'Danny', city: 'Memphis', state: 'TN', grid: 'EM55AA' }],
    checkins: [],
  };
  updateStationLookupAssist();
`, context);
console.log(JSON.stringify({ hint: elements.get('stationLookupHint').innerHTML }));
"""
    result = json.loads(subprocess.check_output(["node", "-e", script], text=True))

    assert "Known station: <strong>K5SUB</strong>" in result["hint"]
    assert "Danny • Memphis, TN • EM55AA" in result["hint"]
    assert "Press Enter to check in this station." in result["hint"]
