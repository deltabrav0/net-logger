from pathlib import Path

from net_logger import config as nl_config
from net_logger.app import create_app


def test_config_file_path_can_be_overridden(monkeypatch, tmp_path):
    path = tmp_path / "net-logger.ini"
    monkeypatch.setenv("NET_LOGGER_CONFIG", str(path))

    assert nl_config.default_config_path() == path


def test_default_config_path_is_cross_platform(monkeypatch):
    monkeypatch.delenv("NET_LOGGER_CONFIG", raising=False)
    monkeypatch.setattr(nl_config, "default_data_dir", lambda: Path("/tmp/Net Logger"))

    assert nl_config.default_config_path() == Path("/tmp/Net Logger") / "config.ini"


def test_ensure_config_file_writes_plain_language_template(tmp_path):
    path = tmp_path / "config.ini"

    created = nl_config.ensure_config_file(path)

    assert created == path
    text = path.read_text()
    assert "[server]" in text
    assert "[wordpress]" in text
    assert "endpoint =" in text
    assert "application_password =" in text
    assert "WordPress Application Password" in text


def test_load_config_file_maps_wordpress_and_path_settings(tmp_path):
    config_path = tmp_path / "config.ini"
    database = tmp_path / "custom.sqlite3"
    logo = tmp_path / "logo.png"
    config_path.write_text(
        f"""
[server]
host = 0.0.0.0
port = 8090
debug = yes

[paths]
database = {database}
logo_path = {logo}

[wordpress]
endpoint = https://example.org/wp-json/net-attendance/v1/net-logger/sessions
username = api-user
application_password = app password with spaces
timeout = 45
""".strip()
    )

    settings = nl_config.load_config_file(config_path)

    assert settings["HOST"] == "0.0.0.0"
    assert settings["PORT"] == 8090
    assert settings["DEBUG"] is True
    assert settings["DATABASE"] == str(database)
    assert settings["LOGO_PATH"] == str(logo)
    assert settings["WORDPRESS_ENDPOINT"].endswith("/net-logger/sessions")
    assert settings["WORDPRESS_USERNAME"] == "api-user"
    assert settings["WORDPRESS_APPLICATION_PASSWORD"] == "app password with spaces"
    assert settings["WORDPRESS_TIMEOUT"] == 45


def test_environment_variables_override_config_file(monkeypatch, tmp_path):
    config_path = tmp_path / "config.ini"
    config_path.write_text("""
[wordpress]
endpoint = https://example.org/from-file
username = file-user
application_password = file-password
timeout = 15
""")
    monkeypatch.setenv("NET_LOGGER_CONFIG", str(config_path))
    monkeypatch.setenv("NET_LOGGER_WORDPRESS_USERNAME", "env-user")
    monkeypatch.setenv("NET_LOGGER_WORDPRESS_TIMEOUT", "60")

    settings = nl_config.load_app_settings()

    assert settings["WORDPRESS_ENDPOINT"] == "https://example.org/from-file"
    assert settings["WORDPRESS_USERNAME"] == "env-user"
    assert settings["WORDPRESS_APPLICATION_PASSWORD"] == "file-password"
    assert settings["WORDPRESS_TIMEOUT"] == 60


def test_create_app_reads_wordpress_settings_from_config_file(monkeypatch, tmp_path):
    config_path = tmp_path / "config.ini"
    db_path = tmp_path / "net.sqlite3"
    config_path.write_text(f"""
[paths]
database = {db_path}

[wordpress]
endpoint = https://example.org/wp-json/net-attendance/v1/net-logger/sessions
username = file-user
application_password = file-password
timeout = 25
""")
    monkeypatch.setenv("NET_LOGGER_CONFIG", str(config_path))

    app = create_app({"TESTING": True})

    assert app.config["DATABASE"] == str(db_path)
    assert app.config["WORDPRESS_ENDPOINT"].endswith("/net-logger/sessions")
    assert app.config["WORDPRESS_USERNAME"] == "file-user"
    assert app.config["WORDPRESS_APPLICATION_PASSWORD"] == "file-password"
    assert app.config["WORDPRESS_TIMEOUT"] == 25
