#!/usr/bin/env python3
"""
Simple Library of Congress Data Scraper
Just collects and saves raw historical data - no processing
"""

import requests
import json
import os
import sys
from datetime import datetime
import time
import logging
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleLOCScraper:
    """Simple Library of Congress data scraper - just collect raw data"""
    
    def __init__(self):
        self.base_url = "https://www.loc.gov/search/"
        self.api_params = {
            'fo': 'json',  # JSON format
            'at': '!online-format:image,audio',  # Text content only
            'c': 50,  # Results per page
        }
        
        # Simple search terms for Black history
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

    def search_loc(self, query, max_results=100):
        """Search Library of Congress and return raw results"""
        all_items = []
        start = 1
        
        while len(all_items) < max_results:
            try:
                params = self.api_params.copy()
                params.update({
                    'q': query,
                    'sp': start,
                    'c': min(50, max_results - len(all_items))
                })
                
                logger.info(f"Searching LOC: '{query}' (page {start//50 + 1})")
                
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if 'results' not in data or not data['results']:
                    break
                
                all_items.extend(data['results'])
                start += 50
                
                # Be nice to the API
                time.sleep(1)
                
                # If we got fewer results than requested, we're done
                if len(data['results']) < 50:
                    break
                    
            except Exception as e:
                logger.error(f"Error searching '{query}': {e}")
                break
        
        logger.info(f"Found {len(all_items)} items for '{query}'")
        return all_items

    def clean_item_data(self, item):
        """Extract useful data from LOC item"""
        cleaned = {}
        
        try:
            # Basic info
            cleaned['id'] = item.get('id', '')
            cleaned['title'] = item.get('title', [''])[0] if item.get('title') else ''
            cleaned['date'] = item.get('date', [''])[0] if item.get('date') else ''
            cleaned['description'] = item.get('description', [''])[0] if item.get('description') else ''
            
            # Subjects and topics
            cleaned['subjects'] = item.get('subject', []) or []
            cleaned['contributors'] = item.get('contributor', []) or []
            cleaned['creators'] = item.get('creator', []) or []
            
            # Format and type
            cleaned['format'] = item.get('original_format', [''])[0] if item.get('original_format') else ''
            cleaned['type'] = item.get('type', [''])[0] if item.get('type') else ''
            
            # Location info
            cleaned['location'] = item.get('location', []) or []
            cleaned['online_format'] = item.get('online_format', []) or []
            
            # URLs and access
            cleaned['url'] = item.get('id', '')
            cleaned['permalink'] = item.get('permalink', '')
            
            # Any text content
            if 'text' in item:
                if isinstance(item['text'], list):
                    cleaned['text_content'] = ' '.join(item['text'])
                else:
                    cleaned['text_content'] = str(item['text'])
            else:
                cleaned['text_content'] = ''
            
            # Combine searchable text
            text_parts = [
                cleaned['title'],
                cleaned['description'], 
                ' '.join(cleaned['subjects']),
                cleaned['text_content']
            ]
            cleaned['full_text'] = ' '.join([part for part in text_parts if part]).strip()
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning item data: {e}")
            return {}

    def scrape_all_terms(self, items_per_term=50):
        """Scrape data for all search terms"""
        all_data = {}
        
        for term in self.search_terms:
            logger.info(f"🔍 Scraping: {term}")
            
            raw_results = self.search_loc(term, max_results=items_per_term)
            
            # Clean the data
            cleaned_items = []
            for item in raw_results:
                cleaned = self.clean_item_data(item)
                if cleaned and len(cleaned.get('full_text', '')) > 50:  # Only keep items with some content
                    cleaned_items.append(cleaned)
            
            all_data[term] = cleaned_items
            logger.info(f"✅ Saved {len(cleaned_items)} items for '{term}'")
            
            # Be extra nice to the API
            time.sleep(2)
        
        return all_data

    def save_data(self, data):
        """Save scraped data to files"""
        # Create output directory
        os.makedirs('loc_data', exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save complete dataset
        filename = f'loc_data/loc_black_history_{timestamp}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'scraped_at': datetime.now().isoformat(),
                'search_terms': list(data.keys()),
                'total_items': sum(len(items) for items in data.values()),
                'data': data
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Complete dataset saved: {filename}")
        
        # Save summary report
        summary_lines = [
            f"# Library of Congress Black History Data",
            f"**Scraped**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Items**: {sum(len(items) for items in data.values())}",
            "",
            "## Items by Search Term:",
        ]
        
        for term, items in data.items():
            summary_lines.append(f"- **{term}**: {len(items)} items")
        
        summary_lines.extend([
            "",
            "## Sample Items:",
        ])
        
        # Add sample items
        for term, items in data.items():
            if items:
                sample = items[0]
                summary_lines.extend([
                    f"### {term}",
                    f"**Title**: {sample.get('title', 'N/A')}",
                    f"**Date**: {sample.get('date', 'N/A')}",
                    f"**Description**: {sample.get('description', 'N/A')[:200]}...",
                    ""
                ])
        
        summary_file = f'loc_data/summary_{timestamp}.md'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_lines))
        
        logger.info(f"📋 Summary saved: {summary_file}")
        
        return filename, summary_file

def main():
    """Main scraping function"""
    logger.info("🚀 Starting Library of Congress data scraping...")
    
    scraper = SimpleLOCScraper()
    
    # Scrape all the data
    logger.info("📚 Scraping historical data...")
    data = scraper.scrape_all_terms(items_per_term=30)  # 30 items per term to start
    
    # Save everything
    logger.info("💾 Saving data...")
    data_file, summary_file = scraper.save_data(data)
    
    # Print summary
    total_items = sum(len(items) for items in data.values())
    logger.info(f"✅ Scraping complete!")
    logger.info(f"📊 Total items collected: {total_items}")
    logger.info(f"📁 Data saved to: {data_file}")
    logger.info(f"📋 Summary: {summary_file}")
    
    print(f"\n🎉 Successfully scraped {total_items} historical items from Library of Congress!")

if __name__ == "__main__":
    main()