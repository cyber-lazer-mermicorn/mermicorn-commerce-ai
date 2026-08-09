"""
Marketplace Integrations — Real API Connections
=================================================
Connects to live marketplace APIs for listings, prices, and inventory.
"""

import os
import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Listing:
    """Marketplace listing."""
    id: str
    title: str
    price: float
    url: str
    source: str
    image: str = ""
    description: str = ""
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "price": self.price,
            "url": self.url, "source": self.source, "image": self.image,
            "description": self.description, "metadata": self.metadata,
        }


class ShopifyIntegration:
    """Shopify Store API."""
    
    def __init__(self):
        self.shop = os.environ.get("SHOPIFY_SHOP", "")
        self.token = os.environ.get("SHOPIFY_ACCESS_TOKEN", "")
        self.base = f"https://{self.shop}/admin/api/2024-01"
    
    def is_configured(self) -> bool:
        return bool(self.shop and self.token)
    
    def _request(self, path: str) -> dict:
        req = urllib.request.Request(
            f"{self.base}{path}",
            headers={"X-Shopify-Access-Token": self.token, "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    
    def list_products(self, limit: int = 50) -> list[Listing]:
        if not self.is_configured():
            return []
        data = self._request(f"/products.json?limit={limit}")
        return [
            Listing(
                id=str(p["id"]), title=p["title"],
                price=float(p["variants"][0]["price"]),
                url=f"https://{self.shop}/products/{p['handle']}",
                source="shopify",
                image=p["image"]["src"] if p.get("image") else "",
                description=p.get("body_html", "")[:200],
            )
            for p in data.get("products", [])
        ]


class EtsyIntegration:
    """Etsy API."""
    
    def __init__(self):
        self.api_key = os.environ.get("ETSY_API_KEY", "")
        self.base = "https://openapi.etsy.com/v3/application"
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def _request(self, path: str) -> dict:
        req = urllib.request.Request(
            f"{self.base}{path}",
            headers={"x-api-key": self.api_key, "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    
    def search_listings(self, keywords: str, limit: int = 25) -> list[Listing]:
        if not self.is_configured():
            return []
        data = self._request(f"/listings/active?keywords={keywords}&limit={limit}")
        return [
            Listing(
                id=str(l["listing_id"]), title=l["title"],
                price=float(l["price"]["amount"]) / 100,
                url=l["url"],
                source="etsy",
                image=l.get("images", [{}])[0].get("url_170x135", "") if l.get("images") else "",
                description=l.get("description", "")[:200],
            )
            for l in data.get("results", [])
        ]


class EbayIntegration:
    """eBay Browse API."""
    
    def __init__(self):
        self.app_id = os.environ.get("EBAY_APP_ID", "")
        self.base = "https://api.ebay.com/buy/browse/v1"
    
    def is_configured(self) -> bool:
        return bool(self.app_id)
    
    def _request(self, path: str) -> dict:
        req = urllib.request.Request(
            f"{self.base}{path}",
            headers={"X-EBAY-C-MARKETPLACE-ID": "EBAY_US", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    
    def search_items(self, query: str, limit: int = 25) -> list[Listing]:
        if not self.is_configured():
            return []
        data = self._request(f"/item_summary/search?q={query}&limit={limit}")
        return [
            Listing(
                id=i["itemId"], title=i["title"],
                price=float(i["price"]["value"]),
                url=i["itemWebUrl"],
                source="ebay",
                image=i.get("thumbnailImages", [{}])[0].get("imageUrl", "") if i.get("thumbnailImages") else "",
            )
            for i in data.get("itemSummaries", [])
        ]


class CoinMarketIntegrations:
    """Numismatic-specific integrations."""
    
    def __init__(self):
        self.pcgs_key = os.environ.get("PCGS_API_KEY", "")
        self.ngc_key = os.environ.get("NGC_API_KEY", "")
    
    def get_pcgs_price(self, coin_name: str, grade: str) -> Optional[dict]:
        if not self.pcgs_key:
            return None
        try:
            url = f"https://api.pcgs.com/prices/{coin_name}?grade={grade}"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.pcgs_key}"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except Exception:
            return None


class AutoMarketIntegrations:
    """Vehicle-specific integrations."""
    
    def __init__(self):
        self.kbb_key = os.environ.get("KBB_API_KEY", "")
        self.edmunds_key = os.environ.get("EDMUNDS_API_KEY", "")
    
    def get_kbb_value(self, year: int, make: str, model: str) -> Optional[dict]:
        if not self.kbb_key:
            return None
        try:
            url = f"https://api.kbb.com/vehicle-value?year={year}&make={make}&model={model}"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.kbb_key}"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except Exception:
            return None


class TravelIntegrations:
    """Travel-specific integrations."""
    
    def __init__(self):
        self.skyscanner_key = os.environ.get("SKYSCANNER_API_KEY", "")
    
    def search_flights(self, origin: str, destination: str) -> list[Listing]:
        if not self.skyscanner_key:
            return []
        try:
            url = f"https://api.skyscanner.net/flights/browse/v1.0/{origin}/{destination}"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.skyscanner_key}"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                return [
                    Listing(
                        id=f"flight_{i}", title=f"{origin} → {destination}",
                        price=float(f.get("price", 0)),
                        url=f"https://skyscanner.com",
                        source="skyscanner",
                    )
                    for i, f in enumerate(data.get("quotes", []))
                ]
        except Exception:
            return []


class MarketplaceManager:
    """Unified marketplace manager."""
    
    def __init__(self):
        self.shopify = ShopifyIntegration()
        self.etsy = EtsyIntegration()
        self.ebay = EbayIntegration()
        self.coins = CoinMarketIntegrations()
        self.auto = AutoMarketIntegrations()
        self.travel = TravelIntegrations()
    
    def get_status(self) -> dict:
        return {
            "shopify": self.shopify.is_configured(),
            "etsy": self.etsy.is_configured(),
            "ebay": self.ebay.is_configured(),
            "pcgs": bool(self.coins.pcgs_key),
            "kbb": bool(self.auto.kbb_key),
            "skyscanner": bool(self.travel.skyscanner_key),
        }
    
    def search_all(self, query: str) -> list[Listing]:
        """Search across all configured marketplaces."""
        results = []
        results.extend(self.shopify.list_products())
        results.extend(self.etsy.search_listings(query))
        results.extend(self.ebay.search_items(query))
        return results
