#!/usr/bin/env python3
"""
Black History Data Collector - Library of Congress
Systematically collect and preserve Black historical records
Focus: Slavery era → Reconstruction → Jim Crow resistance
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
import hashlib
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BlackHistoryCollector:
    """Collect and preserve Black historical materials from Library of Congress"""
    
    def __init__(self):
        self.base_url = "https://www.loc.gov"
        self.api_base = f"{self.base_url}/collections"
        self.search_api = f"{self.base_url}/search"
        
        # Create data directories
        self.data_dir = "data"
        self.images_dir = f"{self.data_dir}/images"
        self.documents_dir = f"{self.data_dir}/documents"
        self.analysis_dir = f"{self.data_dir}/analysis"
        
        for directory in [self.data_dir, self.images_dir, self.documents_dir, self.analysis_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Historical periods to focus on (oldest first)
        self.historical_periods = {
            "slavery_era": {
                "start_year": 1770,
                "end_year": 1865,
                "keywords": [
                    "slave", "slavery", "enslaved", "plantation", "overseer",
                    "runaway slave", "fugitive slave", "slave auction", "slave market",
                    "slave quarters", "field hands", "house servants", "negro",
                    "colored", "freedman", "manumission", "emancipation",
                    "underground railroad", "slave narrative", "slave rebellion",
                    "Nat Turner", "Denmark Vesey", "Gabriel Prosser",
                    "abolition", "abolitionist", "anti-slavery"
                ]
            },
            "reconstruction": {
                "start_year": 1865,
                "end_year": 1877,
                "keywords": [
                    "reconstruction", "freedmen", "freedman's bureau",
                    "black codes", "sharecropping", "tenant farming",
                    "ku klux klan", "klan", "lynching", "violence",
                    "voting rights", "citizenship", "civil rights",
                    "14th amendment", "15th amendment", "carpetbagger"
                ]
            },
            "jim_crow_resistance": {
                "start_year": 1877,
                "end_year": 1955,
                "keywords": [
                    "jim crow", "segregation", "separate but equal",
                    "lynch", "lynching", "race riot", "race violence",
                    "NAACP", "Urban League", "Marcus Garvey", "UNIA",
                    "Ida B Wells", "Booker T Washington", "W.E.B. Du Bois",
                    "Harlem Renaissance", "Negro", "colored",
                    "disenfranchisement", "poll tax", "literacy test",
                    "great migration", "black wall street", "tulsa massacre"
                ]
            }
        }
        
        # Track what we've collected
        self.collected_items = self.load_collected_items()
    
    def load_collected_items(self) -> set:
        """Load previously collected item IDs to avoid duplicates"""
        collected_file = f"{self.data_dir}/collected_items.json"
        if os.path.exists(collected_file):
            with open(collected_file, 'r') as f:
                data = json.load(f)
                return set(data.get('items', []))
        return set()
    
    def save_collected_items(self):
        """Save collected item IDs"""
        collected_file = f"{self.data_dir}/collected_items.json"
        with open(collected_file, 'w') as f:
            json.dump({
                'items': list(self.collected_items),
                'last_updated': datetime.now().isoformat(),
                'total_items': len(self.collected_items)
            }, f, indent=2)
    
    def search_digital_collections(self, keywords: List[str], period: str, 
                                 start_year: int, end_year: int, 
                                 page: int = 1, per_page: int = 100) -> Dict:
        """Search LC digital collections for Black history materials"""
        
        # Build search query
        query_parts = []
        for keyword in keywords[:3]:  # Limit to avoid too complex queries
            query_parts.append(f'"{keyword}"')
        
        search_query = " OR ".join(query_parts)
        
        params = {
            'q': search_query,
            'fo': 'json',
            'c': 100,  # results per page
            'sp': page,
            'dates': f'{start_year}-{end_year}',
            'original-format': 'photo,print,drawing,poster,map,manuscript,book'
        }
        
        try:
            response = requests.get(f"{self.search_api}/", params=params, timeout=30)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                logger.warning(f"Non-JSON response for {search_query}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Search error for {search_query}: {e}")
            return {}
    
    def extract_item_details(self, item: Dict) -> Optional[Dict]:
        """Extract detailed information from search result item"""
        try:
            # Generate unique ID for this item
            item_id = item.get('id', '')
            if not item_id:
                # Create ID from URL or title
                url = item.get('url', '')
                title = item.get('title', '')
                item_id = hashlib.md5(f"{url}{title}".encode()).hexdigest()
            
            # Skip if we've already collected this
            if item_id in self.collected_items:
                return None
            
            details = {
                'id': item_id,
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'description': item.get('description', ''),
                'date': item.get('date', ''),
                'creator': item.get('creator', ''),
                'subject': item.get('subject', []),
                'type': item.get('original_format', ''),
                'collection': item.get('partof', []),
                'repository': item.get('repository', ''),
                'rights': item.get('rights', ''),
                'call_number': item.get('shelf_id', ''),
                'digital_id': item.get('digital_id', ''),
                'thumbnail_url': item.get('image_url', ''),
                'full_text': item.get('full_text', ''),
                'extracted_text': '',
                'analysis': '',
                'collected_date': datetime.now().isoformat(),
                'keywords_matched': [],
                'historical_period': '',
                'significance_score': 0
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error extracting item details: {e}")
            return None
    
    def analyze_historical_significance(self, item: Dict, period: str) -> Dict:
        """Analyze the historical significance of collected item"""
        
        title = item.get('title', '').lower()
        description = item.get('description', '').lower()
        text_content = f"{title} {description} {item.get('full_text', '')}".lower()
        
        significance_indicators = {
            'slavery_era': [
                'slave narrative', 'runaway', 'auction', 'plantation records',
                'freedom papers', 'manumission', 'underground railroad',
                'rebellion', 'resistance', 'escape', 'overseer records'
            ],
            'reconstruction': [
                'freedmen bureau', 'voting', 'citizenship', 'land ownership',
                'schools', 'churches', 'political participation',
                'violence', 'klan', 'black codes', 'sharecropping'
            ],
            'jim_crow_resistance': [
                'protest', 'organization', 'NAACP', 'civil rights',
                'lynching', 'segregation', 'resistance', 'migration',
                'business', 'education', 'newspapers', 'activism'
            ]
        }
        
        # Calculate significance score
        score = 0
        matched_keywords = []
        
        period_indicators = significance_indicators.get(period, [])
        for indicator in period_indicators:
            if indicator in text_content:
                score += 1
                matched_keywords.append(indicator)
        
        # Additional scoring based on content type
        if any(word in text_content for word in ['rare', 'unique', 'only known', 'first']):
            score += 2
        
        if any(word in text_content for word in ['photograph', 'daguerreotype', 'image']):
            score += 1
        
        if any(word in text_content for word in ['manuscript', 'handwritten', 'original']):
            score += 1
        
        # Generate analysis
        analysis = self.generate_item_analysis(item, matched_keywords, period)
        
        return {
            'significance_score': score,
            'matched_keywords': matched_keywords,
            'analysis': analysis,
            'historical_period': period
        }
    
    def generate_item_analysis(self, item: Dict, keywords: List[str], period: str) -> str:
        """Generate analytical summary of historical item"""
        
        title = item.get('title', 'Untitled')
        date = item.get('date', 'Unknown date')
        description = item.get('description', '')
        
        analysis = f"# Historical Analysis: {title}\n\n"
        analysis += f"**Period:** {period.replace('_', ' ').title()}\n"
        analysis += f"**Date:** {date}\n"
        analysis += f"**Significance Score:** {item.get('significance_score', 0)}\n\n"
        
        analysis += "## Historical Context\n"
        if period == 'slavery_era':
            analysis += "This item documents the period of American slavery (1770-1865), "
            analysis += "providing evidence of the systematic oppression and resistance during this era.\n\n"
        elif period == 'reconstruction':
            analysis += "This item documents the Reconstruction period (1865-1877), "
            analysis += "showing the brief moment of Black political power and the violent backlash that followed.\n\n"
        elif period == 'jim_crow_resistance':
            analysis += "This item documents the Jim Crow era (1877-1955), "
            analysis += "revealing both systematic oppression and organized Black resistance.\n\n"
        
        if keywords:
            analysis += f"## Key Historical Elements\n"
            analysis += f"This item relates to: {', '.join(keywords)}\n\n"
        
        if description:
            analysis += f"## Description\n{description}\n\n"
        
        analysis += "## Preservation Note\n"
        analysis += f"Collected as part of comprehensive Black history preservation project. "
        analysis += f"Original source: Library of Congress Digital Collections.\n"
        
        return analysis
    
    def save_item(self, item: Dict, period: str):
        """Save collected item to appropriate files"""
        
        item_id = item['id']
        
        # Save raw data as JSON
        json_file = f"{self.documents_dir}/{period}_{item_id}.json"
        with open(json_file, 'w') as f:
            json.dump(item, f, indent=2)
        
        # Save analysis as Markdown
        if item.get('analysis'):
            md_file = f"{self.analysis_dir}/{period}_{item_id}.md"
            with open(md_file, 'w') as f:
                f.write(item['analysis'])
        
        # Add to collected items
        self.collected_items.add(item_id)
        
        logger.info(f"Saved {period} item: {item.get('title', 'Untitled')[:50]}...")
    
    def collect_period_data(self, period: str, max_items: int = 500):
        """Collect data for specific historical period"""
        
        logger.info(f"Starting collection for {period}")
        
        period_config = self.historical_periods[period]
        keywords = period_config['keywords']
        start_year = period_config['start_year']
        end_year = period_config['end_year']
        
        items_collected = 0
        page = 1
        
        while items_collected < max_items:
            logger.info(f"Searching {period} - Page {page}")
            
            # Search for items
            results = self.search_digital_collections(
                keywords, period, start_year, end_year, page
            )
            
            if not results or 'results' not in results:
                logger.info(f"No more results for {period}")
                break
            
            items = results['results']
            if not items:
                break
            
            for item in items:
                if items_collected >= max_items:
                    break
                
                # Extract and analyze item
                details = self.extract_item_details(item)
                if not details:
                    continue
                
                # Analyze historical significance
                analysis_data = self.analyze_historical_significance(details, period)
                details.update(analysis_data)
                
                # Only save items with some significance
                if details['significance_score'] > 0:
                    self.save_item(details, period)
                    items_collected += 1
                
                # Rate limiting
                time.sleep(0.5)
            
            page += 1
            
            # Save progress periodically
            if items_collected % 50 == 0:
                self.save_collected_items()
        
        logger.info(f"Completed {period}: {items_collected} items collected")
        return items_collected
    
    def generate_period_summary(self, period: str):
        """Generate summary report for collected period data"""
        
        # Count files for this period
        period_files = [f for f in os.listdir(self.documents_dir) if f.startswith(period)]
        
        summary = f"# {period.replace('_', ' ').title()} Collection Summary\n\n"
        summary += f"**Collection Date:** {datetime.now().strftime('%Y-%m-%d')}\n"
        summary += f"**Total Items:** {len(period_files)}\n\n"
        
        summary += "## Collection Focus\n"
        period_config = self.historical_periods[period]
        summary += f"**Period:** {period_config['start_year']}-{period_config['end_year']}\n"
        summary += f"**Keywords:** {', '.join(period_config['keywords'][:10])}...\n\n"
        
        summary += "## Significance\n"
        summary += "This collection preserves crucial Black historical materials "
        summary += "that document both systematic oppression and community resistance. "
        summary += "These primary sources provide evidence often missing from mainstream historical narratives.\n\n"
        
        summary += "## Next Steps\n"
        summary += "- Continue expanding collection\n"
        summary += "- Develop thematic analyses\n"
        summary += "- Create educational resources\n"
        summary += "- Build searchable database\n"
        
        # Save summary
        summary_file = f"{self.analysis_dir}/{period}_summary.md"
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        return summary
    
    def run_collection(self, periods: List[str] = None, items_per_period: int = 200):
        """Run the complete collection process"""
        
        if not periods:
            # Default: start with oldest materials
            periods = ['slavery_era', 'reconstruction', 'jim_crow_resistance']
        
        logger.info("Starting Black History Data Collection")
        
        total_collected = 0
        
        for period in periods:
            logger.info(f"\n=== COLLECTING {period.upper()} ===")
            
            collected = self.collect_period_data(period, items_per_period)
            total_collected += collected
            
            # Generate summary
            self.generate_period_summary(period)
            
            # Save progress
            self.save_collected_items()
            
            logger.info(f"Period {period} complete: {collected} items")
            
            # Longer pause between periods
            time.sleep(2)
        
        logger.info(f"\nCollection complete! Total items: {total_collected}")
        
        # Generate overall summary
        self.generate_overall_summary(total_collected)
    
    def generate_overall_summary(self, total_items: int):
        """Generate overall collection summary"""
        
        summary = f"# Black History Digital Preservation Project\n\n"
        summary += f"**Total Items Collected:** {total_items}\n"
        summary += f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        summary += "## Mission\n"
        summary += "Systematically collect and preserve Black historical materials from the "
        summary += "Library of Congress digital collections, focusing on the oldest and "
        summary += "most difficult-to-access records that document both oppression and resistance.\n\n"
        
        summary += "## Coverage\n"
        for period in self.historical_periods:
            config = self.historical_periods[period]
            summary += f"- **{period.replace('_', ' ').title()}** "
            summary += f"({config['start_year']}-{config['end_year']})\n"
        
        summary += "\n## Repository Structure\n"
        summary += "```\n"
        summary += "data/\n"
        summary += "├── documents/     # Raw JSON data for each item\n"
        summary += "├── analysis/      # Markdown analyses and summaries\n"
        summary += "└── images/        # Downloaded historical images\n"
        summary += "```\n\n"
        
        summary += "## Significance\n"
        summary += "This collection ensures crucial Black historical materials remain "
        summary += "accessible and preserved for future generations, researchers, and "
        summary += "community organizers working for justice.\n"
        
        # Save main README
        with open(f"{self.data_dir}/README.md", 'w') as f:
            f.write(summary)

def main():
    """Main execution function"""
    collector = BlackHistoryCollector()
    
    # Start with slavery era (oldest, hardest to find materials)
    collector.run_collection(
        periods=['slavery_era'],  # Start here, expand later
        items_per_period=100  # Manageable batch size
    )

if __name__ == "__main__":
    main()