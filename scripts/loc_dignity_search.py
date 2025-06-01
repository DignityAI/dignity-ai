#!/usr/bin/env python3
"""
Complete Fixed Library of Congress Scraper
Handles all data types safely and downloads images
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

class FixedLOCScraper:
    """Fixed Library of Congress scraper with proper error handling"""
    
    def __init__(self):
        self.base_url = "https://www.loc.gov/search/"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        self.search_terms = [
            "slavery", "enslaved people", "slave", "plantation",
            "African Americans", "freedmen", "reconstruction", 
            "emancipation", "civil rights", "abolition",
            "underground railroad", "black history", "negro",
            "colored people", "jim crow", "segregation"
        ]

    def safe_get_string(self, data, key, default=''):
        """Safely extract string from data that might be list or string"""
        try:
            value = data.get(key, default)
            if isinstance(value, list):
                return str(value[0]) if value else default
            return str(value) if value else default
        except:
            return default

    def safe_get_list(self, data, key, default=None):
        """Safely extract list from data"""
        if default is None:
            default = []
        try:
            value = data.get(key, default)
            if isinstance(value, list):
                return value
            elif value:
                return [value]
            return default
        except:
            return default

    def search_loc_safe(self, query, search_type='both', max_results=25):
        """Safe search with proper error handling"""
        all_items = []
        
        if search_type == 'both':
            # Search text first
            text_items = self.search_loc_safe(query, 'text', max_results // 2)
            # Search images second  
            image_items = self.search_loc_safe(query, 'images', max_results // 2)
            return text_items + image_items
        
        # Single search type
        params = {
            'q': query,
            'fo': 'json',
            'c': min(50, max_results)
        }
        
        if search_type == 'images':
            params['fa'] = 'online-format:image'
        elif search_type == 'text':
            params['fa'] = 'online-format:text'
        
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
                    # Tag items with search type
                    for item in data['results']:
                        item['search_type'] = search_type
                    all_items = data['results']
                    logger.info(f"✅ Found {len(all_items)} {search_type} items")
                else:
                    logger.warning(f"No {search_type} results found for '{query}'")
            else:
                logger.warning(f"HTTP {response.status_code} for {search_type} search")
                
        except Exception as e:
            logger.error(f"Error searching {search_type} for '{query}': {e}")
        
        return all_items

    def clean_item_safe(self, item):
        """Safely clean item data with proper type checking"""
        try:
            cleaned = {}
            
            # Basic info - safe extraction
            cleaned['id'] = self.safe_get_string(item, 'id')
            cleaned['title'] = self.safe_get_string(item, 'title')
            cleaned['date'] = self.safe_get_string(item, 'date')
            cleaned['description'] = self.safe_get_string(item, 'description')
            cleaned['format'] = self.safe_get_string(item, 'original_format')
            
            # Search type
            cleaned['search_type'] = item.get('search_type', 'unknown')
            
            # Lists - safe extraction
            cleaned['subjects'] = self.safe_get_list(item, 'subject')
            cleaned['contributors'] = self.safe_get_list(item, 'contributor') 
            cleaned['creators'] = self.safe_get_list(item, 'creator')
            cleaned['location'] = self.safe_get_list(item, 'location')
            cleaned['online_format'] = self.safe_get_list(item, 'online_format')
            
            # URLs
            cleaned['url'] = self.safe_get_string(item, 'id')
            cleaned['permalink'] = self.safe_get_string(item, 'permalink')
            
            # Image handling - completely safe
            cleaned['image_url'] = None
            cleaned['thumbnail_url'] = None
            cleaned['downloaded_image'] = None
            
            # Look for image URLs safely
            if 'image_url' in item:
                cleaned['image_url'] = self.safe_get_string(item, 'image_url')
            
            if 'thumbnail' in item:
                cleaned['thumbnail_url'] = self.safe_get_string(item, 'thumbnail')
            
            # Check resources for images
            resources = self.safe_get_list(item, 'resources')
            for resource in resources:
                if isinstance(resource, dict):
                    label_value = self.safe_get_string(resource, 'label')
                    label = label_value.lower() if isinstance(label_value, str) else ""
                    if 'image' in label:
                        cleaned['image_url'] = self.safe_get_string(resource, 'url')
                        break
            
            # Text content - safe
            text_parts = self.safe_get_list(item, 'text')
            cleaned['text_content'] = ' '.join(str(t) for t in text_parts if t)
            
            # Full text for searching
            all_text = [
                cleaned['title'],
                cleaned['description'],
                ' '.join(str(s) for s in cleaned['subjects']),
                cleaned['text_content']
            ]
            cleaned['full_text'] = ' '.join(t for t in all_text if t and str(t).strip())
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning item: {e}")
            return {}

    def download_image_safe(self, image_url, filename):
        """Safely download image"""
        try:
            if not image_url or not isinstance(image_url, str):
                return False
                
            response = requests.get(image_url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            logger.error(f"Failed to download {image_url}: {e}")
        return False

    def get_safe_filename(self, term, title, count):
        """Create safe filename"""
        safe_term = "".join(c for c in str(term) if c.isalnum() or c in ('-', '_'))[:20]
        safe_title = "".join(c for c in str(title) if c.isalnum() or c in ('-', '_'))[:30]
        return f"{safe_term}_{safe_title}_{count}"

    def get_file_extension(self, url):
        """Safely get file extension from URL"""
        try:
            if not url or not isinstance(url, str):
                return 'jpg'
            
            # Check for common extensions
            if not url or not isinstance(url, str):
                return 'jpg'
            url_lower = url.lower()
            for ext in ['.jpg', '.jpeg', '.png', '.gif']:
                if ext in url_lower:
                    return ext[1:]  # Remove the dot
            return 'jpg'
        except:
            return 'jpg'

    def scrape_all_terms(self, items_per_term=20, download_images=True):
        """Scrape all terms safely"""
        all_data = {}
        
        # Create directories
        os.makedirs('loc_data', exist_ok=True)
        if download_images:
            os.makedirs('loc_data/images', exist_ok=True)
        
        for term in self.search_terms:
            logger.info(f"🔍 Processing term: '{term}'")
            
            # Search safely
            raw_results = self.search_loc_safe(term, 'both', items_per_term)
            
            cleaned_items = []
            image_count = 0
            
            for item in raw_results:
                try:
                    cleaned = self.clean_item_safe(item)
                    if not cleaned:
                        continue
                    
                    # Handle image downloads safely
                    if download_images and cleaned['search_type'] == 'images':
                        image_url = cleaned.get('image_url') or cleaned.get('thumbnail_url')
                        
                        if image_url and isinstance(image_url, str) and image_url.strip():
                            # Create safe filename
                            base_filename = self.get_safe_filename(term, cleaned['title'], image_count)
                            ext = self.get_file_extension(image_url)
                            filename = f"loc_data/images/{base_filename}.{ext}"
                            
                            if self.download_image_safe(image_url, filename):
                                cleaned['downloaded_image'] = filename
                                image_count += 1
                                logger.info(f"📸 Downloaded: {filename}")
                    
                    # Keep items with content
                    if len(cleaned.get('full_text', '')) > 10 or cleaned.get('downloaded_image'):
                        cleaned_items.append(cleaned)
                        
                except Exception as e:
                    logger.error(f"Error processing item: {e}")
                    continue
            
            all_data[term] = cleaned_items
            
            text_count = len([i for i in cleaned_items if i['search_type'] == 'text'])
            image_count = len([i for i in cleaned_items if i['search_type'] == 'images'])
            downloaded_count = len([i for i in cleaned_items if i.get('downloaded_image')])
            
            logger.info(f"✅ '{term}': {text_count} text, {image_count} images, {downloaded_count} downloaded")
            time.sleep(2)  # Be nice to API
        
        return all_data

    def save_data(self, data):
        """Save all data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Calculate stats
        total_items = sum(len(items) for items in data.values())
        total_text = sum(len([i for i in items if i['search_type'] == 'text']) for items in data.values())
        total_images = sum(len([i for i in items if i['search_type'] == 'images']) for items in data.values())
        downloaded = sum(len([i for i in items if i.get('downloaded_image')]) for items in data.values())
        
        # Save JSON
        filename = f'loc_data/loc_historical_data_{timestamp}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'scraped_at': datetime.now().isoformat(),
                'search_terms': list(data.keys()),
                'stats': {
                    'total_items': total_items,
                    'text_items': total_text,
                    'image_items': total_images,
                    'downloaded_images': downloaded
                },
                'data': data
            }, f, indent=2, ensure_ascii=False)
        
        # Save summary
        summary_lines = [
            f"# Library of Congress Historical Collection",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Items**: {total_items}",
            f"**Text Items**: {total_text}", 
            f"**Image Items**: {total_images}",
            f"**Images Downloaded**: {downloaded}",
            "",
            "## Results by Search Term:",
        ]
        
        for term, items in data.items():
            t_count = len([i for i in items if i['search_type'] == 'text'])
            i_count = len([i for i in items if i['search_type'] == 'images'])
            d_count = len([i for i in items if i.get('downloaded_image')])
            summary_lines.append(f"- **{term}**: {len(items)} total ({t_count} text, {i_count} images, {d_count} downloaded)")
        
        summary_file = f'loc_data/summary_{timestamp}.md'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_lines))
        
        logger.info(f"💾 Data saved: {filename}")
        logger.info(f"📋 Summary: {summary_file}")
        
        return filename, summary_file

def main():
    """Main function"""
    logger.info("🚀 Starting FIXED Library of Congress scraper...")
    
    scraper = FixedLOCScraper()
    
    # Scrape data
    logger.info("📚 Scraping historical data and images...")
    data = scraper.scrape_all_terms(items_per_term=15, download_images=True)
    
    # Save everything
    data_file, summary_file = scraper.save_data(data)
    
    # Final stats
    total_items = sum(len(items) for items in data.values())
    total_images = sum(len([i for i in items if i.get('downloaded_image')]) for items in data.values())
    
    print(f"\n🎉 SUCCESS!")
    print(f"📊 Collected {total_items} historical items")
    print(f"📸 Downloaded {total_images} images")
    print(f"📁 Data saved to: {data_file}")
    print(f"📋 Summary: {summary_file}")

if __name__ == "__main__":
    main()
