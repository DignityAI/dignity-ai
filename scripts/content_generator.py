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
from knowledge_accumulation import LiberationKnowledgeSystem, extract_location_from_article, extract_domain_from_article, extract_themes_from_article

# Initialize Claude API and Knowledge System
client = Anthropic(api_key=os.environ['CLAUDE_API_KEY'])
knowledge_system = LiberationKnowledgeSystem()

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

# Enhanced keywords organized by SDOH categories
SDOH_KEYWORDS = {
   'economic_stability': [
       'unemployment', 'wage', 'salary', 'benefits', 'welfare', 'snap', 'food stamps',
       'medicaid', 'medicare', 'social security', 'disability', 'poverty', 'income',
       'layoffs', 'hiring', 'minimum wage', 'living wage', 'eviction', 'foreclosure',
       'debt', 'bankruptcy', 'economic relief', 'stimulus', 'unemployment benefits'
   ],
   
   'neighborhood_environment': [
       'pollution', 'toxic', 'environmental', 'housing crisis', 'affordable housing',
       'transit', 'transportation', 'bus', 'subway', 'gentrification', 'displacement',
       'zoning', 'development', 'construction', 'infrastructure', 'lead', 'asbestos',
       'air quality', 'water quality', 'climate', 'flooding', 'heat island'
   ],
   
   'education_access': [
       'school closure', 'school funding', 'education budget', 'teacher', 'curriculum',
       'special education', 'school board', 'CPS', 'charter school', 'voucher',
       'student loans', 'college', 'university', 'graduation', 'dropout',
       'digital divide', 'remote learning', 'school discipline', 'suspension'
   ],
   
   'healthcare_access': [
       'medicaid', 'medicare', 'insurance', 'clinic closure', 'hospital merger',
       'healthcare', 'medical', 'mental health', 'pharmacy', 'prescription',
       'emergency room', 'maternal health', 'reproductive health', 'dental',
       'addiction', 'substance abuse', 'ambulance', 'nursing home', 'dialysis'
   ],
   
   'social_community_context': [
       'police', 'policing', 'arrest', 'incarceration', 'prison', 'jail',
       'family separation', 'child welfare', 'foster care', 'domestic violence',
       'isolation', 'social services', 'community center', 'senior center',
       'discrimination', 'hate crime', 'violence', 'safety', 'neighborhood watch'
   ],
   
   'food_access': [
       'food desert', 'food apartheid', 'grocery store', 'supermarket',
       'school meals', 'free lunch', 'food pantry', 'food bank', 'nutrition',
       'farmers market', 'urban farming', 'food stamps', 'snap', 'wic',
       'restaurant', 'fast food', 'healthy food', 'corner store'
   ]
}

# Flatten for backward compatibility with existing system
RELEVANT_KEYWORDS = []
for category_keywords in SDOH_KEYWORDS.values():
   RELEVANT_KEYWORDS.extend(category_keywords)

# Add existing keywords
RELEVANT_KEYWORDS.extend([
   'police', 'housing', 'health', 'school', 'education', 'city council',
   'mayor', 'budget', 'development', 'community', 'neighborhood',
   'crime', 'safety', 'racism', 'discrimination', 'inequality', 'tenant',
   'eviction', 'gentrification', 'affordable', 'CPS', 'teacher', 'student'
])

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

def identify_sdoh_categories(article):
   """Identify which SDOH categories an article relates to"""
   text = (article['title'] + ' ' + article.get('content', '')).lower()
   
   relevant_categories = []
   for category, keywords in SDOH_KEYWORDS.items():
       if any(keyword in text for keyword in keywords):
           relevant_categories.append(category)
   
   return relevant_categories

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

