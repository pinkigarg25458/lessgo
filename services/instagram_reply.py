"""
Instagram Auto-Reply Service
Sends automated replies to comments after token deployment
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')

def reply_to_comment(comment_id, token_name, ticker, mint_address, transaction_signature, metadata_uri=None):
    """
    Reply to an Instagram comment with token deployment details
    
    Args:
        comment_id: Instagram comment ID to reply to
        token_name: Name of the deployed token
        ticker: Token ticker/symbol
        mint_address: Solana mint address
        transaction_signature: Transaction signature
        metadata_uri: IPFS metadata URI (optional)
    
    Returns:
        dict: Response with success status and reply details
    """
    
    # Construct reply message
    pump_url = f"https://pump.fun/{mint_address}"
    tx_url = f"https://solscan.io/tx/{transaction_signature}"
    
    reply_message = f"""✅ Token deployed successfully

🪙 {token_name} (${ticker}) 
{pump_url}

🔗 Solana tx 
{tx_url}

Created via @feedo3app"""
    
    # Instagram Graph API endpoint for comment replies
    url = f"https://graph.facebook.com/v18.0/{comment_id}/replies"
    
    payload = {
        'message': reply_message,
        'access_token': INSTAGRAM_ACCESS_TOKEN
    }
    
    try:
        print(f"\n💬 Sending auto-reply to comment {comment_id}...")
        
        response = requests.post(url, data=payload)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"✅ Reply sent successfully!")
        print(f"   Reply ID: {result.get('id', 'N/A')}")
        
        return {
            'success': True,
            'reply_id': result.get('id'),
            'message': reply_message
        }
        
    except requests.exceptions.HTTPError as e:
        error_data = e.response.json() if e.response else {}
        error_message = error_data.get('error', {}).get('message', str(e))
        
        print(f"❌ Failed to send reply: {error_message}")
        
        return {
            'success': False,
            'error': error_message,
            'details': error_data
        }
    
    except Exception as e:
        print(f"❌ Error sending reply: {e}")
        
        return {
            'success': False,
            'error': str(e)
        }

def reply_with_error(comment_id, error_message):
    """
    Reply to comment with error message when deployment fails
    
    Args:
        comment_id: Instagram comment ID
        error_message: Error description
    
    Returns:
        dict: Response with success status
    """
    
    reply_message = f"""❌ Token deployment failed

Error: {error_message}

Please try again or contact @feedo3app for support."""
    
    url = f"https://graph.facebook.com/v18.0/{comment_id}/replies"
    
    payload = {
        'message': reply_message,
        'access_token': INSTAGRAM_ACCESS_TOKEN
    }
    
    try:
        print(f"\n💬 Sending error reply to comment {comment_id}...")
        
        response = requests.post(url, data=payload)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"✅ Error reply sent")
        
        return {
            'success': True,
            'reply_id': result.get('id')
        }
        
    except Exception as e:
        print(f"❌ Failed to send error reply: {e}")
        
        return {
            'success': False,
            'error': str(e)
        }

def reply_with_custom_message(comment_id, message):
    """
    Send a custom reply to a comment
    
    Args:
        comment_id: Instagram comment ID
        message: Custom message text
    
    Returns:
        dict: Response with success status
    """
    
    url = f"https://graph.facebook.com/v18.0/{comment_id}/replies"
    
    payload = {
        'message': message,
        'access_token': INSTAGRAM_ACCESS_TOKEN
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            'success': True,
            'reply_id': result.get('id')
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    # Test the reply functionality
    print("🧪 Instagram Reply Service Test")
    print("=" * 80)
    
    # Example usage
    test_comment_id = "YOUR_COMMENT_ID_HERE"
    
    result = reply_to_comment(
        comment_id=test_comment_id,
        token_name="TestToken",
        ticker="TEST",
        mint_address="ABC123XYZ",
        transaction_signature="sig123456789"
    )
    
    print("\nResult:", result)
