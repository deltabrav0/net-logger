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
