#!/usr/bin/env python3
"""
Library of Congress Workflow Processor for DignityAI
Takes LOC search results and processes them through Claude for Dignity Lens analysis
Generates case studies, community journalism, and educational content
"""

import json
import os
import sys
from datetime import datetime
from anthropic import Anthropic
import time
import logging
import glob

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Claude API
try:
    client = Anthropic(api_key=os.environ.get('CLAUDE_API_KEY') or os.environ.get('ANTHROPIC_API_KEY'))
    logger.info("✅ Anthropic client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Anthropic client: {e}")
    sys.exit(1)

class LOCWorkflowProcessor:
    """Processes Library of Congress results through Dignity Lens analysis"""
    
    def __init__(self):
        self.dignity_lens_framework = {
            "power_structures": {
                "title": "Power Structures",
                "question": "Who holds decision-making authority and how is it maintained?",
                "description": "Government institutions, corporate control, resource allocation, educational systems, media oversight, policy development, community exclusion from decision-making processes"
            },
            "control_mechanisms": {
                "title": "Control Mechanisms", 
                "question": "How are Black communities contained and suppressed?",
                "description": "Policing and surveillance systems, legal system manipulation, economic exclusion and exploitation, geographic containment, cultural suppression and narrative control"
            },
            "community_resistance": {
                "title": "Community Resistance",
                "question": "How do Black communities survive and fight back?", 
                "description": "Organizing strategies and movement building tactics, mutual aid and community care systems, cultural preservation and innovation as resistance"
            },
            "liberation_strategies": {
                "title": "Liberation Strategies",
                "question": "What has actually worked to build Black freedom and power?",
                "description": "Successful organizing innovations across eras, institution-building and alternative system creation, coalition-building and sustainable organizing approaches"
            }
        }
        
        self.historical_context = {
            "slave_era": {
                "period": "1619-1865",
                "context": "Foundation period of systematic oppression establishing legal frameworks for racial hierarchy, labor exploitation, and community survival strategies"
            },
            "reconstruction": {
                "period": "1865-1877", 
                "context": "Brief liberation moment followed by systematic rollback, establishing patterns of legal suppression, economic exclusion, and organized terror"
            }
        }

    def load_loc_results(self, results_file=None):
        """Load Library of Congress search results"""
        if not results_file:
            # Find most recent results file
            pattern = 'loc_results/loc_dignity_results_*.json'
            files = glob.glob(pattern)
            if not files:
                logger.error("No LOC results files found. Run loc_dignity_search.py first.")
                return None
            results_file = max(files, key=os.path.getctime)
        
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"✅ Loaded results from: {results_file}")
            return data
        except Exception as e:
            logger.error(f"Error loading results: {e}")
            return None

    def select_best_items(self, results_data, items_per_domain=3):
        """Select highest quality items for analysis"""
        selected_items = {}
        
        for period, period_data in results_data['results'].items():
            selected_items[period] = {}
            
            for domain, items in period_data.items():
                # Sort by relevance score and text length
                sorted_items = sorted(
                    items, 
                    key=lambda x: (
                        x.get('relevance_score', {}).get('score', 0),
                        len(x.get('combined_text', ''))
                    ),
                    reverse=True
                )
                
                # Select top items with substantial content
                selected = []
                for item in sorted_items:
                    if len(item.get('combined_text', '')) >= 200:  # Minimum length
                        selected.append(item)
                        if len(selected) >= items_per_domain:
                            break
                
                selected_items[period][domain] = selected
                logger.info(f"Selected {len(selected)} items for {period} + {domain}")
        
        return selected_items

    def create_historical_case_study_prompt(self, items, domain, period):
        """Create prompt for historical case study using LOC materials"""
        domain_info = self.dignity_lens_framework[domain]
        period_info = self.historical_context[period]
        
        # Prepare item summaries
        item_summaries = []
        for i, item in enumerate(items, 1):
            summary = f"""
            ITEM {i}:
            Title: {item.get('title', 'Unknown')}
            Date: {item.get('date', 'Unknown')}
            Type: {item.get('type', 'Unknown')}
            Content: {item.get('combined_text', '')[:1000]}...
            URL: {item.get('url', '')}
            """
            item_summaries.append(summary)
        
        items_text = '\n'.join(item_summaries)
        
        return f"""
You are DignityAI analyzing historical Library of Congress materials through the Dignity Lens framework.

DOMAIN FOCUS: {domain_info['title']}
Domain Question: {domain_info['question']}
Domain Description: {domain_info['description']}

HISTORICAL PERIOD: {period.replace('_', ' ').title()} ({period_info['period']})
Period Context: {period_info['context']}

LIBRARY OF CONGRESS MATERIALS:
{items_text}

Create a comprehensive historical case study (2000-2500 words) that:

1. **Historical Analysis**: Examine these LOC materials through the {domain_info['title']} lens
2. **Pattern Recognition**: Identify systematic patterns that connect to contemporary issues
3. **Community Agency**: Center Black community experiences and resistance strategies
4. **Contemporary Connections**: Draw explicit connections to modern organizing
5. **Educational Value**: Make complex historical analysis accessible for community education

Format as:
# {domain_info['title']} in {period.replace('_', ' ').title()}: Lessons from the Library of Congress

## Executive Summary
[2-3 sentences summarizing key findings]

## Historical Context: {period_info['period']}
[Set the stage with period overview]

## Library of Congress Evidence
[Analyze the specific materials, quoting and citing LOC sources]

## Dignity Lens Analysis: {domain_info['title']}
[Deep dive into how these materials reveal {domain_info['question'].lower()}]

## Patterns Across Time
[Connect historical patterns to contemporary systematic racism]

## Community Organizing Lessons
[What can current organizers learn from this history?]

## Contemporary Applications
[Specific Chicago organizing opportunities informed by this history]

## Conclusion
[Synthesis and call to action]

**Sources**: Cite all Library of Congress materials with titles, dates, and URLs.

Focus on building community power through historical understanding.
"""

    def create_community_education_prompt(self, items, domain, period):
        """Create prompt for accessible community education content"""
        domain_info = self.dignity_lens_framework[domain]
        period_info = self.historical_context[period]
        
        # Select most compelling item
        best_item = max(items, key=lambda x: len(x.get('combined_text', ''))) if items else {}
        
        return f"""
You are writing accessible community education content for DRC's People's History series.

HISTORICAL FOCUS: {period.replace('_', ' ').title()} ({period_info['period']})
DIGNITY LENS DOMAIN: {domain_info['title']} - {domain_info['question']}

FEATURED HISTORICAL SOURCE:
Title: {best_item.get('title', 'Unknown')}
Date: {best_item.get('date', 'Unknown')}
Content: {best_item.get('combined_text', '')[:800]}
URL: {best_item.get('url', '')}

Create accessible educational content (800-1000 words) that:
- Makes historical analysis accessible to general community readers
- Shows how {domain_info['title'].lower()} operated in {period.replace('_', ' ')}
- Connects historical patterns to current experiences
- Inspires community organizing through historical lessons
- Uses storytelling to make analysis engaging

Format as:
# The Real History They Don't Teach: {domain_info['title']} in {period.replace('_', ' ').title()}

## The Story They Don't Want You to Know
[Engaging opening using the LOC source]

## How the System Worked Then
[Explain {domain_info['title'].lower()} in accessible terms]

## The Pattern That Continues
[Connect to contemporary examples]

## What Our Ancestors Teach Us
[Organizing lessons for today]

## Taking Action Today
[Specific organizing opportunities in Chicago]

**Learn More**: [Include LOC source information]

Write for community members who may not have formal education but deserve to understand their history and power.
"""

    def create_organizer_briefing_prompt(self, all_items, period):
        """Create strategic briefing for community organizers"""
        period_info = self.historical_context[period]
        
        # Combine insights from all domains
        domain_summaries = []
        for domain, items in all_items.items():
            if items:
                domain_info = self.dignity_lens_framework[domain]
                best_item = items[0]  # Use top item
                summary = f"**{domain_info['title']}**: {best_item.get('title', 'Unknown')} - {best_item.get('combined_text', '')[:200]}..."
                domain_summaries.append(summary)
        
        domains_text = '\n'.join(domain_summaries)
        
        return f"""
You are creating a strategic briefing for Chicago community organizers.

HISTORICAL PERIOD: {period.replace('_', ' ').title()} ({period_info['period']})
CONTEXT: {period_info['context']}

LIBRARY OF CONGRESS INSIGHTS BY DOMAIN:
{domains_text}

Create a strategic organizer briefing (1200-1500 words) that:
1. Synthesizes insights across all four Dignity Lens domains
2. Identifies strategic patterns organizers should understand
3. Provides historical context for current organizing challenges
4. Offers tactical lessons from historical resistance
5. Connects to specific Chicago organizing opportunities

Format as:
# Organizer Briefing: {period.replace('_', ' ').title()} Lessons for Chicago

## Historical Context
[Why this period matters for current organizing]

## Strategic Insights by Domain
### Power Structures: Who Had Control?
### Control Mechanisms: How They Maintained It
### Community Resistance: How People Fought Back  
### Liberation Strategies: What Actually Worked

## Key Patterns for Organizers
[Strategic lessons that apply today]

## Chicago Applications
[Specific organizing opportunities informed by this history]

## Tactical Recommendations
[Concrete strategies based on historical analysis]

## Resources for Further Learning
[LOC sources and organizing connections]

Write for experienced organizers who understand systematic analysis.
"""

    def call_claude_api(self, prompt, max_retries=3):
        """Send prompt to Claude API with retry logic"""
        for attempt in range(max_retries):
            try:
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                time.sleep(2)  # Rate limiting
                return message.content[0].text
            except Exception as e:
                logger.error(f"Claude API error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    return None

    def save_content(self, content, content_type, filename_prefix):
        """Save generated content"""
        if not content:
            return
        
        # Create directory
        os.makedirs(f'loc_output/{content_type}', exist_ok=True)
        
        # Create filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'loc_output/{content_type}/{timestamp}_{filename_prefix}.md'
        
        # Save content
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"✅ Saved: {filename}")

    def process_historical_case_studies(self, selected_items):
        """Generate historical case studies for each domain/period combination"""
        logger.info("📚 Generating historical case studies...")
        
        for period, period_data in selected_items.items():
            for domain, items in period_data.items():
                if not items:
                    continue
                
                logger.info(f"🔍 Creating case study: {period} × {domain}")
                
                prompt = self.create_historical_case_study_prompt(items, domain, period)
                content = self.call_claude_api(prompt)
                
                if content:
                    filename = f"{period}_{domain}_case_study"
                    self.save_content(content, 'case_studies', filename)
                
                time.sleep(3)  # Rate limiting

    def process_community_education(self, selected_items):
        """Generate accessible community education content"""
        logger.info("🏫 Generating community education content...")
        
        for period, period_data in selected_items.items():
            for domain, items in period_data.items():
                if not items:
                    continue
                
                logger.info(f"📖 Creating education content: {period} × {domain}")
                
                prompt = self.create_community_education_prompt(items, domain, period)
                content = self.call_claude_api(prompt)
                
                if content:
                    filename = f"{period}_{domain}_education"
                    self.save_content(content, 'community_education', filename)
                
                time.sleep(3)  # Rate limiting

    def process_organizer_briefings(self, selected_items):
        """Generate strategic briefings for organizers"""
        logger.info("📋 Generating organizer briefings...")
        
        for period, period_data in selected_items.items():
            if not any(period_data.values()):  # Skip if no items in period
                continue
                
            logger.info(f"🎯 Creating organizer briefing: {period}")
            
            prompt = self.create_organizer_briefing_prompt(period_data, period)
            content = self.call_claude_api(prompt)
            
            if content:
                filename = f"{period}_organizer_briefing"
                self.save_content(content, 'organizer_briefings', filename)
            
            time.sleep(3)  # Rate limiting

    def create_master_summary(self, results_data, selected_items):
        """Create comprehensive summary of all generated content"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Count items processed
        total_processed = 0
        processing_summary = []
        
        for period, period_data in selected_items.items():
            period_total = 0
            period_details = []
            
            for domain, items in period_data.items():
                item_count = len(items)
                period_total += item_count
                total_processed += item_count
                
                if item_count > 0:
                    period_details.append(f"  - {domain.replace('_', ' ').title()}: {item_count} items")
            
            if period_total > 0:
                processing_summary.append(f"- **{period.replace('_', ' ').title()}**: {period_total} items")
                processing_summary.extend(period_details)
        
        summary_content = f"""# Library of Congress Dignity Lens Analysis Summary

