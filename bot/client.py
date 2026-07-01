"""Binance Futures Testnet client initialization."""

import os
from pathlib import Path

from binance.client import Client
from dotenv import load_dotenv

FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"
FUTURES_TESTNET_API_URL = f"{FUTURES_TESTNET_BASE_URL}/fapi"
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

API_KEY_ENV = "API_KEY"
API_SECRET_ENV = "API_SECRET"


class CredentialError(Exception):
    """Raised when required API credentials are missing."""


def load_credentials() -> tuple[str, str]:
    """Load API credentials from environment variables."""
    load_dotenv(ENV_PATH)

    api_key = os.getenv(API_KEY_ENV, "").strip()
    api_secret = os.getenv(API_SECRET_ENV, "").strip()

    missing = [
        name
        for name, value in ((API_KEY_ENV, api_key), (API_SECRET_ENV, api_secret))
        if not value
    ]
    if missing:
        raise CredentialError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Set them in a .env file at the project root."
        )

    return api_key, api_secret


def create_futures_client() -> Client:
    """Create and configure a Binance USD-M Futures Testnet client."""
    api_key, api_secret = load_credentials()

    client = Client(api_key=api_key, api_secret=api_secret, testnet=True)
    # Explicit testnet URL per assignment; matches python-binance default.
    client.FUTURES_TESTNET_URL = FUTURES_TESTNET_API_URL

    return client
