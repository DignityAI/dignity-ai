#!/usr/bin/env python3
"""
Enhanced Content Generator for DignityAI
Fully functional version with all issues fixed
"""

import feedparser
import requests
from bs4 import BeautifulSoup
import os
import json
import sys
from datetime import datetime
from anthropic import Anthropic
import time
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Claude API with proper error handling
def initialize_claude_client():
    """Initialize Claude client with multiple API key options"""
    api_key = (os.environ.get('ANTHROPIC_API_KEY') or 
               os.environ.get('CLAUDE_API_KEY') or 
               os.environ.get('ANTHROPIC_API_TOKEN'))
    
    if not api_key:
        logger.error("❌ No API key found. Set ANTHROPIC_API_KEY environment variable.")
        logger.error("Available env vars: " + str(list(os.environ.keys())))
        sys.exit(1)
    
    try:
        client = Anthropic(api_key=api_key)
        logger.info("✅ Anthropic client initialized successfully")
        logger.info(f"API Key length: {len(api_key)}")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to initialize Anthropic client: {e}")
        sys.exit(1)

client = initialize_claude_client()

# RSS Feeds to monitor - FIXED syntax errors
RSS_FEEDS = [
    # Community Organizing & Social Justice (Better sources for positive news)
    "https://thesocialchangeagency.org/feed",
    "https://progressive.org/topics/social-justice/feed", 
    "https://interactioninstitute.org/blog/feed",
    "https://socialchangeconsulting.com/feed",
    
    # Government/Legal Feeds
    "http://feeds.feedburner.com/abajournal/dailynews",  # FIXED: Added comma
    "https://follow.it/scotusblog/rss",                   # FIXED: Added comma
    
    # News Feeds
    "https://rss.app/feeds/_2ZZUGhJ4rmRCnCOL.xml",
    "https://billypenn.com/feed",
    "https://wtop.com/feed",
    "https://www.kxan.com/feed",
    "https://ktla.com/feed",
    "https://wgntv.com/feed",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://www.npr.org/rss/rss.php?id=1001",
    "https://feeds.foxnews.com/foxnews/latest",
    "https://www.chicagotribune.com/arcio/rss/",
    "https://www.fox32chicago.com/rss/category/news",
    "https://blockclubchicago.org/feed/",
]

# EXPANDED keywords for better content detection
RELEVANT_KEYWORDS = [
    # Community Organizing & Social Justice
    'organizing', 'activism', 'protest', 'movement', 'coalition', 'advocacy', 'campaign',
    'community', 'residents', 'neighborhood', 'families', 'grassroots', 'mutual aid',
    
    # Law and Justice
    'police', 'court', 'lawsuit', 'civil rights', 'discrimination', 'justice', 'legal', 'ruling', 'judge',
    'settlement', 'violation', 'constitutional', 'federal', 'statute', 'law', 'bill', 'legislation',
    
    # Housing and Development
    'housing', 'eviction', 'gentrification', 'affordable', 'rent', 'landlord', 'tenant', 'displacement',
    'development', 'zoning', 'neighborhood', 'community', 'redlining', 'segregation',
    
    # Health and Social Determinants
    'health', 'healthcare', 'medicaid', 'medicare', 'insurance', 'hospital', 'clinic', 'mental health',
    'food', 'nutrition', 'hunger', 'food desert', 'environmental', 'pollution', 'lead', 'asthma',
    
    # Education
    'school', 'education', 'student', 'teacher', 'CPS', 'funding', 'academic', 'literacy', 'graduation',
    'college', 'university', 'scholarship', 'achievement gap',
    
    # Economic Justice
    'employment', 'unemployment', 'wages', 'minimum wage', 'poverty', 'inequality', 'economic',
    'job training', 'workforce', 'benefits', 'social security', 'welfare', 'snap', 'wic',
    
    # Government and Policy
    'city council', 'mayor', 'budget', 'policy', 'government', 'federal', 'state', 'local',
    'officials', 'department', 'program', 'funding', 'resources', 'public', 'services',
    
    # Social Issues
    'racism', 'discrimination', 'inequality', 'bias', 'systemic', 'systematic', 'institutional',
    'civil rights', 'voting', 'democracy'
]

# Quality assessment keywords
SYSTEMATIC_KEYWORDS = [
    'pattern', 'systematic', 'ongoing', 'historical', 'community impact', 'widespread',
    'residents', 'organizing', 'policy', 'decision', 'funding', 'resources',
    'government', 'officials', 'department', 'program', 'institution', 'service'
]

