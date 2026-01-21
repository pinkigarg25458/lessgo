"""
Complete Token Deployment Workflow
Fetches Instagram comments, scrapes profile pictures, and deploys tokens on Pump.fun
"""

import os
import sys
import time
import requests
import json
import re
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.instagram_reply import reply_to_comment, reply_with_error
from services.database import DatabaseService

# Load environment variables
load_dotenv()

# Configuration
INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
APIFY_API_TOKEN = os.getenv('APIFY_API_TOKEN')
OUR_USERNAME = 'feedo3app'
POLLING_INTERVAL = 60  # seconds

# Initialize database
db = DatabaseService()

# Store processed comments to avoid duplicates
processed_comments = set()

def fetch_recent_media():
    """Fetch recent media posts from Instagram Business Account"""
    url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
    params = {
        'fields': 'id,caption,media_type,media_url,timestamp,permalink,comments_count',
        'access_token': INSTAGRAM_ACCESS_TOKEN,
        'limit': 25
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
        
        # Debug: Print response
        if 'error' in data:
            print(f"   ⚠️  API Error for {media_id}: {data['error'].get('message', 'Unknown error')}")
            print(f"   Error code: {data['error'].get('code', 'N/A')}")
            print(f"   Error type: {data['error'].get('type', 'N/A')}")
        
        comments = data.get('data', [])
        return comments
    except Exception as e:
        print(f"❌ Error fetching comments: {e}")
        import traceback
        traceback.print_exc()
        return []

def parse_deploy_command(comment_text, our_username):
    """Parse deploy command from comment text"""
    # Pattern 1: @username deploy TokenName $TICKER
    pattern1 = rf'@{our_username}\s+(?:deploy|launch)\s+(\w+)\s+\$(\w+)'
    # Pattern 2: @username TokenName $TICKER
    pattern2 = rf'@{our_username}\s+(\w+)\s+\$(\w+)'
    
    match = re.search(pattern1, comment_text, re.IGNORECASE)
    if not match:
        match = re.search(pattern2, comment_text, re.IGNORECASE)
    
    if match:
        token_name = match.group(1)
        ticker = match.group(2).upper()
        
        # Validate ticker (3-10 characters, A-Z and 0-9 only)
        if len(ticker) >= 3 and len(ticker) <= 10 and ticker.isalnum():
            return {
                'name': token_name,
                'ticker': ticker,
                'valid': True
            }
    
    return {'valid': False}

def scrape_profile_picture(username):
    """Scrape Instagram profile picture using Apify API and download it"""
    print(f"\n🔍 Scraping profile picture for @{username}...")
    
    url = f"https://api.apify.com/v2/acts/apify~instagram-profile-scraper/runs"
    headers = {'Content-Type': 'application/json'}
    payload = {'usernames': [username], 'resultsLimit': 1}
    params = {'token': APIFY_API_TOKEN}
    
    try:
        # Start the scraper run
        print(f"📤 Starting Apify scraper...")
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        run_data = response.json()
        
        run_id = run_data['data']['id']
        dataset_id = run_data['data']['defaultDatasetId']
        print(f"✅ Scraper started - Run ID: {run_id}")
        
        # Wait for completion
        print("⏳ Waiting for scraper to complete...")
        run_status_url = f"https://api.apify.com/v2/acts/apify~instagram-profile-scraper/runs/{run_id}"
        
        max_wait = 60
        wait_time = 0
        
        while wait_time < max_wait:
            time.sleep(5)
            wait_time += 5
            
            status_response = requests.get(run_status_url, params=params)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            status = status_data['data']['status']
            
            if status in ['SUCCEEDED', 'FAILED', 'ABORTED']:
                break
        
        if status != 'SUCCEEDED':
            print(f"❌ Scraper failed with status: {status}")
            return None
        
        # Get results
        print("📥 Fetching scraped data...")
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        result_response = requests.get(dataset_url, params=params)
        result_response.raise_for_status()
        results = result_response.json()
        
        if results and len(results) > 0:
            profile_data = results[0]
            profile_pic_url = profile_data.get('profilePicUrlHD') or profile_data.get('profilePicUrl', '')
            
            print(f"✅ Profile picture URL found")
            
            # Download the profile picture
            print(f"📥 Downloading profile picture...")
            pic_response = requests.get(profile_pic_url, stream=True)
            pic_response.raise_for_status()
            
            # Save to temporary file
            scripts_dir = os.path.dirname(os.path.abspath(__file__))
            temp_image_path = os.path.join(scripts_dir, f'temp_profile_{username}.jpg')
            
            with open(temp_image_path, 'wb') as f:
                for chunk in pic_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Profile picture downloaded to: {temp_image_path}")
            
            return {
                'username': username,
                'profile_pic_url': profile_pic_url,
                'profile_pic_path': temp_image_path,
                'full_name': profile_data.get('fullName', ''),
                'followers': profile_data.get('followersCount', 0)
            }
        else:
            print(f"❌ No profile data found")
            return None
            
    except Exception as e:
        print(f"❌ Error scraping profile: {e}")
        return None

def deploy_token_on_pumpfun(token_name, ticker, image_path, username):
    """Deploy token on Pump.fun using Node.js script"""
    print(f"\n🚀 Deploying token on Pump.fun...")
    print(f"   Token Name: {token_name}")
    print(f"   Ticker: ${ticker}")
    print(f"   Image: {image_path}")
    print(f"   Creator: @{username}")
    
    try:
        # Create a temporary Node.js script for deployment
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        deploy_script_path = os.path.join(scripts_dir, 'deploy-single-token.js')
        
        deploy_script_content = f"""
const fs = require('fs');
const path = require('path');
require('dotenv').config({{path: path.join(__dirname, '..', '.env')}});
const {{ VersionedTransaction, Connection, Keypair }} = require('@solana/web3.js');
const bs58 = require('bs58');
const FormData = require('form-data');
const axios = require('axios');

const RPC_ENDPOINT = "https://api.mainnet-beta.solana.com";
const web3Connection = new Connection(RPC_ENDPOINT, 'confirmed');

async function deploy() {{
  try {{
    const signerKeyPair = Keypair.fromSecretKey(
      bs58.decode(process.env.PUMPPORTAL_WALLET_PRIVATE_KEY)
    );
    
    const mintKeypair = Keypair.generate();
    
    console.log('\\n📤 Uploading metadata to Pump.fun IPFS...');
    
    const formData = new FormData();
    formData.append("file", fs.createReadStream('{image_path}'));
    formData.append("name", '{token_name}');
    formData.append("symbol", '{ticker}');
    formData.append("description", 'Token created by @{username} via Instagram comment on Feedo3');
    formData.append("showName", "true");
    
    const metadataResponse = await axios.post(
      "https://pump.fun/api/ipfs",
      formData,
      {{
        headers: formData.getHeaders(),
        maxBodyLength: Infinity,
        maxContentLength: Infinity
      }}
    );
    
    if (metadataResponse.status !== 200) {{
      throw new Error(`IPFS upload failed: ${{metadataResponse.statusText}}`);
    }}
    
    const metadataResponseJSON = metadataResponse.data;
    console.log('✅ Metadata uploaded to IPFS');
    console.log('📍 Metadata URI:', metadataResponseJSON.metadataUri);
    
    console.log('\\n🔨 Creating transaction via PumpPortal...');
    
    const createTxPayload = {{
      publicKey: signerKeyPair.publicKey.toString(),
      action: "create",
      tokenMetadata: {{
        name: metadataResponseJSON.metadata.name,
        symbol: metadataResponseJSON.metadata.symbol,
        uri: metadataResponseJSON.metadataUri
      }},
      mint: mintKeypair.publicKey.toBase58(),
      denominatedInSol: "true",
      amount: 0.02,
      slippage: 10,
      priorityFee: 0.0005,
      pool: "pump"
    }};
    
    const response = await axios.post(
      'https://pumpportal.fun/api/trade-local',
      createTxPayload,
      {{
        headers: {{"Content-Type": "application/json"}},
        responseType: 'arraybuffer'
      }}
    );
    
    if (response.status === 200) {{
      const data = response.data;
      const tx = VersionedTransaction.deserialize(new Uint8Array(data));
      tx.sign([mintKeypair, signerKeyPair]);
      
      const signature = await web3Connection.sendTransaction(tx);
      
      console.log('\\n✅ DEPLOYMENT SUCCESSFUL!');
      console.log(JSON.stringify({{
        success: true,
        signature: signature,
        mintAddress: mintKeypair.publicKey.toString(),
        txUrl: `https://solscan.io/tx/${{signature}}`,
        tokenUrl: `https://pump.fun/${{mintKeypair.publicKey.toString()}}`,
        metadataUri: metadataResponseJSON.metadataUri
      }}));
      
      await web3Connection.confirmTransaction(signature, 'confirmed');
      process.exit(0);
    }} else {{
      throw new Error(`Transaction creation failed: ${{response.statusText}}`);
    }}
    
  }} catch (error) {{
    console.error('ERROR:', error.message);
    process.exit(1);
  }}
}}

deploy();
"""
        
        with open(deploy_script_path, 'w') as f:
            f.write(deploy_script_content)
        
        # Run the Node.js deployment script
        print("\n📡 Executing deployment script...")
        result = subprocess.run(
            ['node', deploy_script_path],
            cwd=os.path.join(scripts_dir, '..'),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Debug: Print full output
        print("\n🔍 DEBUG - Full deployment output:")
        print(result.stdout)
        print("\n🔍 DEBUG - Errors (if any):")
        print(result.stderr)
        
        # Parse output - look for JSON on any line
        output_lines = result.stdout.split('\n')
        
        # Look for the JSON success output
        for line in output_lines:
            line = line.strip()
            if line.startswith('{') and '"success"' in line:
                try:
                    deployment_result = json.loads(line)
                    
                    print(f"\n✅ Successfully parsed deployment result")
                    print(f"   Success: {deployment_result.get('success')}")
                    print(f"   Mint: {deployment_result.get('mintAddress')}")
                    
                    # Clean up temp files
                    try:
                        os.remove(deploy_script_path)
                        if os.path.exists(image_path):
                            os.remove(image_path)
                    except:
                        pass
                    
                    return deployment_result
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON: {e}")
                    print(f"   Line was: {line}")
                    continue
        
        # If we get here, deployment failed
        print("\n❌ No success JSON found in output")
        print("Full stdout:")
        print(result.stdout)
        if result.stderr:
            print("\nFull stderr:")
            print(result.stderr)
        
        return {'success': False, 'error': 'Could not parse deployment result'}
        
    except subprocess.TimeoutExpired:
        print(f"❌ Deployment script timed out after 120 seconds")
        return {'success': False, 'error': 'Deployment timeout'}
    except Exception as e:
        print(f"❌ Error deploying token: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def process_comment(comment, media_permalink):
    """Process a single comment - complete workflow"""
    comment_id = comment['id']
    comment_text = comment['text']
    username = comment['username']
    timestamp = comment['timestamp']
    
    # Skip if already processed
    if comment_id in processed_comments:
        return
    
    # Check database if comment already processed
    if db.check_comment_processed(comment_id):
        print(f"⏭️  Skipping - already processed in database")
        processed_comments.add(comment_id)
        return
    
    print(f"\\n{'='*80}")
    print(f"💬 NEW COMMENT DETECTED")
    print(f"{'='*80}")
    print(f"📋 Comment ID: {comment_id}")
    print(f"👤 Username: @{username}")
    print(f"💭 Text: {comment_text}")
    print(f"🕐 Timestamp: {timestamp}")
    print(f"🔗 Post: {media_permalink}")
    
    # Check if comment mentions our username
    if f'@{OUR_USERNAME}' not in comment_text.lower():
        print(f"⏭️  Skipping - doesn't mention @{OUR_USERNAME}")
        processed_comments.add(comment_id)
        return
    
    # Parse deploy command
    print(f"\\n🔍 Parsing deploy command...")
    parsed = parse_deploy_command(comment_text, OUR_USERNAME)
    
    if not parsed['valid']:
        print(f"❌ Invalid deploy command format")
        print(f"   Expected: @{OUR_USERNAME} deploy TokenName $TICKER")
        processed_comments.add(comment_id)
        return
    
    token_name = parsed['name']
    ticker = parsed['ticker']
    
    print(f"✅ Deploy command parsed successfully!")
    print(f"   Token Name: {token_name}")
    print(f"   Ticker: ${ticker}")
    
    # Check if user exists in database
    print(f"\n🔍 Checking database for user @{username}...")
    user = db.get_or_create_user(username)
    
    # Try to get stored profile picture from database
    profile_data = None
    if user:
        stored_pic = db.get_user_profile_picture(username)
        if stored_pic and stored_pic.get('path'):
            print(f"✅ Using stored profile picture from database")
            profile_data = {
                'username': username,
                'profile_pic_path': stored_pic['path'],
                'profile_pic_url': stored_pic.get('url', ''),
                'full_name': user.get('fullName', ''),
                'followers': user.get('followersCount', 0)
            }
    
    # If no stored picture, scrape from Instagram
    if not profile_data:
        print(f"\n🔍 No stored picture found, scraping from Instagram...")
        profile_data = scrape_profile_picture(username)
        
        if profile_data:
            # Save new user to database
            if not user:
                user = db.get_or_create_user(username, profile_data)
    
    # Scrape profile picture
    # profile_data = scrape_profile_picture(username)
    
    if not profile_data or not profile_data.get('profile_pic_path'):
        print(f"❌ Failed to scrape profile picture - cannot deploy token")
        processed_comments.add(comment_id)
        return
    
    print(f"\\n📊 Creator Profile:")
    print(f"   Username: @{profile_data['username']}")
    print(f"   Full Name: {profile_data['full_name']}")
    print(f"   Followers: {profile_data['followers']}")
    
    # Deploy token on Pump.fun
    deployment_result = deploy_token_on_pumpfun(
        token_name, 
        ticker, 
        profile_data['profile_pic_path'],
        username
    )
    
    if deployment_result.get('success'):
        print(f"\\n{'='*80}")
        print(f"🎉 TOKEN DEPLOYED SUCCESSFULLY!")
        print(f"{'='*80}")
        print(f"📋 Comment ID: {comment_id}")
        print(f"👤 Creator: @{username}")
        print(f"🪙 Token Name: {token_name}")
        print(f"🎯 Ticker: ${ticker}")
        print(f"📍 Mint Address: {deployment_result['mintAddress']}")
        print(f"🔗 Transaction: {deployment_result['txUrl']}")
        print(f"🚀 Pump.fun: {deployment_result['tokenUrl']}")
        print(f"📦 Metadata: {deployment_result.get('metadataUri', 'N/A')}")
        print(f"{'='*80}")
        
        # Send auto-reply to Instagram comment
        print(f"\\n💬 Sending auto-reply to @{username}...")
        reply_result = reply_to_comment(
            comment_id=comment_id,
            token_name=token_name,
            ticker=ticker,
            mint_address=deployment_result['mintAddress'],
            transaction_signature=deployment_result['signature'],
            metadata_uri=deployment_result.get('metadataUri')
        )
        
        if reply_result.get('success'):
            print(f"✅ Auto-reply sent successfully!")
            print(f"   Reply ID: {reply_result.get('reply_id')}")
        else:
            print(f"❌ Failed to send auto-reply: {reply_result.get('error')}")
        
        # Save deployment to database
        print(f"\n💾 Saving deployment to database...")
        deployment_data = {
            'comment_id': comment_id,
            'comment_text': comment_text,
            'post_url': media_permalink,
            'token_name': token_name,
            'ticker': ticker,
            'mint_address': deployment_result['mintAddress'],
            'transaction_hash': deployment_result['signature'],
            'pumpfun_url': deployment_result['tokenUrl'],
            'metadata_uri': deployment_result.get('metadataUri', ''),
            'auto_reply_id': reply_result.get('reply_id') if reply_result.get('success') else None,
            'status': 'SUCCESS'
        }
        
        try:
            db_save_result = db.save_deployment(user['id'], deployment_data)
            if db_save_result:
                print(f"✅ Deployment saved to database (ID: {db_save_result.get('id')})")
            else:
                print(f"⚠️ Failed to save deployment to database")
        except Exception as e:
            print(f"⚠️ Database save error: {e}")
        
        # Save deployment record
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        record_file = os.path.join(data_dir, f'deployment_{comment_id}.json')
        with open(record_file, 'w') as f:
            json.dump({
                'comment': {
                    'id': comment_id,
                    'text': comment_text,
                    'username': username,
                    'timestamp': timestamp,
                    'post_url': media_permalink
                },
                'token': {
                    'name': token_name,
                    'ticker': ticker,
                    'mint_address': deployment_result['mintAddress'],
                    'transaction': deployment_result['signature'],
                    'pump_url': deployment_result['tokenUrl'],
                    'metadata_uri': deployment_result.get('metadataUri', '')
                },
                'creator': {
                    'username': username,
                    'full_name': profile_data['full_name'],
                    'followers': profile_data['followers']
                },
                'deployed_at': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"💾 Deployment record saved to: deployment_{comment_id}.json")
    else:
        print(f"\\n❌ TOKEN DEPLOYMENT FAILED")
        print(f"   Error: {deployment_result.get('error', 'Unknown error')}")
        
        # Send error reply to user
        print(f"\\n💬 Sending error notification to @{username}...")
        error_reply = reply_with_error(
            comment_id=comment_id,
            error_message=deployment_result.get('error', 'Unknown error')
        )
        
        if error_reply.get('success'):
            print(f"✅ Error notification sent")
        else:
            print(f"❌ Failed to send error notification")        
        # Save failed deployment to database
        print(f"\n💾 Saving failed deployment to database...")
        deployment_data = {
            'comment_id': comment_id,
            'comment_text': comment_text,
            'post_url': media_permalink,
            'token_name': token_name,
            'ticker': ticker,
            'auto_reply_id': error_reply.get('reply_id') if error_reply.get('success') else None,
            'status': 'FAILED',
            'error_message': deployment_result.get('error', 'Unknown error')
        }
        
        try:
            db_save_result = db.save_deployment(user['id'], deployment_data)
            if db_save_result:
                print(f"✅ Failed deployment saved to database (ID: {db_save_result.get('id')})")
            else:
                print(f"⚠️ Failed to save deployment to database")
        except Exception as e:
            print(f"⚠️ Database save error: {e}")    
    # Mark as processed
    processed_comments.add(comment_id)

def main():
    """Main polling loop"""
    print("🤖 FEEDO3 - Instagram to Pump.fun Token Deployer")
    print("=" * 80)
    print(f"📊 Polling interval: {POLLING_INTERVAL} seconds")
    print(f"👤 Monitoring account: @{OUR_USERNAME}")
    print(f"🎯 Looking for: @{OUR_USERNAME} deploy TokenName $TICKER")
    print("=" * 80)
    
    while True:
        try:
            print(f"\\n🔄 Checking for new comments... [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            
            # Fetch recent media
            media_posts = fetch_recent_media()
            print(f"📱 Found {len(media_posts)} recent posts")
            
            # Debug: Show all posts with comment counts
            for idx, media in enumerate(media_posts, 1):
                media_type = media.get('media_type', 'UNKNOWN')
                comments_count = media.get('comments_count', 0)
                caption = media.get('caption', 'No caption')[:30]
                print(f"   Post {idx}: {media_type} - {comments_count} comments - '{caption}...'")
            
            # Check comments on each post
            new_comments_count = 0
            for media in media_posts:
                media_id = media['id']
                media_permalink = media.get('permalink', 'N/A')
                
                comments = fetch_comments_for_media(media_id)
                print(f"   📝 Post {media_id}: {len(comments)} comments")
                
                # Debug: Show all comments
                if comments:
                    for i, comment in enumerate(comments, 1):
                        print(f"      Comment {i}: @{comment.get('username', 'unknown')} - {comment.get('text', '')[:50]}...")
                
                for comment in comments:
                    if comment['id'] not in processed_comments:
                        new_comments_count += 1
                        process_comment(comment, media_permalink)
            
            if new_comments_count == 0:
                print("✅ No new comments found")
            else:
                print(f"\\n✅ Processed {new_comments_count} new comment(s)")
            
            # Wait before next check
            print(f"\\n⏳ Waiting {POLLING_INTERVAL} seconds before next check...")
            time.sleep(POLLING_INTERVAL)
            
        except KeyboardInterrupt:
            print("\\n\\n👋 Stopping token deployer...")
            break
        except Exception as e:
            print(f"\\n❌ Error in main loop: {e}")
            import traceback
            traceback.print_exc()
            print(f"⏳ Retrying in {POLLING_INTERVAL} seconds...")
            time.sleep(POLLING_INTERVAL)

if __name__ == "__main__":
    main()
