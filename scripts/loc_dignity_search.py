#!/usr/bin/env python3
"""
Standalone Library of Congress API Integration for DignityAI
Designed to work with separate Claude workflows
Searches Black history materials across Dignity Lens domains (slave era & reconstruction)
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

class LOCDiginityAPI:
    """Library of Congress API client for Dignity Lens historical research"""
    
    def __init__(self):
        self.base_url = "https://www.loc.gov/search/"
        self.api_params = {
            'fo': 'json',  # JSON format
            'at': '!online-format:image,audio',  # Exclude images and audio for text analysis
            'c': 50,  # Results per page
        }
        
        # Dignity Lens Domain Keywords
        self.domain_keywords = {
            "power_structures": [
                "plantation owner", "slave master", "overseer", "government", "legislation",
                "congress", "senate", "president", "governor", "mayor", "official",
                "authority", "control", "decision", "policy", "law", "regulation",
                "institution", "administration", "bureaucracy", "leadership"
            ],
            "control_mechanisms": [
                "slave patrol", "fugitive slave", "black codes", "jim crow", "lynching",
                "violence", "punishment", "surveillance", "restriction", "prohibition",
                "segregation", "discrimination", "exclusion", "containment", "suppression",
                "enforcement", "police", "military", "terror", "intimidation"
            ],
            "community_resistance": [
                "underground railroad", "rebellion", "revolt", "resistance", "escape",
                "organize", "organizing", "protest", "strike", "boycott", "petition",
                "mutual aid", "church", "community", "network", "coalition",
                "freedom", "liberation", "rights", "activism", "movement"
            ],
            "liberation_strategies": [
                "abolition", "emancipation", "reconstruction", "civil rights", "education",
                "institution building", "economic development", "political participation",
                "voting", "representation", "leadership", "organization", "strategy",
                "success", "victory", "achievement", "progress", "advancement"
            ]
        }
        
        # Historical period search terms
        self.period_terms = {
            "slave_era": [
                "slavery", "enslaved", "slave", "plantation", "antebellum",
                "1619", "1776", "1800", "1820", "1840", "1850", "1860",
                "colonial", "revolutionary", "early republic"
            ],
            "reconstruction": [
                "reconstruction", "freedmen", "freedpeople", "emancipation",
                "thirteenth amendment", "fourteenth amendment", "fifteenth amendment",
                "1865", "1866", "1867", "1868", "1869", "1870", "1871", "1872", "1873", "1874", "1875", "1876", "1877",
                "freedmens bureau", "black codes", "carpetbagger", "scalawag"
            ]
        }
        
        # Subject areas to focus on
        self.subject_areas = [
            "African Americans", "slavery", "slaves", "freedmen", "plantation",
            "civil rights", "abolition", "emancipation", "reconstruction",
            "black history", "negro", "colored", "freedpeople"
        ]

    def build_search_query(self, domain, period, additional_terms=None):
        """Build targeted search query for specific domain and period"""
        domain_terms = self.domain_keywords.get(domain, [])
        period_terms = self.period_terms.get(period, [])
        
        # Combine terms strategically
        core_terms = []
        
        # Add subject area
        core_terms.extend(["African Americans", "slavery", "slaves"])
        
        # Add period-specific terms
        if period_terms:
            core_terms.extend(period_terms[:3])  # Top 3 period terms
        
        # Add domain-specific terms
        if domain_terms:
            core_terms.extend(domain_terms[:5])  # Top 5 domain terms
        
        # Add any additional terms
        if additional_terms:
            core_terms.extend(additional_terms)
        
        # Create search query
        query = ' OR '.join([f'"{term}"' for term in core_terms[:10]])  # Limit to 10 terms max
        
        return query

    def search_loc(self, query, start=1, count=50):
        """Execute search against Library of Congress API"""
        try:
            params = self.api_params.copy()
            params.update({
                'q': query,
                'sp': start,
                'c': count
            })
            
            logger.info(f"Searching LOC with query: {query[:100]}...")
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Add delay to be respectful of API
            time.sleep(1)
            
            return data
            
        except Exception as e:
            logger.error(f"Error searching LOC: {e}")
            return None

    def extract_relevant_content(self, item):
        """Extract relevant text content from LOC item"""
        content = {
            'title': '',
            'description': '',
            'subjects': [],
            'date': '',
            'url': '',
            'type': '',
            'contributors': [],
            'full_text': ''
        }
        
        try:
            # Basic metadata
            content['title'] = item.get('title', [''])[0] if item.get('title') else ''
            content['description'] = item.get('description', [''])[0] if item.get('description') else ''
            content['date'] = item.get('date', [''])[0] if item.get('date') else ''
            content['url'] = item.get('id', '')
            content['type'] = item.get('original_format', [''])[0] if item.get('original_format') else ''
            
            # Subjects and contributors
            content['subjects'] = item.get('subject', []) or []
            content['contributors'] = item.get('contributor', []) or []
            
            # Try to get full text if available
            if 'text' in item:
                content['full_text'] = ' '.join(item['text']) if isinstance(item['text'], list) else str(item['text'])
            
            # Combine available text for analysis
            text_parts = [
                content['title'],
                content['description'],
                ' '.join(content['subjects']),
                content['full_text']
            ]
            
            content['combined_text'] = ' '.join([part for part in text_parts if part]).strip()
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return content

    def assess_content_relevance(self, content, domain, period):
        """Assess how relevant content is to specified domain and period"""
        text = content.get('combined_text', '').lower()
        
        if not text or len(text) < 50:
            return {'relevant': False, 'reason': 'Insufficient text content'}
        
        # Check for period relevance
        period_terms = self.period_terms.get(period, [])
        period_matches = sum(1 for term in period_terms if term.lower() in text)
        
        # Check for domain relevance
        domain_terms = self.domain_keywords.get(domain, [])
        domain_matches = sum(1 for term in domain_terms if term.lower() in text)
        
        # Check for general African American history relevance
        aa_terms = ['african american', 'negro', 'colored', 'black', 'slave', 'enslaved', 'freedmen', 'freedpeople']
        aa_matches = sum(1 for term in aa_terms if term in text)
        
        total_score = period_matches + domain_matches + aa_matches
        
        if total_score >= 3 and len(text) >= 100:
            return {
                'relevant': True, 
                'score': total_score,
                'period_matches': period_matches,
                'domain_matches': domain_matches,
                'aa_matches': aa_matches,
                'text_length': len(text)
            }
        else:
            return {
                'relevant': False, 
                'reason': f'Low relevance score: {total_score} (need >= 3)',
                'score': total_score
            }

    def search_domain_period(self, domain, period, max_results=25):
        """Search for materials in specific domain and period"""
        logger.info(f"🔍 Searching {domain} + {period}...")
        
        query = self.build_search_query(domain, period)
        results = self.search_loc(query, count=max_results * 2)  # Get extra to filter
        
        if not results or 'results' not in results:
            logger.warning(f"No results for {domain} + {period}")
            return []
        
        relevant_items = []
        
        for item in results['results'][:max_results * 2]:
            content = self.extract_relevant_content(item)
            relevance = self.assess_content_relevance(content, domain, period)
            
            if relevance['relevant']:
                content['relevance_score'] = relevance
                relevant_items.append(content)
                
                if len(relevant_items) >= max_results:
                    break
        
        logger.info(f"✅ Found {len(relevant_items)} relevant items for {domain} + {period}")
        return relevant_items

    def generate_comprehensive_search(self):
        """Generate comprehensive search across all domains and periods"""
        all_results = {}
        
        domains = list(self.domain_keywords.keys())
        periods = list(self.period_terms.keys())
        
        total_searches = len(domains) * len(periods)
        search_count = 0
        
        for period in periods:
            all_results[period] = {}
            
            for domain in domains:
                search_count += 1
                logger.info(f"🔍 Search {search_count}/{total_searches}: {period} × {domain}")
                
                results = self.search_domain_period(domain, period, max_results=15)
                all_results[period][domain] = results
                
                # Be respectful of API
                time.sleep(2)
        
        return all_results

    def save_results(self, results, filename=None):
        """Save search results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'loc_dignity_results_{timestamp}.json'
        
        # Create output directory
        os.makedirs('loc_results', exist_ok=True)
        filepath = os.path.join('loc_results', filename)
        
        # Add metadata
        output = {
            'generated_at': datetime.now().isoformat(),
            'search_type': 'dignity_lens_historical',
            'periods': list(self.period_terms.keys()),
            'domains': list(self.domain_keywords.keys()),
            'total_items': sum(len(items) for period in results.values() for items in period.values()),
            'results': results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to: {filepath}")
        return filepath

    def create_summary_report(self, results):
        """Create summary report of findings"""
        report_lines = [
            "# Library of Congress Dignity Lens Search Results",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Search Overview",
            "Searched Library of Congress digital collections for Black history materials",
            "focusing on slave era (1619-1865) and reconstruction (1865-1877) periods",
            "across four Dignity Lens domains.",
            ""
        ]
        
        # Summary statistics
        total_items = 0
        for period_name, period_data in results.items():
            report_lines.append(f"### {period_name.replace('_', ' ').title()}")
            period_total = 0
            
            for domain_name, domain_items in period_data.items():
                item_count = len(domain_items)
                period_total += item_count
                total_items += item_count
                
                report_lines.append(f"- **{domain_name.replace('_', ' ').title()}**: {item_count} items")
            
            report_lines.append(f"- **Period Total**: {period_total} items")
            report_lines.append("")
        
        report_lines.extend([
            f"## Total Items Found: {total_items}",
            "",
            "## Next Steps",
            "1. Review JSON results file for detailed item data",
            "2. Send relevant items to Claude for Dignity Lens analysis",
            "3. Generate case studies and educational content",
            "4. Build community organizing materials from historical insights",
            "",
            "---",
            "*Generated by DignityAI Library of Congress Integration*"
        ])
        
        return '\n'.join(report_lines)

def main():
    """Main execution function"""
    logger.info("🚀 Starting Library of Congress Dignity Lens search...")
    
    # Initialize API client
    loc_client = LOCDiginityAPI()
    
    # Perform comprehensive search
    logger.info("📚 Searching across all domains and periods...")
    results = loc_client.generate_comprehensive_search()
    
    # Save results
    logger.info("💾 Saving results...")
    results_file = loc_client.save_results(results)
    
    # Create summary report
    logger.info("📊 Creating summary report...")
    summary = loc_client.create_summary_report(results)
    
    # Save summary
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_file = f'loc_results/summary_report_{timestamp}.md'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    logger.info(f"📋 Summary saved to: {summary_file}")
    
    # Print summary to console
    print("\n" + "="*60)
    print(summary)
    print("="*60)
    
    logger.info("✅ Library of Congress search complete!")
    logger.info(f"📁 Check the loc_results/ directory for:")
    logger.info(f"   - {results_file}")
    logger.info(f"   - {summary_file}")

if __name__ == "__main__":
    main()