def fetch_full_article_content(url):
    """Fetch complete article content from URL with better error handling"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement', '.ad', '.ads']):
            element.decompose()
        
        # Try multiple selectors for article content
        content_selectors = [
            'article', '.article-content', '.story-body', '.entry-content',
            '.post-content', '.content', '.story', 'main', '.article-body',
            '.article-text', '.story-content', '.post-body', '.post',
            '.news-content', '.article-wrap', '.story-wrap'
        ]
        
        article_content = ""
        title = ""
        
        # Get title
        title_element = soup.find('h1') or soup.find('title')
        if title_element:
            title = title_element.get_text(strip=True)
        
        # Get content
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                # Get text and clean it
                text = content_div.get_text(separator=' ', strip=True)
                if len(text) > 200:  # Minimum reasonable article length
                    article_content = text
                    break
        
        # If no content found with selectors, try paragraphs
        if not article_content:
            paragraphs = soup.find_all('p')
            if len(paragraphs) > 2:
                article_content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
        
        # Clean up the content
        article_content = re.sub(r'\s+', ' ', article_content)
        article_content = re.sub(r'Advertisement\s*', '', article_content)
        article_content = re.sub(r'Sign up for.*?newsletter', '', article_content, flags=re.IGNORECASE)
        
        return {
            'title': title,
            'content': article_content,
            'url': url,
            'word_count': len(article_content.split())
        }
        
    except Exception as e:
        logger.error(f"Error fetching full content from {url}: {e}")
        return None

def assess_content_quality(article):
    """RELAXED quality assessment for more content generation"""
    if not article or not article.get('content'):
        return {'sufficient': False, 'reason': 'No content'}
    
    content = article['content'].lower()
    title = article.get('title', '').lower()
    combined_text = content + ' ' + title
    word_count = article.get('word_count', 0)
    
    # RELAXED minimum length requirements
    if word_count < 100:  # Reduced from 200
        return {'sufficient': False, 'reason': f'Too short ({word_count} words)'}
    
    # Check for systematic elements
    systematic_score = sum(1 for keyword in SYSTEMATIC_KEYWORDS if keyword in combined_text)
    
    # Check for community context
    community_keywords = ['community', 'residents', 'neighborhood', 'families', 'people', 'local', 'area']
    community_score = sum(1 for keyword in community_keywords if keyword in combined_text)
    
    # Check for institutional elements
    institution_keywords = ['city', 'government', 'department', 'official', 'policy', 'program', 'service', 'public']
    institution_score = sum(1 for keyword in institution_keywords if keyword in combined_text)
    
    # Quality scoring - MUCH MORE RELAXED
    total_score = systematic_score + community_score + institution_score
    
    # Very relaxed requirements for testing
    if total_score >= 1 and word_count >= 100:  # Much lower thresholds
        return {'sufficient': True, 'score': total_score, 'word_count': word_count}
    else:
        return {'sufficient': False, 'reason': f'Insufficient context (score: {total_score}, words: {word_count})'}

def fetch_rss_articles():
    """Fetch articles from RSS feeds with better error handling"""
    articles = []
    
    logger.info(f"📡 Processing {len(RSS_FEEDS)} RSS feeds...")
    
    for i, feed_url in enumerate(RSS_FEEDS):
        try:
            logger.info(f"Fetching from {feed_url}...")
            
            # Add timeout and better error handling
            feed = feedparser.parse(feed_url)
            
            if hasattr(feed, 'status') and feed.status != 200:
                logger.warning(f"Feed returned status {feed.status}: {feed_url}")
                continue
                
            if not hasattr(feed, 'entries') or not feed.entries:
                logger.warning(f"No entries found in feed: {feed_url}")
                continue
            
            # Get more articles per feed for testing
            for entry in feed.entries[:5]:  # Increased from 3 to 5
                articles.append({
                    'title': getattr(entry, 'title', 'No title'),
                    'content': getattr(entry, 'summary', ''),
                    'url': getattr(entry, 'link', ''),
                    'published': getattr(entry, 'published', ''),
                    'source': feed_url
                })
                
            logger.info(f"✅ Got {len(feed.entries[:5])} articles from feed {i+1}")
            
        except Exception as e:
            logger.error(f"❌ Error fetching {feed_url}: {e}")
            continue
    
    logger.info(f"📰 Total articles collected: {len(articles)}")
    return articles

def filter_relevant_articles(articles):
    """Filter articles for relevant content with more liberal matching"""
    relevant = []
    
    for article in articles:
        title = article.get('title', '').lower()
        content = article.get('content', '').lower()
        text = title + ' ' + content
        
        # More liberal keyword matching
        keyword_matches = sum(1 for keyword in RELEVANT_KEYWORDS if keyword in text)
        
        # Accept articles with even 1 keyword match for testing
        if keyword_matches >= 1:
            relevant.append(article)
            logger.debug(f"✅ Relevant: {article['title'][:50]} (matches: {keyword_matches})")
        else:
            logger.debug(f"❌ Filtered out: {article['title'][:50]}")
    
    return relevant

def create_enhanced_case_study_prompt(article):
    """Create enhanced prompt for Dignity Lens case study"""
    return f"""
