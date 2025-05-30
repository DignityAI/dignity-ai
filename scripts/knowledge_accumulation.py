# knowledge_accumulation.py
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any

class LiberationKnowledgeSystem:
    """
    Persistent knowledge accumulation system for Liberation Technology
    Tracks power structures, organizing strategies, patterns, and case studies
    """
    
    def __init__(self):
        self.base_dirs = {
            'power_structures': 'knowledge/power-structures',
            'organizing_strategies': 'knowledge/organizing-strategies', 
            'pattern_maps': 'knowledge/pattern-maps',
            'case_index': 'knowledge/case-index'
        }
        self._create_directories()
        
    def _create_directories(self):
        """Create knowledge directory structure"""
        for dir_path in self.base_dirs.values():
            os.makedirs(dir_path, exist_ok=True)
    
    def extract_power_structures(self, content: str, location: str, domain: str) -> Dict[str, Any]:
        """
        Extract power structure information from case study content
        """
        power_structure = {
            'location': location,
            'domain': domain,
            'last_updated': datetime.now().isoformat(),
            'key_actors': [],
            'institutions': [],
            'funding_sources': [],
            'control_mechanisms': [],
            'policies': []
        }
        
        # Extract key actors (officials, agencies, corporations)
        actor_patterns = [
            r'(Mayor|Governor|Police Chief|Superintendent|CEO|Director)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+(Mayor|Governor|Police Chief|Superintendent|CEO|Director)',
            r'(Chicago Police Department|Austin ISD|Los Angeles City Council|[A-Z][a-z]+\s+Department)',
        ]
        
        for pattern in actor_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    power_structure['key_actors'].extend([m for m in match if m.strip()])
                else:
                    power_structure['key_actors'].append(match)
        
        # Extract institutions
        institution_patterns = [
            r'(City Council|School Board|Police Department|Health Department|Housing Authority)',
            r'([A-Z][a-z]+\s+(Corporation|Company|LLC|Inc))',
        ]
        
        for pattern in institution_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            power_structure['institutions'].extend([m[0] if isinstance(m, tuple) else m for m in matches])
        
        # Extract control mechanisms
        control_patterns = [
            r'(surveillance|policing|budget cuts|privatization|gentrification)',
            r'(voter suppression|gerrymandering|redlining|discrimination)',
        ]
        
        for pattern in control_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            power_structure['control_mechanisms'].extend(matches)
        
        # Remove duplicates
        for key in ['key_actors', 'institutions', 'control_mechanisms']:
            power_structure[key] = list(set(power_structure[key]))
            
        return power_structure
    
    def save_power_structure(self, power_structure: Dict[str, Any]):
        """Save power structure to persistent storage"""
        location = power_structure['location'].lower().replace(' ', '-')
        domain = power_structure['domain'].lower().replace(' ', '-')
        filename = f"{location}-{domain}.json"
        filepath = os.path.join(self.base_dirs['power_structures'], filename)
        
        # Load existing if it exists, merge with new data
        existing = {}
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                existing = json.load(f)
        
        # Merge new data with existing
        for key in ['key_actors', 'institutions', 'control_mechanisms', 'policies']:
            if key in existing:
                existing[key] = list(set(existing.get(key, []) + power_structure.get(key, [])))
            else:
                existing[key] = power_structure.get(key, [])
        
        existing.update({
            'location': power_structure['location'],
            'domain': power_structure['domain'],
            'last_updated': power_structure['last_updated']
        })
        
        with open(filepath, 'w') as f:
            json.dump(existing, f, indent=2)
        
        print(f"📊 Updated power structure: {filename}")
    
    def extract_organizing_strategies(self, content: str) -> List[Dict[str, Any]]:
        """Extract organizing strategies from case study content"""
        strategies = []
        
        # Common organizing strategy patterns
        strategy_patterns = [
            r'(community organizing|coalition building|direct action|boycott|protest)',
            r'(voter registration|electoral organizing|policy advocacy|legal challenge)',
            r'(mutual aid|cooperative|community land trust|worker cooperative)',
            r'(media campaign|digital organizing|know your rights|community education)',
        ]
        
        strategy_indicators = [
            'Liberation Strategies:', 'Community Resistance:', 'Organizing Opportunities:',
            'What Worked:', 'Successful Strategies:', 'Community Power Building:'
        ]
        
        # Extract sections that contain strategies
        for indicator in strategy_indicators:
            if indicator in content:
                # Get text after the indicator
                start_idx = content.find(indicator)
                # Find next major section or end
                next_section = start_idx + 1000  # Default chunk size
                for next_indicator in ['##', '###', 'Conclusion:', 'References:']:
                    idx = content.find(next_indicator, start_idx + len(indicator))
                    if idx != -1 and idx < next_section:
                        next_section = idx
                
                strategy_text = content[start_idx:next_section]
                
                # Extract specific strategies
                for pattern in strategy_patterns:
                    matches = re.findall(pattern, strategy_text, re.IGNORECASE)
                    for match in matches:
                        strategies.append({
                            'name': match,
                            'context': strategy_text[:200] + '...',
                            'extracted_from': indicator,
                            'date_added': datetime.now().isoformat()
                        })
        
        return strategies
    
    def save_organizing_strategy(self, strategy: Dict[str, Any]):
        """Save organizing strategy to persistent registry"""
        strategy_name = strategy['name'].lower().replace(' ', '-')
        filename = f"{strategy_name}.json"
        filepath = os.path.join(self.base_dirs['organizing_strategies'], filename)
        
        # Load existing or create new
        existing = {'examples': [], 'tactics': [], 'conditions': [], 'risks': []}
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                existing = json.load(f)
        
        # Add new example
        existing['examples'].append({
            'context': strategy['context'],
            'source': strategy['extracted_from'],
            'date': strategy['date_added']
        })
        
        existing.update({
            'name': strategy['name'],
            'last_updated': datetime.now().isoformat()
        })
        
        with open(filepath, 'w') as f:
            json.dump(existing, f, indent=2)
    
    def update_pattern_map(self, pattern_name: str, content: str, era: str):
        """Update historical pattern tracking"""
        filename = f"{pattern_name.lower().replace(' ', '-')}.json"
        filepath = os.path.join(self.base_dirs['pattern_maps'], filename)
        
        # Load existing pattern map
        pattern_map = {
            'pattern_name': pattern_name,
            'eras': {
                'enslavement_resistance': {},
                'reconstruction_backlash': {},
                'jim_crow_institution_building': {},
                'civil_rights_black_power': {},
                'neoliberalization_mass_incarceration': {},
                'digital_rebellion_corporate_capture': {},
                'abolitionist_futuring_ai_counterinsurgency': {}
            },
            'last_updated': datetime.now().isoformat()
        }
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                pattern_map = json.load(f)
        
        # Add content to appropriate era
        era_key = era.lower().replace(' ', '_').replace('-', '_')
        if era_key in pattern_map['eras']:
            if 'examples' not in pattern_map['eras'][era_key]:
                pattern_map['eras'][era_key]['examples'] = []
            
            pattern_map['eras'][era_key]['examples'].append({
                'content_snippet': content[:300] + '...',
                'date_added': datetime.now().isoformat()
            })
        
        pattern_map['last_updated'] = datetime.now().isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(pattern_map, f, indent=2)
    
    def index_case_study(self, title: str, content: str, city: str = None):
        """Add case study to searchable index"""
        index_file = os.path.join(self.base_dirs['case_index'], 'case-index.json')
        
        # Load existing index
        index = []
        if os.path.exists(index_file):
            with open(index_file, 'r') as f:
                index = json.load(f)
        
        # Extract themes and strategies from content
        themes = self._extract_themes(content)
        eras = self._extract_eras(content)
        strategies = [s['name'] for s in self.extract_organizing_strategies(content)]
        
        case_entry = {
            'title': title,
            'city': city,
            'themes': themes,
            'eras': eras,
            'strategies': strategies,
            'date_created': datetime.now().isoformat(),
            'content_preview': content[:500] + '...'
        }
        
        # Add to index
        index.append(case_entry)
        
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)
        
        print(f"📚 Indexed case study: {title}")
    
    def _extract_themes(self, content: str) -> List[str]:
        """Extract thematic tags from content"""
        theme_patterns = [
            r'(police violence|housing discrimination|educational inequality|healthcare racism)',
            r'(gentrification|voter suppression|mass incarceration|environmental racism)',
            r'(reproductive justice|immigration enforcement|economic exclusion|digital surveillance)'
        ]
        
        themes = []
        for pattern in theme_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            themes.extend(matches)
        
        return list(set(themes))
    
    def _extract_eras(self, content: str) -> List[str]:
        """Extract historical eras mentioned in content"""
        era_patterns = [
            r'(Enslavement|Reconstruction|Jim Crow|Civil Rights|Black Power)',
            r'(Mass Incarceration|Digital Era|Abolitionist)',
            r'(Era \d+|Historical Era)'
        ]
        
        eras = []
        for pattern in era_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            eras.extend(matches)
        
        return list(set(eras))
    
    def get_relevant_context(self, location: str = None, domain: str = None, themes: List[str] = None) -> Dict[str, Any]:
        """Retrieve relevant context for new case study generation"""
        context = {
            'power_structures': [],
            'organizing_strategies': [],
            'similar_cases': [],
            'historical_patterns': []
        }
        
        # Get relevant power structures
        if location and domain:
            ps_file = f"{location.lower().replace(' ', '-')}-{domain.lower().replace(' ', '-')}.json"
            ps_path = os.path.join(self.base_dirs['power_structures'], ps_file)
            if os.path.exists(ps_path):
                with open(ps_path, 'r') as f:
                    context['power_structures'].append(json.load(f))
        
        # Get organizing strategies
        strategy_dir = self.base_dirs['organizing_strategies']
        if os.path.exists(strategy_dir):
            for filename in os.listdir(strategy_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(strategy_dir, filename), 'r') as f:
                        context['organizing_strategies'].append(json.load(f))
        
        # Get similar cases from index
        index_file = os.path.join(self.base_dirs['case_index'], 'case-index.json')
        if os.path.exists(index_file) and themes:
            with open(index_file, 'r') as f:
                all_cases = json.load(f)
                for case in all_cases:
                    if any(theme in case.get('themes', []) for theme in themes):
                        context['similar_cases'].append(case)
        
        return context
    
    def process_case_study(self, title: str, content: str, city: str = None, domain: str = None):
        """Full processing pipeline for new case study"""
        print(f"🧠 Processing knowledge from: {title}")
        
        # Extract and save power structures
        if city and domain:
            power_structure = self.extract_power_structures(content, city, domain)
            self.save_power_structure(power_structure)
        
        # Extract and save organizing strategies
        strategies = self.extract_organizing_strategies(content)
        for strategy in strategies:
            self.save_organizing_strategy(strategy)
        
        # Update pattern maps
        themes = self._extract_themes(content)
        eras = self._extract_eras(content)
        
        for theme in themes:
            for era in eras:
                self.update_pattern_map(theme, content, era)
        
        # Index the case study
        self.index_case_study(title, content, city)
        
        print(f"✅ Knowledge accumulation complete for {title}")

