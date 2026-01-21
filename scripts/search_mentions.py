""" Instagram Mention Scraper using Apify
Detects all posts/reels where @feedo3app is mentioned/tagged
"""

import os
import time
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
APIFY_API_TOKEN = os.getenv('APIFY_API_TOKEN')
TARGET_USERNAME = 'feedo3app'  # Username to search for mentions

def search_instagram_mentions(username, max_results=50):
    """
    Search for mentions of a username on Instagram using Apify
    """
    print(f"🔍 Searching for mentions of @{username} on Instagram...")
    print("=" * 80)
    
    # Using Instagram Hashtag Scraper to search for username mentions
    # This will search posts that mention the username
    url = "https://api.apify.com/v2/acts/apify~instagram-hashtag-scraper/runs"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    # Input for Apify actor
    # We'll search for the username as a hashtag/mention
    payload = {
        "hashtags": [username],
        "resultsLimit": max_results,
        "resultsType": "posts",
        "searchType": "hashtag",
        "searchLimit": max_results
    }
    
    params = {
        'token': APIFY_API_TOKEN
    }
    
    try:
        # Start the scraper run
        print(f"📤 Starting Apify Instagram Hashtag Scraper...")
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        run_data = response.json()
        
        run_id = run_data['data']['id']
        dataset_id = run_data['data']['defaultDatasetId']
        print(f"✅ Scraper started")
        print(f"   Run ID: {run_id}")
        print(f"   Dataset ID: {dataset_id}")
        
        # Wait for the run to complete
        print(f"\n⏳ Waiting for scraper to complete...")
        run_status_url = f"https://api.apify.com/v2/acts/apify~instagram-hashtag-scraper/runs/{run_id}"
        
        max_wait = 180  # Maximum 3 minutes wait
        wait_time = 0
        
        while wait_time < max_wait:
            time.sleep(10)
            wait_time += 10
            
            status_response = requests.get(run_status_url, params=params)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            status = status_data['data']['status']
            print(f"   Status: {status} (waited {wait_time}s)")
            
            if status in ['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']:
                break
        
        if status != 'SUCCEEDED':
            print(f"\n❌ Scraper ended with status: {status}")
            return []
        
        # Get the results from dataset
        print(f"\n📥 Fetching scraped data...")
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        result_response = requests.get(dataset_url, params=params)
        result_response.raise_for_status()
        results = result_response.json()
        
        print(f"✅ Found {len(results)} posts/mentions")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return []

def search_mentions_alternative(username, max_results=20):
    """
    Alternative method: Search for posts using Instagram Post Scraper
    """
    print(f"\n🔍 Alternative Search: Using Instagram Post URL Scraper...")
    print("=" * 80)
    
    # We can also try searching specific posts if we have URLs
    # Or use the Instagram Search Scraper
    url = "https://api.apify.com/v2/acts/apify~instagram-scraper/runs"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    payload = {
        "directUrls": [],
        "resultsType": "posts",
        "resultsLimit": max_results,
        "searchType": "user",
        "searchLimit": 1
    }
    
    params = {
        'token': APIFY_API_TOKEN
    }
    
    try:
        print(f"📤 Starting Instagram Scraper...")
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        run_data = response.json()
        
        run_id = run_data['data']['id']
        dataset_id = run_data['data']['defaultDatasetId']
        
        print(f"✅ Scraper started - Run ID: {run_id}")
        
        # Wait for completion
        print(f"\n⏳ Waiting for scraper to complete...")
        run_status_url = f"https://api.apify.com/v2/acts/apify~instagram-scraper/runs/{run_id}"
        
        max_wait = 180
        wait_time = 0
        
        while wait_time < max_wait:
            time.sleep(10)
            wait_time += 10
            
            status_response = requests.get(run_status_url, params=params)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            status = status_data['data']['status']
            print(f"   Status: {status} (waited {wait_time}s)")
            
            if status in ['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']:
                break
        
        if status != 'SUCCEEDED':
            print(f"\n❌ Scraper ended with status: {status}")
            return []
        
        # Get results
        print(f"\n📥 Fetching scraped data...")
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        result_response = requests.get(dataset_url, params=params)
        result_response.raise_for_status()
        results = result_response.json()
        
        print(f"✅ Found {len(results)} posts")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return []

