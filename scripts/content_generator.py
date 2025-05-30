# scripts/content_generator.py
import feedparser
import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime
from anthropic import Anthropic
import time
import re
from urllib.parse import urljoin, urlparse

# Initialize Claude API
client = Anthropic(api_key=os.environ['CLAUDE_API_KEY'])

# RSS Feeds to monitor
RSS_FEEDS = [
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

# Keywords to filter relevant articles
RELEVANT_KEYWORDS = [
    'police', 'housing', 'health', 'school', 'education', 'city council',
    'mayor', 'budget', 'development', 'community', 'neighborhood',
    'crime', 'safety', 'racism', 'discrimination', 'inequality', 'tenant',
    'eviction', 'gentrification', 'affordable', 'CPS', 'teacher', 'student'
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
        print(f"Error fetching full content from {url}: {e}")
        return None

def fact_check_content(article):
    """
    Fact-check article content for accuracy and context
    """
    fact_check_prompt = f"""
FACT-CHECK ASSESSMENT for Dignity Lens Analysis:

ARTICLE: {article['title']}
URL: {article['url']}
CONTENT: {article['content'][:2000]}...

Please evaluate this content for:

1. FACTUAL ACCURACY:
- Are claims supported by evidence?
- Are statistics/data presented correctly?
- Are quotes and attributions accurate?
- Any obvious misinformation or bias?

2. CONTEXT COMPLETENESS:
- Missing important background information?
- One-sided presentation of complex issues?
- Historical context provided or absent?
- Community perspectives included or excluded?

3. SOURCE RELIABILITY:
- Credible publication/outlet?
- Author expertise on the topic?
- Primary sources vs. speculation?
- Corporate/political interests that might bias coverage?

4. SYSTEMATIC ANALYSIS READINESS:
- Sufficient detail for institutional analysis?
- Connects to broader patterns beyond individual incident?
- Relates to community organizing or policy implications?
- Addresses root causes vs. just symptoms?

RESPOND WITH:
- FACT_CHECK_PASS: Content is factually sound and suitable for Dignity Lens analysis
- FACT_CHECK_CONCERNS: Content has issues but may still be usable (explain concerns)
- FACT_CHECK_FAIL: Content is unreliable or insufficient for serious analysis

If PASS or CONCERNS, provide brief summary of any important context or background information that should be included in the analysis.

If FAIL, explain specific factual problems or missing context that makes this unsuitable for systematic racism analysis.
"""
    return fact_check_prompt

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
            print(f"Fetching from {feed_url}...")
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
            print(f"Error fetching {feed_url}: {e}")
    
    return articles

def filter_relevant_articles(articles):
    """Filter articles for relevant content"""
    relevant = []
    
    for article in articles:
        text = (article['title'] + ' ' + article['content']).lower()
        if any(keyword in text for keyword in RELEVANT_KEYWORDS):
            relevant.append(article)
    
    return relevant

def create_enhanced_case_study_prompt(article, fact_check_result=None):
    """Create enhanced prompt for Dignity Lens case study with fact-check integration"""
    fact_check_context = ""
    if fact_check_result and "FACT_CHECK_PASS" in fact_check_result:
        fact_check_context = f"\n\nFACT-CHECK CLEARED: This content has been verified for accuracy and systematic analysis readiness.\n{fact_check_result}\n"
    elif fact_check_result and "FACT_CHECK_CONCERNS" in fact_check_result:
        fact_check_context = f"\n\nFACT-CHECK NOTES: Please address these concerns in your analysis:\n{fact_check_result}\n"
    
    return f"""
You are DignityAI. Create a comprehensive case study using the Dignity Lens framework.
{fact_check_context}
ARTICLE TO ANALYZE:
Title: {article['title']}
Content: {article['content']}
Word Count: {article.get('word_count', 'Unknown')}
Source: {article['url']}

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
## Fact-Check and Context Notes
## Community Organizing Opportunities
## Conclusion

Connect to historical patterns, provide concrete Chicago organizing opportunities, and address any fact-check concerns identified above.
"""

def create_news_article_prompt(article, fact_check_result=None):
    """Create prompt for community journalism article with fact-check integration"""
    fact_check_context = ""
    if fact_check_result:
        fact_check_context = f"\n\nFACT-CHECK NOTES: {fact_check_result}\n"
    
    return f"""
You are a Liberation Technology journalist for the People's Newsroom.
{fact_check_context}
ARTICLE:
Title: {article['title']}
Content: {article['content']}
Source: {article['url']}

Rewrite from a community organizing perspective (700-900 words):
- Center community voices and impacts
- Analyze systematic patterns, not just individual events
- Connect to broader liberation organizing
- Provide community organizing context
- Include actionable information for residents
- Address any fact-check concerns noted above

Format as:
# [Community-Centered Headline]
## [Subheading focusing on community impact]

[Article content with Liberation Technology perspective]

**Fact-Check and Sources:**
[Any additional context or verification needed]

**Community Organizing Opportunities:**
- [Specific actions residents can take]
- [Organizations to connect with]
- [Relevant meetings/events]
"""

def create_blog_post_prompt(article, fact_check_result=None):
    """Create prompt for accessible blog post with fact-check integration"""
    fact_check_context = ""
    if fact_check_result:
        fact_check_context = f"\n\nFACT-CHECK NOTES: {fact_check_result}\n"
    
    return f"""
You are writing for DRC's blog to make systematic racism analysis accessible.
{fact_check_context}
ARTICLE:
Title: {article['title']}
Content: {article['content']}
Source: {article['url']}

Create an accessible blog post (500-700 words) that:
- Makes systematic racism analysis accessible to general readers
- Uses concrete examples from the news story
- Connects individual story to bigger patterns
- Provides hope and organizing pathways
- Addresses any fact-check concerns

Format as:
# [Engaging, accessible headline]

[Content explaining systematic patterns through this example]

## What This Really Means
[Connect to bigger patterns]

## The Full Context
[Address any fact-check concerns or missing context]

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
            time.sleep(1.5)
            return message.content[0].text
        except Exception as e:
            print(f"Claude API error (attempt {attempt + 1}): {e}")
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
        print(f"Skipped {content_type}: {article_title[:50]} - insufficient content")
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
    
    print(f"✅ Saved: {filename}")

def main():
    """Main content generation function with fact-checking"""
    print("🚀 Starting enhanced daily content generation with fact-checking...")
    
    # Fetch and filter articles
    print("📰 Fetching RSS articles...")
    articles = fetch_rss_articles()
    relevant_articles = filter_relevant_articles(articles)
    
    print(f"📋 Found {len(relevant_articles)} relevant articles")
    print("🔍 Fetching full article content and assessing quality...")
    
    processed_count = 0
    
    for i, article in enumerate(relevant_articles[:6]):  # Reduced for fact-checking overhead
        print(f"\n📖 Processing article {i+1}: {article['title'][:60]}...")
        
        # Get full article content
        full_article = fetch_full_article_content(article['url'])
        if not full_article:
            print("❌ Could not fetch full content")
            continue
        
        # Assess quality
        quality = assess_content_quality(full_article)
        if not quality['sufficient']:
            print(f"⚠️ Skipping - {quality['reason']}")
            continue
        
        print(f"✅ Quality check passed - Score: {quality.get('score', 'N/A')}, Words: {quality.get('word_count', 'N/A')}")
        
        # Use full article for analysis
        enhanced_article = {**article, **full_article}
        
        # Fact-check the content
        print("🔍 Fact-checking content...")
        fact_check_prompt = fact_check_content(enhanced_article)
        fact_check_result = call_claude_api(fact_check_prompt)
        
        if fact_check_result and "FACT_CHECK_FAIL" in fact_check_result:
            print(f"❌ Fact-check failed: {fact_check_result[:100]}...")
            continue
        
        if fact_check_result and "FACT_CHECK_PASS" in fact_check_result:
            print("✅ Fact-check passed")
        elif fact_check_result and "FACT_CHECK_CONCERNS" in fact_check_result:
            print("⚠️ Fact-check has concerns - will address in analysis")
        
        # Generate case study
        print("🧠 Generating Dignity Lens case study...")
        case_study_prompt = create_enhanced_case_study_prompt(enhanced_article, fact_check_result)
        case_study = call_claude_api(case_study_prompt)
        save_content(case_study, 'case-studies', enhanced_article['title'])
        
        # Generate news article
        print("📰 Generating community journalism article...")
        news_prompt = create_news_article_prompt(enhanced_article, fact_check_result)
        news_article = call_claude_api(news_prompt)
        save_content(news_article, 'news-articles', enhanced_article['title'])
        
        # Generate blog post
        print("📝 Generating accessible blog post...")
        blog_prompt = create_blog_post_prompt(enhanced_article, fact_check_result)
        blog_post = call_claude_api(blog_prompt)
        save_content(blog_post, 'blog-posts', enhanced_article['title'])
        
        processed_count += 1
        print(f"✅ Completed article {i+1} with fact-checking")
    
    print(f"\n🎉 Daily content generation complete! Processed {processed_count} fact-checked, high-quality articles.")

if __name__ == "__main__":
    main()
