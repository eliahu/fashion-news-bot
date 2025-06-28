# Project Plan: Fashion News Aggregator

## 1. Project Setup
- [x] Choose Python as the stack (for strong RSS, text, and CLI support).
- [x] Initialize the project structure and requirements file.

## 2. Configuration
- [x] Create a config file (feeds.json or feeds.yaml) listing all RSS feed URLs.
- [x] Allow for easy modification of feed sources.

## 3. RSS Fetching & Parsing
- [x] Implement logic to fetch and parse each RSS feed.
- [x] Extract: Title, Link, Publication Date, Short Description/Body.
- [x] Handle network and parsing errors with logging.

## 4. Deduplication
- [x] Deduplicate entries by URL.
- [x] Deduplicate by high text similarity (>80% overlap) using a text similarity metric (e.g., fuzzywuzzy, difflib, or similar).

## 5. Ranking & Selection
- [x] Filter articles from the last 24 hours.
- [x] Select the top 50 articles.

## 6. Output
- [x] Output results in a configurable format (e.g., JSON, YAML, or plain text).
- [x] Allow user to specify output format via CLI argument or config.

## 7. Error Handling & Logging
- [x] Add robust error handling for network, parsing, and config errors.
- [x] Implement logging for all major steps and errors.

## 8. CLI/Serverless Interface
- [x] Implement a simple CLI interface (or serverless handler if preferred).
- [x] Allow user to trigger aggregation and specify output options.

## 9. Testing & Documentation
- [x] Add basic tests for core logic (fetching, deduplication, ranking).
- [x] Document usage and configuration in a README.

## 10. Telegram Bot Interface
- [ ] Install python-telegram-bot package
- [ ] Set up bot token and configuration
- [ ] Implement Telegram command to fetch and send top news
- [ ] Handle output formatting for Telegram (plaintext or compact)
- [ ] Deploy or run the bot
- [ ] Update documentation for Telegram bot usage 