"""NetBox API Configuration Module.

This module provides configuration for accessing NetBox API endpoints
from scripts and CI/CD pipelines. It supports both local development
and remote NetBox instances through environment variables.

Environment Variables:
    NETBOX_URL: NetBox API endpoint URL (default: http://localhost:8000/api/)
    NETBOX_API_TOKEN: NetBox API authentication token (required)

Example:
    >>> from nb_config import NETBOX_URL, TOKEN
    >>> print(f"Connecting to: {NETBOX_URL}")
    Connecting to: http://localhost:8000/api/

    >>> # TOKEN will be available for API authentication
"""

import os

# NetBox API endpoint URL
# Defaults to local development instance if not specified
NETBOX_URL = os.getenv("NETBOX_URL", "http://localhost:8000/api/")

# NetBox API authentication token
# This MUST be set via environment variable for security
TOKEN = os.getenv("NETBOX_API_TOKEN")

# Validate that the token is configured
assert TOKEN, (
    "NetBox API token required. Set NETBOX_API_TOKEN environment variable.\n"
    "For local development: export NETBOX_API_TOKEN='your-token-here'\n"
    "For CI/CD: Configure as a repository secret."
)
