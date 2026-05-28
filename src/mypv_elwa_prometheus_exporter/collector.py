#!/usr/bin/env python3
"""Prometheus Collector for my-PV AC ELWA devices.

This module provides the MyPVCollector class for collecting metrics from
my-PV AC ELWA devices and exposing them in Prometheus format.
"""

import logging
import time
from collections.abc import Iterator
from typing import Any

from prometheus_client.core import (
    CounterMetricFamily,
    GaugeMetricFamily,
    InfoMetricFamily,
)
from prometheus_client.registry import Collector

from mypv_elwa_prometheus_exporter.api import MyPVAPI

log = logging.getLogger(__name__)


class MyPVCollector(Collector):
    """Custom Prometheus collector for my-PV AC ELWA metrics."""

    def __init__(self, apis: list[MyPVAPI]) -> None:
        """Initialize the my-PV collector.

        :param apis: List of MyPVAPI client instances.
        :type apis: list[MyPVAPI]
        """
        self.apis = apis

    def collect(
        self,
    ) -> Iterator[GaugeMetricFamily | CounterMetricFamily | InfoMetricFamily]:
        """Collect metrics from my-PV devices and yield metric families.

        :return: Iterator of metric families.
        :rtype: Iterator[GaugeMetricFamily | CounterMetricFamily | InfoMetricFamily]
        """
        # Yield timestamp metric
        timestamp = int(time.time() * 1000)
        timestamp_metric = GaugeMetricFamily(
            "mypv_exporter_last_scrape_timestamp_ms",
            "Timestamp of last successful scrape",
        )
        timestamp_metric.add_metric([], timestamp)
        yield timestamp_metric

        # Collect metrics from all devices
        for api in self.apis:
            try:
                data = api.get_data()
                device_info = api.get_device_info()

                log.debug(f"Collecting metrics from device {device_info['instance']}")

                # Yield all metric categories
                yield from self._collect_device_info(data, device_info)
                yield from self._collect_power_metrics(data, device_info)
                yield from self._collect_temperature_metrics(data, device_info)
                yield from self._collect_electrical_metrics(data, device_info)
                yield from self._collect_control_metrics(data, device_info)
                yield from self._collect_system_metrics(data, device_info)
                yield from self._collect_network_metrics(data, device_info)

                log.debug(f"Successfully collected metrics from device {device_info['instance']}")

            except Exception as e:
                log.error(f"Error collecting metrics from device {api.instance}: {e}")
                # Add error metric
                error_metric = GaugeMetricFamily(
                    "mypv_scrape_errors_total",
                    "Total scrape errors",
                    labels=["instance"],
                )
                error_metric.add_metric([api.instance], 1)
                yield error_metric

    def _get_common_labels(self, device_info: dict[str, str]) -> list[str]:
        """Get common labels for all metrics.

        :param device_info: Device information dictionary.
        :type device_info: dict[str, str]
        :return: List of label values.
        :rtype: list[str]
        """
        return [device_info["device"], device_info["instance"]]

    def _collect_device_info(
        self,
        data: dict[str, Any],
        device_info: dict[str, str],
    ) -> Iterator[InfoMetricFamily]:
        """Collect device information metrics.

        :param data: Device data from API.
        :type data: dict[str, Any]
        :param device_info: Device info for labels.
        :type device_info: dict[str, str]
        :return: Iterator of info metric families.
        :rtype: Iterator[InfoMetricFamily]
        """
        # Device info
        device_info_metric = InfoMetricFamily(
            "mypv_device_info",
            "Device information",
        )
        device_info_metric.add_metric(
            [],
            {
                "device": device_info["device"],
                "firmware_version": device_info["firmware_version"],
                "power_system_version": device_info["power_system_version"],
                "control_version": device_info["control_version"],
                "instance": device_info["instance"],
            },
        )
        yield device_info_metric

        # Firmware latest info
        firmware_latest_metric = InfoMetricFamily(
            "mypv_firmware_latest_info",
            "Latest firmware information",
        )
        firmware_latest_metric.add_metric(
            [],
            {
                "latest_firmware": data.get("fwversionlatest", "unknown"),
                "latest_control": data.get("coversionlatest", "unknown"),
                "latest_power_system": data.get("psversionlatest", "unknown"),
                "instance": device_info["instance"],
            },
        )
        yield firmware_latest_metric

    def _collect_power_metrics(
        self,
        data: dict[str, Any],
        device_info: dict[str, str],
    ) -> Iterator[GaugeMetricFamily]:
        """Collect power measurement metrics.

        :param data: Device data from API.
        :type data: dict[str, Any]
        :param device_info: Device info for labels.
        :type device_info: dict[str, str]
        :return: Iterator of power metric families.
        :rtype: Iterator[GaugeMetricFamily]
        """
        common_labels = ["device", "instance"]
        common_values = self._get_common_labels(device_info)

        # Main power metrics
        elwa_power_metric = GaugeMetricFamily(
            "mypv_power_elwa_watts",
            "AC ELWA device power consumption in watts",
            labels=common_labels,
        )
        elwa_power_metric.add_metric(common_values, data.get("power_elwa2", 0))
        yield elwa_power_metric

        solar_power_metric = GaugeMetricFamily(
            "mypv_power_solar_watts",
            "Solar power generation in watts",
            labels=common_labels,
        )
        solar_power_metric.add_metric(common_values, data.get("power_solar", 0))
        yield solar_power_metric

        grid_power_metric = GaugeMetricFamily(
            "mypv_power_grid_watts",
            "Grid power (positive=import, negative=export) in watts",
            labels=common_labels,
        )
        grid_power_metric.add_metric(common_values, data.get("power_grid", 0))
        yield grid_power_metric

        # Per-phase solar power
        solar_phase_metric = GaugeMetricFamily(
            "mypv_power_solar_phase_watts",
            "Solar power generation per phase in watts",
            labels=common_labels + ["phase"],
        )
        for phase in [1, 2, 3]:
            value = data.get(f"power{phase}_solar", 0)
            solar_phase_metric.add_metric(common_values + [str(phase)], value)
        yield solar_phase_metric

        # Per-phase grid power
        grid_phase_metric = GaugeMetricFamily(
            "mypv_power_grid_phase_watts",
            "Grid power per phase in watts",
            labels=common_labels + ["phase"],
        )
        for phase in [1, 2, 3]:
            value = data.get(f"power{phase}_grid", 0)
            grid_phase_metric.add_metric(common_values + [str(phase)], value)
        yield grid_phase_metric

        # Power limits and ratings
        nominal_power_metric = GaugeMetricFamily(
            "mypv_power_nominal_watts",
            "Device nominal power rating in watts",
            labels=common_labels,
        )
        nominal_power_metric.add_metric(common_values, data.get("power_nominal", 0))
        yield nominal_power_metric

        max_power_metric = GaugeMetricFamily(
            "mypv_power_max_watts",
            "Current maximum power limit in watts",
            labels=common_labels,
        )
        max_power_metric.add_metric(common_values, data.get("power_max", 0))
        yield max_power_metric

        # Surplus power (if available)
        surplus = data.get("surplus")
        if surplus is not None:
            surplus_metric = GaugeMetricFamily(
                "mypv_power_surplus_watts",
                "Available surplus power in watts",
                labels=common_labels,
            )
            surplus_metric.add_metric(common_values, surplus)
            yield surplus_metric

    def _collect_temperature_metrics(
        self,
        data: dict[str, Any],
        device_info: dict[str, str],
    ) -> Iterator[GaugeMetricFamily]:
        """Collect temperature measurement metrics.

        :param data: Device data from API.
        :type data: dict[str, Any]
        :param device_info: Device info for labels.
        :type device_info: dict[str, str]
        :return: Iterator of temperature metric families.
        :rtype: Iterator[GaugeMetricFamily]
        """
        common_labels = ["device", "instance", "sensor"]
        common_values = self._get_common_labels(device_info)

        # Temperature sensors (with unit conversion: raw value / 10 = Celsius)
        temp_metric = GaugeMetricFamily(
            "mypv_temperature_celsius",
            "Temperature readings in Celsius",
            labels=common_labels,
        )

        for sensor in [1, 2]:
            raw_temp = data.get(f"temp{sensor}", 0)
            temp_celsius = raw_temp / 10.0 if raw_temp else 0
            temp_metric.add_metric(common_values + [str(sensor)], temp_celsius)
        yield temp_metric

        # Power system temperature
        ps_temp_metric = GaugeMetricFamily(
            "mypv_temperature_power_system_celsius",
            "Power system temperature in Celsius",
            labels=["device", "instance"],
        )
        raw_ps_temp = data.get("temp_ps", 0)
        ps_temp_celsius = raw_ps_temp / 10.0 if raw_ps_temp else 0
        ps_temp_metric.add_metric(common_values, ps_temp_celsius)
        yield ps_temp_metric

    def _collect_electrical_metrics(
        self,
        data: dict[str, Any],
        device_info: dict[str, str],
    ) -> Iterator[GaugeMetricFamily]:
        """Collect electrical system metrics.

        :param data: Device data from API.
        :type data: dict[str, Any]
        :param device_info: Device info for labels.
        :type device_info: dict[str, str]
        :return: Iterator of electrical metric families.
        :rtype: Iterator[GaugeMetricFamily]
        """
        common_labels = ["device", "instance"]
        common_values = self._get_common_labels(device_info)

        # Voltage measurements
        mains_voltage_metric = GaugeMetricFamily(
            "mypv_voltage_mains_volts",
            "Mains voltage in volts",
            labels=common_labels,
        )
        mains_voltage_metric.add_metric(common_values, data.get("volt_mains", 0))
        yield mains_voltage_metric

        aux_voltage_metric = GaugeMetricFamily(
            "mypv_voltage_auxiliary_volts",
            "Auxiliary voltage in volts",
            labels=common_labels,
        )
        aux_voltage_metric.add_metric(common_values, data.get("volt_aux", 0))
        yield aux_voltage_metric

        # Frequency (with unit conversion: raw value / 1000 = Hz)
        freq_metric = GaugeMetricFamily(
            "mypv_frequency_hertz",
            "Mains frequency in hertz",
            labels=common_labels,
        )
        raw_freq = data.get("freq", 0)
        freq_hz = raw_freq / 1000.0 if raw_freq else 0
        freq_metric.add_metric(common_values, freq_hz)
        yield freq_metric

        # Fan speed
        fan_speed_metric = GaugeMetricFamily(
            "mypv_fan_speed_rpm",
            "Cooling fan speed in RPM",
            labels=common_labels,
        )
        fan_speed_metric.add_metric(common_values, data.get("fan_speed", 0))
        yield fan_speed_metric

    def _collect_control_metrics(
        self,
        data: dict[str, Any],
        device_info: dict[str, str],
    ) -> Iterator[GaugeMetricFamily | InfoMetricFamily]:
        """Collect control state and relay metrics.

        :param data: Device data from API.
        :type data: dict[str, Any]
        :param device_info: Device info for labels.
        :type device_info: dict[str, str]
        :return: Iterator of control metric families.
        :rtype: Iterator[GaugeMetricFamily | InfoMetricFamily]
        """
        common_labels = ["device", "instance"]
        common_values = self._get_common_labels(device_info)

        # Control state as info metric
        ctrl_state_metric = InfoMetricFamily(
            "mypv_control_state",
            "Current control state",
        )
        ctrl_state_metric.add_metric(
            [],
            {
                "state": data.get("ctrlstate", "Unknown"),
                "instance": device_info["instance"],
            },
        )
        yield ctrl_state_metric

        # Boolean control flags
        boost_active_metric = GaugeMetricFamily(
            "mypv_boost_active",
            "Boost mode active (0=inactive, 1=active)",
            labels=common_labels,
        )
        boost_active_metric.add_metric(common_values, data.get("boostactive", 0))
        yield boost_active_metric

        block_active_metric = GaugeMetricFamily(
            "mypv_block_active",
            "Block mode active (0=inactive, 1=active)",
            labels=common_labels,
        )
        block_active_metric.add_metric(common_values, data.get("blockactive", 0))
        yield block_active_metric

        # Relay states
        relay_metric = GaugeMetricFamily(
            "mypv_relay_state",
            "Relay output state (0=off, 1=on)",
            labels=common_labels + ["relay"],
        )
        relay_metric.add_metric(common_values + ["1"], data.get("rel1_out", 0))
        relay_metric.add_metric(common_values + ["selv"], data.get("rel_selv", 0))
        yield relay_metric

        # System states
        ps_state_metric = GaugeMetricFamily(
            "mypv_power_system_state",
            "Power system state code",
            labels=common_labels,
        )
        ps_state_metric.add_metric(common_values, data.get("ps_state", 0))
        yield ps_state_metric

    def _collect_system_metrics(
        self,
        data: dict[str, Any],
        device_info: dict[str, str],
    ) -> Iterator[GaugeMetricFamily | CounterMetricFamily]:
        """Collect system health and status metrics.

        :param data: Device data from API.
        :type data: dict[str, Any]
        :param device_info: Device info for labels.
        :type device_info: dict[str, str]
        :return: Iterator of system metric families.
        :rtype: Iterator[GaugeMetricFamily | CounterMetricFamily]
        """
        common_labels = ["device", "instance"]
        common_values = self._get_common_labels(device_info)

        # Uptime as counter
        uptime_metric = CounterMetricFamily(
            "mypv_uptime_seconds_total",
            "Device uptime in seconds",
            labels=common_labels,
        )
        uptime_metric.add_metric(common_values, data.get("uptime", 0))
        yield uptime_metric

        # Error and warning counts
        errors_metric = GaugeMetricFamily(
            "mypv_control_errors_total",
            "Control errors count",
            labels=common_labels,
        )
        errors_metric.add_metric(common_values, data.get("ctrl_errors", 0))
        yield errors_metric

        warnings_metric = GaugeMetricFamily(
            "mypv_warnings_total",
            "Warnings count",
            labels=common_labels,
        )
        warnings_metric.add_metric(common_values, data.get("warnings", 0))
        yield warnings_metric

        # System status flags
        screen_mode_metric = GaugeMetricFamily(
            "mypv_screen_mode",
            "Display screen mode",
            labels=common_labels,
        )
        screen_mode_metric.add_metric(common_values, data.get("screen_mode_flag", 0))
        yield screen_mode_metric

        first_setup_metric = GaugeMetricFamily(
            "mypv_first_setup",
            "First setup flag (0=complete, 1=needed)",
            labels=common_labels,
        )
        first_setup_metric.add_metric(common_values, data.get("fsetup", 0))
        yield first_setup_metric

    def _collect_network_metrics(
        self,
        data: dict[str, Any],
        device_info: dict[str, str],
    ) -> Iterator[GaugeMetricFamily | InfoMetricFamily]:
        """Collect network status and configuration metrics.

        :param data: Device data from API.
        :type data: dict[str, Any]
        :param device_info: Device info for labels.
        :type device_info: dict[str, str]
        :return: Iterator of network metric families.
        :rtype: Iterator[GaugeMetricFamily | InfoMetricFamily]
        """
        common_labels = ["device", "instance"]
        common_values = self._get_common_labels(device_info)

        # Network configuration as info metric
        network_info_metric = InfoMetricFamily(
            "mypv_network_info",
            "Network configuration information",
        )
        network_info_metric.add_metric(
            [],
            {
                "ip": data.get("cur_ip", "unknown"),
                "subnet": data.get("cur_sn", "unknown"),
                "gateway": data.get("cur_gw", "unknown"),
                "dns": data.get("cur_dns", "unknown"),
                "instance": device_info["instance"],
            },
        )
        yield network_info_metric

        # Network status metrics
        eth_mode_metric = GaugeMetricFamily(
            "mypv_ethernet_mode",
            "Ethernet mode setting",
            labels=common_labels,
        )
        eth_mode_metric.add_metric(common_values, data.get("cur_eth_mode", 0))
        yield eth_mode_metric

        wifi_signal_metric = GaugeMetricFamily(
            "mypv_wifi_signal_strength",
            "WiFi signal strength",
            labels=common_labels,
        )
        wifi_signal_metric.add_metric(common_values, data.get("wifi_signal", 0))
        yield wifi_signal_metric

        cloud_state_metric = GaugeMetricFamily(
            "mypv_cloud_connection_state",
            "Cloud connection state",
            labels=common_labels,
        )
        cloud_state_metric.add_metric(common_values, data.get("cloudstate", 0))
        yield cloud_state_metric
