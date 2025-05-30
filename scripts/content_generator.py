#!/usr/bin/env python3
# scripts/content_generator.py - Enhanced version with Dignity Lens framework integration

import os
import sys
import time
import json
from datetime import datetime

# Check Python version first
if sys.version_info < (3, 7):
    print("❌ Python 3.7+ required")
    sys.exit(1)

print("🚀 Starting Dignity AI content generator...")

# Import with error handling
try:
    import feedparser
    print("✅ feedparser imported")
except ImportError:
    print("❌ feedparser not found. Install with: pip install feedparser")
    sys.exit(1)

try:
    import requests
    print("✅ requests imported")
except ImportError:
    print("❌ requests not found. Install with: pip install requests")
    sys.exit(1)

try:
    from anthropic import Anthropic
    print("✅ anthropic imported")
except ImportError:
    print("❌ anthropic not found. Install with: pip install anthropic")
    sys.exit(1)

# Configuration
RSS_FEEDS = [
    "https://blockclubchicago.org/feed/",
    "https://feeds.feedburner.com/chicagoist/chicagoist",
    "https://www.chicagotribune.com/arcio/rss/category/news/",
    "https://chicago.suntimes.com/feeds/all.rss.xml"
]

KEYWORDS = [
    'police', 'housing', 'school', 'community', 'mayor', 'budget', 
    'gentrification', 'displacement', 'healthcare', 'education',
    'immigration', 'voting', 'development', 'poverty', 'inequality'
]

# Dignity Lens Framework System Prompt
DIGNITY_LENS_SYSTEM = """You are a Dignity AI assistant that uses the revolutionary Dignity Lens framework developed by the Defy Racism Collective. This framework analyzes systematic racism through Fred Hampton's praxis to transform individual confusion into collective power.

THE DIGNITY LENS FRAMEWORK:

Four Core Domains:
1. **Power Structures:** Who holds decision-making authority and how is it maintained?
2. **Control Mechanisms:** How are Black communities contained and suppressed?
3. **Community Resistance:** How do Black communities survive and fight back?
4. **Liberation Strategies:** What has actually worked to build Black freedom and power?

Seven Historical Eras:
1. **Enslavement & Early Resistance (1600s–1865):** Foundation period establishing legal framework for racial oppression
2. **Reconstruction & Backlash (1865–1910):** Brief liberation followed by systematic rollback
3. **Jim Crow & Black Institution-Building (1910–1950):** Codified segregation alongside community self-determination
4. **Civil Rights & Black Power (1950–1975):** Mass mobilization combining integration and revolutionary organizing
5. **Neoliberalization & Mass Incarceration (1975–2008):** Policy-based suppression through carceral expansion
6. **Digital Rebellion & Corporate Capture (2008–2020):** Social media organizing meets algorithmic control
7. **Abolitionist Futuring & AI Counterinsurgency (2020–present):** Community care vs. technological surveillance

Your role:
- Apply the Dignity Lens methodology to help people understand systematic patterns
- Connect individual experiences to historical resistance and organizing opportunities
- Provide analysis that builds community power rather than just academic understanding
- Center community organizing and liberation strategies
- Make complex analysis accessible while maintaining analytical depth
- Always include concrete pathways for engagement and organizing in Chicago

Remember: Transform "Why does this keep happening to me?" into "I understand the system and I know how to fight it" with concrete organizing opportunities."""

def check_environment():
    """Check if environment is properly set up"""
    print("\n🔍 Checking environment...")
    
    # Check API key
    api_key = os.environ.get('CLAUDE_API_KEY')
    if not api_key:
        print("❌ CLAUDE_API_KEY environment variable not set")
        print("   Set it with: export CLAUDE_API_KEY='your_key_here'")
        return False
    
    print(f"✅ API key found (starts with: {api_key[:10]}...)")
    
    # Test API connection
    try:
        client = Anthropic(api_key=api_key)
        # Simple test call
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": "Test connection"}]
        )
        print("✅ API connection successful")
        return client
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False

