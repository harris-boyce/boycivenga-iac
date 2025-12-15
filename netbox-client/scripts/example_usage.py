#!/usr/bin/env python3
"""Example script demonstrating NetBox API configuration usage.

This script shows how to use the nb_config module to connect to NetBox
and make API requests. It can be used as a template for other scripts.
"""

from nb_config import NETBOX_URL, TOKEN

# Example: Print configuration (for testing only)
if __name__ == "__main__":
    print("NetBox Configuration:")
    print(f"  URL: {NETBOX_URL}")
    # Safely mask token, showing only last 4 chars if available
    masked_token = "*" * 10 + (TOKEN[-4:] if len(TOKEN) >= 4 else TOKEN)
    print(f"  Token: {masked_token}")
    print("\nConfiguration loaded successfully!")
    print("You can now use NETBOX_URL and TOKEN to make API requests.")
