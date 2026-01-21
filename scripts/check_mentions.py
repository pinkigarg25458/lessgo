#!/usr/bin/env python3
"""
Instagram Mention Checker
Check when someone mentions @feedo3app anywhere on Instagram
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')

def fetch_mentions():
    """Fetch all mentions of @feedo3app"""
    
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_BUSINESS_ACCOUNT_ID:
        print("❌ Error: Missing credentials in .env file")
        return
    
    print("🔍 Checking for mentions of @feedo3app...\n")
    print(f"📱 Account ID: {INSTAGRAM_BUSINESS_ACCOUNT_ID}\n")
    
    # Method 1: Check for media tags (when someone tags you in their post)
    print("=" * 60)
    print("Method 1: Checking Tagged Media")
    print("=" * 60 + "\n")
    
    try:
        url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/tags"
        params = {
            'fields': 'id,media_type,media_url,permalink,timestamp,caption,username',
            'limit': 25,
            'access_token': INSTAGRAM_ACCESS_TOKEN
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            print(f"✅ Found {len(data['data'])} posts where you were tagged!\n")
            
            for i, media in enumerate(data['data'], 1):
                print(f"{i}. Tagged in post by @{media.get('username', 'Unknown')}")
                print(f"   Media ID: {media['id']}")
                print(f"   Type: {media.get('media_type', 'N/A')}")
                print(f"   Link: {media.get('permalink', 'N/A')}")
                print(f"   Time: {media.get('timestamp', 'N/A')}")
                if media.get('caption'):
                    print(f"   Caption: {media['caption'][:100]}...")
                print()
        else:
            print("⚠️  No tagged media found")
            print("   Someone needs to TAG you in a post/reel\n")
            
    except Exception as e:
        print(f"❌ Method 1 failed: {e}\n")
    
    # Method 2: Check own media for comment mentions
    print("=" * 60)
    print("Method 2: Checking Your Posts for Comment Mentions")
    print("=" * 60 + "\n")
    
    try:
        url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
        params = {
            'fields': 'id,caption,permalink,timestamp,comments{id,text,username,timestamp}',
            'limit': 10,
            'access_token': INSTAGRAM_ACCESS_TOKEN
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            print(f"✅ Found {len(data['data'])} of your posts\n")
            
            mention_count = 0
            for i, media in enumerate(data['data'], 1):
                if 'comments' in media and 'data' in media['comments']:
                    # Filter comments mentioning @feedo3app
                    mentions = [c for c in media['comments']['data'] 
                               if '@feedo3app' in c['text'].lower()]
                    
                    if mentions:
                        print(f"📍 Post {i}: {media.get('permalink', 'N/A')}")
                        print(f"   Found {len(mentions)} mention(s):\n")
                        
                        for j, comment in enumerate(mentions, 1):
                            mention_count += 1
                            print(f"   {j}. @{comment['username']} commented:")
                            print(f"      \"{comment['text']}\"")
                            print(f"      Comment ID: {comment['id']}")
                            print(f"      Time: {comment['timestamp']}\n")
            
            if mention_count == 0:
                print("⚠️  No mentions found in your posts")
                print("   Post a reel and ask someone to comment with @feedo3app\n")
            else:
                print(f"✅ Total mentions found: {mention_count}\n")
                
        else:
            print("⚠️  No media posts found")
            print("   Post a reel/photo from @feedo3app account first\n")
            
    except Exception as e:
        print(f"❌ Method 2 failed: {e}\n")
    
    # Instructions
    print("=" * 60)
    print("💡 How to Test")
    print("=" * 60 + "\n")
    print("Since @feedo3app has no posts yet:\n")
    print("1. Post a reel from @feedo3app Instagram account")
    print("2. Comment on it: @feedo3app deploy Test $TOKEN")
    print("3. Run this script again")
    print("4. You'll see the comment!\n")
    print("Note: Instagram Graph API can only detect mentions in:")
    print("  - Your own posts' comments")
    print("  - Tags in other people's posts (rare)")
    print("  - Real-time webhooks (production setup)\n")

if __name__ == "__main__":
    fetch_mentions()
