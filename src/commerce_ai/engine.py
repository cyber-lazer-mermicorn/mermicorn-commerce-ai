"""
Mermicorn Commerce AI — Product → Listing → Sales Package
=========================================================
Turns product data into market-ready listings.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass(slots=True)
class Product:
    """A product to be listed."""
    id: str
    name: str
    description: str
    price: float
    currency: str = "USD"
    category: str = ""
    images: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "currency": self.currency,
            "category": self.category,
            "images": self.images,
            "features": self.features,
            "tags": self.tags,
        }


@dataclass(slots=True)
class Listing:
    """A market-ready listing."""
    product: Product
    title: str
    headline: str
    bullets: list[str]
    seo_description: str
    marketplace: str
    formatted_price: str
    cta: str = "Shop Now"
    created_at: float = field(default_factory=time.time)
    
    def to_html(self) -> str:
        """Generate HTML for this listing."""
        bullets_html = "".join(f"<li>{b}</li>" for b in self.bullets)
        
        return f"""<article class="listing" data-marketplace="{self.marketplace}">
  <header>
    <h2>{self.title}</h2>
    <p class="headline">{self.headline}</p>
  </header>
  <div class="price">{self.formatted_price}</div>
  <ul class="features">{bullets_html}</ul>
  <p class="description">{self.product.description}</p>
  <button class="cta">{self.cta}</button>
</article>"""


class CommerceAI:
    """
    Mermicorn Commerce Engine
    
    Product pipeline:
    1. Intake product data
    2. Generate optimized listings
    3. Format for marketplaces
    4. Track performance
    """
    
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.products: list[Product] = []
        self.listings: list[Listing] = []
    
    def add_product(
        self,
        name: str,
        description: str,
        price: float,
        category: str = "",
        features: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> Product:
        """Add a product to the catalog."""
        product_id = hashlib.sha256(
            f"{name}:{description}:{price}".encode()
        ).hexdigest()[:12]
        
        product = Product(
            id=product_id,
            name=name,
            description=description,
            price=price,
            category=category,
            features=features or [],
            tags=tags or [],
        )
        self.products.append(product)
        return product
    
    def generate_listing(
        self,
        product: Product,
        marketplace: str = "general",
    ) -> Listing:
        """Generate an optimized listing for a product."""
        # Generate SEO-optimized title
        title = f"{product.name} — {product.category}" if product.category else product.name
        
        # Generate headline
        headline = f"Premium {product.name} for the modern lifestyle"
        
        # Generate bullets from features
        bullets = product.features[:5] if product.features else [
            f"High-quality {product.name}",
            "Fast shipping & easy returns",
            "Cherry-approved quality",
        ]
        
        # SEO description
        seo = f"{product.name}: {product.description[:150]}"
        
        # Format price
        formatted = f"${product.price:.2f}"
        
        listing = Listing(
            product=product,
            title=title,
            headline=headline,
            bullets=bullets,
            seo_description=seo,
            marketplace=marketplace,
            formatted_price=formatted,
        )
        self.listings.append(listing)
        return listing
    
    def export_listing(self, listing: Listing) -> str:
        """Export a listing to HTML file."""
        filename = f"listing-{listing.product.id}.html"
        filepath = self.output_dir / filename
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{listing.title}</title>
    <meta name="description" content="{listing.seo_description}">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', system-ui, sans-serif; background: #0a0a0f; color: #fff; }}
        .listing {{ max-width: 600px; margin: 2rem auto; padding: 2rem; background: #1a1a2e; border-radius: 16px; }}
        h2 {{ font-size: 1.5rem; margin-bottom: 0.5rem; }}
        .headline {{ color: #C44DFF; font-size: 0.9rem; margin-bottom: 1rem; }}
        .price {{ font-size: 2rem; font-weight: 700; color: #FF6B9D; margin: 1rem 0; }}
        .features {{ margin: 1rem 0; padding-left: 1.5rem; }}
        .features li {{ margin: 0.5rem 0; color: #ccc; }}
        .description {{ color: #888; margin: 1rem 0; line-height: 1.6; }}
        .cta {{ background: linear-gradient(135deg, #FF6B9D, #C44DFF); color: #fff; border: none; padding: 1rem 2rem; border-radius: 999px; font-size: 1rem; cursor: pointer; width: 100%; }}
        .cta:hover {{ transform: scale(1.02); }}
    </style>
</head>
<body>
{listing.to_html()}
</body>
</html>"""
        
        filepath.write_text(html)
        return str(filepath)
    
    def generate_catalog(self) -> str:
        """Generate a full product catalog."""
        items = ""
        for listing in self.listings:
            items += f"""
    <div class="catalog-item">
      <h3>{listing.title}</h3>
      <p class="price">{listing.formatted_price}</p>
      <p>{listing.headline}</p>
    </div>"""
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cherry's Catalog</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', system-ui, sans-serif; background: #0a0a0f; color: #fff; padding: 2rem; }}
        h1 {{ text-align: center; margin-bottom: 2rem; background: linear-gradient(135deg, #FF6B9D, #C44DFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .catalog {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }}
        .catalog-item {{ background: #1a1a2e; padding: 1.5rem; border-radius: 16px; border: 1px solid #333; }}
        .catalog-item:hover {{ border-color: #C44DFF; transform: translateY(-2px); }}
        .price {{ color: #FF6B9D; font-size: 1.25rem; font-weight: 700; margin: 0.5rem 0; }}
    </style>
</head>
<body>
    <h1>🍒 Cherry's Catalog</h1>
    <div class="catalog">{items}
    </div>
</body>
</html>"""
    
    def get_stats(self) -> dict[str, Any]:
        """Get commerce statistics."""
        return {
            "products": len(self.products),
            "listings": len(self.listings),
            "total_value": sum(p.price for p in self.products),
            "categories": list(set(p.category for p in self.products if p.category)),
        }


# Standalone usage
if __name__ == "__main__":
    commerce = CommerceAI()
    
    print("🛒 Mermicorn Commerce AI")
    
    # Add sample products
    p1 = commerce.add_product(
        name="Cherry Rave Top",
        description="Premium rave wear top with LED-compatible fabric",
        price=89.99,
        category="Ravewear",
        features=["UV-reactive fabric", "Breathable mesh", "LED pocket"],
    )
    
    p2 = commerce.add_product(
        name="Mermicorn Pendant",
        description="Sterling silver mermaid unicorn pendant",
        price=149.99,
        category="Jewelry",
        features=["925 sterling silver", "Handcrafted", "Gift box included"],
    )
    
    # Generate listings
    listing1 = commerce.generate_listing(p1, "shopify")
    listing2 = commerce.generate_listing(p2, "etsy")
    
    # Export
    commerce.export_listing(listing1)
    commerce.export_listing(listing2)
    
    print(f"   Products: {commerce.get_stats()['products']}")
    print(f"   Listings: {commerce.get_stats()['listings']}")
    print(f"   Total Value: ${commerce.get_stats()['total_value']:.2f}")
    print()
    print("Generated listings in ./output/")
