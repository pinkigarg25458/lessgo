/**
 * Database Service using Prisma
 * Handles all database operations for token deployments
 */

const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

/**
 * Get or create user
 */
async function getOrCreateUser(username, profileData = null) {
  try {
    // Check if user exists
    let user = await prisma.user.findUnique({
      where: { instagramUsername: username }
    });

    if (user) {
      console.log(`✅ User @${username} found in database (ID: ${user.id})`);
      return user;
    }

    // Create new user if profile data provided
    if (profileData) {
      let profilePictureData = null;

      // Read profile picture if path exists
      if (profileData.profile_pic_path) {
        const fs = require('fs');
        if (fs.existsSync(profileData.profile_pic_path)) {
          profilePictureData = fs.readFileSync(profileData.profile_pic_path);
        }
      }

      user = await prisma.user.create({
        data: {
          instagramUsername: username,
          instagramAccountUrl: `https://instagram.com/${username}`,
          fullName: profileData.full_name || '',
          followersCount: profileData.followers || 0,
          profilePictureUrl: profileData.profile_pic_url || '',
          profilePictureData: profilePictureData
        }
      });

      console.log(`✅ New user @${username} created (ID: ${user.id})`);
      return user;
    }

    return null;
  } catch (error) {
    console.error(`❌ Error with user: ${error.message}`);
    return null;
  }
}

/**
 * Get user's stored profile picture
 */
async function getUserProfilePicture(username) {
  try {
    const user = await prisma.user.findUnique({
      where: { instagramUsername: username },
      select: {
        profilePictureData: true,
        profilePictureUrl: true,
        fullName: true,
        followersCount: true
      }
    });

    if (user && user.profilePictureData) {
      // Save profile picture to temp file
      const fs = require('fs');
      const path = require('path');
      const os = require('os');
      
      const tempDir = os.tmpdir();
      const fileName = `profile_${username}_${Date.now()}.jpg`;
      const filePath = path.join(tempDir, fileName);
      
      fs.writeFileSync(filePath, user.profilePictureData);
      
      return {
        path: filePath,
        url: user.profilePictureUrl,
        fullName: user.fullName,
        followers: user.followersCount
      };
    }

    return null;
  } catch (error) {
    console.error(`❌ Error fetching profile picture: ${error.message}`);
    return null;
  }
}

/**
 * Save token deployment
 */
async function saveDeployment(userId, deploymentData) {
  try {
    const deployment = await prisma.tokenDeployment.create({
      data: {
        userId: userId,
        commentId: deploymentData.comment_id,
        commentText: deploymentData.comment_text,
        postUrl: deploymentData.post_url,
        tokenName: deploymentData.token_name,
        ticker: deploymentData.ticker,
        mintAddress: deploymentData.mint_address,
        transactionHash: deploymentData.transaction_hash,
        pumpfunUrl: deploymentData.pumpfun_url,
        metadataUri: deploymentData.metadata_uri || null,
        autoReplyId: deploymentData.auto_reply_id || null,
        status: deploymentData.status || 'SUCCESS',
        errorMessage: deploymentData.error_message || null
      }
    });

    console.log(`✅ Deployment saved to database (ID: ${deployment.id})`);
    return deployment;
  } catch (error) {
    console.error(`❌ Error saving deployment: ${error.message}`);
    return null;
  }
}

/**
 * Check if comment has been processed
 */
async function checkCommentProcessed(commentId) {
  try {
    const deployment = await prisma.tokenDeployment.findUnique({
      where: { commentId: commentId }
    });

    return deployment !== null;
  } catch (error) {
    console.error(`❌ Error checking comment: ${error.message}`);
    return false;
  }
}

/**
 * Get user's recent deployments
 */
async function getUserDeployments(username, limit = 10) {
  try {
    const user = await prisma.user.findUnique({
      where: { instagramUsername: username },
      include: {
        deployments: {
          orderBy: { deployedAt: 'desc' },
          take: limit
        }
      }
    });

    return user?.deployments || [];
  } catch (error) {
    console.error(`❌ Error fetching deployments: ${error.message}`);
    return [];
  }
}

/**
 * Get deployment statistics
 */
async function getStats() {
  try {
    const totalDeployments = await prisma.tokenDeployment.count();
    const totalUsers = await prisma.user.count();
    const successfulDeployments = await prisma.tokenDeployment.count({
      where: { status: 'SUCCESS' }
    });
    const failedDeployments = await prisma.tokenDeployment.count({
      where: { status: 'FAILED' }
    });

    return {
      totalDeployments,
      totalUsers,
      successfulDeployments,
      failedDeployments
    };
  } catch (error) {
    console.error(`❌ Error fetching stats: ${error.message}`);
    return null;
  }
}

// CLI interface for Python to call
if (require.main === module) {
  const args = process.argv.slice(2);
  const command = args[0];

  (async () => {
    try {
      let result;

      switch (command) {
        case 'get-or-create-user':
          const username = args[1];
          const profileData = args[2] ? JSON.parse(args[2]) : null;
          result = await getOrCreateUser(username, profileData);
          break;

        case 'get-profile-picture':
          result = await getUserProfilePicture(args[1]);
          if (result && result.data) {
            // Save to temp file
            const fs = require('fs');
            const tempPath = `/tmp/profile_${args[1]}.jpg`;
            fs.writeFileSync(tempPath, result.data);
            result = { path: tempPath, url: result.url };
          }
          break;

        case 'save-deployment':
          const userId = args[1];
          const deploymentData = JSON.parse(args[2]);
          result = await saveDeployment(userId, deploymentData);
          break;

        case 'check-comment':
          result = await checkCommentProcessed(args[1]);
          break;

        case 'get-deployments':
          result = await getUserDeployments(args[1], parseInt(args[2] || '10'));
          break;

        case 'stats':
          result = await getStats();
          break;

        default:
          console.error('Unknown command:', command);
          process.exit(1);
      }

      // Output result as JSON
      console.log(JSON.stringify(result));
      process.exit(0);
    } catch (error) {
      console.error('Error:', error.message);
      process.exit(1);
    } finally {
      await prisma.$disconnect();
    }
  })();
}

module.exports = {
  getOrCreateUser,
  getUserProfilePicture,
  saveDeployment,
  checkCommentProcessed,
  getUserDeployments,
  getStats,
  prisma
};