def create_power_mapping_prompt(article, sdoh_categories, fact_check_result=None):
   """Create power mapping analysis for SDOH issues"""
   categories_text = ', '.join(sdoh_categories) if sdoh_categories else 'Multiple SDOH factors'
   
   fact_check_context = ""
   if fact_check_result:
       fact_check_context = f"\n\nFACT-CHECK NOTES: {fact_check_result}\n"
   
   return f"""
You are DignityAI creating a POWER MAPPING analysis for community organizers.
{fact_check_context}

ARTICLE:
Title: {article['title']}
Content: {article['content']}
Source: {article['url']}

IDENTIFIED SDOH CATEGORIES: {categories_text}

Create a comprehensive POWER MAPPING analysis (1000-1200 words) that organizers can use to understand and challenge the power dynamics in this story:

# POWER MAPPING ANALYSIS: [Title]

## Executive Summary: Who Has Power and How to Challenge It
[3-sentence summary of the key power relationships and organizing opportunities]

## PRIMARY POWER HOLDERS

### Decision Makers (Those with direct authority)
- **Individual Names/Titles:** [Specific people who made these decisions]
- **Institutions:** [Government agencies, corporations, boards]
- **Decision-Making Process:** [How decisions are made, who's excluded]
- **Accountability Mechanisms:** [How they can be influenced/pressured]

### Influencers (Those who shape decisions)
- **Corporate Interests:** [Companies that benefit from these decisions]
- **Political Networks:** [Politicians, lobbyists, party connections]
- **Professional Networks:** [Industry associations, think tanks]
- **Media Influences:** [How story is being framed, by whom]

### Resource Controllers (Those who control money/resources)
- **Funding Sources:** [Who provides the money for these programs/policies]
- **Budget Decision Points:** [Where money gets allocated]
- **Private Sector Beneficiaries:** [Who profits from current arrangements]
- **Resource Flow Analysis:** [How money moves, where it comes from/goes]

## COMMUNITY POWER ANALYSIS

### Affected Communities
- **Primary Impact Groups:** [Who is most affected by these decisions]
- **Secondary Impact Groups:** [Who else is affected]
- **Community Assets:** [What resources/power do communities have]
- **Existing Organization:** [What groups are already organizing]

### Current Community Representation
- **Formal Representation:** [Elected officials, board members from community]
- **Advocacy Groups:** [Organizations claiming to represent community]
- **Authenticity Assessment:** [How accountable are these reps to community]
- **Representation Gaps:** [Where community voice is missing]

## POWER DYNAMICS & RELATIONSHIPS

### Alliance Map
- **Potential Allies in Power:** [People in power who might support community]
- **Swing Votes:** [Those who could be influenced either direction]
- **Opposition:** [Those actively working against community interests]
- **Corporate/Government Partnerships:** [How private and public power connect]

### Pressure Points
- **Electoral Vulnerabilities:** [Elections, political pressure points]
- **Economic Pressure Points:** [Budget cycles, contract renewals, protests]
- **Legal Vulnerabilities:** [Possible legal challenges, policy violations]
- **Reputational Concerns:** [Public image issues, media attention]

## ORGANIZING STRATEGY RECOMMENDATIONS

### Short-Term Tactics (Next 3-6 months)
- **Direct Pressure:** [Specific actions to pressure decision-makers]
- **Coalition Building:** [Who to partner with for immediate impact]
- **Media Strategy:** [How to shift narrative and apply public pressure]
- **Policy Interventions:** [Specific policy changes to demand]

### Medium-Term Power Building (6-18 months)
- **Electoral Strategy:** [Elections to target, candidates to recruit/support]
- **Institution Building:** [What organizations/capacity need to be built]
- **Policy Development:** [Longer-term policy goals and campaigns]
- **Coalition Expansion:** [Building broader movements and alliances]

### Long-Term System Change (1-3 years)
- **Structural Changes:** [What systematic changes are needed]
- **Community Control:** [How to build lasting community power]
- **Alternative Institutions:** [What community-controlled alternatives to build]
- **Movement Building:** [How this connects to broader liberation movements]

## TACTICAL POWER ANALYSIS

### Leverage Points
- **Economic Leverage:** [Boycotts, divestment, economic pressure]
- **Political Leverage:** [Votes, endorsements, electoral consequences]
- **Legal Leverage:** [Lawsuits, regulatory challenges, compliance issues]
- **Social Leverage:** [Public pressure, reputation, community mobilization]

### Resource Mobilization
- **Community Resources:** [What the community can contribute]
- **External Resources:** [Potential funding, technical assistance]
- **Coalition Resources:** [What allies can provide]
- **Opposition Resources:** [What the opposition has, how to counter]

## SDOH-SPECIFIC POWER ANALYSIS

### Health Equity Power Dynamics
- **Health System Power:** [Who controls health resources in this situation]
- **Social Determinant Controllers:** [Who makes decisions affecting health]
- **Community Health Assets:** [Health-related community resources/capacity]
- **Health Justice Organizing:** [How this connects to health equity organizing]

## ACTION RECOMMENDATIONS

### Immediate Actions (Next 30 days)
1. [Specific action with target, timeline, responsible parties]
2. [Specific action with target, timeline, responsible parties]
3. [Specific action with target, timeline, responsible parties]

### Capacity Building Needs
- **Research:** [What additional information is needed]
- **Organizing:** [What organizing capacity needs to be built]
- **Coalition:** [What relationships need to be developed]
- **Resources:** [What funding/support is needed]

### Success Metrics
- **Short-term wins:** [How to measure immediate progress]
- **Power building indicators:** [How to measure growing community power]
- **Long-term transformation:** [How to measure systematic change]

## CONCLUSION: From Power Analysis to Community Power
[Connect this power mapping to broader liberation organizing and community power building]

**Key Takeaway:** [One-sentence summary of the most important organizing opportunity]

**Next Steps:** [Three concrete actions organizers can take immediately]

This analysis should help organizers understand exactly who has power, how to pressure them, and how to build community power to create lasting change on this issue.
"""

