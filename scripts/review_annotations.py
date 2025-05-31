#!/usr/bin/env python3
"""Interactive annotation review and editing"""

import re
from pathlib import Path
import subprocess

class AnnotationReviewer:
    def __init__(self):
        self.tag_pattern = re.compile(r'\*\*\[([^\]]+)\]\*\*')
    
    def extract_tags(self, content):
        """Extract all tags from content"""
        return self.tag_pattern.findall(content)
    
    def validate_tags(self, tags):
        """Validate tags against Dignity Lens requirements"""
        required_domains = ['DOMAIN:POWER_STRUCTURES', 'DOMAIN:CONTROL_MECHANISMS', 
                           'DOMAIN:COMMUNITY_RESISTANCE', 'DOMAIN:LIBERATION_STRATEGIES']
        
        found_domains = [tag for tag in tags if tag.startswith('DOMAIN:')]
        missing_domains = [d for d in required_domains if d not in found_domains]
        
        return {
            'total_tags': len(tags),
            'domain_tags': found_domains,
            'missing_domains': missing_domains,
            'era_tags': [tag for tag in tags if tag.startswith('ERA:')],
            'case_tags': [tag for tag in tags if tag.startswith('CASE:')]
        }
    
    def review_file(self, filepath):
        """Review single file annotations"""
        with open(filepath, 'r') as f:
            content = f.read()
        
        tags = self.extract_tags(content)
        validation = self.validate_tags(tags)
        
        print(f"\n=== REVIEWING: {filepath} ===")
        print(f"Total tags: {validation['total_tags']}")
        print(f"Domain coverage: {len(validation['domain_tags'])}/4")
        print(f"Missing domains: {validation['missing_domains']}")
        print(f"Era connections: {len(validation['era_tags'])}")
        print(f"Case studies: {len(validation['case_tags'])}")
        
        if validation['total_tags'] < 50:
            print("⚠️  WARNING: Less than 50 tags (minimum requirement)")
        
        if validation['missing_domains']:
            print("⚠️  WARNING: Missing required domain coverage")
        
        # Open in editor for manual review
        choice = input("\nOpen in VS Code for manual review? (y/n): ")
        if choice.lower() == 'y':
            subprocess.run(['code', str(filepath)])

if __name__ == "__main__":
    reviewer = AnnotationReviewer()
    
    for md_file in Path('content/studies/').glob('*.md'):
        reviewer.review_file(md_file)
