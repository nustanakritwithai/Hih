#!/usr/bin/env python3
"""
Daily News Automation - Fetches top news from multiple RSS feeds
using only Python standard library (no external dependencies required).
"""

import json
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import unescape
from pathlib import Path


# -------------------------
# News Sources Configuration
# -------------------------
NEWS_SOURCES = [
    {
        "name": "BBC News - World",
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "category": "World",
    },
    {
        "name": "BBC News - Technology",
        "url": "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "category": "Technology",
    },
    {
        "name": "Reuters - Top News",
        "url": "https://feeds.reuters.com/reuters/topNews",
        "category": "Top News",
    },
    {
        "name": "CNN - Top Stories",
        "url": "http://rss.cnn.com/rss/edition.rss",
        "category": "Top News",
    },
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "category": "Technology",
    },
    {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
        "category": "Technology",
    },
    {
        "name": "Hacker News - Best",
        "url": "https://hnrss.org/best",
        "category": "Tech Community",
    },
    {
        "name": "NASA Breaking News",
        "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "category": "Science",
    },
    {
        "name": "Al Jazeera - World",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "category": "World",
    },
    {
        "name": "Science Daily",
        "url": "https://www.sciencedaily.com/rss/top/science.xml",
        "category": "Science",
    },
]

MAX_ARTICLES_PER_SOURCE = 5
REQUEST_TIMEOUT = 15  # seconds


def clean_html(text: str) -> str:
    """Remove HTML tags and decode HTML entities."""
    if not text:
        return ""
    text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_tag_text(element, tag: str, namespaces: dict | None = None) -> str:
    """Safely get text from an XML element by tag name."""
    # Try plain tag first
    child = element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    # Try with namespace prefixes
    if namespaces:
        for prefix, uri in namespaces.items():
            child = element.find(f"{{{uri}}}{tag}")
            if child is not None and child.text:
                return child.text.strip()
    return ""


def parse_rss(xml_bytes: bytes, source_name: str, category: str) -> list[dict]:
    """Parse RSS/Atom XML and extract articles."""
    articles = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"     [XML parse error] {e}")
        return articles

    # Detect namespaces used in the document
    ns_map = {}
    for event, elem in ET.iterparse(
        __import__("io").BytesIO(xml_bytes), events=["start-ns"]
    ):
        prefix, uri = elem
        ns_map[prefix or "default"] = uri

    # Handle both RSS 2.0 (<item>) and Atom 1.0 (<entry>)
    items = root.findall(".//item") or root.findall(
        ".//{http://www.w3.org/2005/Atom}entry"
    )

    for item in items[:MAX_ARTICLES_PER_SOURCE]:
        # Title
        title = (
            get_tag_text(item, "title")
            or get_tag_text(item, "{http://www.w3.org/2005/Atom}title")
            or "No title"
        )
        title = clean_html(title)

        # Link
        link = get_tag_text(item, "link") or ""
        if not link:
            # Atom style: <link href="..."/>
            link_el = item.find("{http://www.w3.org/2005/Atom}link")
            if link_el is not None:
                link = link_el.get("href", "")

        # Summary / description
        summary = (
            get_tag_text(item, "description")
            or get_tag_text(item, "summary")
            or get_tag_text(item, "{http://www.w3.org/2005/Atom}summary")
            or get_tag_text(item, "{http://www.w3.org/2005/Atom}content")
            or ""
        )
        summary = clean_html(summary)
        if len(summary) > 300:
            summary = summary[:297] + "..."

        # Published date
        published = (
            get_tag_text(item, "pubDate")
            or get_tag_text(item, "published")
            or get_tag_text(item, "{http://www.w3.org/2005/Atom}published")
            or get_tag_text(item, "{http://www.w3.org/2005/Atom}updated")
            or ""
        )

        articles.append(
            {
                "source": source_name,
                "category": category,
                "title": title,
                "summary": summary,
                "link": link,
                "published": published,
            }
        )

    return articles


def fetch_feed(source: dict) -> list[dict]:
    """Download and parse a single RSS/Atom feed."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; DailyNewsBot/1.0; "
            "+https://github.com/nustanakritwithai/hih)"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    try:
        req = urllib.request.Request(source["url"], headers=headers)
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            xml_bytes = resp.read()
        return parse_rss(xml_bytes, source["name"], source["category"])
    except urllib.error.HTTPError as e:
        print(f"     [HTTP {e.code}] {e.reason}")
    except urllib.error.URLError as e:
        print(f"     [URL Error] {e.reason}")
    except Exception as e:
        print(f"     [Error] {e}")
    return []


def group_by_category(articles: list[dict]) -> dict:
    """Group articles by category, preserving insertion order."""
    grouped: dict[str, list] = {}
    for article in articles:
        cat = article["category"]
        grouped.setdefault(cat, []).append(article)
    return grouped


def generate_markdown(articles: list[dict], datetime_str: str) -> str:
    """Generate a formatted Markdown report."""
    grouped = group_by_category(articles)
    total = len(articles)

    lines = [
        "# Daily News Report",
        "",
        f"> **Date:** {datetime_str}  ",
        f"> **Total Articles:** {total}  ",
        f"> **Sources:** {len(NEWS_SOURCES)}",
        "",
        "---",
        "",
        "## Table of Contents",
        "",
    ]

    for cat in grouped:
        anchor = cat.lower().replace(" ", "-")
        lines.append(f"- [{cat}](#{anchor})")

    lines += ["", "---", ""]

    for cat, cat_articles in grouped.items():
        lines.append(f"## {cat}")
        lines.append("")
        for article in cat_articles:
            lines.append(f"### {article['title']}")
            lines.append("")
            if article["summary"]:
                lines.append(article["summary"])
                lines.append("")
            meta: list[str] = [f"**Source:** {article['source']}"]
            if article["published"]:
                meta.append(f"**Published:** {article['published']}")
            if article["link"]:
                meta.append(f"[Read more]({article['link']})")
            lines.append(" | ".join(meta))
            lines.append("")
            lines.append("---")
            lines.append("")

    lines.append(
        f"*Report generated automatically on {datetime_str} by Daily News Automation.*"
    )
    return "\n".join(lines)


def save_json(articles: list[dict], output_path: Path) -> None:
    """Save raw articles as JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_articles": len(articles),
                "articles": articles,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def main() -> int:
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    datetime_str = now.strftime("%Y-%m-%d %H:%M UTC")

    output_dir = Path(__file__).parent.parent / "news_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching news for {date_str}...")

    all_articles: list[dict] = []
    for source in NEWS_SOURCES:
        print(f"  -> {source['name']}...")
        articles = fetch_feed(source)
        all_articles.extend(articles)
        print(f"     {len(articles)} articles fetched")

    print(f"\nTotal: {len(all_articles)} articles from {len(NEWS_SOURCES)} sources")

    if not all_articles:
        print("No articles fetched. Exiting without writing files.")
        return 0

    # Save Markdown report
    md_path = output_dir / f"news_{date_str}.md"
    markdown = generate_markdown(all_articles, datetime_str)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"Markdown saved: {md_path}")

    # Save JSON data
    json_path = output_dir / f"news_{date_str}.json"
    save_json(all_articles, json_path)
    print(f"JSON saved:     {json_path}")

    # Always keep a "latest.md" up to date
    latest_md = output_dir / "latest.md"
    with open(latest_md, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"Latest updated: {latest_md}")

    return len(all_articles)


if __name__ == "__main__":
    count = main()
    print(f"\nDone! {count} articles saved.")