def create_enhanced_case_study_prompt(article, fact_check_result=None):
   """Create enhanced prompt for Dignity Lens case study with fact-check integration"""
   fact_check_context = ""
   if fact_check_result and "FACT_CHECK_PASS" in fact_check_result:
       fact_check_context = f"\n\nFACT-CHECK CLEARED: This content has been verified for accuracy and systematic analysis readiness.\n{fact_check_result}\n"
   elif fact_check_result and "FACT_CHECK_CONCERNS" in fact_check_result:
       fact_check_context = f"\n\nFACT-CHECK NOTES: Please address these concerns in your analysis:\n{fact_check_result}\n"
   
   return f"""
You are DignityAI. Create TWO complementary case studies using the Dignity Lens framework.
{fact_check_context}
ARTICLE TO ANALYZE:
Title: {article['title']}
Content: {article['content']}
Word Count: {article.get('word_count', 'Unknown')}
Source: {article['url']}

GENERATE TWO CASE STUDIES:

## CASE STUDY A: LOCAL SYSTEMATIC ANALYSIS
Focus specifically on the city/region mentioned in the article. Analyze local Power Structures, Control Mechanisms, Community Resistance, and Liberation Strategies.

## CASE STUDY B: NATIONAL COMPARATIVE ANALYSIS  
Compare this local pattern to how the same systematic issue operates in other major cities (Chicago, LA, Austin, Philadelphia, DC, Houston, Atlanta, etc.).

Format as markdown with:

# LOCAL CASE STUDY: [City Name] - [Issue]
## Executive Summary
## Local Dignity Lens Analysis
### Power Structures (City/County/State Level)
### Control Mechanisms (How This Operates Locally)
### Community Resistance (Local Organizing Examples)
### Liberation Strategies (What's Worked in This City)
## Local Organizing Opportunities
## Conclusion

---

# NATIONAL COMPARATIVE ANALYSIS: [Issue] Across U.S. Cities
## Executive Summary
## Cross-City Pattern Analysis
### How Power Structures Vary by Region
### Control Mechanisms: Common Tactics vs. Local Variations
### Community Resistance: Successful Models from Different Cities
### Liberation Strategies: What's Replicable Nationwide
## State-by-State Policy Comparisons
## Federal Policy Connections
## Cross-City Organizing Opportunities
### Regional Coalition Building
### National Movement Connections
### Policy Advocacy at Multiple Levels
## Conclusion

Each case study should be 1000-1200 words. Connect local incidents to systematic patterns while providing both city-specific and nationally replicable organizing strategies.
"""

