"""Shared fixtures and sample device data for the test suite."""

import pytest  # pyright: ignore[reportMissingImports]  # dev dependency (uv/nix)

DEVICE_DATA = {
    "device": "ELWA2",
    "fwversion": "1.2.3",
    "psversion": "2.0.1",
    "coversion": "0.9.4",
    "fwversionlatest": "1.2.3",
    "coversionlatest": "0.9.4",
    "psversionlatest": "2.0.1",
    "power_elwa2": 1500,
    "power_solar": 2400,
    "power_grid": -900,
    "power1_solar": 800,
    "power2_solar": 800,
    "power3_solar": 800,
    "power1_grid": -300,
    "power2_grid": -300,
    "power3_grid": -300,
    "power_nominal": 3000,
    "power_max": 3000,
    "temp1": 425,
    "temp2": 380,
    "temp_ps": 350,
    "volt_mains": 230,
    "volt_aux": 12,
    "freq": 50000,
    "fan_speed": 0,
    "ctrlstate": "MPPT",
    "boostactive": 0,
    "blockactive": 0,
    "rel1_out": 0,
    "rel_selv": 1,
    "ps_state": 2,
    "uptime": 123456,
}


@pytest.fixture
def device_data():
    """Return a fresh copy of a representative device payload."""
    return dict(DEVICE_DATA)
