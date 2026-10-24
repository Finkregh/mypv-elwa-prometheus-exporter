"""Tests for the my-PV HTTP API client. All requests are mocked with responses."""

import responses  # pyright: ignore[reportMissingImports]  # dev dependency (uv/nix)

from mypv_elwa_prometheus_exporter.api import MyPVAPI

DEVICE_URL = "http://192.168.1.125"
DATA_URL = f"{DEVICE_URL}/data.jsn"


def test_url_is_normalized():
    assert MyPVAPI("192.168.1.125").base_url == DEVICE_URL
    assert MyPVAPI("http://192.168.1.125/").base_url == DEVICE_URL
    assert MyPVAPI("https://elwa.local").base_url == "https://elwa.local"


def test_instance_is_derived_from_url():
    assert MyPVAPI(DEVICE_URL).instance == "192.168.1.125"


@responses.activate
def test_get_data_returns_json(device_data):
    responses.add(responses.GET, DATA_URL, json=device_data)

    assert MyPVAPI(DEVICE_URL).get_data() == device_data


@responses.activate
def test_test_connection_true(device_data):
    responses.add(responses.GET, DATA_URL, json=device_data)

    assert MyPVAPI(DEVICE_URL).test_connection() is True


@responses.activate
def test_test_connection_false_on_error():
    responses.add(responses.GET, DATA_URL, status=500)

    assert MyPVAPI(DEVICE_URL).test_connection() is False


@responses.activate
def test_test_connection_false_on_incomplete_payload():
    responses.add(responses.GET, DATA_URL, json={"unexpected": "payload"})

    assert MyPVAPI(DEVICE_URL).test_connection() is False


@responses.activate
def test_get_device_info(device_data):
    responses.add(responses.GET, DATA_URL, json=device_data)

    assert MyPVAPI(DEVICE_URL).get_device_info() == {
        "device": "ELWA2",
        "firmware_version": "1.2.3",
        "power_system_version": "2.0.1",
        "control_version": "0.9.4",
        "instance": "192.168.1.125",
    }