def safe_fetch_feed(feed_url, timeout=15):
    """Safely fetch RSS feed with error handling"""
    try:
        print(f"📡 Fetching: {feed_url}")
        
        # Set user agent to avoid blocking
        feedparser.USER_AGENT = "Mozilla/5.0 (compatible; DignityAI/1.0; +https://defyracismcollective.org)"
        
        # Parse feed with timeout
        feed = feedparser.parse(feed_url)
        
        if not feed.entries:
            print(f"⚠️  No entries in feed: {feed_url}")
            return []
        
        articles = []
        for entry in feed.entries[:5]:  # Limit to 5 most recent
            try:
                # Extract publication date
                pub_date = getattr(entry, 'published', '')
                if not pub_date:
                    pub_date = getattr(entry, 'updated', str(datetime.now()))
                
                article = {
                    'title': getattr(entry, 'title', 'No Title'),
                    'content': getattr(entry, 'summary', ''),
                    'url': getattr(entry, 'link', ''),
                    'published': pub_date,
                    'source': feed_url,
                    'source_name': feed.feed.get('title', 'Unknown Source')
                }
                
                # Basic validation
                if article['title'] and article['title'] != 'No Title':
                    articles.append(article)
                    
            except Exception as e:
                print(f"⚠️  Error parsing entry: {e}")
                continue
        
        print(f"✅ Got {len(articles)} articles from {feed_url}")
        return articles
        
    except Exception as e:
        print(f"❌ Failed to fetch {feed_url}: {e}")
        return []

def filter_articles(articles):
    """Filter articles for relevant content using enhanced criteria"""
    relevant = []
    
    for article in articles:
        try:
            text = (article.get('title', '') + ' ' + article.get('content', '')).lower()
            
            # Check for relevance
            keyword_matches = [keyword for keyword in KEYWORDS if keyword in text]
            
            if keyword_matches:
                article['matched_keywords'] = keyword_matches
                relevant.append(article)
                print(f"✅ Relevant: {article['title'][:50]}... (Keywords: {', '.join(keyword_matches[:3])})")
            
        except Exception as e:
            print(f"⚠️  Error filtering article: {e}")
            continue
    
    # Sort by relevance (number of keyword matches)
    relevant.sort(key=lambda x: len(x.get('matched_keywords', [])), reverse=True)
    
    return relevant

