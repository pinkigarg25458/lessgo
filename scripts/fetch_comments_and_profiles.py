"""
Instagram Comment Fetcher with Profile Picture Scraper
Continuously fetches new comments and scrapes commenter's profile pictures using Apify
"""

import os
import time
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
APIFY_API_TOKEN = os.getenv('APIFY_API_TOKEN')
POLLING_INTERVAL = 60  # seconds

# Store processed comments to avoid duplicates
processed_comments = set()

def fetch_recent_media():
    """Fetch recent media posts from Instagram Business Account"""
    url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
    params = {
        'fields': 'id,caption,media_type,media_url,timestamp,permalink',
        'access_token': INSTAGRAM_ACCESS_TOKEN,
        'limit': 10
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    except Exception as e:
        print(f"❌ Error fetching media: {e}")
        return []

def fetch_comments_for_media(media_id):
    """Fetch comments for a specific media post"""
    url = f"https://graph.facebook.com/v18.0/{media_id}/comments"
    params = {
        'fields': 'id,text,username,timestamp,from',
        'access_token': INSTAGRAM_ACCESS_TOKEN
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    except Exception as e:
        print(f"❌ Error fetching comments: {e}")
        return []

def scrape_profile_picture(username):
    """Scrape Instagram profile picture using Apify API"""
    print(f"\n🔍 Scraping profile picture for @{username}...")
    
    # Apify API endpoint for Instagram Profile Scraper
    url = f"https://api.apify.com/v2/acts/apify~instagram-profile-scraper/runs"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    # Input for Apify actor
    payload = {
        'usernames': [username],
        'resultsLimit': 1
    }
    
    params = {
        'token': APIFY_API_TOKEN
    }
    
    try:
        # Start the scraper run
        print(f"📤 Starting Apify scraper for @{username}...")
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        run_data = response.json()
        
        run_id = run_data['data']['id']
        dataset_id = run_data['data']['defaultDatasetId']
        print(f"✅ Scraper started - Run ID: {run_id}")
        
        # Wait for the run to complete
        print("⏳ Waiting for scraper to complete...")
        run_status_url = f"https://api.apify.com/v2/acts/apify~instagram-profile-scraper/runs/{run_id}"
        
        max_wait = 60  # Maximum 60 seconds wait
        wait_time = 0
        
        while wait_time < max_wait:
            time.sleep(5)
            wait_time += 5
            
            status_response = requests.get(run_status_url, params=params)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            status = status_data['data']['status']
            print(f"  Status: {status} (waited {wait_time}s)")
            
            if status in ['SUCCEEDED', 'FAILED', 'ABORTED']:
                break
        
        if status != 'SUCCEEDED':
            print(f"❌ Scraper failed with status: {status}")
            return None
        
        # Get the results from dataset
        print("📥 Fetching scraped data...")
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        result_response = requests.get(dataset_url, params=params)
        result_response.raise_for_status()
        results = result_response.json()
        
        if results and len(results) > 0:
            profile_data = results[0]
            profile_pic_url = profile_data.get('profilePicUrl', profile_data.get('profilePicUrlHD', ''))
            
            print(f"✅ Profile picture found for @{username}")
            print(f"   URL: {profile_pic_url}")
            
            return {
                'username': username,
                'profile_pic_url': profile_pic_url,
                'full_name': profile_data.get('fullName', ''),
                'followers': profile_data.get('followersCount', 0),
                'bio': profile_data.get('biography', '')
            }
        else:
            print(f"❌ No profile data found for @{username}")
            return None
            
    except Exception as e:
        print(f"❌ Error scraping profile: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None

def process_comment(comment, media_permalink):
    """Process a single comment and scrape profile if needed"""
    comment_id = comment['id']
    comment_text = comment['text']
    username = comment['username']
    timestamp = comment['timestamp']
    
    # Skip if already processed
    if comment_id in processed_comments:
        return
    
    print(f"\n{'='*60}")
    print(f"💬 New Comment Found!")
    print(f"{'='*60}")
    print(f"Comment ID: {comment_id}")
    print(f"Username: @{username}")
    print(f"Text: {comment_text}")
    print(f"Timestamp: {timestamp}")
    print(f"Post: {media_permalink}")
    
    # Check if comment contains deploy command
    if '@feedo3app' in comment_text.lower() and 'deploy' in comment_text.lower():
        print(f"\n🚀 Deploy command detected!")
        
        # Scrape profile picture
        profile_data = scrape_profile_picture(username)
        
        if profile_data:
            print(f"\n📊 Profile Data:")
            print(f"   Username: @{profile_data['username']}")
            print(f"   Full Name: {profile_data['full_name']}")
            print(f"   Followers: {profile_data['followers']}")
            print(f"   Profile Picture: {profile_data['profile_pic_url']}")
            
            # Save to JSON file for later use
            output_file = f"profile_{username}_{int(time.time())}.json"
            output_path = os.path.join(os.path.dirname(__file__), '..', 'data', output_file)
            
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump({
                    'comment': {
                        'id': comment_id,
                        'text': comment_text,
                        'timestamp': timestamp,
                        'post_url': media_permalink
                    },
                    'profile': profile_data
                }, f, indent=2)
            
            print(f"💾 Saved profile data to: {output_file}")
        
    # Mark as processed
    processed_comments.add(comment_id)

def main():
    """Main polling loop"""
    print("🤖 Instagram Comment Monitor with Profile Scraper")
    print("=" * 60)
    print(f"📊 Polling interval: {POLLING_INTERVAL} seconds")
    print(f"👤 Monitoring account: {INSTAGRAM_BUSINESS_ACCOUNT_ID}")
    print("=" * 60)
    
    while True:
        try:
            print(f"\n🔄 Checking for new comments... [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            
            # Fetch recent media
            media_posts = fetch_recent_media()
            print(f"📱 Found {len(media_posts)} recent posts")
            
            # Check comments on each post
            new_comments_count = 0
            for media in media_posts:
                media_id = media['id']
                media_permalink = media.get('permalink', 'N/A')
                
                comments = fetch_comments_for_media(media_id)
                
                for comment in comments:
                    if comment['id'] not in processed_comments:
                        new_comments_count += 1
                        process_comment(comment, media_permalink)
            
            if new_comments_count == 0:
                print("✅ No new comments found")
            else:
                print(f"\n✅ Processed {new_comments_count} new comment(s)")
            
            # Wait before next check
            print(f"\n⏳ Waiting {POLLING_INTERVAL} seconds before next check...")
            time.sleep(POLLING_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n👋 Stopping comment monitor...")
            break
        except Exception as e:
            print(f"\n❌ Error in main loop: {e}")
            print(f"⏳ Retrying in {POLLING_INTERVAL} seconds...")
            time.sleep(POLLING_INTERVAL)

if __name__ == "__main__":
    main()
