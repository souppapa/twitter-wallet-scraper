import asyncio
from playwright.async_api import async_playwright
import re
import json
import time
import aiofiles
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Twitter credentials from environment variables
TWITTER_USERNAME = os.getenv('TWITTER_USERNAME')
TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD')

if not TWITTER_USERNAME or not TWITTER_PASSWORD:
    print("Error: Twitter credentials not found in environment variables")
    print("Please create a .env file with TWITTER_USERNAME and TWITTER_PASSWORD")
    exit(1)

# Function to log into Twitter
async def login_to_twitter(page):
    print("Starting login process...")
    await page.goto('https://twitter.com/i/flow/login')  # Open login page
    await page.wait_for_selector('input[autocomplete="username"]', timeout=60000)
    await page.fill('input[autocomplete="username"]', TWITTER_USERNAME)  # Fill username
    await page.click('span:has-text("Next")')  # Click 'Next'
    await page.wait_for_selector('input[name="password"]', timeout=60000)
    await page.fill('input[name="password"]', TWITTER_PASSWORD)  # Fill password
    await page.click('span:has-text("Log in")')  # Click 'Log in'
    print("Waiting for login to complete...")
    await page.wait_for_selector('article[data-testid="tweet"]', timeout=60000)  # Wait for tweets to load
    print("Login successful!")

# Function to save extracted data to a JSON file
async def save_to_json(data, filename="wallets.json"):
    async with aiofiles.open(filename, "w") as f:
        await f.write(json.dumps(data, indent=4))

# Main function to scrape tweet replies
async def scrape_tweet_replies(tweet_url):
    processed_tweets = set()  # Tracks already-processed tweets to avoid duplicates
    extracted_data = []  # Stores valid wallet data

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        try:
            # Log into Twitter
            await login_to_twitter(page)
            print(f"Navigating to {tweet_url}")
            await page.goto(tweet_url, wait_until='load', timeout=30000)
            await asyncio.sleep(5)

            print("Loading replies...")
            last_height = 0
            scroll_count = 0
            max_scrolls = 250  # Maximum number of scrolls to fetch replies
            no_new_content_count = 0  # Track consecutive scrolls without new content

            while scroll_count < max_scrolls:
                # Fetch all tweets currently loaded on the page
                tweets = await page.locator('article[data-testid="tweet"]').all()
                print(f"Found {len(tweets)} tweets on scroll {scroll_count + 1}")
                new_tweets = 0

                for tweet in tweets:
                    try:
                        # Extract the tweet's text
                        tweet_text = await tweet.text_content()
                        tweet_id = hash(tweet_text)  # Generate a unique ID for deduplication

                        # Skip already-processed tweets
                        if tweet_id in processed_tweets:
                            continue
                        processed_tweets.add(tweet_id)  # Mark tweet as processed
                        new_tweets += 1

                        print(f"\nAnalyzing new tweet: {tweet_text[:200]}...")  # Debugging: Show first 200 characters

                        # Find wallets (43–44 characters, base58 encoding rules for Solana)
                        wallets = re.findall(r'[1-9A-HJ-NP-Za-km-z]{43,44}', tweet_text)
                        if wallets:
                            print(f"✓ Found wallets: {wallets}")
                        else:
                            print("✗ No valid wallet found")

                        # Check for your search term
                        hashtag = re.search(r'#\s*(YOUR SEARCH TERM)', tweet_text, re.IGNORECASE)
                        if hashtag:
                            print(f"✓ Found hashtag: {hashtag.group()}")
                        else:
                            print("✗ ")

                        # If both wallet and hashtag are present, extract and save data
                        if wallets and hashtag:
                            try:
                                # Extract username associated with the tweet
                                username = await tweet.locator("[data-testid='User-Name']").text_content()
                                for wallet in wallets:
                                    if len(wallet) in [43, 44]:  # Validate wallet length
                                        data = {
                                            "username": username.strip(),
                                            "wallet": wallet,
                                            "tweet_url": tweet_url,
                                            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                                        }
                                        extracted_data.append(data)  # Append valid data
                                        print(f"✅ Added wallet from {username.strip()}: {wallet}")
                            except Exception as e:
                                print(f"Error getting username: {e}")
                        else:
                            print("✗ Missing wallet or hashtag - skipping")

                    except Exception as e:
                        print(f"Error processing tweet: {e}")

                print(f"Processed {new_tweets} new tweets on this scroll.")

                # Save progress
                if new_tweets > 0 and extracted_data:
                    await save_to_json(extracted_data)
                    print(f"💾 Saved {len(extracted_data)} wallets to wallets.json")

                # Improved scrolling logic
                try:
                    # Scroll in smaller increments
                    for _ in range(3):
                        await page.evaluate("window.scrollBy(0, 500)")
                        await asyncio.sleep(1)
                    
                    # Final scroll to the bottom
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2)

                    # Check if we've reached the bottom
                    new_height = await page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        no_new_content_count += 1
                        print(f"No new content found ({no_new_content_count}/3)")
                        if no_new_content_count >= 3:  # Try 3 times before giving up
                            print("Reached the end of tweets after multiple attempts.")
                            break
                    else:
                        no_new_content_count = 0  # Reset counter if we got new content
                        
                    last_height = new_height
                    scroll_count += 1

                except Exception as e:
                    print(f"Scroll error: {e}")
                    await asyncio.sleep(2)  # Wait and try again
                    continue

            print(f"Scraping complete. Total wallets found: {len(extracted_data)}")
            await save_to_json(extracted_data)  # Final save
            await asyncio.sleep(5)  # Pause for inspection

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    print("Enter tweet URL: ")
    tweet_url = input().strip()
    asyncio.run(scrape_tweet_replies(tweet_url))




