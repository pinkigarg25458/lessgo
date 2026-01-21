"""
Database Service for Token Deployments
Uses Prisma (Node.js) via subprocess calls
"""

import os
import json
import subprocess
from pathlib import Path

class DatabaseService:
    def __init__(self):
        self.db_script = os.path.join(os.path.dirname(__file__), 'database.js')
    
    def _call_db(self, command, *args):
        """Call Node.js database script"""
        try:
            cmd = ['node', self.db_script, command] + list(args)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"❌ Database command failed: {result.stderr}")
                return None
            
            # Parse JSON output
            output_lines = result.stdout.strip().split('\n')
            for line in reversed(output_lines):
                if line.startswith('{') or line.startswith('['):
                    return json.loads(line)
            
            return None
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return None
    
    def get_or_create_user(self, username, profile_data=None):
        """Get existing user or create new one"""
        profile_json = json.dumps(profile_data) if profile_data else 'null'
        return self._call_db('get-or-create-user', username, profile_json)
    
    def get_user_profile_picture(self, username):
        """Get stored profile picture for a user"""
        return self._call_db('get-profile-picture', username)
    
    def save_deployment(self, user_id, deployment_data):
        """Save token deployment record"""
        deployment_json = json.dumps(deployment_data)
        return self._call_db('save-deployment', user_id, deployment_json)
    
    def check_comment_processed(self, comment_id):
        """Check if comment has already been processed"""
        result = self._call_db('check-comment', comment_id)
        return result is True
    
    def get_user_deployments(self, username, limit=10):
        """Get recent deployments for a user"""
        return self._call_db('get-deployments', username, str(limit)) or []
    
    def get_stats(self):
        """Get deployment statistics"""
        return self._call_db('stats')

if __name__ == "__main__":
    # Test database connection
    print("🧪 Testing Database Service")
    print("=" * 80)
    
    db = DatabaseService()
    
    print("\n📊 Getting stats...")
    stats = db.get_stats()
    if stats:
        print(f"Total Deployments: {stats.get('totalDeployments', 0)}")
        print(f"Total Users: {stats.get('totalUsers', 0)}")
        print(f"Successful: {stats.get('successfulDeployments', 0)}")
        print(f"Failed: {stats.get('failedDeployments', 0)}")
    else:
        print("❌ Could not fetch stats")
