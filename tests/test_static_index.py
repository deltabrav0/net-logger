from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "src" / "net_logger" / "static" / "index.html"
USER_GUIDE_HTML = ROOT / "src" / "net_logger" / "static" / "user-guide.html"
LOGO = ROOT / "src" / "net_logger" / "static" / "app-logo.png"
INSTALLATION = ROOT / "docs" / "INSTALLATION.md"
PYPROJECT = ROOT / "pyproject.toml"


def test_packaged_openapi_spec_matches_documented_spec():
    assert (ROOT / "src/net_logger/openapi.yaml").read_text() == (ROOT / "docs/openapi.yaml").read_text()


def test_header_includes_customizable_app_logo():
    html = INDEX.read_text()

    assert '<img class="app-logo" src="/app-logo.png" alt="Net Logger logo" width="96" height="96">' in html


def test_default_logo_asset_is_packaged_square_png():
    assert LOGO.exists()
    assert LOGO.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    with LOGO.open("rb") as f:
        f.seek(16)
        width, height = struct.unpack(">II", f.read(8))
    assert (width, height) == (1024, 1024)
    assert '"static/*.png"' in PYPROJECT.read_text()


def test_installation_docs_explain_logo_customization():
    text = INSTALLATION.read_text()

    assert "## Customizing the application logo" in text
    assert "app-logo.png" in text
    assert "1024 x 1024" in text
    assert "logo_path" in text


def test_installation_docs_explain_plain_language_config_file_and_wordpress_options():
    text = INSTALLATION.read_text()

    assert "## Configuration file" in text
    assert "A configuration file is a small text file" in text
    assert "Windows" in text
    assert "macOS" in text
    assert "Linux" in text
    assert "config.ini" in text
    assert "[wordpress]" in text
    assert "endpoint =" in text
    assert "username =" in text
    assert "application_password =" in text
    assert "NET_LOGGER_CONFIG" in text


def test_session_form_uses_plain_inputs_without_extra_suggestion_controls():
    html = INDEX.read_text()

    assert '<input id="netName" value="Weekly Net">' in html
    assert '<input id="frequency" placeholder="146.520 MHz">' in html
    assert 'netNameSuggestions' not in html
    assert 'frequencySuggestions' not in html
    assert 'netNamePreset' not in html
    assert 'frequencyPreset' not in html


def test_session_buttons_are_capitalized_and_grouped_on_one_row():
    html = INDEX.read_text()

    assert '<div class="session-buttons">' in html
    assert '<button type="submit" id="startNetBtn">Start Net</button>' in html
    assert '<button type="button" id="stopNetBtn" class="secondary danger" disabled>Stop Net</button>' in html
    assert '<button type="button" id="cancelNetBtn" class="secondary danger" disabled>Cancel Net</button>' in html
    assert '<button type="button" id="clearNetBtn" class="secondary" hidden>Clear Net</button>' in html
    buttons = html.split('<div class="session-buttons">', 1)[1].split('</div>', 1)[0]
    assert 'id="startNetBtn"' in buttons
    assert 'id="stopNetBtn"' in buttons
    assert 'id="cancelNetBtn"' in buttons
    assert 'id="clearNetBtn"' in buttons


def test_session_button_group_has_nowrap_css():
    css = Path("src/net_logger/static/styles.css").read_text()

    assert ".session-buttons" in css
    assert "flex-wrap:nowrap" in css


def test_fcc_database_status_and_update_controls_are_present():
    html = INDEX.read_text()

    assert 'id="fccStatus"' in html
    assert 'id="updateFccBtn"' in html
    assert "FCC database" in html


def test_header_has_small_user_and_api_doc_links_next_to_eyebrow():
    html = INDEX.read_text()

    assert '<div class="eyebrow-row">' in html
    eyebrow_row = html.split('<div class="eyebrow-row">', 1)[1].split('</div>', 1)[0]
    assert '<p class="eyebrow">Amateur Radio</p>' in eyebrow_row
    assert 'class="header-links"' in eyebrow_row
    assert 'href="/user-guide.html" target="_blank" rel="noopener"' in eyebrow_row
    assert 'User Docs' in eyebrow_row
    assert 'href="/api/docs" target="_blank" rel="noopener"' in eyebrow_row
    assert 'API Docs' in eyebrow_row


def test_toolbar_uses_one_station_lookup_box_instead_of_separate_search_and_unknown_forms():
    html = INDEX.read_text()

    assert 'id="stationLookupForm"' in html
    assert 'id="stationLookup"' in html
    assert 'Search or add station' in html
    assert 'Search known stations' not in html
    assert 'id="stationSearch"' not in html
    assert 'id="newCallsign"' not in html
    assert 'id="newName"' not in html
    assert 'id="lookupBtn"' not in html


def test_station_lookup_has_known_station_suggestions_and_reuse_hint():
    html = INDEX.read_text()

    assert 'list="stationSuggestions"' in html
    assert '<datalist id="stationSuggestions"></datalist>' in html
    assert 'id="stationLookupHint"' in html
    assert 'Known station details appear here as you type.' in html


def test_main_page_links_to_reports_instead_of_rendering_saved_nets_and_metrics_below_board():
    html = INDEX.read_text()

    assert 'href="/reports.html"' in html
    assert 'Saved Nets / Metrics' in html
    assert 'id="sessionsList"' not in html
    assert 'id="metricsSeriesByNet"' not in html
    assert 'class="lower-grid"' not in html


def test_reports_page_contains_saved_nets_metrics_and_export_controls():
    html = (ROOT / "src" / "net_logger" / "static" / "reports.html").read_text()

    assert '<title>Net Logger Reports</title>' in html
    assert '<link rel="stylesheet" href="/styles.css">' in html
    assert 'href="/"' in html
    assert 'id="sessionsList"' in html
    assert 'id="metricsSeriesByNet"' in html
    assert 'id="metricsNetName"' in html
    assert 'Net name' in html
    assert '<option value="">All nets</option>' in html
    assert 'href="/api/export.csv"' in html
    assert 'Send to WordPress' in (ROOT / "src" / "net_logger" / "static" / "app.js").read_text()
    assert 'sendSessionToWordPress' in (ROOT / "src" / "net_logger" / "static" / "app.js").read_text()


def test_static_app_initializes_main_and_reports_pages_conditionally():
    js = (ROOT / "src" / "net_logger" / "static" / "app.js").read_text()

    assert "function pageHas(id)" in js
    assert "if (!pageHas('netName') || !pageHas('frequency')) return;" in js
    assert "if (pageHas('sessionForm'))" in js
    assert "if (pageHas('sessionsList'))" in js
    assert "if (pageHas('metricsSeriesByNet'))" in js
    assert "function refreshPage()" in js


def test_user_guide_html_page_exists_with_matching_theme_and_updated_lookup_instructions():
    html = Path("src/net_logger/static/user-guide.html").read_text()

    assert '<title>Net Logger User Guide</title>' in html
    assert '<link rel="stylesheet" href="/styles.css">' in html
    assert 'href="/reports.html"' in html
    assert 'Saved Nets / Metrics' in html
    assert 'Enter a callsign or operator name in the single station lookup box' in html
    assert 'reusable known-station suggestions' in html
    assert 'helper text confirms the saved station details' in html
    assert 'Net Logger searches known stations first' in html
    assert 'then searches the local FCC database' in html
    assert 'pre-fills' in html
    assert 'FCC database: updating…' in html
    assert 'api/fcc/status' in html
