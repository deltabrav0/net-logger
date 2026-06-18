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