You are DignityAI, an AI assistant that uses the revolutionary Dignity Lens framework to analyze systematic racism and community organizing opportunities.

ARTICLE TO ANALYZE:
Title: {article['title']}
Content: {article['content']}
Source: {article['url']}

Create a comprehensive Dignity Lens analysis (1500-2000 words) examining this story through the framework:

DIGNITY LENS DOMAINS:
1. **Power Structures**: Who holds decision-making authority? What institutions control resources and policies?
2. **Control Mechanisms**: How are communities contained or limited? What systematic barriers exist?
3. **Community Resistance**: How are people organizing? What strategies are communities using?
4. **Liberation Strategies**: What approaches could build genuine community power?

FORMAT YOUR RESPONSE AS:

# Dignity Lens Analysis: [Create compelling title]

## Executive Summary
[2-3 sentences on key systematic patterns revealed]

## Dignity Lens Analysis

### Power Structures
[Analyze who controls decisions, resources, and policies in this situation]

### Control Mechanisms  
[Examine systematic barriers and limitations affecting communities]

### Community Resistance
[Document how communities are organizing and responding]

### Liberation Strategies
[Identify approaches that could build genuine community power]

## Historical Context
[Connect to historical patterns of systematic oppression and resistance]

## Community Organizing Opportunities
[Provide 3-4 concrete actions communities can take]

## Conclusion
[Summarize key insights and path forward]

Focus on systematic patterns rather than individual incidents. Connect this story to broader community organizing opportunities in Chicago.
"""

def create_news_article_prompt(article):
    """Create prompt for community journalism article"""
    return f"""
You are writing for the People's Newsroom, reframing news from a community organizing perspective.

ORIGINAL ARTICLE:
Title: {article['title']}
Content: {article['content']}
Source: {article['url']}

Rewrite this story (600-800 words) from a Liberation Technology journalism perspective:

- Center community voices and impacts over official statements
- Analyze systematic patterns, not just individual events  
- Connect to broader organizing opportunities
- Include actionable information for residents
- Frame solutions through community power building

FORMAT AS:

# [Community-Centered Headline That Emphasizes Impact]

## [Subheading focusing on community organizing angle]

[Article content with community organizing perspective]

**Community Organizing Opportunities:**
- [Specific actions residents can take]
- [Organizations to connect with]  
- [Relevant meetings, events, or campaigns]

Make systematic patterns visible while providing hope and organizing pathways.
"""

def create_blog_post_prompt(article):
    """Create prompt for accessible blog post"""
    return f"""
You are writing for DRC's blog to make systematic racism analysis accessible to general readers.

ARTICLE:
Title: {article['title']}
Content: {article['content']}
Source: {article['url']}

Create an accessible blog post (500-700 words) that:
- Makes systematic patterns visible through this concrete example
- Uses accessible language without jargon
- Connects individual story to bigger picture
- Provides hope and organizing pathways
- Includes practical next steps

FORMAT AS:

# [Engaging, accessible headline that reveals the pattern]

[Opening that hooks readers with the human story]

## What This Really Reveals
[Explain the systematic patterns this story demonstrates]

## The Bigger Picture  
[Connect to historical patterns and current organizing]

## What We Can Do About It
[Organizing opportunities and reasons for hope]

**Take Action:**
- [Specific ways readers can get involved]
- [Organizations working on this issue]
- [How to stay informed and engaged]

Make complex analysis accessible while inspiring action.
"""

def call_claude_api(prompt, max_retries=3):
    """Send prompt to Claude API with comprehensive retry logic"""
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=4000,
                temperature=0.3,  # Lower temperature for more focused output
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Rate limiting - stay well under API limits
            time.sleep(3)
            
            if message.content and len(message.content) > 0:
                return message.content[0].text
            else:
                logger.warning(f"Empty response from Claude on attempt {attempt + 1}")
                continue
                
        except Exception as e:
            logger.error(f"Claude API error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))  # Exponential backoff
            else:
                logger.error("Max retries exceeded for Claude API")
                return None

def save_content(content, content_type, article_title):
    """Save generated content to appropriate folder"""
    if not content:
        logger.warning(f"No content to save for {content_type}: {article_title[:50]}")
        return
    
    # Skip if content indicates insufficient context
    if any(phrase in content for phrase in ['INSUFFICIENT_CONTEXT', 'INSUFFICIENT_CONTENT', 'lacks sufficient']):
        logger.info(f"Skipped {content_type}: {article_title[:50]} - insufficient content detected")
        return
    
    # Create directories if they don't exist
    os.makedirs(f'drafts/{content_type}', exist_ok=True)
    
    # Create filename
    date_str = datetime.now().strftime('%Y%m%d-%H%M')
    safe_title = "".join(c for c in article_title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:40]
    filename = f'drafts/{content_type}/{date_str}-{safe_title}.md'
    
    # Save content with metadata
    metadata = f"""---