def display_mentions(results, target_username):
    """
    Display all mentions found in a formatted way
    """
    if not results or len(results) == 0:
        print(f"\n❌ No mentions found for @{target_username}")
        return
    
    print(f"\n{'='*80}")
    print(f"📊 MENTIONS OF @{target_username}")
    print(f"{'='*80}")
    print(f"Total mentions found: {len(results)}\n")
    
    for idx, post in enumerate(results, 1):
        print(f"\n{'─'*80}")
        print(f"🔹 MENTION #{idx}")
        print(f"{'─'*80}")
        
        # Extract relevant data
        post_url = post.get('url', post.get('shortCode', 'N/A'))
        if post_url != 'N/A' and not post_url.startswith('http'):
            post_url = f"https://www.instagram.com/p/{post_url}/"
        
        owner_username = post.get('ownerUsername', post.get('username', 'Unknown'))
        caption = post.get('caption', post.get('text', 'No caption'))
        likes = post.get('likesCount', 0)
        comments_count = post.get('commentsCount', 0)
        timestamp = post.get('timestamp', 'Unknown')
        post_type = post.get('type', 'Unknown')
        
        print(f"📍 Post URL: {post_url}")
        print(f"👤 Posted by: @{owner_username}")
        print(f"📝 Caption: {caption[:200]}{'...' if len(str(caption)) > 200 else ''}")
        print(f"❤️  Likes: {likes}")
        print(f"💬 Comments: {comments_count}")
        print(f"📅 Posted: {timestamp}")
        print(f"🎬 Type: {post_type}")
        
        # Check if caption contains deploy command
        if caption and '@' + target_username in str(caption).lower():
            if 'deploy' in str(caption).lower():
                print(f"\n🚀 DEPLOY COMMAND DETECTED!")
                
                # Try to parse the command
                import re
                pattern = rf'@{target_username}\s+(?:deploy|launch)?\s*(\w+)\s+\$(\w+)'
                match = re.search(pattern, str(caption), re.IGNORECASE)
                
                if match:
                    token_name = match.group(1)
                    ticker = match.group(2).upper()
                    print(f"   Token Name: {token_name}")
                    print(f"   Ticker: ${ticker}")
        
        # Display comments if available
        if 'latestComments' in post and post['latestComments']:
            print(f"\n💬 Recent Comments:")
            for comment in post['latestComments'][:3]:
                comment_text = comment.get('text', '')
                comment_owner = comment.get('ownerUsername', 'Unknown')
                print(f"   @{comment_owner}: {comment_text[:100]}")
                
                # Check if comment has mention
                if '@' + target_username in comment_text.lower() and 'deploy' in comment_text.lower():
                    print(f"   ⚠️  DEPLOY COMMAND IN COMMENT!")
    
    print(f"\n{'='*80}")
    print(f"✅ Total: {len(results)} posts/mentions displayed")
    print(f"{'='*80}")

def main():
    """
    Main function
    """
    print("🤖 Instagram Mention Detector - Apify Edition")
    print("=" * 80)
    print(f"Target: @{TARGET_USERNAME}")
    print(f"API: Apify Instagram Scraper")
    print("=" * 80)
    
    # Method 1: Search using hashtag scraper
    print(f"\n📍 METHOD 1: Hashtag Search")
    results = search_instagram_mentions(TARGET_USERNAME, max_results=50)
    
    if results and len(results) > 0:
        display_mentions(results, TARGET_USERNAME)
    else:
        print(f"\n⚠️  No results from hashtag search")
        print(f"\n📍 Trying alternative method...")
        
        # Method 2: Alternative scraper
        results = search_mentions_alternative(TARGET_USERNAME, max_results=20)
        
        if results and len(results) > 0:
            display_mentions(results, TARGET_USERNAME)
        else:
            print(f"\n❌ No mentions found with any method")
            print(f"\n💡 Note: Instagram heavily restricts mention/tag scraping")
            print(f"   Consider these alternatives:")
            print(f"   1. Use Instagram Graph API for your own posts only")
            print(f"   2. Ask users to comment on @{TARGET_USERNAME}'s posts")
            print(f"   3. Use a hashtag like #feedo3deploy instead of mentions")

if __name__ == "__main__":
    main()
