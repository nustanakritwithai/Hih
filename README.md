# Daily News Automation

Automated daily news aggregator that fetches top headlines from multiple RSS feeds
and saves them as Markdown reports in this repository.

## How It Works

1. **GitHub Actions** triggers the workflow every day at **06:00 UTC** (13:00 Bangkok time)
2. `fetch_news.py` pulls articles from 10 news sources
3. Reports are saved to `news_output/news_YYYY-MM-DD.md` and `news_output/latest.md`
4. The bot auto-commits and pushes the new report

## News Sources

| Source | Category |
|--------|----------|
| BBC News - World | World |
| BBC News - Technology | Technology |
| Reuters - Top News | Top News |
| Reuters - Technology | Technology |
| CNN - Top Stories | Top News |
| TechCrunch | Technology |
| The Verge | Technology |
| Hacker News - Best | Tech Community |
| NASA Breaking News | Science |
| Al Jazeera - World | World |

## File Structure

```
.
├── .github/
│   └── workflows/
│       └── daily_news.yml      # GitHub Actions workflow (runs daily)
├── news_automation/
│   ├── fetch_news.py           # Main news fetcher script
│   └── requirements.txt        # Python dependencies
└── news_output/
    ├── latest.md               # Most recent report
    ├── news_2026-04-15.md      # Daily report (by date)
    └── news_2026-04-15.json    # Raw JSON data
```

## Run Locally

```bash
pip install -r news_automation/requirements.txt
python news_automation/fetch_news.py
```

## Manual Trigger

Go to **Actions** tab → **Daily News Automation** → **Run workflow**
