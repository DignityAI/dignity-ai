#!/usr/bin/env python3
"""
Debug version - Simple LOC scraper to isolate the error
"""

import requests
import json
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_search():
    """Simple debug search to see what data we're getting"""
    
    url = "https://www.loc.gov/search/"
    params = {
        'q': 'slavery',
        'fo': 'json',
        'c': 5,
        'fa': 'online-format:image'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        logger.info("Making request to LOC...")
        response = requests.get(url, params=params, headers=headers, timeout=30)
        logger.info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response keys: {list(data.keys())}")
            
            if 'results' in data:
                logger.info(f"Found {len(data['results'])} results")
                
                # Look at the first result in detail
                if data['results']:
                    first_item = data['results'][0]
                    logger.info(f"First item keys: {list(first_item.keys())}")
                    
                    # Save raw data for inspection
                    with open('debug_raw_data.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    logger.info("Raw data saved to debug_raw_data.json")
                    
                    # Try to process each field safely
                    for key, value in first_item.items():
                        logger.info(f"Field '{key}': type={type(value)}, value={str(value)[:100]}...")
                        
                        # This is where we might find the problematic list
                        if isinstance(value, list):
                            logger.warning(f"Found list field '{key}' with {len(value)} items")
                            if value:
                                logger.info(f"First item in list: type={type(value[0])}, value={str(value[0])[:50]}...")
                
            else:
                logger.error("No 'results' key in response")
                logger.info(f"Available keys: {list(data.keys())}")
        
        else:
            logger.error(f"Request failed: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Debug search failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_search()