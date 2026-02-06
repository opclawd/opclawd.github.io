#!/usr/bin/env python3
"""
Web scraping script for books.toscrape.com
Extracts all books from 50 pages with title, price, rating, and availability.
Uses only standard library modules.
"""

import urllib.request
import urllib.error
import re
import csv
import time
import os

# Configuration
BASE_URL = "https://books.toscrape.com"
OUTPUT_PATH = "/home/node/.openclaw/workspace/exports/books.csv"
MAX_PAGES = 50

# Rating mapping from class name to number
RATING_MAP = {
    'One': 1,
    'Two': 2,
    'Three': 3,
    'Four': 4,
    'Five': 5
}

def fetch_page(url):
    """Fetch page content using urllib."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8')
    except urllib.error.URLError as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_rating(star_class):
    """Extract rating number from star class string."""
    for word, num in RATING_MAP.items():
        if word in star_class:
            return num
    return 0

def parse_books(html):
    """Parse HTML and extract book data using regex."""
    books = []
    
    # Pattern to match book article blocks
    book_pattern = r'<article[^>]*class="product_pod"[^>]*>(.*?)</article>'
    book_blocks = re.findall(book_pattern, html, re.DOTALL)
    
    for block in book_blocks:
        try:
            # Extract title from the <a> tag in h3
            title_match = re.search(r'<h3>.*?<a[^>]*title="([^"]+)"', block, re.DOTALL)
            title = title_match.group(1) if title_match else "Unknown"
            
            # Extract price
            price_match = re.search(r'<p[^>]*class="price_color"[^>]*>(.*?)</p>', block)
            price = price_match.group(1).strip() if price_match else ""
            # Remove HTML tags from price
            price = re.sub(r'<[^>]+>', '', price)
            
            # Extract rating from star-rating class
            rating_match = re.search(r'<p[^>]*class="star-rating ([^"]+)"', block)
            if rating_match:
                rating_class = rating_match.group(1)
                rating = extract_rating(rating_class)
            else:
                rating = 0
            
            # Extract availability
            avail_match = re.search(r'<p[^>]*class="instock availability"[^>]*>(.*?)</p>', block, re.DOTALL)
            if avail_match:
                availability = avail_match.group(1)
                # Remove HTML tags and clean whitespace
                availability = re.sub(r'<[^>]+>', '', availability)
                availability = ' '.join(availability.split())
            else:
                availability = "Unknown"
            
            books.append({
                'title': title,
                'price': price,
                'rating': rating,
                'availability': availability
            })
        except Exception as e:
            print(f"Error parsing book block: {e}")
            continue
    
    return books

def scrape_page(page_num):
    """Scrape a single page and return list of book data."""
    if page_num == 1:
        url = f"{BASE_URL}/index.html"
    else:
        url = f"{BASE_URL}/catalogue/page-{page_num}.html"
    
    html = fetch_page(url)
    if html is None:
        return []
    
    return parse_books(html)

def main():
    """Main function to scrape all pages and save to CSV."""
    print("=" * 60)
    print("Book Scraper for books.toscrape.com")
    print("=" * 60)
    print(f"Output path: {OUTPUT_PATH}")
    print(f"Max pages: {MAX_PAGES}")
    print("=" * 60)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    all_books = []
    start_time = time.time()
    
    for page in range(1, MAX_PAGES + 1):
        print(f"[Page {page:2d}/{MAX_PAGES}] Scraping...", end=" ")
        books = scrape_page(page)
        all_books.extend(books)
        print(f"Found {len(books)} books (Total: {len(all_books)})")
        
        # Small delay to be polite to the server
        if page < MAX_PAGES:
            time.sleep(0.3)
    
    elapsed_time = time.time() - start_time
    
    # Write to CSV
    with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'price', 'rating', 'availability'])
        writer.writeheader()
        writer.writerows(all_books)
    
    print("=" * 60)
    print("✓ SCRAPING COMPLETE!")
    print(f"  Total books extracted: {len(all_books)}")
    print(f"  Time taken: {elapsed_time:.2f} seconds")
    print(f"  CSV saved to: {OUTPUT_PATH}")
    print("=" * 60)
    
    return len(all_books), elapsed_time

if __name__ == "__main__":
    main()
