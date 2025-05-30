# scripts/content_generator.py
import feedparser
import requests
import os
import json
from datetime import datetime
from anthropic import Anthropic

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
    'crime', 'safety', 'racism', 'discrimination', 'inequality'
]

def fetch_rss_articles():
    """Fetch articles from RSS feeds"""
    articles = []
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:  # Top 5 from each feed
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
    
    return relevant[:10]  # Process top 10 daily

def create_case_study_prompt(article):
    """Create prompt for Dignity Lens case study"""
    return f"""
You are DignityAI. Analyze this news article through the Dignity Lens framework created by the Defy Racism Collective.

DIGNITY LENS FRAMEWORK:
1. Power Analysis: Who benefits from this system? Who is harmed or excluded?
2. State Violence & Control: What mechanisms maintain power and control?
3. Community Resistance: How do communities respond and create alternatives?
4. Revolutionary Praxis: How do we connect theory to concrete Liberation Technology that builds community infrastructure?

ARTICLE TO ANALYZE:
Title: {article['title']}
Content: {article['content']}
Source: {article['url']}
Published: {article['published']}

Create a comprehensive case study (1800-2200 words) that:
- Analyzes this article through all 4 Dignity Lens domains
- Connects to historical patterns of systematic oppression
- Identifies how this fits into broader systematic racism
- Provides concrete organizing opportunities for Chicago communities
- Includes cross-references to related systematic issues

Format as markdown with:
# Case Study Title
## Executive Summary
## Dignity Lens Analysis
### Power Analysis
### State Violence & Control  
### Community Resistance
### Revolutionary Praxis
## Historical Context
## Community Organizing Opportunities
## Conclusion

Use Liberation Technology perspective throughout.
"""

def create_news_article_prompt(article):
    """Create prompt for community journalism article"""
    return f"""
You are a Liberation Technology journalist for the People's Newsroom. Rewrite this mainstream news article from a community organizing perspective.

ORIGINAL ARTICLE:
Title: {article['title']}
Content: {article['content']}
Source: {article['url']}

Create a news article (700-900 words) that:
- Centers community voices and impacts
- Analyzes systematic patterns, not just individual events
- Connects to broader liberation organizing
- Provides community organizing context
- Includes actionable information for residents
- Uses Liberation Technology analysis

Format as:
# [Compelling Community-Centered Headline]
## [Subheading that centers community impact]

[Article content with Liberation Technology perspective]

**Community Organizing Opportunities:**
- [Specific actions residents can take]
- [Organizations to connect with]
- [Upcoming relevant meetings/events]

Style: Community journalism that builds organizing capacity, not mainstream media that perpetuates oppression.
"""

def create_blog_post_prompt(article):
    """Create prompt for accessible blog post"""
    return f"""
You are writing for DRC's blog. Create an accessible, engaging blog post that helps people understand systematic racism through this news story.

NEWS STORY:
Title: {article['title']}
Content: {article['content']}
Source: {article['url']}

Create a blog post (500-700 words) that:
- Makes systematic racism analysis accessible to general readers
- Uses concrete examples from the news story
- Connects individual story to bigger patterns
- Provides hope and organizing pathways
- Includes community organizing opportunities

Format as:
# [Engaging, accessible headline]

[Accessible explanation of systematic racism through this example]

## What This Really Means
[Connect to bigger patterns]

## What We Can Do About It
[Organizing opportunities and hope]

**Get Involved:**
- [Specific actions]
- [Organizations to support]

Style: Accessible, educational, empowering. Help readers see systematic patterns and feel empowered to act.
"""

def call_claude_api(prompt):
    """Send prompt to Claude API"""
    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Claude API error: {e}")
        return None

def save_content(content, content_type, article_title):
    """Save generated content to appropriate folder"""
    if not content:
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
    
    print(f"Saved: {filename}")

def main():
    """Main content generation function"""
    print("Starting daily content generation...")
    
    # Fetch and filter articles
    articles = fetch_rss_articles()
    relevant_articles = filter_relevant_articles(articles)
    
    print(f"Processing {len(relevant_articles)} relevant articles...")
    
    for article in relevant_articles:
        print(f"Processing: {article['title'][:50]}...")
        
        # Generate case study
        case_study_prompt = create_case_study_prompt(article)
        case_study = call_claude_api(case_study_prompt)
        save_content(case_study, 'case-studies', article['title'])
        
        # Generate news article
        news_prompt = create_news_article_prompt(article)
        news_article = call_claude_api(news_prompt)
        save_content(news_article, 'news-articles', article['title'])
        
        # Generate blog post
        blog_prompt = create_blog_post_prompt(article)
        blog_post = call_claude_api(blog_prompt)
        save_content(blog_post, 'blog-posts', article['title'])
    
    print("Daily content generation complete!")

if __name__ == "__main__":
    main()
