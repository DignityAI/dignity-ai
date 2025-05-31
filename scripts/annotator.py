#!/usr/bin/env python3
"""
Dignity Lens Framework Annotator
Specializes in annotating case studies with focus on Power Structures analysis
"""

import re
import spacy
from pathlib import Path
from typing import List, Dict, Set

class DignityAnnotator:
    def __init__(self):
        # Load spaCy model
        self.nlp = spacy.load('en_core_web_sm')
        
        # Define annotation patterns
        self.PATTERNS = {
            'DOMAINS': {
                'POWER_STRUCTURES': [
                    'decision-making', 'authority', 'control', 'governance',
                    'leadership', 'administration', 'management', 'oversight',
                    'power structure', 'systematic exclusion'
                ],
                'CONTROL_MECHANISMS': [
                    'systematic exclusion', 'closed-door meetings', 'appointed',
                    'technical expertise', 'resource barriers', 'corporate interests',
                    'containment', 'suppression', 'limitation'
                ],
                'COMMUNITY_RESISTANCE': [
                    'organizing', 'protest', 'resistance', 'coalition', 'direct action',
                    'challenge', 'movement', 'boycott', 'community power'
                ],
                'LIBERATION_STRATEGIES': [
                    'community-controlled', 'democratic', 'participatory',
                    'alternative institution', 'cooperative', 'collective action',
                    'liberation', 'freedom', 'justice'
                ]
            },
            'ERAS': {
                'ENSLAVEMENT': ['slavery', 'enslavement', '1600s-1865'],
                'RECONSTRUCTION': ['reconstruction', '1865-1877'],
                'JIM_CROW': ['jim crow', 'segregation', '1877-1954'],
                'CIVIL_RIGHTS': ['civil rights', '1954-1968'],
                'MASS_INCARCERATION': ['mass incarceration', 'prison', '1968-present'],
                'DIGITAL_REBELLION': ['digital', 'social media', 'algorithm'],
                'ABOLITIONIST_FUTURING': ['abolition', 'future', 'liberation']
            },
            'MECHANISMS': {
                'POLICE_TARGETING': ['police', 'law enforcement', 'surveillance'],
                'ECONOMIC_EXCLUSION': ['economic', 'financial', 'investment', 'development'],
                'GEOGRAPHIC_CONTAINMENT': ['zoning', 'district', 'boundary', 'neighborhood'],
                'EDUCATIONAL_LIMITATION': ['school', 'education', 'curriculum', 'testing'],
                'HEALTHCARE_RATIONING': ['health', 'medical', 'hospital', 'clinic'],
                'VOTER_SUPPRESSION': ['voting', 'election', 'representation']
            },
            'STRATEGIES': {
                'COMMUNITY_LAND_TRUSTS': ['land trust', 'community ownership'],
                'WORKER_COOPERATIVES': ['cooperative', 'worker-owned'],
                'ELECTORAL_ORGANIZING': ['electoral', 'voting', 'campaign'],
                'MUTUAL_AID': ['mutual aid', 'community support'],
                'LEGAL_CHALLENGES': ['legal', 'lawsuit', 'court'],
                'COMMUNITY_HEALTH_WORKERS': ['health worker', 'community health']
            }
        }

    def find_patterns(self, text: str, patterns: List[str]) -> Set[str]:
        """Find matching patterns in text"""
        matches = set()
        text_lower = text.lower()
        for pattern in patterns:
            if pattern.lower() in text_lower:
                matches.add(pattern)
        return matches

    def add_tag(self, text: str, tag: str, match: str) -> str:
        """Add a tag to text at the location of match"""
        if match not in text:
            return text
        tag_str = f'**[{tag}]**'
        if tag_str not in text:
            return text.replace(match, f'{tag_str} {match}', 1)
        return text

    def annotate_section(self, text: str) -> str:
        """Annotate a section of text with Dignity Lens tags"""
        annotated = text
        
        # Process with spaCy for named entities
        doc = self.nlp(text)
        
        # Add named entity tags
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                annotated = self.add_tag(annotated, 'PERSON_NAME', ent.text)
            elif ent.label_ == 'ORG':
                annotated = self.add_tag(annotated, 'ORGANIZATION_NAME', ent.text)
            elif ent.label_ == 'GPE':
                annotated = self.add_tag(annotated, 'LOCATION', ent.text)
            elif ent.label_ == 'DATE':
                annotated = self.add_tag(annotated, 'DATE', ent.text)
        
        # Add domain tags
        for domain_type, patterns in self.PATTERNS['DOMAINS'].items():
            matches = self.find_patterns(text, patterns)
            for match in matches:
                annotated = self.add_tag(annotated, f'DOMAIN:{domain_type}', match)
        
        # Add era tags
        for era, patterns in self.PATTERNS['ERAS'].items():
            matches = self.find_patterns(text, patterns)
            for match in matches:
                annotated = self.add_tag(annotated, f'ERA:{era}', match)
        
        # Add mechanism tags
        for mech, patterns in self.PATTERNS['MECHANISMS'].items():
            matches = self.find_patterns(text, patterns)
            for match in matches:
                annotated = self.add_tag(annotated, f'MECHANISM:{mech}', match)
        
        # Add strategy tags
        for strategy, patterns in self.PATTERNS['STRATEGIES'].items():
            matches = self.find_patterns(text, patterns)
            for match in matches:
                annotated = self.add_tag(annotated, f'STRATEGY:{strategy}', match)
        
        return annotated

    def validate_annotations(self, text: str) -> Dict:
        """Validate if text meets annotation requirements"""
        tag_pattern = re.compile(r'\*\*\[([^\]]+)\]\*\*')
        tags = tag_pattern.findall(text)
        
        domains = [t for t in tags if t.startswith('DOMAIN:')]
        eras = [t for t in tags if t.startswith('ERA:')]
        mechanisms = [t for t in tags if t.startswith('MECHANISM:')]
        strategies = [t for t in tags if t.startswith('STRATEGY:')]
        
        return {
            'total_tags': len(tags),
            'unique_domains': len(set(domains)),
            'unique_eras': len(set(eras)),
            'unique_mechanisms': len(set(mechanisms)),
            'unique_strategies': len(set(strategies)),
            'meets_requirements': all([
                len(tags) >= 50,
                len(set(domains)) >= 4,
                len(set(eras)) >= 3,
                len(set(mechanisms)) >= 5,
                len(set(strategies)) >= 5
            ])
        }

    def process_case_study(self, text: str, title: str = "") -> str:
        """Process a complete case study"""
        if title:
            print(f"Processing: {title}")
        
        # Split into sections based on markdown headers
        sections = re.split(r'\n### \*\*', text)
        
        annotated_sections = []
        for section in sections:
            if section.strip():
                print(f"Processing section: {section.split('\\n')[0]}")
                annotated_section = self.annotate_section(section)
                annotated_sections.append(annotated_section)
        
        annotated_text = '\n### **'.join(annotated_sections)
        
        # Validate
        validation = self.validate_annotations(annotated_text)
        print("\nValidation Results:")
        print(f"Total tags: {validation['total_tags']} (minimum 50 required)")
        print(f"Unique domains: {validation['unique_domains']}/4 required")
        print(f"Unique eras: {validation['unique_eras']}/3 required")
        print(f"Unique mechanisms: {validation['unique_mechanisms']}/5 required")
        print(f"Unique strategies: {validation['unique_strategies']}/5 required")
        print(f"Meets all requirements: {'✅' if validation['meets_requirements'] else '❌'}")
        
        return annotated_text

if __name__ == "__main__":
    from dotenv import load_dotenv
    import sys
    
    # Load environment variables
    load_dotenv()
    
    # Initialize annotator
    annotator = DignityAnnotator()
    
    # Process input file
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
        if not input_file.exists():
            print(f"Error: File not found - {input_file}")
            sys.exit(1)
            
        print(f"Processing file: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
            
        annotated_text = annotator.process_case_study(text, input_file.name)
        
        # Save output
        output_file = input_file.parent / f"annotated_{input_file.name}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(annotated_text)
            
        print(f"\nAnnotated file saved to: {output_file}")
    else:
        print("Usage: python annotator.py <input_file>")
        sys.exit(1)
