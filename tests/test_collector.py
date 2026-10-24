"""Tests for the Prometheus collector using a fake API client."""

from mypv_elwa_prometheus_exporter.collector import MyPVCollector


class FakeAPI:
    """Minimal stand-in for MyPVAPI."""

    instance = "192.168.1.125"

    def __init__(self, data):
        self._data = data
        self.fail = False

    def get_data(self):
        if self.fail:
            msg = "device unreachable"
            raise ConnectionError(msg)
        return self._data

    def get_device_info(self):
        return {
            "device": "ELWA2",
            "firmware_version": "1.2.3",
            "power_system_version": "2.0.1",
            "control_version": "0.9.4",
            "instance": self.instance,
        }


def collect_by_name(apis):
    return {family.name: family for family in MyPVCollector(apis).collect()}


def test_collects_expected_metric_families(device_data):
    families = collect_by_name([FakeAPI(device_data)])

    for name in (
        "mypv_exporter_last_scrape_timestamp_ms",
        "mypv_device_info",
        "mypv_power_elwa_watts",
        "mypv_power_solar_watts",
        "mypv_power_grid_watts",
        "mypv_temperature_celsius",
        "mypv_voltage_mains_volts",
        "mypv_frequency_hertz",
        "mypv_control_state",
        "mypv_uptime_seconds",
    ):
        assert name in families

    assert "mypv_scrape_errors_total" not in families


def test_power_metric_value_and_labels(device_data):
    families = collect_by_name([FakeAPI(device_data)])

    [sample] = families["mypv_power_elwa_watts"].samples
    assert sample.value == 1500
    assert sample.labels == {
        "device": "ELWA2",
        "instance": "192.168.1.125",
    }


def test_temperature_is_scaled(device_data):
    families = collect_by_name([FakeAPI(device_data)])

    samples = {sample.labels["sensor"]: sample.value for sample in families["mypv_temperature_celsius"].samples}
    assert samples == {"1": 42.5, "2": 38.0}


def test_frequency_is_scaled(device_data):
    families = collect_by_name([FakeAPI(device_data)])

    [sample] = families["mypv_frequency_hertz"].samples
    assert sample.value == 50.0


def test_unreachable_device_yields_error_metric(device_data):
    api = FakeAPI(device_data)
    api.fail = True

    families = collect_by_name([api])

    [sample] = families["mypv_scrape_errors_total"].samples
    assert sample.value == 1
    assert sample.labels == {"instance": "192.168.1.125"}
