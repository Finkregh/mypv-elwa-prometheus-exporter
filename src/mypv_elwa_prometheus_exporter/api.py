#!/usr/bin/env python3
"""MyPV API Client for AC ELWA devices

This module provides the MyPVAPI class for communicating with my-PV AC ELWA
devices via their HTTP JSON API.
"""

import json
import logging
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

log = logging.getLogger(__name__)


class MyPVAPI:
    """Client for interacting with my-PV AC ELWA device API."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 10,
    ) -> None:
        """Initialize the my-PV API client.

        :param base_url: The base URL of the device (e.g. http://192.168.1.125).
        :type base_url: str
        :param timeout: Request timeout in seconds. Default is 10 seconds.
        :type timeout: int
        """
        self.base_url = self._normalize_url(base_url)
        self.timeout = timeout
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "mypv-elwa-prometheus-exporter/1.0.0",
        }

        # Extract instance identifier from URL
        parsed = urlparse(self.base_url)
        self.instance = parsed.netloc or parsed.path.strip("/")

    def _normalize_url(self, url: str) -> str:
        """Normalize device URL to ensure proper format.

        :param url: The input URL.
        :type url: str
        :return: Normalized URL.
        :rtype: str
        """
        if not url.startswith(("http://", "https://")):
            url = f"http://{url}"
        return url.rstrip("/")

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
    ) -> dict[str, Any]:
        """Make HTTP request to device API.

        :param endpoint: The API endpoint to request.
        :type endpoint: str
        :param method: The HTTP method to use.
        :type method: str
        :return: The JSON response from the API.
        :rtype: Dict[str, Any]
        :raises requests.exceptions.RequestException: If request fails.
        :raises json.JSONDecodeError: If response is not valid JSON.
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        log.debug(f"Making {method} request to: {url}")

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()

            log.debug(f"Request successful: {response.status_code}")
            return response.json()

        except requests.exceptions.HTTPError:
            log.exception("HTTP Error %s for %s", response.status_code, url)
            raise
        except requests.exceptions.ConnectTimeout:
            log.critical("Connection Timeout for %s", url)
            raise
        except requests.exceptions.Timeout:
            log.critical("Timeout Error for %s", url)
            raise
        except requests.exceptions.RequestException:
            log.critical("Request Error for %s", url)
            raise
        except json.JSONDecodeError:
            log.critical("JSON decode error for response from %s", url)
            raise

    def get_data(self) -> dict[str, Any]:
        """Get device data from /data.jsn endpoint.

        :return: Dictionary containing device data.
        :rtype: Dict[str, Any]
        :raises requests.exceptions.RequestException: If request fails.
        """
        return self._make_request("/data.jsn")

    def test_connection(self) -> bool:
        """Test connection to device.

        :return: True if device is reachable and returns valid data.
        :rtype: bool
        """
        try:
            data = self.get_data()
            # Basic validation - check for expected device fields
            required_fields = ["device", "fwversion"]
            return all(field in data for field in required_fields)
        except Exception as e:
            log.debug(f"Connection test failed for {self.base_url}: {e}")
            return False

    def get_device_info(self) -> dict[str, str]:
        """Get device information for labeling.

        :return: Dictionary with device info for labels.
        :rtype: Dict[str, str]
        """
        try:
            data = self.get_data()
            return {
                "device": data.get("device", "unknown"),
                "firmware_version": data.get("fwversion", "unknown"),
                "power_system_version": data.get("psversion", "unknown"),
                "control_version": data.get("coversion", "unknown"),
                "instance": self.instance,
            }
        except Exception as e:
            log.warning(f"Failed to get device info from {self.base_url}: {e}")
            return {
                "device": "unknown",
                "firmware_version": "unknown",
                "power_system_version": "unknown",
                "control_version": "unknown",
                "instance": self.instance,
            }