**Generated**: {timestamp}  
**Total Historical Items Processed**: {total_processed}

## Processing Overview
{chr(10).join(processing_summary)}

## Content Generated

### 📚 Historical Case Studies
Deep analytical pieces examining each domain/period combination through the Dignity Lens framework. Located in `loc_output/case_studies/`

### 🏫 Community Education
Accessible educational content making historical analysis available to general community readers. Located in `loc_output/community_education/`

### 📋 Organizer Briefings
Strategic briefings synthesizing insights for community organizers. Located in `loc_output/organizer_briefings/`

## Key Insights Summary

### Slave Era (1619-1865)
Historical materials reveal systematic patterns of:
- **Power Structures**: Legal frameworks establishing racial hierarchy
- **Control Mechanisms**: Violence, surveillance, and movement restriction
- **Community Resistance**: Underground networks and cultural preservation
- **Liberation Strategies**: Institution building and strategic organizing

### Reconstruction (1865-1877)
Historical materials demonstrate:
- **Power Structures**: Federal intervention and local resistance to change
- **Control Mechanisms**: Legal rollback and organized terror campaigns
- **Community Resistance**: Political participation and institution building
- **Liberation Strategies**: Constitutional amendments and community organizing

## Next Steps

1. **Review Generated Content**: Examine case studies and educational materials in output directories
2. **Community Sharing**: Distribute educational content through DRC networks
3. **Organizer Training**: Use briefings for political education and strategy sessions
4. **Further Research**: Identify gaps and areas for deeper investigation

