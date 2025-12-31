"""UniFi API client wrapper for integration testing.

Provides a simplified interface to the UniFi controller API for creating,
reading, updating, and deleting network resources during tests.
"""

import os
from typing import Any, Dict, List, Optional

import requests
import urllib3

# Disable SSL warnings for self-signed UniFi certificates in tests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class UniFiClient:
    """Client for interacting with UniFi controller API."""

    def __init__(
        self,
        url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize UniFi client with credentials.

        Args:
            url: UniFi controller URL
                (defaults to UNIFI_CONTROLLER_URL or UNIFI_TEST_CONTROLLER_URL)
            username: Admin username
                (defaults to UNIFI_USERNAME or TF_VAR_unifi_username)
            password: Admin password
                (defaults to UNIFI_PASSWORD or TF_VAR_unifi_password)

        Note:
            Prefers UNIFI_* environment variables,
            falls back to TF_VAR_* for backward compatibility.
        """
        # Prefer UNIFI_* variables, fall back to TF_VAR_* for backward compatibility
        self.url = (
            url
            or os.getenv("UNIFI_CONTROLLER_URL")
            or os.getenv("UNIFI_TEST_CONTROLLER_URL")
            or "https://localhost:8443"
        )
        self.username = (
            username
            or os.getenv("UNIFI_USERNAME")
            or os.getenv("TF_VAR_unifi_username")
            or "admin"
        )
        self.password = (
            password
            or os.getenv("UNIFI_PASSWORD")
            or os.getenv("TF_VAR_unifi_password")
            or "unifi-integration-test-password"
        )

        self.session = requests.Session()
        self.session.verify = False  # Allow self-signed certificates in tests

        self._csrf_token: Optional[str] = None
        self._logged_in = False

    def login(self) -> None:
        """Authenticate with UniFi controller."""
        login_url = f"{self.url}/api/login"
        payload = {"username": self.username, "password": self.password}

        response = self.session.post(login_url, json=payload)
        response.raise_for_status()

        # Extract CSRF token from response
        self._csrf_token = response.headers.get("X-CSRF-Token")
        self._logged_in = True

    def _ensure_logged_in(self) -> None:
        """Ensure client is logged in before making API calls."""
        if not self._logged_in:
            self.login()

    def get_sites(self) -> List[Dict[str, Any]]:
        """Get list of sites from UniFi controller.

        Returns:
            List of site dictionaries
        """
        self._ensure_logged_in()

        response = self.session.get(f"{self.url}/api/self/sites")
        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

    def get_networks(self, site: str = "default") -> List[Dict[str, Any]]:
        """Get list of networks for a site.

        Args:
            site: Site name (default: "default")

        Returns:
            List of network dictionaries
        """
        self._ensure_logged_in()

        response = self.session.get(f"{self.url}/api/s/{site}/rest/networkconf")
        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

    def create_network(
        self, name: str, vlan_id: Optional[int] = None, site: str = "default"
    ) -> Dict[str, Any]:
        """Create a new network.

        Args:
            name: Network name
            vlan_id: VLAN ID (optional)
            site: Site name (default: "default")

        Returns:
            Created network dictionary
        """
        self._ensure_logged_in()

        payload = {
            "name": name,
            "purpose": "corporate",
            "networkgroup": "LAN",
        }

        if vlan_id is not None:
            payload["vlan_enabled"] = True
            payload["vlan"] = vlan_id

        headers = {}
        if self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token

        response = self.session.post(
            f"{self.url}/api/s/{site}/rest/networkconf", json=payload, headers=headers
        )
        response.raise_for_status()

        data = response.json()
        return data.get("data", [{}])[0]

    def delete_network(self, network_id: str, site: str = "default") -> None:
        """Delete a network by ID.

        Args:
            network_id: Network ID to delete
            site: Site name (default: "default")
        """
        self._ensure_logged_in()

        headers = {}
        if self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token

        response = self.session.delete(
            f"{self.url}/api/s/{site}/rest/networkconf/{network_id}", headers=headers
        )
        response.raise_for_status()

    def update_network(
        self, network_id: str, config: Dict[str, Any], site: str = "default"
    ) -> Dict[str, Any]:
        """Update an existing network.

        Args:
            network_id: Network ID to update
            config: Network configuration dictionary
            site: Site name (default: "default")

        Returns:
            Updated network dictionary
        """
        self._ensure_logged_in()

        headers = {}
        if self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token

        response = self.session.put(
            f"{self.url}/api/s/{site}/rest/networkconf/{network_id}",
            json=config,
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        result_data = data.get("data", [])
        if isinstance(result_data, list) and len(result_data) > 0:
            return result_data[0]
        else:
            # If update doesn't return data, query to get the updated network
            networks = self.get_networks(site)
            return next((net for net in networks if net["_id"] == network_id), config)

    def find_network_by_name(
        self, name: str, site: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """Find a network by name.

        Args:
            name: Network name to search for
            site: Site name (default: "default")

        Returns:
            Network dictionary if found, None otherwise
        """
        networks = self.get_networks(site)
        return next((net for net in networks if net.get("name") == name), None)

    def find_network_by_vlan(
        self, vlan_id: int, site: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """Find a network by VLAN ID.

        Args:
            vlan_id: VLAN ID to search for
            site: Site name (default: "default")

        Returns:
            Network dictionary if found, None otherwise
        """
        networks = self.get_networks(site)
        return next((net for net in networks if net.get("vlan") == vlan_id), None)

    def create_or_update_network(
        self, config: Dict[str, Any], site: str = "default"
    ) -> Dict[str, Any]:
        """Create or update a network (idempotent operation).

        Checks if network exists by name. If it exists, updates it.
        If it doesn't exist, creates it.

        Args:
            config: Network configuration dictionary (must include 'name')
            site: Site name (default: "default")

        Returns:
            Network dictionary (created or updated)
        """
        name = config.get("name")
        if not name:
            raise ValueError("Network config must include 'name' field")

        existing = self.find_network_by_name(name, site)

        if existing:
            # Update existing network
            network_id = existing["_id"]
            # Merge existing config with updates
            updated_config = {**existing, **config}
            return self.update_network(network_id, updated_config, site)
        else:
            # Create new network
            headers = {}
            if self._csrf_token:
                headers["X-CSRF-Token"] = self._csrf_token

            response = self.session.post(
                f"{self.url}/api/s/{site}/rest/networkconf",
                json=config,
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            result_data = data.get("data", [])
            if isinstance(result_data, list) and len(result_data) > 0:
                return result_data[0]
            else:
                # If no data returned, query to get the created network
                return self.find_network_by_name(name, site) or config

    def delete_network_by_name(self, name: str, site: str = "default") -> bool:
        """Delete a network by name.

        Args:
            name: Network name to delete
            site: Site name (default: "default")

        Returns:
            True if network was found and deleted, False otherwise
        """
        networks = self.get_networks(site)

        for network in networks:
            if network.get("name") == name:
                self.delete_network(network["_id"], site)
                return True

        return False

    def cleanup_test_networks(self, site: str = "default") -> int:
        """Delete all networks with names starting with 'test-'.

        Useful for cleaning up orphaned test resources.

        Args:
            site: Site name (default: "default")

        Returns:
            Number of networks deleted
        """
        networks = self.get_networks(site)
        deleted_count = 0

        for network in networks:
            name = network.get("name", "")
            if name.startswith("test-"):
                try:
                    self.delete_network(network["_id"], site)
                    deleted_count += 1
                except Exception as e:
                    print(f"Warning: Failed to delete network {name}: {e}")

        return deleted_count

    def logout(self) -> None:
        """Logout from UniFi controller."""
        if self._logged_in:
            try:
                self.session.post(f"{self.url}/api/logout")
            except Exception:
                pass  # Best effort, ignore errors
            finally:
                self._logged_in = False

    def __enter__(self):
        """Context manager entry."""
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.logout()
