"""
Instagram Mention/Tag Monitor using Apify
Monitors posts where @feedo3app is tagged/mentioned
"""

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
TARGET_USERNAME = 'feedo3app'

def monitor_tagged_posts(username):
    """
    Monitor posts where the username is tagged using Instagram Comment Scraper
    This will search for comments/captions that mention @username
    """
    print(f"🔍 Monitoring Instagram for @{username} tags and mentions...")
    print("=" * 80)
    
    # Use Instagram Comment Scraper to find mentions in comments
    url = "https://api.apify.com/v2/acts/apify~instagram-comment-scraper/runs"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    # We'll scrape popular/recent posts and search for our username in comments
    # You can add specific post URLs here if you know where people might tag you
    payload = {
        "directUrls": [
            # Add Instagram post URLs here where you expect mentions
            # For now, we'll leave empty and use search
        ],
        "resultsLimit": 100,
        "searchText": f"@{username}"
    }
    
    params = {
        'token': APIFY_API_TOKEN
    }
    
    try:
        print(f"📤 Starting Apify Comment Scraper...")
        print(f"   Searching for: @{username}")
        
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        run_data = response.json()
        
        run_id = run_data['data']['id']
        dataset_id = run_data['data']['defaultDatasetId']
        
        print(f"✅ Scraper started")
        print(f"   Run ID: {run_id}")
        
        # Monitor the run
        print(f"\n⏳ Waiting for scraper to complete...")
        run_status_url = f"https://api.apify.com/v2/acts/apify~instagram-comment-scraper/runs/{run_id}"
        
        max_wait = 120
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
        print(f"\n📥 Fetching mentions...")
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        result_response = requests.get(dataset_url, params=params)
        result_response.raise_for_status()
        results = result_response.json()
        
        print(f"✅ Found {len(results)} comments/mentions")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text[:500]}")
        return []

def simple_search_by_url(post_urls):
    """
    Simpler approach: Give specific post URLs to scrape
    """
    print(f"\n🔍 Scraping specific Instagram posts for mentions...")
    print("=" * 80)
    
    url = "https://api.apify.com/v2/acts/apify~instagram-post-scraper/runs"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    payload = {
        "directUrls": post_urls,
        "resultsType": "details",
        "includeHasStories": False
    }
    
    params = {
        'token': APIFY_API_TOKEN
    }
    
    try:
        print(f"📤 Starting Instagram Post Scraper...")
        print(f"   Scraping {len(post_urls)} post(s)")
        
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        run_data = response.json()
        
        run_id = run_data['data']['id']
        dataset_id = run_data['data']['defaultDatasetId']
        
        print(f"✅ Scraper started - Run ID: {run_id}")
        
        # Wait for completion
        print(f"\n⏳ Waiting for scraper...")
        run_status_url = f"https://api.apify.com/v2/acts/apify~instagram-post-scraper/runs/{run_id}"
        
        max_wait = 120
        wait_time = 0
        
        while wait_time < max_wait:
            time.sleep(8)
            wait_time += 8
            
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
        print(f"\n📥 Fetching post data...")
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        result_response = requests.get(dataset_url, params=params)
        result_response.raise_for_status()
        results = result_response.json()
        
        print(f"✅ Scraped {len(results)} post(s)")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return []

