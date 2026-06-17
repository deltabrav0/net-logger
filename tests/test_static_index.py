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
