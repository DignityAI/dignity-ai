#!/usr/bin/env python3
"""
Fixed Library of Congress Data Scraper
Debugged version with proper API parameters and error handling
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
import logging
from urllib.parse import quote, urlencode

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LOCScraper:
    """Library of Congress API scraper with debugging"""
    
    def __init__(self):
        # LOC API endpoint - using the correct JSON API
        self.base_url = "https://www.loc.gov/search/"
        
        # Headers to appear more like a browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        # Search terms
        self.search_terms = [
            "slavery",
            "enslaved people", 
            "slave",
            "plantation",
            "African Americans",
            "freedmen",
            "reconstruction", 
            "emancipation",
            "civil rights",
            "abolition",
            "underground railroad",
            "black history",
            "negro",
            "colored people",
            "jim crow",
            "segregation"
        ]

    def test_connection(self):
        """Test if we can connect to LOC API"""
        test_url = "https://www.loc.gov/search/"
        test_params = {
            'q': 'test',
            'fo': 'json',
            'c': 1
        }
        
        try:
            logger.info("🔍 Testing LOC connection...")
            response = requests.get(test_url, params=test_params, headers=self.headers, timeout=10)
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response URL: {response.url}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f"✅ JSON response received")
                    logger.info(f"Keys in response: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    return True, data
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Invalid JSON response: {e}")
                    logger.info(f"Response content preview: {response.text[:500]}")
                    return False, None
            else:
                logger.error(f"❌ HTTP {response.status_code}: {response.reason}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False, None

    def search_loc_simple(self, query, max_results=50):
        """Simple search with basic parameters"""
        all_items = []
        
        # Try different parameter combinations
        param_sets = [
            # Standard search
            {'q': query, 'fo': 'json', 'c': min(50, max_results)},
            # Search with format filter
            {'q': query, 'fo': 'json', 'c': min(50, max_results), 'fa': 'online-format:text'},
            # Basic search without format filter
            {'q': query, 'fo': 'json', 'c': min(50, max_results), 'sb': 'date'},
        ]
        
        for i, params in enumerate(param_sets):
            try:
                logger.info(f"🔍 Trying parameter set {i+1} for '{query}'")
                logger.info(f"Parameters: {params}")
                
                response = requests.get(
                    self.base_url, 
                    params=params, 
                    headers=self.headers, 
                    timeout=30
                )
                
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Final URL: {response.url}")
                
                if response.status_code != 200:
                    logger.warning(f"HTTP {response.status_code}, trying next parameter set...")
                    continue
                
                try:
                    data = response.json()
                    if 'results' in data and data['results']:
                        all_items.extend(data['results'])
                        logger.info(f"✅ Found {len(data['results'])} items with parameter set {i+1}")
                        break
                    else:
                        logger.warning(f"No results in response, trying next parameter set...")
                        logger.info(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    logger.info(f"Response preview: {response.text[:200]}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error with parameter set {i+1}: {e}")
                continue
        
        return all_items

    def search_with_images(self, query, max_results=50):
        """Search for both text and images"""
        all_items = []
        
        # Search for text content
        text_params = {
            'q': query,
            'fo': 'json',
            'c': min(25, max_results // 2),
            'fa': 'online-format:text'
        }
        
        # Search for images
        image_params = {
            'q': query,
            'fo': 'json', 
            'c': min(25, max_results // 2),
            'fa': 'online-format:image'
        }
        
        for search_type, params in [('text', text_params), ('images', image_params)]:
            try:
                logger.info(f"🔍 Searching {search_type} for '{query}'")
                
                response = requests.get(
                    self.base_url,
                    params=params,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data and data['results']:
                        # Tag items with their type
                        for item in data['results']:
                            item['search_type'] = search_type
                        all_items.extend(data['results'])
                        logger.info(f"✅ Found {len(data['results'])} {search_type} items")
                    else:
                        logger.warning(f"No {search_type} results found")
                else:
                    logger.warning(f"Failed to search {search_type}: HTTP {response.status_code}")
                    
                time.sleep(1)  # Be nice to the API
                
            except Exception as e:
                logger.error(f"Error searching {search_type}: {e}")
        
        return all_items

    def download_image(self, image_url, filename):
        """Download an image from URL"""
        try:
            response = requests.get(image_url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            logger.error(f"Failed to download image {image_url}: {e}")
        return False

    def clean_item_data(self, item):
        """Extract and clean data from LOC item"""
        cleaned = {}
        
        try:
            # Basic info
            cleaned['id'] = item.get('id', '')
            cleaned['title'] = item.get('title', [''])[0] if item.get('title') else ''
            cleaned['date'] = item.get('date', [''])[0] if item.get('date') else ''
            cleaned['description'] = item.get('description', [''])[0] if item.get('description') else ''
            
            # Type of content
            cleaned['search_type'] = item.get('search_type', 'unknown')
            cleaned['format'] = item.get('original_format', [''])[0] if item.get('original_format') else ''
            cleaned['online_format'] = item.get('online_format', []) or []
            
            # Subjects and contributors
            cleaned['subjects'] = item.get('subject', []) or []
            cleaned['contributors'] = item.get('contributor', []) or []
            cleaned['creators'] = item.get('creator', []) or []
            cleaned['location'] = item.get('location', []) or []
            
            # URLs and links
            cleaned['url'] = item.get('id', '')
            cleaned['permalink'] = item.get('permalink', '')
            
            # Image-specific data
            cleaned['image_url'] = None
            cleaned['thumbnail_url'] = None
            cleaned['downloaded_image'] = None
            
            # Look for image URLs in various places
            if 'image_url' in item:
                cleaned['image_url'] = item['image_url']
            elif 'resources' in item and isinstance(item['resources'], list):
                for resource in item['resources']:
                    if isinstance(resource, dict) and 'label' in resource:
                        if 'image' in str(resource.get('label', '')).lower():
                            cleaned['image_url'] = resource.get('url', '')
                            break
            
            # Look for thumbnails
            if 'thumbnail' in item:
                cleaned['thumbnail_url'] = item['thumbnail']
            
            # Text content
            text_content = ''
            if 'text' in item:
                if isinstance(item['text'], list):
                    text_content = ' '.join(item['text'])
                else:
                    text_content = str(item['text'])
            
            cleaned['text_content'] = text_content
            
            # Combine all searchable text
            text_parts = [
                cleaned['title'],
                cleaned['description'],
                ' '.join(cleaned['subjects']),
                text_content
            ]
            cleaned['full_text'] = ' '.join([part for part in text_parts if part]).strip()
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning item data: {e}")
            return {}

    def scrape_with_images(self, items_per_term=30, download_images=True):
        """Scrape both text and images for all search terms"""
        all_data = {}
        
        # Create directories
        os.makedirs('loc_data', exist_ok=True)
        if download_images:
            os.makedirs('loc_data/images', exist_ok=True)
        
        for term in self.search_terms:
            logger.info(f"🔍 Scraping '{term}' (text + images)")
            
            # Search for both text and images
            raw_results = self.search_with_images(term, max_results=items_per_term)
            
            # Clean and process the data
            cleaned_items = []
            image_count = 0
            
            for item in raw_results:
                cleaned = self.clean_item_data(item)
                if not cleaned:
                    continue
                
                # Download images if available
                if download_images and cleaned['search_type'] == 'images':
                    image_url = cleaned.get('image_url') or cleaned.get('thumbnail_url')
                    if image_url:
                        # Create safe filename
                        safe_term = "".join(c for c in term if c.isalnum() or c in (' ', '-', '_')).strip()
                        safe_title = "".join(c for c in cleaned['title'][:50] if c.isalnum() or c in (' ', '-', '_')).strip()
                        
                        # Get file extension from URL
                        ext = 'jpg'
                        if isinstance(image_url, str) and image_url.lower().endswith(('.png', '.gif', '.jpeg', '.jpg')):
                            ext = image_url.split('.')[-1].lower()
                        
                        filename = f"loc_data/images/{safe_term}_{safe_title}_{image_count}.{ext}"
                        
                        if self.download_image(image_url, filename):
                            cleaned['downloaded_image'] = filename
                            image_count += 1
                            logger.info(f"📸 Downloaded image: {filename}")
                
                # Only keep items with some content
                if len(cleaned.get('full_text', '')) > 20 or cleaned.get('downloaded_image'):
                    cleaned_items.append(cleaned)
            
            all_data[term] = cleaned_items
            text_items = len([i for i in cleaned_items if i['search_type'] == 'text'])
            image_items = len([i for i in cleaned_items if i['search_type'] == 'images'])
            
            logger.info(f"✅ '{term}': {text_items} text items, {image_items} image items")
            
            # Be extra nice to the API
            time.sleep(2)
        
        return all_data

    def save_data_with_images(self, data):
        """Save scraped data including image information"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save complete dataset
        filename = f'loc_data/loc_complete_{timestamp}.json'
        
        # Calculate stats
        total_items = sum(len(items) for items in data.values())
        total_text = sum(len([i for i in items if i['search_type'] == 'text']) for items in data.values())
        total_images = sum(len([i for i in items if i['search_type'] == 'images']) for items in data.values())
        downloaded_images = sum(len([i for i in items if i.get('downloaded_image')]) for items in data.values())
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'scraped_at': datetime.now().isoformat(),
                'search_terms': list(data.keys()),
                'stats': {
                    'total_items': total_items,
                    'text_items': total_text,
                    'image_items': total_images,
                    'downloaded_images': downloaded_images
                },
                'data': data
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Complete dataset saved: {filename}")
        
        # Create enhanced summary
        summary_lines = [
            f"# Library of Congress Historical Data Collection",
            f"**Scraped**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Items**: {total_items}",
            f"**Text Items**: {total_text}",
            f"**Image Items**: {total_images}",
            f"**Downloaded Images**: {downloaded_images}",
            "",
            "## Items by Search Term:",
        ]
        
        for term, items in data.items():
            text_count = len([i for i in items if i['search_type'] == 'text'])
            image_count = len([i for i in items if i['search_type'] == 'images'])
            downloaded_count = len([i for i in items if i.get('downloaded_image')])
            summary_lines.append(f"- **{term}**: {len(items)} total ({text_count} text, {image_count} images, {downloaded_count} downloaded)")
        
        summary_lines.extend([
            "",
            "## Sample Items:",
        ])
        
        # Add samples for each type
        for term, items in data.items():
            if items:
                # Show text sample
                text_items = [i for i in items if i['search_type'] == 'text']
                if text_items:
                    sample = text_items[0]
                    summary_lines.extend([
                        f"### {term} - Text Sample",
                        f"**Title**: {sample.get('title', 'N/A')}",
                        f"**Date**: {sample.get('date', 'N/A')}",
                        f"**Description**: {sample.get('description', 'N/A')[:200]}...",
                        ""
                    ])
                
                # Show image sample
                image_items = [i for i in items if i['search_type'] == 'images']
                if image_items:
                    sample = image_items[0]
                    summary_lines.extend([
                        f"### {term} - Image Sample",
                        f"**Title**: {sample.get('title', 'N/A')}",
                        f"**Date**: {sample.get('date', 'N/A')}",
                        f"**Downloaded**: {'✅' if sample.get('downloaded_image') else '❌'}",
                        ""
                    ])
        
        summary_file = f'loc_data/summary_{timestamp}.md'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_lines))
        
        logger.info(f"📋 Summary saved: {summary_file}")
        return filename, summary_file

def main():
    """Main scraping function with debugging"""
    logger.info("🚀 Starting Library of Congress scraper with image support...")
    
    scraper = LOCScraper()
    
    # Test connection first
    success, test_data = scraper.test_connection()
    if not success:
        logger.error("❌ Cannot connect to LOC API. Exiting.")
        return
    
    logger.info("✅ Connection test successful!")
    
    # Scrape data and images
    logger.info("📚 Scraping historical data and images...")
    data = scraper.scrape_with_images(items_per_term=20, download_images=True)
    
    # Save everything
    logger.info("💾 Saving data and generating summary...")
    data_file, summary_file = scraper.save_data_with_images(data)
    
    # Print final summary
    total_items = sum(len(items) for items in data.values())
    total_images = sum(len([i for i in items if i.get('downloaded_image')]) for items in data.values())
    
    logger.info(f"✅ Scraping complete!")
    logger.info(f"📊 Total items: {total_items}")
    logger.info(f"📸 Images downloaded: {total_images}")
    logger.info(f"📁 Data: {data_file}")
    logger.info(f"📋 Summary: {summary_file}")
    
    print(f"\n🎉 Successfully collected {total_items} historical items with {total_images} images!")

if __name__ == "__main__":
    main()