# Integration function for main content generator
def integrate_knowledge_system():
    """Initialize and return knowledge system for use in content generation"""
    return LiberationKnowledgeSystem()

# Example usage in content generator
def enhanced_case_study_with_context(article, knowledge_system):
    """Generate case study with accumulated knowledge context"""
    
    # Extract location and domain from article
    location = extract_location_from_article(article)
    domain = extract_domain_from_article(article)
    themes = extract_themes_from_article(article)
    
    # Get relevant context from knowledge system
    context = knowledge_system.get_relevant_context(location, domain, themes)
    
    # Enhanced prompt with institutional memory
    context_prompt = f"""
INSTITUTIONAL MEMORY CONTEXT:

KNOWN POWER STRUCTURES in {location}:
{json.dumps(context['power_structures'], indent=2)}

PROVEN ORGANIZING STRATEGIES:
{json.dumps([s['name'] for s in context['organizing_strategies']], indent=2)}

SIMILAR PAST CASES:
{json.dumps([c['title'] for c in context['similar_cases']], indent=2)}

Use this accumulated knowledge to provide deeper analysis and more specific organizing recommendations.
"""
    
    return context_prompt

def extract_location_from_article(article):
    """Extract city/location from article content"""
    location_patterns = [
        r'(Chicago|Austin|Los Angeles|Philadelphia|Washington DC|Houston|Atlanta|Detroit)',
        r'([A-Z][a-z]+),\s+(Illinois|Texas|California|Pennsylvania)'
    ]
    
    content = article.get('title', '') + ' ' + article.get('content', '')
    for pattern in location_patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)
    return None

def extract_domain_from_article(article):
    """Extract policy domain from article content"""
    domain_patterns = [
        r'(police|housing|education|healthcare|environment|economic|immigration)',
        r'(criminal justice|public health|environmental|reproductive)'
    ]
    
    content = article.get('title', '') + ' ' + article.get('content', '')
    for pattern in domain_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def extract_themes_from_article(article):
    """Extract themes from article content"""
    content = article.get('title', '') + ' ' + article.get('content', '')
    theme_patterns = [
        r'(police violence|housing discrimination|educational inequality|healthcare racism)',
        r'(gentrification|voter suppression|mass incarceration|environmental racism)'
    ]
    
    themes = []
    for pattern in theme_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        themes.extend(matches)
    
    return list(set(themes))
