/**
 * PumpPortal Service - Token Deployment
 * Handles token creation on Pump.fun via PumpPortal API
 */

require('dotenv').config();
const { Keypair } = require('@solana/web3.js');
const bs58 = require('bs58');
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const PUMPPORTAL_API_KEY = process.env.PUMPPORTAL_API_KEY;

/**
 * Deploy a new token on Pump.fun
 * @param {Object} tokenData - Token information
 * @param {string} tokenData.name - Token name
 * @param {string} tokenData.symbol - Token symbol/ticker
 * @param {string} tokenData.description - Token description
 * @param {string} tokenData.imageUrl - Token image URL (optional)
 * @param {string} tokenData.twitter - Twitter URL (optional)
 * @param {string} tokenData.telegram - Telegram URL (optional)
 * @param {string} tokenData.website - Website URL (optional)
 * @returns {Promise<Object>} Deployment result with signature and contract address
 */
async function deployToken(tokenData) {
  try {
    console.log('🚀 Starting token deployment...');
    console.log('Token Name:', tokenData.name);
    console.log('Token Symbol:', tokenData.symbol);

    if (!PUMPPORTAL_API_KEY) {
      throw new Error('PUMPPORTAL_API_KEY not found in environment variables');
    }

    // Generate a random keypair for token mint
    const mintKeypair = Keypair.generate();
    console.log('✅ Generated mint keypair');

    // Step 1: Fetch random image from Unsplash (DISABLED FOR NOW)
    console.log('📤 Uploading metadata to IPFS (without image for testing)...');
    
    /*
    let imageBuffer;
    try {
      console.log('🖼️  Fetching random image from Unsplash...');
      const unsplashResponse = await axios.get('https://api.unsplash.com/photos/random', {
        params: {
          query: 'abstract gradient',
          client_id: 'your_unsplash_access_key',
          orientation: 'square'
        },
        responseType: 'json'
      });
      
      const imageUrl = unsplashResponse.data.urls.small;
      console.log('✅ Got image from Unsplash:', imageUrl);
      
      const imageResponse = await axios.get(imageUrl, { responseType: 'arraybuffer' });
      imageBuffer = Buffer.from(imageResponse.data);
      console.log('✅ Downloaded image');
      
    } catch (error) {
      console.log('⚠️  Unsplash failed, using fallback...');
      imageBuffer = null;
    }
    */

    // Step 2: Create token metadata and upload to IPFS
    
    const formData = new FormData();
    
    // Skip image for now - Pump.fun IPFS might have issues
    /*
    if (imageBuffer) {
      formData.append("file", imageBuffer, {
        filename: 'token-image.jpg',
        contentType: 'image/jpeg'
      });
    }
    */
    
    formData.append("name", tokenData.name);
    formData.append("symbol", tokenData.symbol);
    formData.append("description", tokenData.description || `${tokenData.name} token deployed via Instagram`);
    
    if (tokenData.twitter) formData.append("twitter", tokenData.twitter);
    if (tokenData.telegram) formData.append("telegram", tokenData.telegram);
    if (tokenData.website) formData.append("website", tokenData.website);
    
    formData.append("showName", "true");

    // Create token directly without IPFS upload (PumpPortal will handle it)
    console.log('🔨 Creating token via PumpPortal...');
    
    // Get wallet private key from env
    const walletPrivateKey = process.env.PUMPPORTAL_WALLET_PRIVATE_KEY;
    if (!walletPrivateKey) {
      throw new Error('PUMPPORTAL_WALLET_PRIVATE_KEY not found in environment variables');
    }

    const createTokenPayload = {
      "action": "create",
      "tokenMetadata": {
        name: tokenData.name,
        symbol: tokenData.symbol,
        description: tokenData.description || `${tokenData.name} token`,
      },
      "mint": bs58.encode(mintKeypair.secretKey),
      "denominatedInSol": "true",
      "amount": 0.1, // 0.1 SOL dev buy
      "slippage": 10,
      "priorityFee": 0.0005,
      "pool": "pump"
    };

    console.log('📦 Payload:', JSON.stringify(createTokenPayload, null, 2));

    const response = await axios.post(
      `https://pumpportal.fun/api/trade?api-key=${PUMPPORTAL_API_KEY}`,
      createTokenPayload,
      {
        headers: {
          "Content-Type": "application/json"
        }
      }
    );

    if (response.status === 200) {
      const data = response.data;
      
      // Wait a bit for transaction to settle
      console.log('⏳ Waiting for transaction confirmation...');
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      console.log('✅ Token deployed successfully!');
      console.log('Transaction:', `https://solscan.io/tx/${data.signature}`);
      console.log('Mint Address:', mintKeypair.publicKey.toString());

      return {
        success: true,
        signature: data.signature,
        mintAddress: mintKeypair.publicKey.toString(),
        txUrl: `https://solscan.io/tx/${data.signature}`,
        tokenUrl: `https://pump.fun/${mintKeypair.publicKey.toString()}`
      };
    } else {
      throw new Error(`Failed to deploy token: ${response.statusText}`);
    }

  } catch (error) {
    console.error('❌ Token deployment failed:', error.message);
    
    if (error.response) {
      console.error('API Response Status:', error.response.status);
      console.error('API Response Data:', JSON.stringify(error.response.data, null, 2));
    }

    return {
      success: false,
      error: error.message,
      details: error.response?.data || null
    };
  }
}

/**
 * Validate token data before deployment
 * @param {Object} tokenData 
 * @returns {Object} Validation result
 */
function validateTokenData(tokenData) {
  const errors = [];

  if (!tokenData.name || tokenData.name.trim().length === 0) {
    errors.push('Token name is required');
  }

  if (!tokenData.symbol || tokenData.symbol.trim().length === 0) {
    errors.push('Token symbol is required');
  }

  if (tokenData.symbol && (tokenData.symbol.length < 3 || tokenData.symbol.length > 10)) {
    errors.push('Token symbol must be 3-10 characters');
  }

  if (tokenData.symbol && !/^[A-Z0-9]+$/.test(tokenData.symbol)) {
    errors.push('Token symbol must contain only A-Z and 0-9');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

module.exports = {
  deployToken,
  validateTokenData
};
