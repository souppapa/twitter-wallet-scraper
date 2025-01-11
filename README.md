# Headed Twitter Wallet Scraper 

Twitter scraper that extracts SOL wallet addresses from tweet replies.

## Features

- Asynchronous scraping with Playwright
- Auto-login to Twitter
- Extracts wallet addresses (43-44 characters)
- Deduplicates tweets
- Saves results to JSON

## Setup

1. Install dependencies: 

pip install -r requirements.txt

2. Create a .env file in the project root:

```env
TWITTER_USERNAME="your_username"
TWITTER_PASSWORD="your_password"
```

Make sure to add your actual Twitter credentials in the .env file.

## Usage

Run:

python tweet_scraper.py


Enter tweet URL when prompted. Results save to wallets.json.

## Output Format

json
{
"username": "twitter_user",
"wallet": "wallet_address",
"tweet_url": "original_tweet_url",
"timestamp": "YYYY-MM-DD HH:MM:SS"
}

⚠️ Never commit your Twitter credentials!!!
