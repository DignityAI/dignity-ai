# Dignity AI Content Generator

🎯 **Transforming News into Community Power**

Automated content generation using the revolutionary Dignity Lens framework developed by the Defy Racism Collective. This system analyzes Chicago news through systematic racism analysis to build community understanding and organizing capacity.

## 🌟 Framework Overview

The **Dignity Lens** examines systematic racism through four interconnected domains across seven historical eras:

### Four Core Domains:
1. **Power Structures** - Who holds decision-making authority and how is it maintained?
2. **Control Mechanisms** - How are Black communities contained and suppressed? 
3. **Community Resistance** - How do Black communities survive and fight back?
4. **Liberation Strategies** - What has actually worked to build Black freedom and power?

### Seven Historical Eras:
1. **Enslavement & Early Resistance** (1600s–1865)
2. **Reconstruction & Backlash** (1865–1910)
3. **Jim Crow & Black Institution-Building** (1910–1950)
4. **Civil Rights & Black Power** (1950–1975)
5. **Neoliberalization & Mass Incarceration** (1975–2008)
6. **Digital Rebellion & Corporate Capture** (2008–2020)
7. **Abolitionist Futuring & AI Counterinsurgency** (2020–present)

## 🚀 How It Works

### Daily Content Generation
1. **Fetches** Chicago news from multiple RSS feeds
2. **Filters** for articles about systematic issues (housing, police, education, etc.)
3. **Analyzes** using the Dignity Lens framework
4. **Generates** comprehensive analyses connecting individual stories to systematic patterns
5. **Provides** concrete organizing opportunities for Chicago communities

### Content Types Generated:
- **Individual Article Analysis** - Deep dive into specific news stories
- **Trend Analysis** - Connections across multiple current issues  
- **Daily Organizing Prompts** - When no relevant news is found

## 📁 Repository Structure

```
dignity-ai/
├── scripts/
│   └── content_generator.py     # Main content generator
├── generated_content/           # Output directory for analyses
├── .github/workflows/
│   └── generate-content.yml     # GitHub Actions automation
├── requirements.txt             # Python dependencies
└── README.md                   # This file
```

## ⚙️ Setup & Configuration

### Local Development

1. **Clone repository:**
   ```bash
   git clone https://github.com/DignityAI/dignity-ai.git
   cd dignity-ai
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variable:**
   ```bash
   export CLAUDE_API_KEY="your_anthropic_api_key_here"
   ```

4. **Run generator:**
   ```bash
   python scripts/content_generator.py
   ```

### GitHub Actions (Automated)

The system runs automatically daily at 9 AM UTC (4 AM Central Time) via GitHub Actions.

**Required Secret:**
- `CLAUDE_API_KEY` - Your Anthropic API key

**Setup:**
1. Go to repository Settings → Secrets and variables → Actions
2. Add `CLAUDE_API_KEY` with your Anthropic API key
3. The workflow will run automatically on schedule

## 📊 Output Examples

### Individual Analysis Structure:
```markdown
---
Generated: 2024-12-XX
Framework: Dignity Lens
Organization: Defy Racism Collective
---

# Analysis Title

## Power Structures Analysis
Who controls decision-making in this situation?

## Control Mechanisms  
How does this issue contain/suppress communities?

## Community Resistance
How are communities organizing around this?

## Liberation Strategies
What approaches could build genuine power?

## Historical Context
How does this connect to systematic patterns?

## Chicago Organizing Opportunities
1. Concrete action item 1
2. Concrete action item 2
3. Concrete action item 3

#DignityLens
```

## 🔧 Configuration

### RSS Feeds Monitored:
- Block Club Chicago
- Chicagoist  
- Chicago Tribune
- Chicago Sun-Times

### Keywords for Relevance:
- police, housing, school, community, mayor, budget
- gentrification, displacement, healthcare, education  
- immigration, voting, development, poverty, inequality

### Customization:
Edit `RSS_FEEDS` and `KEYWORDS` in `scripts/content_generator.py`

## 🛠️ Technical Details

### Dependencies:
- **anthropic** - Claude API integration
- **feedparser** - RSS feed parsing
- **requests** - HTTP requests
- **python-dateutil** - Date handling

### AI Model:
- **Claude 3.5 Haiku** - Optimized for speed and cost-efficiency
- **3000 token limit** per analysis
- **Rate limiting** - 3 second delays between API calls

### Error Handling:
- Comprehensive retry logic for API calls
- Graceful fallbacks when feeds are unavailable  
- Detailed logging and error reporting
- Automatic issue creation on workflow failures

## 📈 Monitoring & Maintenance

### GitHub Actions Monitoring:
- Workflow runs daily at 9 AM UTC
- Creates GitHub issues on failures
- Provides detailed logs and error reporting

### Content Quality:
- Each analysis includes metadata an
