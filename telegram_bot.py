import os
from dotenv import load_dotenv
load_dotenv()
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from fashion_news import load_feeds, fetch_feed
from datetime import datetime
from dateutil import tz
from fuzzywuzzy import fuzz
import re
import openai

def get_top_news(max_items=50):
    feeds = load_feeds()
    all_entries = []
    for feed in feeds:
        entries = fetch_feed(feed)
        # Deduplicate by URL within this feed
        seen_urls = set()
        deduped_entries = []
        for entry in entries:
            if entry['link'] not in seen_urls:
                deduped_entries.append(entry)
                seen_urls.add(entry['link'])
        # Deduplicate by text similarity within this feed
        final_entries = []
        for entry in deduped_entries:
            is_duplicate = False
            for kept in final_entries:
                if fuzz.token_set_ratio(entry['description'], kept['description']) > 80:
                    is_duplicate = True
                    break
            if not is_duplicate:
                final_entries.append(entry)
        # Filter last 24h within this feed
        now = datetime.now(tz=tz.UTC)
        last_24h = []
        for entry in final_entries:
            pub_date = entry['pub_date']
            if pub_date:
                if pub_date.tzinfo is None or pub_date.tzinfo.utcoffset(pub_date) is None:
                    pub_date = pub_date.replace(tzinfo=tz.UTC)
                if (now - pub_date).total_seconds() <= 86400:
                    entry['pub_date'] = pub_date
                    last_24h.append(entry)
        # Sort and select top 5 for this feed
        ranked = sorted(
            last_24h,
            key=lambda e: (e['pub_date'], len(e['description'].split())),
            reverse=True
        )
        all_entries.extend(ranked[:5])
    # Now deduplicate and rank globally
    seen_urls = set()
    deduped_entries = []
    for entry in all_entries:
        if entry['link'] not in seen_urls:
            deduped_entries.append(entry)
            seen_urls.add(entry['link'])
    final_entries = []
    for entry in deduped_entries:
        is_duplicate = False
        for kept in final_entries:
            if fuzz.token_set_ratio(entry['description'], kept['description']) > 80:
                is_duplicate = True
                break
        if not is_duplicate:
            final_entries.append(entry)
    # Sort and select top max_items globally
    ranked = sorted(
        final_entries,
        key=lambda e: (e['pub_date'], len(e['description'].split())),
        reverse=True
    )
    top_entries = ranked[:max_items]
    return top_entries

def escape_markdown(text):
    escape_chars = r'_ * [ ] ( ) ~ ` > # + - = | { } . !'
    for c in escape_chars.split():
        text = text.replace(c, '\\' + c)
    return text

def escape_markdown_url(url):
    # Only escape ')' in the URL, as per Telegram's docs
    return url.replace(')', '\)')

def format_news_item(entry):
    title = escape_markdown(entry['title'])
    link = entry['link']  # Do NOT escape the URL
    # Only show emoji and clickable title, no source, no description
    link_text = f'🔹 {title}'
    msg = f'[{link_text}]({link})'
    return msg

def get_openai_selected_titles(entries):
    openai.api_key = os.getenv('OPENAI_API_KEY')
    titles = [entry['title'] for entry in entries]
    prompt = (
        "Act as a fashion enthusiast. Read all the titles and return from 5 to 7 the most interesting news that tell about people, or new trends or new collections. Include one item (but not more than one) about Anna Vintour if there's something about her. Avoide news about sales."
        "Return only the exact titles, one per line, no extra text."
    )
    joined_titles = '\n'.join(titles)
    full_prompt = f"{prompt}\n\nTITLES:\n{joined_titles}"
    response = openai.ChatCompletion.create(
        model="gpt-4.1-mini-2025-04-14",
        messages=[{"role": "user", "content": full_prompt}],
        max_tokens=512,
        temperature=0.2,
    )
    result = response.choices[0].message['content']
    selected_titles = [line.strip() for line in result.split('\n') if line.strip()]
    return selected_titles

async def topnews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("Fetching top fashion news")
        entries = get_top_news()
        if not entries:
            await update.message.reply_text("No news found in the last 24 hours.")
            return
        # Get selected titles from OpenAI
        selected_titles = get_openai_selected_titles(entries)
        # Map selected titles back to entries
        selected_entries = [entry for entry in entries if entry['title'] in selected_titles]
        # Format and send as one message
        messages = [format_news_item(entry) for entry in selected_entries]
        full_text = '\n\n'.join(messages)
        max_len = 4096
        for i in range(0, len(full_text), max_len):
            await update.message.reply_text(full_text[i:i+max_len], parse_mode='MarkdownV2', disable_web_page_preview=False)
    except Exception as e:
        logging.error(f"Error in /topnews: {e}")
        await update.message.reply_text(f"An error occurred while fetching news: {e}")

async def send_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        channel_id = os.getenv('CHANNEL_ID')
        if not channel_id:
            await update.message.reply_text("Channel ID not configured. Please set CHANNEL_ID environment variable.")
            return
        await update.message.reply_text("Sending news to channel...")
        entries = get_top_news()
        if not entries:
            await context.bot.send_message(chat_id=channel_id, text="No news found in the last 24 hours.")
            return
        # Get selected titles from OpenAI
        selected_titles = get_openai_selected_titles(entries)
        # Map selected titles back to entries
        selected_entries = [entry for entry in entries if entry['title'] in selected_titles]
        # Format and send as one message
        messages = [format_news_item(entry) for entry in selected_entries]
        full_text = '\n\n'.join(messages)
        max_len = 4096
        for i in range(0, len(full_text), max_len):
            await context.bot.send_message(
                chat_id=channel_id,
                text=full_text[i:i+max_len],
                parse_mode='MarkdownV2',
                disable_web_page_preview=False
            )
        await update.message.reply_text("News sent to channel successfully!")
    except Exception as e:
        logging.error(f"Error in /send_to_channel: {e}")
        await update.message.reply_text(f"An error occurred while sending to channel: {e}")

def main():
    logging.basicConfig(level=logging.INFO)
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("Please set your Telegram bot token in the TELEGRAM_BOT_TOKEN environment variable.")
        return
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("topnews", topnews))
    app.add_handler(CommandHandler("send_to_channel", send_to_channel))
    print("Bot is running. Send /topnews to get the latest fashion news or /send_to_channel to send to channel.")
    app.run_polling()

if __name__ == "__main__":
    main() 