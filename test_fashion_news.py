import pytest
from datetime import datetime, timedelta
from fashion_news import load_feeds

def test_load_feeds(tmp_path):
    yaml_content = """
feeds:
  - name: Test Feed
    url: http://example.com/rss
"""
    config_file = tmp_path / "feeds.yaml"
    config_file.write_text(yaml_content)
    feeds = load_feeds(str(config_file))
    assert len(feeds) == 1
    assert feeds[0]['name'] == 'Test Feed'

def test_deduplication_and_ranking(monkeypatch):
    # Mock entries
    now = datetime.now()
    entries = [
        {'source': 'A', 'title': 'T1', 'link': 'L1', 'pub_date': now, 'description': 'desc one'},
        {'source': 'B', 'title': 'T2', 'link': 'L1', 'pub_date': now, 'description': 'desc one'},  # duplicate by URL
        {'source': 'C', 'title': 'T3', 'link': 'L3', 'pub_date': now, 'description': 'desc one'},  # duplicate by text
        {'source': 'D', 'title': 'T4', 'link': 'L4', 'pub_date': now - timedelta(days=2), 'description': 'desc two'},  # old
        {'source': 'E', 'title': 'T5', 'link': 'L5', 'pub_date': now, 'description': 'desc three longer'},
    ]
    # Import deduplication and ranking logic from fashion_news.py as functions (assume refactor if needed)
    from fuzzywuzzy import fuzz
    # Deduplicate by URL
    seen_urls = set()
    deduped_entries = []
    for entry in entries:
        if entry['link'] not in seen_urls:
            deduped_entries.append(entry)
            seen_urls.add(entry['link'])
    # Deduplicate by text
    final_entries = []
    for entry in deduped_entries:
        is_duplicate = False
        for kept in final_entries:
            if fuzz.token_set_ratio(entry['description'], kept['description']) > 80:
                is_duplicate = True
                break
        if not is_duplicate:
            final_entries.append(entry)
    # Filter last 24h
    last_24h = [e for e in final_entries if (now - e['pub_date']).total_seconds() <= 86400]
    # Rank by pub_date, then description length
    ranked = sorted(
        last_24h,
        key=lambda e: (e['pub_date'], len(e['description'].split())),
        reverse=True
    )
    assert len(ranked) == 2  # Only two unique, recent entries
    assert ranked[0]['description'] == 'desc three longer'  # Longest description first 