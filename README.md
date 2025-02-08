# Arizona Lottery Scratcher Analysis

🚨 **Critical Disclaimer** 🚨  
**This project is a quick experiment in web scraping and data analysis - not a rigorous statistical study. Important Notes:**

- 🎲 **Gambling Warning**: Lottery tickets are designed to lose money. Never consider this an investment strategy
- 🛠️ **Code Quality**: Built rapidly for learning purposes, not representative of production-grade code
- 📉 **Methodology Notes**:  
  - Prize odds calculations make simplifying assumptions  
  - No error margins calculated for estimates
  - Web scraping approach may break with website changes
- 📜 **No Guarantees**: Analysis may contain inaccuracies - verify with official sources

**Treat this as a curiosity, not financial advice or technical best practices.**

## Project Overview
Automated pipeline that:
1. 🕷️ Scrapes Arizona Lottery scratcher data daily
2. 📊 Analyzes prize pool statistics
3. 📈 Generates interactive visualizations
4. 🚀 Auto-deploys results to GitHub Pages

## Features
- **Automated Daily Updates** via GitHub Actions
- Prize pool tracking with historical trends
- Expected value calculations
- Self-updating website
- Data validation checks

## Requirements
- Python 3.10+
- Chrome Browser
- Chromedriver
- SQLite

## Local Setup
```bash
git clone https://github.com/ImmaZoni/Scratcha.git
cd scratcha

# Install dependencies
python -m pip install -r requirements.txt

# Initialize database
python db_handler.py
```

## Usage
**Full pipeline**:  
```bash
python scraper.py && python analysis_engine.py
```

**Scraper Options**:
```bash
# Limit to 5 pages
python scraper.py --max-page 5

# Run in headless mode
python scraper.py --headless
```

## Data Flow
1. **Scraper** (`scraper.py`) collects raw game data
2. **DB Handler** stores structured records
3. **Analysis Engine** calculates metrics
4. **GitHub Actions** deploys results hourly

## Website Features
- Live odds tracking
- Historical prize pool graphs
- Game comparison tools
- Auto-updating sitemap

## Contributing
This project is open for educational purposes:

1. Fork repository
2. Create feature branch  
   `git checkout -b feature/your-idea`
3. Submit PR with detailed notes

**Please Note**:
- Focus on technical improvements only
- No gambling-related suggestions
- Maintain academic tone

## Legal
Not affiliated with Arizona Lottery. Data sourced from public [AZ Lottery website](https://www.arizonalottery.com). Use at your own risk.

---

**Remember**: 🎰 Lottery tickets always have negative expected value. This project exists purely as a technical demonstration of web scraping and data analysis techniques. 