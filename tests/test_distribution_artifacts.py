import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_install_module():
    spec = importlib.util.spec_from_file_location("net_logger_installer", ROOT / "install.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_cross_platform_installer_builds_default_github_pipx_command_without_git_requirement():
    installer = _load_install_module()

    command = installer.build_install_command(source="github", method="pipx", package_url="https://github.com/deltabrav0/net-logger/archive/refs/heads/main.zip")

    assert command == ["pipx", "install", "https://github.com/deltabrav0/net-logger/archive/refs/heads/main.zip"]


def test_cross_platform_installer_supports_local_checkout_upgrade_and_dry_run(capsys):
    installer = _load_install_module()

    code = installer.main(["--source", "local", "--method", "pipx", "--upgrade", "--dry-run"])

    assert code == 0
    output = capsys.readouterr().out
    assert "pipx install --force ." in output
    assert "net-logger serve" in output


def test_unix_and_windows_install_wrappers_delegate_to_python_installer():
    install_sh = (ROOT / "install.sh").read_text()
    install_ps1 = (ROOT / "install.ps1").read_text()

    assert "python3" in install_sh
    assert "install.py" in install_sh
    assert "py" in install_ps1
    assert "install.py" in install_ps1


def test_unix_and_windows_install_wrappers_check_python_version_before_running_installer():
    install_sh = (ROOT / "install.sh").read_text()
    install_ps1 = (ROOT / "install.ps1").read_text()

    assert "PYTHON_VERSION_CHECK" in install_sh
    assert "sys.version_info >= (3, 11)" in install_sh
    assert "Found Python" in install_sh
    assert "is too old; Python 3.11 or newer is required" in install_sh

    assert "$VersionCheck" in install_ps1
    assert "sys.version_info >= (3, 11)" in install_ps1
    assert "Found Python" in install_ps1
    assert "is too old; Python 3.11 or newer is required" in install_ps1


def test_dockerfile_runs_installed_app_as_non_root_on_lan_port():
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "FROM python:3.12-slim" in dockerfile
    assert "useradd" in dockerfile
    assert "USER netlogger" in dockerfile
    assert "EXPOSE 8088" in dockerfile
    assert 'CMD ["net-logger", "serve"' in dockerfile
    assert '"--host", "0.0.0.0"' in dockerfile


def test_docker_compose_defines_persistent_data_logo_and_fcc_mounts():
    compose = (ROOT / "docker-compose.yml").read_text()

    assert "net-logger:" in compose
    assert "build: ." in compose
    assert '"8088:8088"' in compose
    assert "NET_LOGGER_DATA_DIR: /data" in compose
    assert "NET_LOGGER_FCC_LOOKUP_PATH: /fcc" in compose
    assert "NET_LOGGER_LOGO_PATH: /config/app-logo.png" in compose
    assert "net-logger-data:/data" in compose
    assert "./fcc-data:/fcc" in compose
    assert "./fcc-data:/fcc:ro" not in compose
    assert "./config:/config:ro" in compose
    assert "net-logger-data:" in compose


def test_dockerignore_excludes_runtime_and_build_artifacts_but_keeps_source():
    lines = set((ROOT / ".dockerignore").read_text().splitlines())

    assert ".venv" in lines
    assert "dist" in lines
    assert "*.sqlite3" in lines
    assert "src" not in lines


def test_docker_documentation_covers_compose_data_logo_fcc_and_security():
    text = (ROOT / "docs" / "DOCKER.md").read_text()

    assert "docker compose up -d" in text
    assert "net-logger-data" in text
    assert "./config/app-logo.png" in text
    assert "./fcc-data" in text
    assert "Do not expose" in text


def test_installation_docs_reference_installer_and_docker_options():
    text = (ROOT / "docs" / "INSTALLATION.md").read_text()

    assert "## Cross-platform installer script" in text
    assert "python install.py" in text
    assert "archive/refs/heads/main.zip" in text
    assert "Git. The recommended commands below install from GitHub's ZIP archive" in text
    assert "$env:USERPROFILE\\.local\\bin\\net-logger.exe" in text
    assert "py -m net_logger.cli serve" in text
    assert "install.sh" in text
    assert "install.ps1" in text
    assert "## Docker installation" in text
    assert "docker compose up -d" in text
