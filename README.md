# Fashion News Aggregator CLI

A command-line tool to aggregate, deduplicate, and rank top fashion news from multiple RSS feeds.

## Features
- Ingests a configurable list of fashion news RSS feeds
- Deduplicates news by URL and text similarity
- Ranks by recency and article depth
- Outputs in JSON, YAML, or plaintext
- Robust error handling and logging

## Setup
1. Clone the repository
2. Install dependencies:
   ```
   pip3 install -r requirements.txt
   ```

## Configuration
Edit `feeds.yaml` to add or remove RSS sources. Example:
```yaml
feeds:
  - name: ELLE (Fashion)
    url: https://www.elle.com/rss/fashion.xml
  # ... more feeds ...
```

## Usage
Run the CLI to fetch and display top news:
```sh
python3 fashion_news.py --output-format json
```

### Options
- `--config`: Path to feeds YAML config (default: feeds.yaml)
- `--output-format`: Output format: `json`, `yaml`, or `plaintext` (default: `json`)

## Output
- Up to 50 top articles from the last 24 hours, ranked by recency and article length.

## Testing
Run tests with:
```sh
pytest
``` 