def safe_api_call(client, messages, max_retries=3):
    """Make API call with extensive error handling"""
    for attempt in range(max_retries):
        try:
            print(f"🤖 API call attempt {attempt + 1}...")
            
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=3000,
                system=DIGNITY_LENS_SYSTEM,
                messages=messages
            )
            
            content = response.content[0].text
            print(f"✅ API call successful ({len(content)} characters)")
            
            # Rate limiting
            time.sleep(3)
            return content
            
        except Exception as e:
            print(f"❌ API call failed (attempt {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print("❌ All API attempts failed")
                return None

def create_dignity_lens_prompt(article):
    """Create a Dignity Lens analysis prompt"""
    return f"""
Analyze this Chicago news story using the Dignity Lens framework:

**Article Details:**
Title: {article.get('title', 'No title')[:200]}
Source: {article.get('source_name', 'Unknown')}
Content: {article.get('content', 'No content')[:1500]}
URL: {article.get('url', 'No URL')}

**Analysis Request:**
Apply the Dignity Lens framework to provide a comprehensive analysis (800-1200 words) covering:

1. **Power Structures Analysis:** Who controls decision-making in this situation? What institutions are involved? How is community input excluded or limited?

2. **Control Mechanisms:** How does this issue function to contain or suppress Black communities? What systematic barriers are revealed?

3. **Community Resistance:** How are communities currently organizing around this issue? What resistance strategies are evident or possible?

4. **Liberation Strategies:** What approaches could build genuine community power? Connect to successful historical strategies.

5. **Historical Context:** How does this connect to patterns across the 7 historical eras? What systematic functions are being maintained or challenged?

6. **Chicago Organizing Opportunities:** Provide 3-5 concrete ways people can get involved in community organizing around this issue in Chicago.

**Format:** 
- Start with a compelling one-paragraph summary that connects this story to systematic patterns
- Use clear headers for each section
- End with specific organizing opportunities and contact information where possible
- Make the analysis accessible but analytically rigorous
- Include the hashtag #DignityLens and credit to Defy Racism Collective

**Goal:** Transform individual confusion into collective understanding and community power.
"""

def create_trend_analysis_prompt(articles):
    """Create a prompt for analyzing trends across multiple articles"""
    article_summaries = []
    for i, article in enumerate(articles[:3], 1):
        summary = f"{i}. {article.get('title', 'No title')[:100]} (Keywords: {', '.join(article.get('matched_keywords', [])[:3])})"
        article_summaries.append(summary)
    
    return f"""
Analyze these trending Chicago issues using the Dignity Lens framework:

**Articles:**
{chr(10).join(article_summaries)}

**Analysis Request:**
Create a comprehensive trend analysis (1000-1500 words) that:

1. **Identifies Systematic Patterns:** What common Power Structures and Control Mechanisms appear across these stories?

2. **Reveals Historical Continuity:** How do these current issues connect to patterns from previous eras? What systematic functions are being maintained?

3. **Maps Community Resistance:** What organizing opportunities and resistance strategies emerge from analyzing these issues together?

4. **Develops Liberation Strategy:** What coordinated community organizing approach could address these interconnected issues?

5. **Provides Action Framework:** Create a concrete organizing agenda for Chicago communities.

**Format:**
- Start with "The Pattern Behind the Headlines" section
- Use the Dignity Lens domains as organizing structure
- End with "From Analysis to Action" section with specific organizing steps
- Include #DignityLens and credit to Defy Racism Collective

**Goal:** Help communities see connections between separate news stories and build coordinated resistance.
"""

def safe_save_content(content, filename, metadata=None):
    """Safely save content with metadata"""
    try:
        # Create directory
        os.makedirs('generated_content', exist_ok=True)
        
        # Clean filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.')).strip()
        
        # Create full content with metadata
        full_content = f"""---
Generated: {datetime.now().isoformat()}
Framework: Dignity Lens
Organization: Defy Racism Collective
Website: https://defyracismcollective.org
"""
        
        if metadata:
            for key, value in metadata.items():
                full_content += f"{key}: {value}\n"
        
        full_content += f"""---

{content}

---
*This analysis was generated using the Dignity Lens Framework developed by the Defy Racism Collective. For more information about community organizing and political education, visit defyracismcollective.org*
"""
        
        # Save markdown file
        filepath = os.path.join('generated_content', safe_filename)
        with open(filepath, 'w', encoding='utf-8', errors='replace') as f:
            f.write(full_content)
        
        print(f"✅ Saved: {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save {filename}: {e}")
        return False

def main():
    """Main function with comprehensive error handling"""
    print("=" * 70)
    print("🎯 DIGNITY LENS CONTENT GENERATOR")
    print("   Transforming News into Community Power")
    print("=" * 70)
    
    # Step 1: Check environment
    client = check_environment()
    if not client:
        print("\n❌ Environment check failed. Exiting.")
        sys.exit(1)
    
    # Step 2: Fetch articles
    print("\n📰 Fetching Chicago news articles...")
    all_articles = []
    
    for feed_url in RSS_FEEDS:
        articles = safe_fetch_feed(feed_url)
        all_articles.extend(articles)
        time.sleep(2)  # Be respectful to servers
    
    if not all_articles:
        print("❌ No articles found. Exiting.")
        sys.exit(1)
    
    print(f"📊 Total articles found: {len(all_articles)}")
    
    # Step 3: Filter for relevance
    print("\n🔍 Filtering for systematic racism analysis opportunities...")
    relevant_articles = filter_articles(all_articles)
    
    if not relevant_articles:
        print("⚠️  No relevant articles found.")
        # Generate a daily organizing prompt instead
        print("📝 Generating daily organizing content...")
        return generate_daily_content(client)
    
    print(f"🎯 Relevant articles: {len(relevant_articles)}")
    
    # Step 4: Generate individual analyses
    print("\n🧠 Generating Dignity Lens analyses...")
    date_str = datetime.now().strftime('%Y-%m-%d')
    successful_generations = 0
    
    # Analyze top 2 most relevant articles
    for i, article in enumerate(relevant_articles[:2]):
        print(f"\n--- Analyzing Article {i+1} ---")
        print(f"Title: {article['title'][:60]}...")
        print(f"Keywords: {', '.join(article.get('matched_keywords', []))}")
        
        try:
            # Create Dignity Lens prompt
            prompt = create_dignity_lens_prompt(article)
            messages = [{"role": "user", "content": prompt}]
            
            # Generate analysis
            analysis = safe_api_call(client, messages)
            
            if analysis:
                # Create metadata
                metadata = {
                    'Source': article.get('source_name', 'Unknown'),
                    'Original_URL': article.get('url', ''),
                    'Keywords': ', '.join(article.get('matched_keywords', [])),
                    'Analysis_Type': 'Individual Article'
                }
                
                # Save content
                title_slug = article['title'][:30].lower().replace(' ', '-').replace(',', '').replace('.', '')
                filename = f"{date_str}-{title_slug}-analysis.md"
                
                if safe_save_content(analysis, filename, metadata):
                    successful_generations += 1
            
        except Exception as e:
            print(f"❌ Error processing article {i+1}: {e}")
            continue
    
    # Step 5: Generate trend analysis if we have multiple articles
    if len(relevant_articles) >= 2:
        print(f"\n--- Generating Trend Analysis ---")
        try:
            prompt = create_trend_analysis_prompt(relevant_articles)
            messages = [{"role": "user", "content": prompt}]
            
            trend_analysis = safe_api_call(client, messages)
            
            if trend_analysis:
                metadata = {
                    'Analysis_Type': 'Trend Analysis',
                    'Articles_Analyzed': len(relevant_articles[:3]),
                    'Keywords': ', '.join(set([kw for article in relevant_articles[:3] for kw in article.get('matched_keywords', [])]))
                }
                
                filename = f"{date_str}-chicago-trends-analysis.md"
                if safe_save_content(trend_analysis, filename, metadata):
                    successful_generations += 1
        
        except Exception as e:
            print(f"❌ Error generating trend analysis: {e}")
    
    # Step 6: Generate index file
    try:
        index_data = {
            'generated_at': datetime.now().isoformat(),
            'total_articles_found': len(all_articles),
            'relevant_articles': len(relevant_articles),
            'successful_generations': successful_generations,
            'framework': 'Dignity Lens',
            'organization': 'Defy Racism Collective',
            'website': 'https://defyracismcollective.org'
        }
        
        with open('generated_content/index.json', 'w') as f:
            json.dump(index_data, f, indent=2)
            
        print("✅ Generated index.json")
        
    except Exception as e:
        print(f"⚠️  Could not create index: {e}")
    
    # Step 7: Summary
    print("\n" + "=" * 70)
    print("📋 GENERATION SUMMARY")
    print("=" * 70)
    print(f"Articles processed: {len(relevant_articles[:2])}")
    print(f"Successful generations: {successful_generations}")
    print(f"Content saved to: ./generated_content/")
    print(f"Framework: Dignity Lens (Defy Racism Collective)")
    
    if successful_generations > 0:
        print("🎉 Success! Check the generated_content directory.")
        print("🔗 Learn more: https://defyracismcollective.org")
    else:
        print("⚠️  No content was successfully generated.")
        sys.exit(1)

def generate_daily_content(client):
    """Generate daily organizing content when no news articles are relevant"""
    print("📝 Generating daily organizing prompt...")
    
    prompt = """
Create a daily organizing reflection using the Dignity Lens framework for Chicago communities.

Include:
1. A systematic racism analysis prompt for the day
2. A historical connection to this date in liberation history
3. 3 concrete organizing actions people can take today
4. A community care reminder

Keep it 400-600 words, inspirational but analytically grounded.
Use #DignityLens and credit Defy Racism Collective.
"""
    
    messages = [{"role": "user", "content": prompt}]
    content = safe_api_call(client, messages)
    
    if content:
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"{date_str}-daily-organizing-prompt.md"
        metadata = {'Analysis_Type': 'Daily Organizing Prompt'}
        
        if safe_save_content(content, filename, metadata):
            print("✅ Generated daily organizing content")
            return True
    
    return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
