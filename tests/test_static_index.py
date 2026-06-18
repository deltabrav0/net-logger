from pathlib import Path


def test_packaged_openapi_spec_matches_documented_spec():
    assert Path("src/net_logger/openapi.yaml").read_text() == Path("docs/openapi.yaml").read_text()


INDEX = Path("src/net_logger/static/index.html")


def test_session_buttons_are_capitalized_and_grouped_on_one_row():
    html = INDEX.read_text()

    assert '<div class="session-buttons">' in html
    assert '<button type="submit" id="startNetBtn">Start Net</button>' in html
    assert '<button type="button" id="stopNetBtn" class="secondary danger" disabled>Stop Net</button>' in html
    assert '<button type="button" id="clearNetBtn" class="secondary" hidden>Clear Net</button>' in html
    buttons = html.split('<div class="session-buttons">', 1)[1].split('</div>', 1)[0]
    assert 'id="startNetBtn"' in buttons
    assert 'id="stopNetBtn"' in buttons
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


def test_user_guide_html_page_exists_with_matching_theme_and_updated_lookup_instructions():
    html = Path("src/net_logger/static/user-guide.html").read_text()

    assert '<title>Net Logger User Guide</title>' in html
    assert '<link rel="stylesheet" href="/styles.css">' in html
    assert 'Enter a callsign in the single station lookup box' in html
    assert 'Net Logger searches known stations first' in html
    assert 'then searches the local FCC database' in html
