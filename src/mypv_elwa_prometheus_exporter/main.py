#!/usr/bin/env python3
"""my-PV AC ELWA Prometheus Exporter.

This script exports my-PV AC ELWA device statistics as Prometheus metrics.
It collects data about power consumption, temperatures, electrical system status,
and device health.
"""

import logging
import time

import typer
from prometheus_client import REGISTRY, Info, start_http_server
from rich.console import Console
from rich.logging import RichHandler

from mypv_elwa_prometheus_exporter.api import MyPVAPI
from mypv_elwa_prometheus_exporter.collector import MyPVCollector

app = typer.Typer(
    help="my-PV AC ELWA Prometheus Exporter - Export device statistics as Prometheus metrics",
    context_settings={"auto_envvar_prefix": "MYPVELWAEXPORTER"},
)

# Global logger - will be configured in setup_logging()
log = logging.getLogger(__name__)


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    *,
    use_stderr: bool = True,
) -> None:
    """Setup logging configuration.

    :param level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    :type level: str
    :param log_file: Optional log file path
    :type log_file: str | None
    :param use_stderr: Whether to log to stderr (default) or stdout
    :type use_stderr: bool
    """
    # Clear any existing handlers
    for handler in log.handlers[:]:
        log.removeHandler(handler)

    # Set logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    log.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        log.addHandler(file_handler)
    else:
        # Add console handler
        console = Console(stderr=use_stderr)
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
        )
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        log.addHandler(console_handler)


def parse_urls(url_str: str) -> list[str]:
    """Parse comma-separated device URLs.

    :param url_str: Comma-separated device URLs
    :type url_str: str
    :return: List of device URLs
    :rtype: list[str]
    """
    return [url.strip() for url in url_str.split(",") if url.strip()]


@app.command()
def serve(
    url: str = typer.Option(
        ...,
        "--url",
        "-u",
        help="Device URL(s) - comma separated for multiple devices (e.g., http://192.168.178.125,http://192.168.178.126)",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to serve metrics on",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
    log_file: str | None = typer.Option(
        None,
        "--log-file",
        help="Log file path (default: stderr)",
    ),
) -> None:
    """Start HTTP server to serve my-PV AC ELWA metrics in Prometheus format.

    :param url: Device URL(s) - comma separated for multiple devices.
    :type url: str
    :param port: Port to serve metrics on.
    :type port: int
    :param log_level: Logging level.
    :type log_level: str
    :param log_file: Optional log file path.
    :type log_file: str | None
    :raises typer.Exit: If required parameters are missing or server fails to start.
    """
    # Setup logging
    setup_logging(level=log_level, log_file=log_file, use_stderr=True)

    log.info("Starting my-PV AC ELWA Prometheus Exporter HTTP Server")
    log.info("Device URLs: %s", url)
    log.info("Serving metrics on port: %s", port)
    log.info("Log level: %s", log_level)
    if log_file:
        log.info("Logging to file: %s", log_file)
    else:
        log.info("Logging to stderr")

    try:
        # Parse device URLs
        device_urls = parse_urls(url)
        log.info("Found %d device(s) to monitor", len(device_urls))

        # Initialize API clients
        apis = []
        for device_url in device_urls:
            api = MyPVAPI(device_url)
            if api.test_connection():
                apis.append(api)
                log.info("Successfully connected to device at %s", device_url)
            else:
                log.warning("Failed to connect to device at %s", device_url)

        if not apis:
            log.error("No devices are reachable")
            raise typer.Exit(1)

        # Initialize and register collector
        collector = MyPVCollector(apis)
        REGISTRY.register(collector)
        log.info("Registered my-PV collector")

        # Add exporter info
        info = Info("mypv_exporter", "my-PV AC ELWA Prometheus Exporter")
        info.info({"version": "1.0.0", "devices": str(len(apis))})

        # Start HTTP server
        start_http_server(port)
        log.info("HTTP server started on port %s", port)
        log.info("Metrics available at http://localhost:%s/metrics", port)
        log.info("Press Ctrl+C to stop")

        # Keep the server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Server stopped by user")

    except Exception as e:
        log.error("Error starting server: %s", e)
        raise typer.Exit(1)


@app.command()
def export(
    url: str = typer.Option(
        ...,
        "--url",
        "-u",
        help="Device URL(s) - comma separated for multiple devices (e.g., http://192.168.178.125)",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file (default: stdout)",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
) -> None:
    """Export my-PV AC ELWA metrics in Prometheus format once.

    :param url: Device URL(s) - comma separated for multiple devices.
    :type url: str
    :param output: Optional output file path. If not provided, outputs to stdout.
    :type output: str | None
    :param log_level: Logging level.
    :type log_level: str
    :raises typer.Exit: If required parameters are missing or export fails.
    """
    # Setup logging to stderr to avoid mixing with metrics output
    setup_logging(level=log_level, use_stderr=True)

    log.info("Starting my-PV AC ELWA metrics export")
    log.info("Device URLs: %s", url)

    try:
        # Parse device URLs
        device_urls = parse_urls(url)

        # Initialize API clients and test connections
        apis = []
        for device_url in device_urls:
            api = MyPVAPI(device_url)
            if api.test_connection():
                apis.append(api)
                log.info("Connected to device at %s", device_url)
            else:
                log.warning("Failed to connect to device at %s", device_url)

        if not apis:
            log.error("No devices are reachable")
            raise typer.Exit(1)

        # Collect metrics manually
        collector = MyPVCollector(apis)

        # Build Prometheus output
        output_lines = []
        for metric_family in collector.collect():
            # Add help and type comments
            output_lines.append(
                f"# HELP {metric_family.name} {metric_family.documentation}"
            )
            output_lines.append(f"# TYPE {metric_family.name} {metric_family.type}")

            # Add metric samples
            for sample in metric_family.samples:
                if sample.labels:
                    label_str = (
                        "{"
                        + ",".join(f'{k}="{v}"' for k, v in sample.labels.items())
                        + "}"
                    )
                else:
                    label_str = ""
                output_lines.append(f"{sample.name}{label_str} {sample.value}")

        metrics_output = "\n".join(output_lines) + "\n"

        # Output metrics
        if output:
            with open(output, "w") as f:
                f.write(metrics_output)
            log.info("Metrics exported to %s", output)
        else:
            print(metrics_output)

        log.info("Export completed successfully")

    except Exception as e:
        log.error("Error during export: %s", e)
        raise typer.Exit(1)


@app.command()
def test_connection(
    url: str = typer.Option(
        ..., "--url", "-u", help="Device URL (e.g., http://192.168.178.125)"
    ),
) -> None:
    """Test connection to my-PV AC ELWA device.

    Verifies that the provided URL can successfully connect to the device
    and that the device returns valid data.

    :param url: The device URL.
    :type url: str
    :raises typer.Exit: If connection fails.
    """
    try:
        api = MyPVAPI(url)

        # Test basic connectivity
        data = api.get_data()
        typer.echo("✅ Connection successful!")
        typer.echo(f"Device: {data.get('device', 'Unknown')}")
        typer.echo(f"Firmware: {data.get('fwversion', 'Unknown')}")
        typer.echo(f"Power (ELWA): {data.get('power_elwa2', 0)}W")
        typer.echo(f"Temperature 1: {data.get('temp1', 0) / 10:.1f}°C")
        typer.echo(f"Temperature 2: {data.get('temp2', 0) / 10:.1f}°C")

        device_info = api.get_device_info()
        typer.echo(f"Instance: {device_info['instance']}")

    except Exception as e:
        typer.echo(f"❌ Connection failed: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
