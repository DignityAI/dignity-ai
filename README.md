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
- Each analysis includes metadata and source attribution
- Framework consistency enforced through system prompts
- Concrete organizing opportunities in every analysis
- Historical connections to build systematic understanding

### Output Monitoring:
- `generated_content/index.json` tracks generation metrics
- Git commits include file counts and timestamps
- Failed generations logged with detailed error messages

## 🎯 Goals & Impact

### Transform Understanding:
**From:** "Why does this keep happening to me?"  
**To:** "I understand the system and I know how to fight it"

### Build Community Power:
- Connect individual news stories to systematic patterns
- Provide concrete organizing opportunities
- Build historical consciousness and strategic thinking
- Center community organizing and liberation strategies

### Educational Outcomes:
- **Systematic Analysis** - Help people see patterns across centuries
- **Historical Consciousness** - Connect current issues to resistance history  
- **Organizing Strategy** - Provide concrete pathways for community engagement
- **Liberation Framework** - Build understanding of what actually works

## 🤝 Community Engagement

### Chicago Organizing Connections:
Each analysis includes specific opportunities to engage with:
- Community organizations and campaigns
- Policy advocacy and electoral organizing  
- Mutual aid and community defense networks
- Educational and cultural organizing

### Cross-Movement Building:
- Connect housing justice to police accountability
- Link education organizing to economic development
- Build solidarity across racial and geographic lines
- Center intersectional analysis and coalition building

## 📚 Learn More

### Dignity Lens Framework:
- **Website:** https://defyracismcollective.org
- **Framework Documentation:** Complete case studies and historical analysis
- **Political Education:** Study guides and organizing tools
- **Community Organizing:** Local engagement opportunities

### Related Projects:
- **People's Newsroom** - Community journalism with systematic analysis
- **Community Health Worker Training** - Healthcare organizing with dignity metrics
- **Participatory Budgeting** - Direct democracy and community control

## 🔐 Privacy & Ethics

### Data Handling:
- **No personal data collection** - Only public RSS feeds analyzed
- **No storage of sensitive information** - Temporary processing only
- **Open source methodology** - Transparent analysis framework

### Ethical AI Use:
- **Community-controlled technology** - Serves organizing rather than surveillance
- **Liberation-focused analysis** - Centers community power building
- **Anti-oppression framework** - Challenges rather than perpetuates systematic bias

## 🚀 Contributing

### Code Contributions:
1. Fork the repository
2. Create feature branch: `git checkout -b feature/improvement-name`
3. Commit changes: `git commit -m "Add improvement"`
4. Push to branch: `git push origin feature/improvement-name`
5. Open Pull Request with detailed description

### Content Feedback:
- Open GitHub issues for analysis improvements
- Suggest new RSS feeds or keywords for monitoring
- Propose framework enhancements or applications

### Community Organizing:
- Use generated analyses in your organizing work
- Share with community organizations and study groups
- Adapt framework for local issues and campaigns
- Connect with Defy Racism Collective for partnership opportunities

## 📄 License & Attribution

### Framework Credit:
The Dignity Lens framework was developed by the **Defy Racism Collective** as a tool for community organizing and political education.

### Usage Requirements:
- **Attribution:** Credit Defy Racism Collective and include #DignityLens
- **Community Benefit:** Use for organizing, education, and community empowerment
- **No Commercial Use:** Framework serves liberation, not profit

### Contact:
- **Organization:** Defy Racism Collective
- **Website:** https://defyracismcollective.org
- **Framework:** Dignity Lens for systematic racism analysis

## 🔄 Changelog

### Version 1.0 (Current)
- ✅ Core Dignity Lens framework integration
- ✅ Chicago RSS feed monitoring  
- ✅ Individual article analysis generation
- ✅ Trend analysis across multiple articles
- ✅ Daily organizing prompt fallback
- ✅ GitHub Actions automation
- ✅ Comprehensive error handling and logging

### Planned Features:
- 📋 Community feedback integration
- 📋 Multi-city expansion beyond Chicago
- 📋 Interactive analysis dashboard
- 📋 Community organizing campaign tracking
- 📋 Historical archive search functionality

---

**🎯 Mission:** Transform individual confusion into collective understanding and community power through systematic racism analysis.

**🔗 Learn More:** https://defyracismcollective.org

**#DignityLens #CommunityPower #SystematicAnalysis**
