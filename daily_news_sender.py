#!/usr/bin/env python3
"""
Standalone script to send daily fashion news to Telegram channel.
This script can be run by GitHub Actions or manually.
"""

import os
import logging
import asyncio
from telegram import Bot
from telegram_bot import get_top_news, get_openai_selected_titles, format_news_item

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

async def send_daily_news():
    """Send daily fashion news to Telegram channel."""
    try:
        # Get environment variables
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        channel_id = os.getenv('CHANNEL_ID')
        
        if not token:
            logging.error("TELEGRAM_BOT_TOKEN not set")
            return
        if not channel_id:
            logging.error("CHANNEL_ID not set")
            return
            
        # Initialize bot
        bot = Bot(token=token)
        
        # Get news
        logging.info("Fetching news...")
        entries = get_top_news()
        
        if not entries:
            logging.info("No news found in the last 24 hours.")
            await bot.send_message(chat_id=channel_id, text="No news found in the last 24 hours.")
            return
            
        # Get selected titles from OpenAI
        logging.info("Getting AI-selected titles...")
        selected_titles = get_openai_selected_titles(entries)
        
        # Map selected titles back to entries
        selected_entries = [entry for entry in entries if entry['title'] in selected_titles]
        
        if not selected_entries:
            logging.warning("No entries matched selected titles")
            await bot.send_message(chat_id=channel_id, text="No news selected for today.")
            return
            
        # Format and send as one message
        logging.info(f"Sending {len(selected_entries)} news items to channel...")
        messages = [format_news_item(entry) for entry in selected_entries]
        full_text = '\n\n'.join(messages)
        
        # Split if message is too long
        max_len = 4096
        for i in range(0, len(full_text), max_len):
            await bot.send_message(
                chat_id=channel_id,
                text=full_text[i:i+max_len],
                parse_mode='MarkdownV2',
                disable_web_page_preview=False
            )
            
        logging.info("Daily news sent successfully!")
        
    except Exception as e:
        logging.error(f"Error sending daily news: {e}")
        # Try to send error message to channel if possible
        try:
            await bot.send_message(
                chat_id=channel_id,
                text=f"Error sending daily news: {str(e)[:100]}..."
            )
        except:
            pass

def main():
    """Main function to run the async task."""
    asyncio.run(send_daily_news())

if __name__ == "__main__":
    main() 