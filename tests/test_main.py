"""CLI tests. All device traffic is mocked with responses."""

import responses  # pyright: ignore[reportMissingImports]  # dev dependency (uv/nix)
from typer.testing import CliRunner  # pyright: ignore[reportMissingImports]  # dev dependency (uv/nix)

from mypv_elwa_prometheus_exporter.main import app, parse_urls

runner = CliRunner()

DEVICE_URL = "http://192.168.1.125"
DATA_URL = f"{DEVICE_URL}/data.jsn"


def test_parse_urls_ignores_whitespace_and_empty_entries():
    assert parse_urls("http://a, http://b ,") == ["http://a", "http://b"]
    assert parse_urls("") == []


def test_help_lists_commands():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ("serve", "export", "test-connection"):
        assert command in result.stdout


def test_serve_help_is_non_interactive():
    result = runner.invoke(app, ["serve", "--help"])

    assert result.exit_code == 0
    assert "--url" in result.stdout
    assert "--port" in result.stdout


@responses.activate
def test_export_prints_metrics(device_data):
    responses.add(responses.GET, DATA_URL, json=device_data)

    result = runner.invoke(app, ["export", "--url", DEVICE_URL])

    assert result.exit_code == 0
    assert "mypv_power_elwa_watts" in result.stdout
    assert 'mypv_power_elwa_watts{device="ELWA2",instance="192.168.1.125"} 1500' in result.stdout


@responses.activate
def test_test_connection_command(device_data):
    responses.add(responses.GET, DATA_URL, json=device_data)

    result = runner.invoke(app, ["test-connection", "--url", DEVICE_URL])

    assert result.exit_code == 0
    assert "Connection successful" in result.stdout
