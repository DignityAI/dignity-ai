#!/usr/bin/env python3
import os
import re
import anthropic
import frontmatter
from pathlib import Path

class DignityAnnotator:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.tag_patterns = self.load_tag_patterns()
    
    def load_tag_patterns(self):
        return {
            'domains': ['POWER_STRUCTURES', 'CONTROL_MECHANISMS', 'COMMUNITY_RESISTANCE', 'LIBERATION_STRATEGIES'],
            'eras': ['ENSLAVEMENT', 'RECONSTRUCTION', 'JIM_CROW', 'CIVIL_RIGHTS', 'MASS_INCARCERATION', 'DIGITAL_REBELLION', 'ABOLITIONIST_FUTURING'],
            'mechanisms': ['POLICE_TARGETING', 'ECONOMIC_EXCLUSION', 'GEOGRAPHIC_CONTAINMENT', 'EDUCATIONAL_LIMITATION'],
            'strategies': ['COMMUNITY_LAND_TRUSTS', 'WORKER_COOPERATIVES', 'ELECTORAL_ORGANIZING', 'MUTUAL_AID']
        }
    
    def annotate_document(self, content, filename):
        system_prompt = """You are an expert annotator for the Dignity Lens Framework. 
        
        Add hierarchical tags throughout this document using this exact format:
        **[CATEGORY:SPECIFIC_ELEMENT]** for major concepts
        **[CONCEPT_NAME]** for standalone important terms
        
        REQUIRED TAG CATEGORIES:
        - DOMAIN: [DOMAIN:POWER_STRUCTURES], [DOMAIN:CONTROL_MECHANISMS], [DOMAIN:COMMUNITY_RESISTANCE], [DOMAIN:LIBERATION_STRATEGIES]
        - ERA: [ERA:ENSLAVEMENT], [ERA:RECONSTRUCTION], [ERA:JIM_CROW], [ERA:CIVIL_RIGHTS], [ERA:MASS_INCARCERATION], [ERA:DIGITAL_REBELLION], [ERA:ABOLITIONIST_FUTURING]
        - MECHANISM: [MECHANISM:POLICE_TARGETING], [MECHANISM:ECONOMIC_EXCLUSION], etc.
        - STRATEGY: [STRATEGY:COMMUNITY_LAND_TRUSTS], [STRATEGY:WORKER_COOPERATIVES], etc.
        - CASE: [CASE:SANDRA_BLAND], [CASE:FLINT_WATER_CRISIS], etc.
        - Proper nouns: [PERSON_NAME], [LOCATION], [ORGANIZATION_NAME]
        
        Minimum 50 tags per document. Focus on concepts that will help AI understand systematic patterns."""
        
        user_prompt = f"""Annotate this Dignity Lens document: {filename}

        Content:
        {content}
        
        Return the fully annotated version with all tags added."""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8000,
                temperature=0.1,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Error annotating {filename}: {e}")
            return content
    
    def process_directory(self, content_dir):
        """Process all markdown files in content directory"""
        content_path = Path(content_dir)
        
        for md_file in content_path.glob("**/*.md"):
            print(f"Processing: {md_file}")
            
            # Read file with frontmatter
            with open(md_file, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
            
            # Skip if already annotated
            if post.metadata.get('annotated'):
                print(f"Skipping {md_file} - already annotated")
                continue
            
            # Annotate content
            annotated_content = self.annotate_document(post.content, md_file.name)
            
            # Update metadata
            post.metadata['annotated'] = True
            post.metadata['annotation_date'] = datetime.now().isoformat()
            post.content = annotated_content
            
            # Write back
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))
            
            print(f"Annotated: {md_file}")

if __name__ == "__main__":
    annotator = DignityAnnotator(os.getenv('CLAUDE_API_KEY'))
    annotator.process_directory('content/studies/')
