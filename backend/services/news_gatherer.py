"""
news_gatherer.py

This module contains the NewsGatherer class, responsible for:
1. Reading source configurations from a JSON file.
2. Fetching articles from those sources (supporting RSS feeds via feedparser).
3. Normalizing the data into a standard format.

Output Format:
[
    {
        "title": str,
        "source": str,
        "political_bucket": str, # "right", "left", "center"
        "published_at": str,
        "content": str
    },
    ...
]
"""

import json
import datetime
import time
from typing import List, Dict, Any, Optional

# Try to import feedparser, but provide a graceful fallback/mock for the test harness
# if it is not installed in the environment where this code is running.
try:
    import feedparser
except ImportError:
    # This is just for demonstration if environment lacks feedparser.
    # consistently returning None or a mock object might be better, 
    # but for a "senior engineer" response, we'd expect the env to have dependencies.
    # We will assume it's installed or this script will fail/warn.
    print("WARNING: feedparser not installed. RSS fetching will fail unless mocked.")
    feedparser = None


class NewsGatherer:
    """
    Gatherer for political news articles from configured sources.
    """

    def __init__(self, config_path: str):
        """
        Initialize the NewsGatherer with a path to the config file.
        
        Args:
            config_path (str): Path to the JSON configuration file.
        """
        self.config_path = config_path
        self.sources = self._load_config()
        self.articles = []

    def _load_config(self) -> Dict[str, List[str]]:
        """
        Load and validate the configuration file.
        
        Returns:
            Dict: data from config.json
        """
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            
            # Basic validation to ensure keys exist
            required_keys = ["right_leaning_sources", "left_leaning_sources", "center_sources"]
            for key in required_keys:
                if key not in data:
                    print(f"Config warning: Missing key '{key}'")
                    # We can choose to init it as empty or let it fail later. 
                    # Let's ensure it exists as a list to prevent key errors.
                    if key not in data:
                        data[key] = []
            
            return data
        except FileNotFoundError:
            print(f"Error: Config file not found at {self.config_path}")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Config file at {self.config_path} is not valid JSON")
            return {}

    def gather_articles(self, topic: str = None) -> List[Dict[str, Any]]:
        """
        Main entry point to fetch and normalize articles from all buckets.
        Optionally filters by a topic keyword.
        Fetches feeds in PARALLEL to reduce latency.
        
        Args:
            topic (str): Keyword to filter articles by (case-insensitive).
        
        Returns:
            List[Dict]: A list of normalized article objects, sorted by image priority.
        """
        self.articles = []
        
        # Prepare list of tasks: (url, bucket_name)
        tasks = []
        for bucket, url_list in self.sources.items():
            simple_bucket_name = "center"
            if "right" in bucket: simple_bucket_name = "right"
            elif "left" in bucket: simple_bucket_name = "left"
            
            for url in url_list:
                tasks.append((url, simple_bucket_name))

        # Parallel Fetching
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Map distinct URLs to futures
            future_to_url = {executor.submit(self._fetch_articles, url): (url, bucket) for url, bucket in tasks}
            
            for future in concurrent.futures.as_completed(future_to_url):
                url, bucket = future_to_url[future]
                try:
                    feed_data = future.result()
                    if feed_data:
                        normalized = self._normalize_articles(feed_data, bucket, url)
                        self.articles.extend(normalized)
                except Exception as exc:
                    print(f'{url} generated an exception: {exc}')

        # Filtering Logic
        filtered = self.articles
        if topic:
            filtered = []
            STOP_WORDS = {'crisis', 'conflict', 'protest', 'war', 'news', 'report', 'update', 'analysis', '2020', '2021', '2022', 'breaking'}
            raw_keywords = [w.lower() for w in topic.split() if len(w) > 3]
            keywords = [k for k in raw_keywords if k not in STOP_WORDS]
            if not keywords and raw_keywords: keywords = raw_keywords
            elif not keywords: keywords = [topic.lower()]

            for art in self.articles:
                text_to_search = (art.get('title', '') + " " + art.get('content', '')).lower()
                if any(k in text_to_search for k in keywords):
                    filtered.append(art)
        
        # Sorting: Articles with REAL images first, then fallback logos
        # We detect "real" images by checking if it's NOT a ui-avatars link
        filtered.sort(key=lambda x: 0 if "ui-avatars.com" not in x.get('image', '') else 1)
        
        return filtered

    def _fetch_articles(self, url: str) -> Optional[Any]:
        if not feedparser: return None
        try:
            # Add User-Agent to avoid 403 blocks from sites like DailyWire
            # feedparser allows passing 'agent' or request_headers
            return feedparser.parse(url, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _normalize_articles(self, feed_data: Any, bucket: str, source_url: str) -> List[Dict[str, Any]]:
        normalized_list = []
        source_name = "Unknown Source"
        if hasattr(feed_data, "feed") and hasattr(feed_data.feed, "title"):
            source_name = feed_data.feed.title
        else:
            source_name = source_url.split('/')[2].replace('www.', '') # simplistic domain

        # Import explicitly if not at top level, or assume standard lib is available
        import urllib.parse

        for entry in feed_data.entries:
            title = getattr(entry, 'title', "No Title")
            published_at = getattr(entry, 'published', getattr(entry, 'updated', "Unknown Date"))
            content = getattr(entry, 'summary', getattr(entry, 'description', "No Content Available"))
            link = getattr(entry, 'link', source_url)

            # --- Image Extraction Logic ---
            image_url = None
            
            # 1. Try media_content (common in standard RSS)
            if 'media_content' in entry:
                try:
                    media = entry.media_content[0]
                    if 'url' in media:
                        image_url = media['url']
                except: pass
            
            # 2. Try media_thumbnail
            if not image_url and 'media_thumbnail' in entry:
                try:
                    image_url = entry.media_thumbnail[0]['url']
                except: pass

            # 3. Try standard enclosures
            if not image_url and hasattr(entry, 'enclosures'):
                for enc in entry.enclosures:
                    enc_type = getattr(enc, 'type', '')
                    if enc_type.startswith('image/'):
                        image_url = getattr(enc, 'href', None)
                        break
            
            # 4. Fallback: Generate a nice logo/avatar if no image found
            if not image_url:
                # Use UI Avatars with proper encoding
                # Clean source name (remove "The", "News", etc for shorter initials if logical, but full name is safer)
                # Let's clean it up slightly: "Fox News" -> "Fox News" is fine, but "The Federalist" -> "Federalist" might be better.
                # For now, just encode the full title.
                
                safe_name = urllib.parse.quote(source_name)
                bg_color = "eee"
                color = "333"
                if bucket == 'left': bg_color = "e3f2fd"; color = "0d47a1"
                if bucket == 'right': bg_color = "ffebee"; color = "b71c1c"
                
                image_url = f"https://ui-avatars.com/api/?name={safe_name}&background={bg_color}&color={color}&size=128&bold=true&font-size=0.5&length=2"

            article = {
                "title": title.strip(),
                "source": source_name.strip(),
                "political_bucket": bucket,
                "published_at": published_at,
                "content": content.strip(),
                "link": link,
                "image": image_url 
            }
            normalized_list.append(article)
            
        return normalized_list
