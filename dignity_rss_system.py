#!/usr/bin/env python3
"""
Dignity AI RSS System - Community-controlled AI for systematic racism education
"""

import os
import json
import requests
import feedparser
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from anthropic import Anthropic

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplifiedRSSSystem:
    """Simplified RSS system that's easy to implement"""
    
    def __init__(self):
        # Load API key
        self.api_key = os.environ.get('CLAUDE_API_KEY')
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY environment variable required")
        
        self.client = Anthropic(api_key=self.api_key)
        
        # Essential feeds (start with just a few good ones)
        self.feeds = {
            "chicago_tribune": {
                "url": "https://www.chicagotribune.com/arcio/rss/",
                "city": "Chicago",
                "priority": "high"
            },
            "block_club_chicago": {
                "url": "https://blockclubchicago.org/feed/",
                "city": "Chicago", 
                "priority": "high"
            },
            "npr_news": {
                "url": "https://www.npr.org/rss/rss.php?id=1001",
                "city": "National",
                "priority": "high"
            },
            "democracy_now": {
                "url": "https://www.democracynow.org/democracynow.rss",
                "city": "National",
                "priority": "high"
            },
            "propublica": {
                "url": "https://www.propublica.org/feeds/propublica/main",
                "city": "National",
                "priority": "high"
            }
        }
        
        # Keywords for filtering relevant content
        self.relevant_keywords = [
            'police', 'housing', 'school', 'education', 'healthcare', 'community',
            'discrimination', 'racism', 'inequality', 'organizing', 'protest',
            'city council', 'mayor', 'budget', 'development', 'gentrification',
            'eviction', 'tenant', 'worker', 'union', 'voting', 'immigration'
        ]
    
    def fetch_articles(self, max_articles_per_feed=3):
        """Fetch articles from RSS feeds"""
        all_articles = []
        
        for feed_name, feed_info in self.feeds.items():
            logger.info(f"Fetching from {feed_name}...")
            
            try:
                # Parse RSS feed
                feed = feedparser.parse(feed_info['url'])
                
                for entry in feed.entries[:max_articles_per_feed]:
                    # Check if article is relevant
                    title = entry.get('title', '').lower()
                    summary = entry.get('summary', '').lower()
                    content = f"{title} {summary}"
                    
                    # Calculate relevance score
                    relevance_score = sum(1 for keyword in self.relevant_keywords if keyword in content)
                    
                    if relevance_score > 0:  # Only include relevant articles
                        article = {
                            'title': entry.get('title', ''),
                            'url': entry.get('link', ''),
                            'summary': entry.get('summary', ''),
                            'published': entry.get('published', ''),
                            'source': feed_name,
                            'city': feed_info['city'],
                            'priority': feed_info['priority'],
                            'relevance_score': relevance_score,
                            'fetched_at': datetime.now().isoformat()
                        }
                        all_articles.append(article)
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching {feed_name}: {e}")
        
        # Sort by relevance score
        all_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        logger.info(f"Found {len(all_articles)} relevant articles")
        return all_articles
    
    def fetch_full_content(self, url):
        """Fetch full article content from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Try to find article content
            content_selectors = [
                'article', '.article-content', '.story-body', '.entry-content',
                '.post-content', '.content', 'main'
            ]
            
            article_content = ""
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    text = content_div.get_text(separator=' ', strip=True)
                    if len(text) > 300:
                        article_content = text
                        break
            
            # Clean up
            import re
            article_content = re.sub(r'\s+', ' ', article_content)
            
            return article_content if len(article_content) > 200 else None
            
        except Exception as e:
            logger.error(f"Error fetching full content from {url}: {e}")
            return None
    
    def generate_dignity_analysis(self, article):
        """Generate Dignity Lens analysis for an article"""
        
        # Try to get full content
        full_content = self.fetch_full_content(article['url'])
        content_to_analyze = full_content if full_content else article['summary']
        
        if not content_to_analyze or len(content_to_analyze) < 100:
            return None
        
        system_prompt = """You are Dignity AI, using the revolutionary Dignity Lens framework to analyze systematic racism.

Apply the 4 domains of analysis:
1. POWER STRUCTURES: Who controls decisions?
2. CONTROL MECHANISMS: How are communities contained?
3. COMMUNITY RESISTANCE: How do communities fight back?
4. LIBERATION STRATEGIES: What builds genuine power?

Connect to historical patterns and provide concrete organizing opportunities."""

        user_prompt = f"""
Analyze this news story using the Dignity Lens framework:

TITLE: {article['title']}
SOURCE: {article['source']} ({article['city']})
URL: {article['url']}

CONTENT:
{content_to_analyze[:3000]}

Provide:
1. Brief systematic analysis through the 4 domains
2. Historical connections to patterns of oppression
3. Concrete organizing opportunities for communities
4. Connections to other liberation movements

Keep analysis accessible but analytically rigorous (800-1000 words).
"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            return response.content[0].text if response.content else None
            
        except Exception as e:
            logger.error(f"Error generating analysis: {e}")
            return None
    
    def save_analysis(self, article, analysis, output_dir="dignity_analyses"):
        """Save analysis to file"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{article['source']}.json"
        filepath = os.path.join(output_dir, filename)
        
        data = {
            "article": article,
            "analysis": analysis,
            "generated_at": datetime.now().isoformat(),
            "framework": "Dignity Lens"
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved analysis to {filepath}")
        return filepath

def main():
    """Main function to run the RSS system"""
    
    # Check for API key
    if not os.environ.get('CLAUDE_API_KEY'):
        print("ERROR: Set CLAUDE_API_KEY environment variable first!")
        print("On Windows: set CLAUDE_API_KEY=your_key_here")
        print("On Mac/Linux: export CLAUDE_API_KEY=your_key_here")
        return
    
    # Initialize system
    rss_system = SimplifiedRSSSystem()
    
    # Fetch articles
    print("Fetching articles from RSS feeds...")
    articles = rss_system.fetch_articles()
    
    if not articles:
        print("No relevant articles found")
        return
    
    # Show top articles
    print(f"\nFound {len(articles)} relevant articles:")
    for i, article in enumerate(articles[:5]):
        print(f"{i+1}. [{article['relevance_score']}] {article['title'][:60]}...")
    
    # Generate analysis for top article
    print(f"\nGenerating Dignity Lens analysis for: {articles[0]['title']}")
    analysis = rss_system.generate_dignity_analysis(articles[0])
    
    if analysis:
        # Save analysis
        filepath = rss_system.save_analysis(articles[0], analysis)
        print(f"\nAnalysis saved to: {filepath}")
        
        # Show preview
        print(f"\nANALYSIS PREVIEW:")
        print("=" * 50)
        print(analysis[:500] + "...")
        print("=" * 50)
    else:
        print("Failed to generate analysis")

if __name__ == "__main__":
    main()