## File Locations

```
loc_output/
├── case_studies/          # Analytical case studies by domain/period
├── community_education/   # Accessible educational content
├── organizer_briefings/   # Strategic organizer briefings
└── summary_report.md      # This file
```

## Library of Congress Sources

All content references primary historical sources from the Library of Congress digital collections. Each piece includes proper citations and links to original materials for further research.

---

*Generated by DignityAI Library of Congress Workflow Processor*  
*Part of the Dignity Lens Framework developed by the Defy Racism Collective*
"""
        
        return summary_content

def main():
    """Main workflow processing function"""
    logger.info("🚀 Starting Library of Congress workflow processing...")
    
    # Initialize processor
    processor = LOCWorkflowProcessor()
    
    # Load LOC search results
    logger.info("📂 Loading Library of Congress search results...")
    results_data = processor.load_loc_results()
    
    if not results_data:
        logger.error("❌ No results data found. Run loc_dignity_search.py first.")
        return
    
    # Select best items for analysis
    logger.info("🎯 Selecting highest quality items for analysis...")
    selected_items = processor.select_best_items(results_data, items_per_domain=3)
    
    # Count total items to process
    total_items = sum(len(items) for period_data in selected_items.values() for items in period_data.values())
    logger.info(f"📊 Processing {total_items} high-quality historical items...")
    
    if total_items == 0:
        logger.warning("⚠️ No high-quality items found for processing.")
        return
    
    # Process content through different formats
    try:
        # Generate historical case studies
        processor.process_historical_case_studies(selected_items)
        
        # Generate community education content
        processor.process_community_education(selected_items)
        
        # Generate organizer briefings
        processor.process_organizer_briefings(selected_items)
        
        # Create master summary
        logger.info("📋 Creating master summary report...")
        summary = processor.create_master_summary(results_data, selected_items)
        
        # Save summary
        os.makedirs('loc_output', exist_ok=True)
        with open('loc_output/summary_report.md', 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info("✅ Library of Congress workflow processing complete!")
        logger.info(f"📁 Check loc_output/ directory for all generated content:")
        logger.info(f"   - case_studies/ - Deep analytical pieces")
        logger.info(f"   - community_education/ - Accessible educational content") 
        logger.info(f"   - organizer_briefings/ - Strategic briefings")
        logger.info(f"   - summary_report.md - Master summary")
        
    except Exception as e:
        logger.error(f"❌ Error during processing: {e}")
        raise

if __name__ == "__main__":
    main()