/**
 * Comment Parser Service
 * Parses Instagram comments to extract token deployment commands
 */

/**
 * Parse Instagram comment to extract token name and ticker
 * Supported formats:
 * - @username deploy TokenName $TICKER
 * - @username launch TokenName $TICKER
 * - @username TokenName $TICKER
 * 
 * @param {string} commentText - The comment text
 * @param {string} ourUsername - Our Instagram username (without @)
 * @returns {Object|null} Parsed token data or null if invalid
 */
function parseComment(commentText, ourUsername) {
  if (!commentText || typeof commentText !== 'string') {
    return null;
  }

  // Normalize the comment
  const text = commentText.trim();
  
  // Check if comment mentions our account
  const mentionRegex = new RegExp(`@${ourUsername}`, 'i');
  if (!mentionRegex.test(text)) {
    return null; // Not mentioning us
  }

  // Pattern 1: @username deploy/launch NAME $TICKER
  const pattern1 = new RegExp(
    `@${ourUsername}\\s+(deploy|launch)\\s+([a-zA-Z0-9\\s]+)\\s+\\$([A-Z0-9]+)`,
    'i'
  );
  
  // Pattern 2: @username NAME $TICKER (without deploy/launch keyword)
  const pattern2 = new RegExp(
    `@${ourUsername}\\s+([a-zA-Z0-9\\s]+)\\s+\\$([A-Z0-9]+)`,
    'i'
  );

  let match = text.match(pattern1);
  let tokenName, ticker;

  if (match) {
    // Pattern 1 matched (with deploy/launch keyword)
    tokenName = match[2].trim();
    ticker = match[3].toUpperCase();
  } else {
    // Try pattern 2
    match = text.match(pattern2);
    if (match) {
      tokenName = match[1].trim();
      ticker = match[2].toUpperCase();
    } else {
      return null; // No valid pattern matched
    }
  }

  // Validate ticker
  if (!ticker || ticker.length < 3 || ticker.length > 10) {
    return {
      valid: false,
      error: 'Ticker must be 3-10 characters',
      rawText: text
    };
  }

  if (!/^[A-Z0-9]+$/.test(ticker)) {
    return {
      valid: false,
      error: 'Ticker must contain only A-Z and 0-9',
      rawText: text
    };
  }

  // Validate token name
  if (!tokenName || tokenName.length === 0) {
    return {
      valid: false,
      error: 'Token name is required',
      rawText: text
    };
  }

  if (tokenName.length > 50) {
    return {
      valid: false,
      error: 'Token name too long (max 50 characters)',
      rawText: text
    };
  }

  return {
    valid: true,
    tokenName,
    ticker,
    rawText: text
  };
}

/**
 * Test the parser with various comment formats
 */
function testParser() {
  const ourUsername = 'feedo3app';
  
  const testCases = [
    '@feedo3app deploy MyToken $TEST',
    '@feedo3app launch CoolCoin $COOL',
    '@feedo3app SuperToken $SUPER',
    '@FEEDO3APP deploy lowercase $test',
    '@feedo3app deploy   Multi Word Token   $MWT  ',
    '@feedo3app $INVALID',
    'Not mentioning anyone $TEST',
    '@feedo3app deploy NoTicker',
    '@feedo3app deploy TooShort $AB',
    '@feedo3app deploy TooLong $VERYLONGTICKER',
    '@feedo3app deploy Test $SPEC!AL',
  ];

  console.log('🧪 Testing Comment Parser\n');
  
  testCases.forEach((comment, i) => {
    console.log(`Test ${i + 1}: "${comment}"`);
    const result = parseComment(comment, ourUsername);
    
    if (result === null) {
      console.log('   ❌ Not a valid command\n');
    } else if (result.valid) {
      console.log(`   ✅ Valid! Name: "${result.tokenName}", Ticker: $${result.ticker}\n`);
    } else {
      console.log(`   ⚠️  Invalid: ${result.error}\n`);
    }
  });
}

module.exports = {
  parseComment,
  testParser
};
