#!/usr/bin/env python3
"""
Sports RSS Fetcher - Fetches sports news from various RSS feeds
Usage: python3 sports_rss_fetcher.py [--output FILE] [--limit N]
"""

import argparse
import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
import json
import sys
from datetime import datetime
from typing import List, Dict, Optional

# RSS Feed URLs for sports news
RSS_FEEDS = {
    'espn': 'https://www.espn.com/espn/rss/news',
    'espn_futbol': 'https://www.espn.com/espn/rss/futbol/news',
    'bbc_sport': 'http://feeds.bbci.co.uk/sport/rss.xml',
    'bbc_football': 'http://feeds.bbci.co.uk/sport/football/rss.xml',
    'goal_com': 'https://www.goal.com/feeds/en/news',
    'transfermarkt': 'https://www.transfermarkt.com/rss/news',
}

class SportsRSSFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def fetch_feed(self, url: str) -> Optional[str]:
        """Fetch RSS feed content from URL"""
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode('utf-8', errors='ignore')
        except urllib.error.URLError as e:
            print(f"Error fetching {url}: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return None
    
    def parse_rss(self, xml_content: str) -> List[Dict]:
        """Parse RSS XML content and extract articles"""
        articles = []
        try:
            root = ET.fromstring(xml_content)
            
            # Handle RSS 2.0
            for item in root.findall('.//item'):
                article = self._extract_item_data(item)
                if article:
                    articles.append(article)
            
            # Handle Atom feeds
            for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                article = self._extract_atom_data(entry)
                if article:
                    articles.append(article)
                    
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}", file=sys.stderr)
        
        return articles
    
    def _extract_item_data(self, item) -> Optional[Dict]:
        """Extract data from RSS item"""
        try:
            title = item.find('title')
            link = item.find('link')
            description = item.find('description')
            pub_date = item.find('pubDate')
            
            return {
                'title': title.text if title is not None else 'No title',
                'link': link.text if link is not None else '',
                'description': description.text if description is not None else '',
                'published': pub_date.text if pub_date is not None else datetime.now().isoformat(),
                'source': 'RSS'
            }
        except Exception:
            return None
    
    def _extract_atom_data(self, entry) -> Optional[Dict]:
        """Extract data from Atom entry"""
        try:
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            title = entry.find('atom:title', ns)
            link = entry.find('atom:link', ns)
            summary = entry.find('atom:summary', ns)
            updated = entry.find('atom:updated', ns)
            
            href = link.get('href') if link is not None else ''
            
            return {
                'title': title.text if title is not None else 'No title',
                'link': href,
                'description': summary.text if summary is not None else '',
                'published': updated.text if updated is not None else datetime.now().isoformat(),
                'source': 'Atom'
            }
        except Exception:
            return None
    
    def fetch_all(self, limit: int = 10) -> List[Dict]:
        """Fetch and combine articles from all feeds"""
        all_articles = []
        
        for source, url in RSS_FEEDS.items():
            print(f"Fetching from {source}...", file=sys.stderr)
            content = self.fetch_feed(url)
            if content:
                articles = self.parse_rss(content)
                for article in articles:
                    article['feed_source'] = source
                all_articles.extend(articles)
        
        # Sort by date (newest first) and limit
        all_articles.sort(key=lambda x: x.get('published', ''), reverse=True)
        return all_articles[:limit]
    
    def save_to_json(self, articles: List[Dict], filename: str):
        """Save articles to JSON file"""
        data = {
            'fetched_at': datetime.now().isoformat(),
            'count': len(articles),
            'articles': articles
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(articles)} articles to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Fetch sports news from RSS feeds')
    parser.add_argument('--output', '-o', default='sports_news.json', help='Output JSON file')
    parser.add_argument('--limit', '-l', type=int, default=10, help='Maximum articles to fetch')
    parser.add_argument('--source', '-s', choices=list(RSS_FEEDS.keys()), help='Specific source to fetch')
    
    args = parser.parse_args()
    
    fetcher = SportsRSSFetcher()
    
    if args.source:
        # Fetch from specific source
        url = RSS_FEEDS[args.source]
        content = fetcher.fetch_feed(url)
        if content:
            articles = fetcher.parse_rss(content)
            for article in articles:
                article['feed_source'] = args.source
        else:
            articles = []
    else:
        # Fetch from all sources
        articles = fetcher.fetch_all(limit=args.limit)
    
    fetcher.save_to_json(articles, args.output)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Fetched {len(articles)} articles")
    print(f"{'='*60}")
    for i, article in enumerate(articles[:5], 1):
        print(f"{i}. [{article.get('feed_source', 'unknown')}] {article['title'][:70]}...")

if __name__ == '__main__':
    main()
