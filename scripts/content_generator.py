#!/usr/bin/env python3
"""
Enhanced Content Generator for DignityAI
Fully functional version for Railway deployment
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

# Initialize Claude API
try:
    client = Anthropic(api_key=os.environ.get('CLAUDE_API_KEY') or os.environ.get('ANTHROPIC_API_KEY'))
    logger.info("✅ Anthropic client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Anthropic client: {e}")
    sys.exit(1)

# RSS Feeds to monitor
RSS_FEEDS = [
    # Government/Legal Feeds
    "https://www.govinfo.gov/rss/uscourts-ilnd.xml",
    "https://www.govinfo.gov/rss/ppp.xml",
    "https://www.govinfo.gov/rss/dcpd.xml",
    "https://www.govinfo.gov/rss/bills.xml",
    "https://www.govinfo.gov/rss/statute.xml",
    "https://www.govinfo.gov/rss/uscode.xml",
    
    # News Feeds
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
    
    # SDOH-Focused Feeds
    "https://www.epi.org/feed/",  # Economic Policy Institute
    "https://feeds.feedburner.com/centeronbudget",  # Center on Budget and Policy Priorities
    "https://khn.org/feed/",  # Kaiser Health News
    "https://shelterforce.org/feed/",  # Housing justice
    "https://www.chalkbeat.org/rss/",  # Education
    "https://civileats.com/feed/",  # Food justice
    "https://www.urban.org/rss.xml",  # Urban Institute
    "https://grist.org/feed/",  # Environmental news
    "https://www.commonwealthfund.org/feeds/all/rss.xml",  # Health policy
    "https://hechingerreport.org/feed/",  # Education reporting
]

# Keywords to filter relevant articles
RELEVANT_KEYWORDS = [
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
    'civil rights', 'voting', 'democracy', 'organizing', 'activism', 'protest', 'movement'
]

# Quality assessment keywords
SYSTEMATIC_KEYWORDS = [
    'pattern', 'systematic', 'ongoing', 'historical', 'community impact',
    'residents', 'organizing', 'policy', 'decision', 'funding', 'resources',
    'government', 'officials', 'department', 'program', 'institution'
]

def fetch_full_article_content(url):
    """Fetch complete article content from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
            element.decompose()
        
        # Try multiple selectors for article content
        content_selectors = [
            'article', '.article-content', '.story-body', '.entry-content',
            '.post-content', '.content', '.story', 'main', '.article-body',
            '.article-text', '.story-content', '.post-body'
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
                if len(text) > 300:  # Minimum reasonable article length
                    article_content = text
                    break
        
        # If no content found with selectors, try paragraphs
        if not article_content:
            paragraphs = soup.find_all('p')
            if len(paragraphs) > 3:
                article_content = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        # Clean up the content
        article_content = re.sub(r'\s+', ' ', article_content)
        article_content = re.sub(r'Advertisement\s*', '', article_content)
        
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
    """Determine if article has sufficient context for Dignity Lens analysis"""
    if not article or not article.get('content'):
        return {'sufficient': False, 'reason': 'No content'}
    
    content = article['content'].lower()
    word_count = article.get('word_count', 0)
    
    # Check minimum length
    if word_count < 200:
        return {'sufficient': False, 'reason': f'Too short ({word_count} words)'}
    
    # Check for systematic elements
    systematic_score = sum(1 for keyword in SYSTEMATIC_KEYWORDS if keyword in content)
    
    # Check for community context
    community_keywords = ['community', 'residents', 'neighborhood', 'families', 'people']
    community_score = sum(1 for keyword in community_keywords if keyword in content)
    
    # Check for institutional elements
    institution_keywords = ['city', 'government', 'department', 'official', 'policy', 'program']
    institution_score = sum(1 for keyword in institution_keywords if keyword in content)
    
    # Quality scoring
    total_score = systematic_score + community_score + institution_score
    
    if total_score >= 3 and word_count >= 300:
        return {'sufficient': True, 'score': total_score, 'word_count': word_count}
    else:
        return {'sufficient': False, 'reason': f'Insufficient context (score: {total_score}, words: {word_count})'}

def fetch_rss_articles():
    """Fetch articles from RSS feeds"""
    articles = []
    
    for feed_url in RSS_FEEDS:
        try:
            logger.info(f"Fetching from {feed_url}...")
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:  # Reduced to 3 per feed for quality
                articles.append({
                    'title': entry.title,
                    'content': getattr(entry, 'summary', ''),
                    'url': entry.link,
                    'published': getattr(entry, 'published', ''),
                    'source': feed_url
                })
        except Exception as e:
            logger.error(f"Error fetching {feed_url}: {e}")
    
    return articles

def filter_relevant_articles(articles):
    """Filter articles for relevant content"""
    relevant = []
    
    for article in articles:
        text = (article['title'] + ' ' + article['content']).lower()
        if any(keyword in text for keyword in RELEVANT_KEYWORDS):
            relevant.append(article)
    
    return relevant

def create_enhanced_case_study_prompt(article):
    """Create enhanced prompt for Dignity Lens case study with quality check"""
    return f"""
You are DignityAI. FIRST assess if this article contains sufficient information for meaningful Dignity Lens analysis.

CONTENT ASSESSMENT CRITERIA:
- Does this article provide enough context to identify specific Power Structures?
- Can you trace systematic patterns rather than isolated incidents?
- Is there enough information to document Community Resistance or organizing opportunities?
- Can you identify concrete Liberation Strategies?

ARTICLE TO ANALYZE:
Title: {article['title']}
Content: {article['content']}
Word Count: {article.get('word_count', 'Unknown')}
Source: {article['url']}

IF THE ARTICLE LACKS SUFFICIENT CONTEXT (less than 300 words OR insufficient systematic analysis potential):
Respond with exactly: "INSUFFICIENT_CONTEXT: This article requires additional research before applying the Dignity Lens framework. The content lacks sufficient detail about systematic patterns, community impact, or institutional context needed for meaningful analysis."

IF THE ARTICLE HAS SUFFICIENT CONTEXT:
Create a comprehensive case study (1800-2200 words) using the Dignity Lens framework:

DIGNITY LENS DOMAINS:
1. Power Structures: Who holds decision-making authority and how is it maintained?
2. Control Mechanisms: How are Black communities contained and suppressed?
3. Community Resistance: How do communities survive and fight back?
4. Liberation Strategies: What has actually worked to build Black freedom and power?

Format as markdown with:
# [Analysis Title]
## Executive Summary
## Dignity Lens Analysis
### Power Structures
### Control Mechanisms
### Community Resistance
### Liberation Strategies
## Historical Context
## Community Organizing Opportunities
## Conclusion

Connect to historical patterns and provide concrete Chicago organizing opportunities.
NEVER generate superficial analysis from incomplete information.
"""

def create_news_article_prompt(article):
    """Create prompt for community journalism article"""
    return f"""
You are a Liberation Technology journalist for the People's Newsroom. 

FIRST: Assess if this article has enough substance for community journalism analysis.

ARTICLE:
Title: {article['title']}
Content: {article['content']}
Source: {article['url']}

IF insufficient context (less than 200 words OR lacks community impact details):
Respond: "INSUFFICIENT_CONTENT: This article lacks sufficient detail for meaningful community journalism rewrite."

IF sufficient context:
Rewrite from a community organizing perspective (700-900 words):
- Center community voices and impacts
- Analyze systematic patterns, not just individual events
- Connect to broader liberation organizing
- Provide community organizing context
- Include actionable information for residents

Format as:
# [Community-Centered Headline]
## [Subheading focusing on community impact]

[Article content with Liberation Technology perspective]

**Community Organizing Opportunities:**
- [Specific actions residents can take]
- [Organizations to connect with]
- [Relevant meetings/events]
"""

def create_blog_post_prompt(article):
    """Create prompt for accessible blog post"""
    return f"""
You are writing for DRC's blog to make systematic racism analysis accessible.

ARTICLE:
Title: {article['title']}
Content: {article['content']}
Source: {article['url']}

IF insufficient context for systematic analysis:
Respond: "INSUFFICIENT_CONTENT: This story lacks the detail needed for meaningful systematic racism analysis."

IF sufficient context:
Create an accessible blog post (500-700 words) that:
- Makes systematic racism analysis accessible to general readers
- Uses concrete examples from the news story
- Connects individual story to bigger patterns
- Provides hope and organizing pathways

Format as:
# [Engaging, accessible headline]

[Content explaining systematic patterns through this example]

## What This Really Means
[Connect to bigger patterns]

## What We Can Do About It
[Organizing opportunities and hope]

**Get Involved:**
- [Specific actions]
- [Organizations to support]
"""

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
            time.sleep(2)
            return message.content[0].text
        except Exception as e:
            logger.error(f"Claude API error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5)  # Wait before retry
            else:
                return None

def save_content(content, content_type, article_title):
    """Save generated content to appropriate folder"""
    if not content:
        return
    
    # Skip if content indicates insufficient context
    if 'INSUFFICIENT_CONTEXT' in content or 'INSUFFICIENT_CONTENT' in content:
        logger.info(f"Skipped {content_type}: {article_title[:50]} - insufficient content")
        return
    
    # Create directories if they don't exist
    os.makedirs(f'drafts/{content_type}', exist_ok=True)
    
    # Create filename
    date_str = datetime.now().strftime('%Y%m%d')
    safe_title = "".join(c for c in article_title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
    filename = f'drafts/{content_type}/{date_str}-{safe_title}.md'
    
    # Save content
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"✅ Saved: {filename}")

def main():
    """Main content generation function"""
    logger.info("🚀 Starting enhanced daily content generation...")
    
    # Fetch and filter articles
    logger.info("📰 Fetching RSS articles...")
    articles = fetch_rss_articles()
    relevant_articles = filter_relevant_articles(articles)
    
    logger.info(f"📋 Found {len(relevant_articles)} relevant articles")
    logger.info("🔍 Fetching full article content and assessing quality...")
    
    processed_count = 0
    
    for i, article in enumerate(relevant_articles[:8]):  # Limit to 8 for cost control
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
        save_content(case_study, 'case-studies', enhanced_article['title'])
        
        # Generate news article
        logger.info("📰 Generating community journalism article...")
        news_prompt = create_news_article_prompt(enhanced_article)
        news_article = call_claude_api(news_prompt)
        save_content(news_article, 'news-articles', enhanced_article['title'])
        
        # Generate blog post
        logger.info("📝 Generating accessible blog post...")
        blog_prompt = create_blog_post_prompt(enhanced_article)
        blog_post = call_claude_api(blog_prompt)
        save_content(blog_post, 'blog-posts', enhanced_article['title'])
        
        processed_count += 1
        logger.info(f"✅ Completed article {i+1}")
    
    logger.info(f"\n🎉 Daily content generation complete! Processed {processed_count} high-quality articles.")

if __name__ == "__main__":
    main()