def create_sdoh_analysis_prompt(article, sdoh_categories, fact_check_result=None):
   """Create SDOH-focused Dignity Lens analysis"""
   categories_text = ', '.join(sdoh_categories) if sdoh_categories else 'Multiple SDOH factors'
   
   fact_check_context = ""
   if fact_check_result:
       fact_check_context = f"\n\nFACT-CHECK NOTES: {fact_check_result}\n"
   
   return f"""
You are DignityAI analyzing Social Determinants of Health through the Dignity Lens framework.
{fact_check_context}

ARTICLE:
Title: {article['title']}
Content: {article['content']}
Source: {article['url']}

IDENTIFIED SDOH CATEGORIES: {categories_text}

Create a comprehensive SDOH analysis (800-1000 words) showing how this story reveals systematic patterns affecting community health:

# SDOH Analysis: [Title focusing on health equity implications]

## Health Equity Impact Summary
[How this story directly affects community health outcomes]

## Dignity Lens Analysis Through SDOH Framework

### Power Structures (Who Controls Health-Affecting Decisions)
- Who makes the decisions described in this story?
- How do these decisions affect community health?
- What health-related institutions are involved?
- How are communities excluded from health-affecting decisions?

### Control Mechanisms (How Health Inequities Are Maintained)
- How does this story show systematic health oppression?
- What barriers to health are created or maintained?
- How do these mechanisms affect specific populations?
- Connection to other SDOH categories

### Community Resistance (Health Justice Organizing)
- How are communities fighting for health equity?
- What organizing strategies address health determinants?
- Community-led health solutions mentioned or possible
- Connections to broader health justice movements

### Liberation Strategies (What Works for Health Equity)
- Policy solutions that address root causes
- Community-controlled health initiatives
- Cross-sector organizing opportunities
- Replicable models from other cities

## Cross-SDOH Connections
[How this issue connects to other social determinants]

## Health Justice Organizing Opportunities
### Local Actions
- [Specific organizing opportunities in this community]
- [Health justice organizations to connect with]

### Policy Advocacy
- [Local, state, federal policy changes needed]
- [How to influence health-affecting decisions]

### Community Health Building
- [Ways to build community health power]
- [Alternative health approaches to develop]

## Conclusion: From Health Disparities to Health Liberation
[Connect individual story to systematic health transformation]

Focus on how social determinants create health inequities and how community organizing can address root causes of poor health outcomes.
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

Rewrite from a MULTI-CITY LIBERATION ORGANIZING perspective (700-900 words):
- Center community voices and impacts in the specific city/region
- Analyze systematic patterns that operate across multiple cities
- Connect local story to broader liberation organizing nationwide
- Compare similar organizing strategies in Chicago, LA, Austin, Philadelphia, DC
- Provide community organizing context that can be replicated
- Include actionable information for residents locally and regionally
- Address any fact-check concerns noted above

Format as:
# [Community-Centered Headline]
## [Subheading focusing on systematic patterns across cities]

[Article content with multi-city Liberation Technology perspective]

**Fact-Check and Sources:**
[Any additional context or verification needed]

**Community Organizing Opportunities:**

**Local Actions (City-Specific):**
- [Actions for residents in this specific city]
- [Local organizations to connect with]
- [City council meetings, local campaigns]

**Regional and National Connections:**
- [How this connects to organizing in other cities]
- [Cross-city coalitions and networks]
- [Federal policy implications and actions]
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

Create an accessible blog post (500-700 words) that makes MULTI-CITY SYSTEMATIC PATTERNS accessible:
- Makes systematic racism analysis accessible to general readers
- Uses concrete examples from the news story
- Connects individual story to patterns across Chicago, LA, Austin, Philadelphia, DC
- Shows how the same systems operate in different cities
- Provides hope and organizing pathways that can be replicated
- Addresses any fact-check concerns

Format as:
# [Engaging, accessible headline that shows broader pattern]

[Content explaining systematic patterns through this example]

## What This Really Means
[Connect local story to systematic patterns across multiple cities]

## The Full Context
[Address any fact-check concerns or missing context]

## How This Shows Up in Other Cities
[Examples of similar patterns in LA, Chicago, Austin, Philadelphia, etc.]

## What We Can Do About It
[Organizing opportunities locally and regionally]

**Get Involved:**

**In Your City:**
- [Local actions relevant to the city discussed]
- [Local organizations to support]

**Regional and National:**
- [Cross-city organizing opportunities]
- [National networks and coalitions]
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

def save_content(content, content_type, article_title, is_dual_case_study=False):
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
   
   # For dual case studies, split and save separately
   if is_dual_case_study and content_type == 'case-studies':
       # Split the content on the separator
       if '# NATIONAL COMPARATIVE ANALYSIS:' in content:
           local_study, national_study = content.split('# NATIONAL COMPARATIVE ANALYSIS:', 1)
           
           # Save local case study
           local_filename = f'drafts/{content_type}/{date_str}-LOCAL-{safe_title}.md'
           with open(local_filename, 'w', encoding='utf-8') as f:
               f.write(local_study.strip())
           print(f"✅ Saved Local: {local_filename}")
           
           # Save national comparative study
           national_filename = f'drafts/{content_type}/{date_str}-NATIONAL-{safe_title}.md'
           with open(national_filename, 'w', encoding='utf-8') as f:
               f.write('# NATIONAL COMPARATIVE ANALYSIS:' + national_study)
           print(f"✅ Saved National: {national_filename}")
           return
   
   # Regular single file save
   filename = f'drafts/{content_type}/{date_str}-{safe_title}.md'
   
   # Save content
   with open(filename, 'w', encoding='utf-8') as f:
       f.write(content)
   
   print(f"✅ Saved: {filename}")

def main():
   """Main content generation function with SDOH analysis and power mapping"""
   print("🚀 Starting enhanced daily content generation with SDOH analysis and power mapping...")
   
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
       
       # Identify SDOH categories
       sdoh_categories = identify_sdoh_categories(enhanced_article)
       if sdoh_categories:
           print(f"🏥 SDOH Categories: {', '.join(sdoh_categories)}")
       
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
       
       # Generate power mapping analysis (NEW)
       if sdoh_categories:
           print("🗺️ Generating power mapping analysis...")
           power_mapping_prompt = create_power_mapping_prompt(enhanced_article, sdoh_categories, fact_check_result)
           power_mapping = call_claude_api(power_mapping_prompt)
           save_content(power_mapping, 'power-mapping', enhanced_article['title'])
       
       # Generate SDOH analysis (NEW)
       if sdoh_categories:
           print("🏥 Generating SDOH health equity analysis...")
           sdoh_prompt = create_sdoh_analysis_prompt(enhanced_article, sdoh_categories, fact_check_result)
           sdoh_analysis = call_claude_api(sdoh_prompt)
           save_content(sdoh_analysis, 'sdoh-analysis', enhanced_article['title'])
       
       # Generate dual case studies (local + national comparative)
       print("🧠 Generating dual Dignity Lens case studies (Local + National)...")
       case_study_prompt = create_enhanced_case_study_prompt(enhanced_article, fact_check_result)
       case_study = call_claude_api(case_study_prompt)
       save_content(case_study, 'case-studies', enhanced_article['title'], is_dual_case_study=True)
       
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
       print(f"✅ Completed article {i+1} with fact-checking, SDOH analysis, and power mapping")
   
   print(f"\n🎉 Daily content generation complete! Processed {processed_count} fact-checked, high-quality articles.")
   print("📁 Generated content saved to:")
   print("  - drafts/case-studies/ (Local + National analyses)")
   print("  - drafts/news-articles/ (Community journalism)")
   print("  - drafts/blog-posts/ (Accessible explanations)")
   print("  - drafts/sdoh-analysis/ (Health equity focus)")
   print("  - drafts/power-mapping/ (Organizing strategy)")

if __name__ == "__main__":
   main()
