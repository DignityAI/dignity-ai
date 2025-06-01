#!/usr/bin/env python3
"""
Black History Data Collector - Library of Congress
Simple data collection focused on Black historical records
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BlackHistoryCollector:
    """Collect Black historical materials from Library of Congress"""
    
    def __init__(self):
        self.base_url = "https://www.loc.gov"
        self.search_api = f"{self.base_url}/search"
        
        # Create data directory
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Search terms for Black history (oldest first)
        self.search_terms = [
            # Slavery era
            "slave", "slavery", "enslaved", "plantation", "runaway slave",
            "slave auction", "negro", "colored", "freedman", "manumission",
            "underground railroad", "slave narrative", "abolition",
            # Reconstruction  
            "reconstruction", "freedmen", "freedman's bureau", "black codes",
            "sharecropping", "ku klux klan", "lynching",
            # Jim Crow resistance
            "jim crow", "segregation", "NAACP", "civil rights", "protest"
        ]
        
        # Track collected items
        self.collected_file = f"{self.data_dir}/collected_items.json"
        self.collected_items = self.load_collected_items()
    
    def load_collected_items(self):
        """Load list of already collected item IDs"""
        if os.path.exists(self.collected_file):
            with open(self.collected_file, 'r') as f:
                data = json.load(f)
                return set(data.get('items', []))
        return set()
    
    def save_collected_items(self):
        """Save list of collected item IDs"""
        with open(self.collected_file, 'w') as f:
            json.dump({
                'items': list(self.collected_items),
                'last_updated': datetime.now().isoformat(),
                'total_items': len(self.collected_items)
            }, f, indent=2)
    
    def search_loc(self, term, start_year=1770, end_year=1865, page=1):
        """Search Library of Congress for specific term"""
        
        params = {
            'q': term,
            'fo': 'json',
            'c': 25,  # results per page
            'sp': page,
            'dates': f'{start_year}-{end_year}'
        }
        
        try:
            response = requests.get(self.search_api, params=params, timeout=30)
            response.raise_for_status()
            
            if 'application/json' in response.headers.get('content-type', ''):
                return response.json()
            else:
                logger.warning(f"Non-JSON response for term: {term}")
                return {}
                
        except Exception as e:
            logger.error(f"Search error for '{term}': {e}")
            return {}
    
    def process_item(self, item):
        """Extract key info from search result"""
        
        # Create unique ID
        url = item.get('url', '')
        title = item.get('title', '')
        item_id = hashlib.md5(f"{url}{title}".encode()).hexdigest()[:12]
        
        # Skip if already collected
        if item_id in self.collected_items:
            return None
        
        # Extract basic info
        processed_item = {
            'id': item_id,
            'title': title,
            'url': url,
            'description': item.get('description', ''),
            'date': item.get('date', ''),
            'type': item.get('original_format', ''),
            'subjects': item.get('subject', []),
            'collection': item.get('partof', []),
            'collected_at': datetime.now().isoformat()
        }
        
        return processed_item
    
    def save_item(self, item):
        """Save item to JSON file"""
        
        filename = f"{self.data_dir}/{item['id']}.json"
        
        with open(filename, 'w') as f:
            json.dump(item, f, indent=2)
        
        # Add to collected set
        self.collected_items.add(item['id'])
        
        logger.info(f"Saved: {item['title'][:50]}...")
    
    def collect_for_term(self, term, max_items=50, start_year=1770, end_year=1865):
        """Collect items for specific search term"""
        
        logger.info(f"Collecting for term: '{term}' ({start_year}-{end_year})")
        
        collected = 0
        page = 1
        
        while collected < max_items:
            # Search
            results = self.search_loc(term, start_year, end_year, page)
            
            if not results or 'results' not in results:
                break
            
            items = results['results']
            if not items:
                break
            
            # Process each item
            for item in items:
                if collected >= max_items:
                    break
                
                processed = self.process_item(item)
                if processed:
                    self.save_item(processed)
                    collected += 1
                
                # Rate limiting
                time.sleep(0.5)
            
            page += 1
            
            # Save progress every 10 items
            if collected % 10 == 0:
                self.save_collected_items()
        
        logger.info(f"Collected {collected} items for '{term}'")
        return collected
    
    def run_collection(self, max_per_term=20):
        """Run collection for all search terms"""
        
        logger.info("Starting Black History data collection from Library of Congress")
        
        total_collected = 0
        
        # Start with slavery era (oldest materials)
        slavery_terms = self.search_terms[:10]  # First 10 terms
        
        for term in slavery_terms:
            collected = self.collect_for_term(
                term, 
                max_items=max_per_term,
                start_year=1770, 
                end_year=1865
            )
            total_collected += collected
            
            # Save progress
            self.save_collected_items()
            
            # Brief pause between terms
            time.sleep(2)
        
        logger.info(f"Collection complete! Total items: {total_collected}")
        
        # Generate simple summary
        self.generate_summary(total_collected)
    
    def generate_summary(self, total_items):
        """Generate basic summary of collection"""
        
        summary = f"# Black History Collection Summary\n\n"
        summary += f"**Collection Date:** {datetime.now().strftime('%Y-%m-%d')}\n"
        summary += f"**Total Items:** {total_items}\n"
        summary += f"**Focus:** Slavery era materials (1770-1865)\n\n"
        
        summary += "## Files Collected\n"
        summary += f"- {total_items} JSON files with historical records\n"
        summary += f"- Items stored in `data/` directory\n"
        summary += f"- Tracking file: `data/collected_items.json`\n\n"
        
        summary += "## Next Steps\n"
        summary += "- Expand to Reconstruction era (1865-1877)\n"
        summary += "- Add Jim Crow resistance materials (1877-1955)\n"
        summary += "- Process and analyze collected data\n"
        
        # Save summary
        with open(f"{self.data_dir}/README.md", 'w') as f:
            f.write(summary)

def main():
    """Run the collection"""
    collector = BlackHistoryCollector()
    collector.run_collection(max_per_term=15)  # Start small

if __name__ == "__main__":
    main()