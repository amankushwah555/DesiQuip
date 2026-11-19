"""Affiliate link helpers. Tagged Amazon *search* links need no API and never invent a product or price.

When the Amazon Creators API unlocks (10 qualifying sales in 30 days), a product-lookup adapter can
replace the search link with exact product links behind the same service.
"""
from __future__ import annotations

from urllib.parse import quote_plus


def amazon_search_link(query: str, tag: str) -> str:
    return f"https://www.amazon.in/s?k={quote_plus(query)}&tag={tag}"


class BitlyShortener:
    def __init__(self, token: str) -> None:
        self.token = token

    def shorten(self, url: str) -> str:
        import requests
        r = requests.post("https://api-ssl.bitly.com/v4/shorten", json={"long_url": url}, timeout=30,
                          headers={"Authorization": f"Bearer {self.token}"})
        r.raise_for_status()
        return r.json()["link"]