title: "{article_title}"
type: "{content_type}"
generated: "{datetime.now().isoformat()}"
---

"""
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(metadata + content)
        
        logger.info(f"✅ Saved: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving {filename}: {e}")
        return None

def main():
    """Main content generation function with comprehensive debugging"""
    logger.info("🚀 Starting enhanced daily content generation...")
    
    # DEBUG: Environment check
    logger.info("🔍 Environment Debug Info:")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Environment variables containing 'API': {[k for k in os.environ.keys() if 'API' in k.upper()]}")
    
    # Fetch and filter articles
    logger.info("📰 Fetching RSS articles...")
    articles = fetch_rss_articles()
    
    if not articles:
        logger.error("❌ No articles fetched from any RSS feeds!")
        return
    
    relevant_articles = filter_relevant_articles(articles)
    logger.info(f"📋 Found {len(relevant_articles)} relevant articles out of {len(articles)} total")
    
    if not relevant_articles:
        logger.warning("⚠️ No relevant articles found after filtering!")
        logger.info("Sample article titles for debugging:")
        for i, article in enumerate(articles[:5]):
            logger.info(f"  {i+1}. {article['title'][:80]}")
        return
    
    logger.info("🔍 Fetching full article content and assessing quality...")
    
    processed_count = 0
    successful_saves = 0
    
    # Process more articles but with cost control
    for i, article in enumerate(relevant_articles[:6]):  # Process up to 6 articles
        logger.info(f"\n📖 Processing article {i+1}: {article['title'][:60]}...")
        
        # Get full article content
        full_article = fetch_full_article_content(article['url'])
        if not full_article:
            logger.warning("❌ Could not fetch full content")
            continue
        
        # Assess quality
        quality = assess_content_quality(full_article)
        if not quality['sufficient']:
            logger.warning(f"⚠️ Skipping - {quality['reason']}")
            continue
        
        logger.info(f"✅ Quality check passed - Score: {quality.get('score', 'N/A')}, Words: {quality.get('word_count', 'N/A')}")
        
        # Use full article for analysis
        enhanced_article = {**article, **full_article}
        
        # Generate case study
        logger.info("🧠 Generating Dignity Lens case study...")
        case_study_prompt = create_enhanced_case_study_prompt(enhanced_article)
        case_study = call_claude_api(case_study_prompt)
        if case_study:
            saved_file = save_content(case_study, 'case-studies', enhanced_article['title'])
            if saved_file:
                successful_saves += 1
        
        # Generate news article
        logger.info("📰 Generating community journalism article...")
        news_prompt = create_news_article_prompt(enhanced_article)
        news_article = call_claude_api(news_prompt)
        if news_article:
            saved_file = save_content(news_article, 'news-articles', enhanced_article['title'])
            if saved_file:
                successful_saves += 1
        
        # Generate blog post
        logger.info("📝 Generating accessible blog post...")
        blog_prompt = create_blog_post_prompt(enhanced_article)
        blog_post = call_claude_api(blog_prompt)
        if blog_post:
            saved_file = save_content(blog_post, 'blog-posts', enhanced_article['title'])
            if saved_file:
                successful_saves += 1
        
        processed_count += 1
        logger.info(f"✅ Completed article {i+1}")
        
        # Add delay between articles to avoid rate limiting
        if i < len(relevant_articles[:6]) - 1:
            logger.info("⏱️ Cooling down for 10 seconds...")
            time.sleep(10)
    
    # Summary
    logger.info(f"\n🎉 Daily content generation complete!")
    logger.info(f"📊 Statistics:")
    logger.info(f"   - Total articles found: {len(articles)}")
    logger.info(f"   - Relevant articles: {len(relevant_articles)}")
    logger.info(f"   - Articles processed: {processed_count}")
    logger.info(f"   - Content pieces saved: {successful_saves}")
    
    if successful_saves == 0:
        logger.warning("⚠️ No content was successfully generated and saved!")
        logger.info("💡 Try relaxing the quality thresholds or adding more community-focused RSS feeds")

if __name__ == "__main__":
    main()
