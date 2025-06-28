import yaml
import feedparser
import click
import logging
from datetime import datetime
from dateutil import parser as date_parser
from fuzzywuzzy import fuzz
import json
from dateutil import tz

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Load feeds from YAML config
def load_feeds(config_path='feeds.yaml'):
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('feeds', [])
    except Exception as e:
        logging.error(f"Failed to load feeds config: {e}")
        return []

# Fetch and parse a single feed
def fetch_feed(feed):
    try:
        parsed = feedparser.parse(feed['url'])
        entries = []
        for entry in parsed.entries:
            title = entry.get('title', '')
            link = entry.get('link', '')
            pub_date = entry.get('published', '') or entry.get('pubDate', '')
            try:
                pub_date = date_parser.parse(pub_date) if pub_date else None
            except Exception:
                pub_date = None
            description = entry.get('summary', '') or entry.get('description', '')
            entries.append({
                'source': feed['name'],
                'title': title,
                'link': link,
                'pub_date': pub_date,
                'description': description
            })
        return entries
    except Exception as e:
        logging.error(f"Error fetching/parsing feed {feed['name']}: {e}")
        return []

@click.command()
@click.option('--config', default='feeds.yaml', help='Path to feeds YAML config.')
@click.option('--output-format', type=click.Choice(['json', 'yaml', 'plaintext']), default='json', help='Output format: json, yaml, or plaintext.')
def main(config, output_format):
    """Aggregate and rank top fashion news from multiple RSS feeds."""
    feeds = load_feeds(config)
    if not feeds:
        logging.error("No feeds loaded. Exiting.")
        return
    all_entries = []
    for feed in feeds:
        logging.info(f"Fetching feed: {feed['name']}")
        entries = fetch_feed(feed)
        all_entries.extend(entries)
    logging.info(f"Fetched {len(all_entries)} total entries.")

    # Deduplicate by URL
    seen_urls = set()
    deduped_entries = []
    for entry in all_entries:
        if entry['link'] not in seen_urls:
            deduped_entries.append(entry)
            seen_urls.add(entry['link'])
    logging.info(f"Entries after URL deduplication: {len(deduped_entries)}")

    # Deduplicate by high text similarity (>80% overlap)
    final_entries = []
    for entry in deduped_entries:
        is_duplicate = False
        for kept in final_entries:
            if fuzz.token_set_ratio(entry['description'], kept['description']) > 80:
                is_duplicate = True
                break
        if not is_duplicate:
            final_entries.append(entry)
    logging.info(f"Entries after text similarity deduplication: {len(final_entries)}")

    # Rank and select top news
    now = datetime.now(tz=tz.UTC)
    last_24h = []
    for entry in final_entries:
        pub_date = entry['pub_date']
        if pub_date:
            # Make pub_date timezone-aware (UTC) if naive
            if pub_date.tzinfo is None or pub_date.tzinfo.utcoffset(pub_date) is None:
                pub_date = pub_date.replace(tzinfo=tz.UTC)
            if (now - pub_date).total_seconds() <= 86400:
                entry['pub_date'] = pub_date  # update in entry for consistency
                last_24h.append(entry)
    logging.info(f"Entries from last 24 hours: {len(last_24h)}")

    # Sort by recency (pub_date desc), then by description word count (desc)
    ranked = sorted(
        last_24h,
        key=lambda e: (e['pub_date'], len(e['description'].split())),
        reverse=True
    )
    top_entries = ranked[:50]
    logging.info(f"Selected top {len(top_entries)} entries.")

    # Output formatting
    if output_format == 'json':
        def serialize(entry):
            return {**entry, 'pub_date': entry['pub_date'].isoformat() if entry['pub_date'] else None}
        print(json.dumps([serialize(e) for e in top_entries], indent=2, ensure_ascii=False))
    elif output_format == 'yaml':
        def serialize(entry):
            return {**entry, 'pub_date': entry['pub_date'].isoformat() if entry['pub_date'] else None}
        print(yaml.dump([serialize(e) for e in top_entries], allow_unicode=True, sort_keys=False))
    else:  # plaintext
        for entry in top_entries:
            print(f"[{entry['source']}] {entry['title']}\n{entry['link']}\n{entry['pub_date']}\n{entry['description'][:200]}...\n")

if __name__ == '__main__':
    main() 