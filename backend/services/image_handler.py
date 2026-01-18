"""
image_handler.py

Simple helper to extract article images for the demo.
Prioritizes reliability and speed over perfect scraping.
"""

import re
import requests
from typing import Optional

# --- CONFIGURATION ---

# Fallback logos for known sources (Hackathon/Demo URLs)
SOURCE_LOGOS = {
    "Fox News": "https://upload.wikimedia.org/wikipedia/commons/6/67/Fox_News_Channel_logo.svg",
    "CNN": "https://upload.wikimedia.org/wikipedia/commons/b/b1/CNN.svg",
    "MSNBC": "https://upload.wikimedia.org/wikipedia/commons/a/a2/MSNBC_Logo.svg",
    "Reuters": "https://upload.wikimedia.org/wikipedia/commons/8/8d/Reuters_Logo.svg",
    "Breitbart": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Breitbart_News.svg/1200px-Breitbart_News.svg.png",
    "BBC": "https://upload.wikimedia.org/wikipedia/commons/e/EB/BBC.svg",
    "NPR": "https://upload.wikimedia.org/wikipedia/commons/d/d7/National_Public_Radio_logo.svg",
    "AP News": "https://upload.wikimedia.org/wikipedia/commons/0/0c/Associated_Press_logo_2012.svg",
    "The Guardian": "https://upload.wikimedia.org/wikipedia/commons/7/75/The_Guardian_2018.svg",
    # Generic fallback
    "default": "https://placehold.co/600x400?text=News+Article"
}

# Simple in-memory cache to avoid banging APIs
_IMAGE_CACHE = {}

def get_article_image(article_url: str, source_name: str) -> str:
    """
    Determines the best image to show for an article.
    
    Strategy:
    1. Check cache.
    2. Try to scrape 'og:image' metadata from the URL.
    3. Fallback to Source Logo.
    4. Fallback to Generic Placeholder.
    
    Args:
        article_url (str): The link to the article.
        source_name (str): The name of the publisher (e.g. "CNN").
        
    Returns:
        str: A valid image URL (never None).
    """
    
    # 1. Check Cache
    cache_key = (article_url, source_name)
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]
        
    # 2. Attempt Extraction (Lightweight Regex)
    image_url = None
    
    # Only attempt scrape if it looks like a real URL
    if article_url and article_url.startswith("http"):
        try:
            # Set timeout to strictly avoid hanging the demo
            response = requests.get(article_url, timeout=2.0, headers={"User-Agent": "HackathonDemoBot/1.0"})
            if response.status_code == 200:
                # Regex for <meta property="og:image" content="..." />
                match = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', response.text, re.IGNORECASE)
                if match:
                    image_url = match.group(1)
        except Exception:
            # Ignore ALL errors (timeout, conn refused, ssl, etc.) for demo stability
            pass

    # 3. Fallback Logic
    if not image_url:
        # Try to find a logo for the source
        # Fuzzy match or exact match keys
        for key, logo in SOURCE_LOGOS.items():
            if key.lower() in source_name.lower():
                image_url = logo
                break
    
    # 4. Ultimate Fallback
    if not image_url:
        image_url = SOURCE_LOGOS["default"]
        
    # Update Cache
    _IMAGE_CACHE[cache_key] = image_url
    
    return image_url
