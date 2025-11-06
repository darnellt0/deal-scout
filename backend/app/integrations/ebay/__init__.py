"""eBay integration module for OAuth and cross-posting."""

from .client import EbayClient
from .exceptions import EbayIntegrationError

__all__ = ["EbayClient", "EbayIntegrationError"]
