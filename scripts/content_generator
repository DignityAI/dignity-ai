# scripts/content_generator.py
import feedparser
import requests
from bs4 import BeautifulSoup
import os
import json
import yaml
from datetime import datetime
from anthropic import Anthropic
import time
import re
from urllib.parse import urljoin, urlparse

# Initialize Claude API
try:
    client = Anthropic(api_key=os.environ.get('CLAUDE_API_KEY'))
except Exception as e:
    print(f"Error initializing Claude API: {e}")
    print("Make sure CLAUDE_API_KEY environment variable is set")
    exit(1)

# RSS Feeds to monitor
RSS_FEEDS = [
    "https://billypenn.com/feed",
    "https://wtop.com/feed", 
    "https://www.kxan.com/feed",
    "https://ktla.com/feed",
    "https://wgntv.com/feed",
    "https://blockclubchicago.org/feed/",
]

# Keywords to filter relevant articles
RELEVANT_KEYWORDS = [
    'police', 'housing', 'health', 'school', 'education', 'city council',
    'mayor', 'budget', 'development', 'community', 'neighborhood',
    'crime', 'safety', 'racism', 'discrimination', 'inequality', 'tenant',
    'eviction', 'gentrification', 'affordable', 'CPS', 'teacher', 'student'
]

def call_claude_api(prompt, max_retries=3):
    """Send prompt to Claude API with retry logic"""
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-3-5-haiku-20241022", 
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            # Rate limiting - stay under API limits
            time.sleep(2)  # Increased delay
            return message.content[0].text
        except Exception as e:
            print(f"Claude API error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5)  # Wait before retry
            else:
                print(f"Failed after {max_retries} attempts")
                return None

def fetch_rss_articles():
    """Fetch articles from RSS feeds"""
    articles = []
    
    for feed_url in RSS_FEEDS:
        try:
            print(f"Fetching from {feed_url}...")
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                print(f"No entries found in {feed_url}")
                continue
                
            for entry in feed.entries[:3]:  # Limit to 3 per feed
                articles.append({
                    'title': getattr(entry, 'title', 'No Title'),
                    'content': getattr(entry, 'summary', ''),
                    'url': getattr(entry, 'link', ''),
                    'published': getattr(entry, 'published', ''),
                    'source': feed_url
                })
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")
    
    return articles

def filter_relevant_articles(articles):
    """Filter articles for relevant content"""
    relevant = []
    
    for article in articles:
        if not article.get('title') or not article.get('content'):
            continue
            
        text = (article['title'] + ' ' + article['content']).lower()
        if any(keyword in text for keyword in RELEVANT_KEYWORDS):
            relevant.append(article)
    
    return relevant

def fetch_full_article_content(url):
    """Fetch complete article content from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Get title
        title_element = soup.find('h1') or soup.find('title')
        title = title_element.get_text(strip=True) if title_element else ""
        
        # Get content
        content_selectors = [
            'article', '.article-content', '.story-body', '.entry-content',
            '.post-content', '.content', '.story', 'main'
        ]
        
        article_content = ""
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                text = content_div.get_text(separator=' ', strip=True)
                if len(text) > 300:
                    article_content = text
                    break
        
        # Clean up content
        article_content = re.sub(r'\s+', ' ', article_content)
        
        return {
            'title': title,
            'content': article_content,
            'url': url,
            'word_count': len(article_content.split())
        }
        
    except Exception as e:
        print(f"Error fetching content from {url}: {e}")
        return None

def assess_content_quality(article):
    """Determine if article has sufficient context"""
    if not article or not article.get('content'):
        return {'sufficient': False, 'reason': 'No content'}
    
    word_count = article.get('word_count', 0)
    
    if word_count < 200:
        return {'sufficient': False, 'reason': f'Too short ({word_count} words)'}
    
    return {'sufficient': True, 'word_count': word_count}

def create_case_study_prompt(article):
    """Create prompt for Dignity Lens case study"""
    return f"""
You are DignityAI, analyzing news through the Dignity Lens framework for community organizing.

ARTICLE TO ANALYZE:
Title: {article['title']}
Content: {article['content'][:2000]}...
Source: {article['url']}

Create a Dignity Lens case study (800-1000 words) analyzing this through the four domains:

# DIGNITY LENS ANALYSIS: {article['title'][:60]}

## Executive Summary
Brief overview connecting this story to systematic patterns.

## Power Structures
Who controls decision-making in this situation? What institutions have authority?

## Control Mechanisms  
How are communities contained or excluded? What policies or practices maintain inequality?

## Community Resistance
How are communities organizing or fighting back? What resistance strategies are evident?

## Liberation Strategies
What approaches could build genuine community power? What has worked in similar situations?

## Cross-City Connections
How does this pattern show up in other cities? What can communities learn from each other?

## Organizing Opportunities
Specific actions communities can take locally and regionally.

## Conclusion
Key takeaways for community organizing and systematic change.

Focus on actionable analysis that helps community organizers understand systematic patterns and develop effective strategies.
"""

def save_content(content, content_type, article_title):
    """Save generated content to appropriate folder"""
    if not content:
        return
    
    # Create directory
    os.makedirs(f'drafts/{content_type}', exist_ok=True)
    
    # Create filename
    date_str = datetime.now().strftime('%Y%m%d')
    safe_title = "".join(c for c in article_title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
    filename = f'drafts/{content_type}/{date_str}-{safe_title}.md'
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Saved: {filename}")
    except Exception as e:
        print(f"Error saving {filename}: {e}")

def main():
    """Main content generation function"""
    print("🚀 Starting content generation...")
    
    # Create directories
    for dir_name in ['drafts/case-studies', 'drafts/news-articles', 'drafts/blog-posts']:
        os.makedirs(dir_name, exist_ok=True)
    
    # Fetch articles
    print("📰 Fetching RSS articles...")
    articles = fetch_rss_articles()
    
    if not articles:
        print("❌ No articles found")
        return
    
    relevant_articles = filter_relevant_articles(articles)
    print(f"📋 Found {len(relevant_articles)} relevant articles")
    
    processed_count = 0
    
    for i, article in enumerate(relevant_articles[:3]):  # Process only 3 to avoid rate limits
        print(f"\n📖 Processing article {i+1}: {article['title'][:60]}...")
        
        # Get full content
        full_article = fetch_full_article_content(article['url'])
        if not full_article:
            print("❌ Could not fetch full content")
            continue
        
        # Check quality
        quality = assess_content_quality(full_article)
        if not quality['sufficient']:
            print(f"⚠️ Skipping - {quality['reason']}")
            continue
        
        # Use full article
        enhanced_article = {**article, **full_article}
        
        # Generate case study
        print("🧠 Generating Dignity Lens case study...")
        case_study_prompt = create_case_study_prompt(enhanced_article)
        case_study = call_claude_api(case_study_prompt)
        
        if case_study:
            save_content(case_study, 'case-studies', enhanced_article['title'])
            processed_count += 1
        
        print(f"✅ Completed article {i+1}")
        
        # Add delay between articles to avoid rate limits
        time.sleep(3)
    
    print(f"\n🎉 Content generation complete! Processed {processed_count} articles.")

if __name__ == "__main__":
    main()