def display_results(results, target_username):
    """
    Display all mentions found
    """
    if not results or len(results) == 0:
        print(f"\n❌ No data found")
        return
    
    print(f"\n{'='*80}")
    print(f"📊 RESULTS FOR @{target_username}")
    print(f"{'='*80}")
    
    mentions_found = 0
    
    for idx, item in enumerate(results, 1):
        print(f"\n{'─'*80}")
        print(f"🔹 RESULT #{idx}")
        print(f"{'─'*80}")
        
        # Handle different result types
        if 'url' in item:
            print(f"📍 Post URL: {item['url']}")
        if 'shortCode' in item:
            print(f"📍 Post: https://www.instagram.com/p/{item['shortCode']}/")
        
        if 'ownerUsername' in item:
            print(f"👤 Owner: @{item['ownerUsername']}")
        
        if 'caption' in item:
            caption = item['caption']
            print(f"📝 Caption: {caption[:300]}{'...' if len(str(caption)) > 300 else ''}")
            
            # Check for mention
            if f'@{target_username}' in str(caption).lower():
                mentions_found += 1
                print(f"\n✅ MENTION FOUND in caption!")
                
                # Check for deploy command
                if 'deploy' in str(caption).lower():
                    print(f"🚀 DEPLOY COMMAND DETECTED!")
                    
                    import re
                    pattern = rf'@{target_username}\s+(?:deploy|launch)?\s*(\w+)\s+\$(\w+)'
                    match = re.search(pattern, str(caption), re.IGNORECASE)
                    
                    if match:
                        print(f"   Token Name: {match.group(1)}")
                        print(f"   Ticker: ${match.group(2).upper()}")
        
        if 'text' in item:  # For comments
            text = item['text']
            print(f"💬 Comment: {text}")
            
            if f'@{target_username}' in str(text).lower():
                mentions_found += 1
                print(f"✅ MENTION FOUND in comment!")
                
                if 'deploy' in str(text).lower():
                    print(f"🚀 DEPLOY COMMAND IN COMMENT!")
        
        if 'commentsCount' in item:
            print(f"💬 Comments: {item['commentsCount']}")
        
        if 'likesCount' in item:
            print(f"❤️  Likes: {item['likesCount']}")
        
        if 'timestamp' in item:
            print(f"📅 Posted: {item['timestamp']}")
        
        # Show recent comments if available
        if 'latestComments' in item and item['latestComments']:
            print(f"\n💬 Recent Comments ({len(item['latestComments'])}):")
            for comment in item['latestComments'][:5]:
                comment_text = comment.get('text', '')
                comment_owner = comment.get('ownerUsername', 'Unknown')
                print(f"   @{comment_owner}: {comment_text[:100]}")
                
                if f'@{target_username}' in comment_text.lower():
                    mentions_found += 1
                    print(f"   ✅ MENTION FOUND!")
                    if 'deploy' in comment_text.lower():
                        print(f"   🚀 DEPLOY COMMAND!")
    
    print(f"\n{'='*80}")
    print(f"✅ Total mentions found: {mentions_found}")
    print(f"✅ Total items processed: {len(results)}")
    print(f"{'='*80}")

def main():
    """
    Main function with multiple approaches
    """
    print("🤖 Instagram Tag & Mention Monitor")
    print("=" * 80)
    print(f"Target: @{TARGET_USERNAME}")
    print("=" * 80)
    
    print(f"\n💡 Choose scraping method:")
    print(f"1. Search comments (requires post URLs)")
    print(f"2. Scrape specific posts")
    print(f"3. Monitor @{TARGET_USERNAME}'s own posts (recommended)")
    
    # For demonstration, let's scrape a specific post if available
    # You can add Instagram post URLs here
    specific_posts = [
        # "https://www.instagram.com/p/DTvLMMPEznL/",  # Your test post
        # Add more post URLs where people might mention you
    ]
    
    if len(specific_posts) > 0:
        print(f"\n📍 Scraping {len(specific_posts)} specific post(s)...")
        results = simple_search_by_url(specific_posts)
        display_results(results, TARGET_USERNAME)
    else:
        print(f"\n⚠️  No specific post URLs provided")
        print(f"\n💡 To find mentions:")
        print(f"   1. Add Instagram post URLs to the 'specific_posts' list")
        print(f"   2. Or use the Graph API to monitor @{TARGET_USERNAME}'s own posts")
        print(f"   3. Apify cannot automatically find all mentions across Instagram")
        print(f"      (This requires knowing which posts to check)")

if __name__ == "__main__":
    main()
