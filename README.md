# Instagram Token Deploy - MVP

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
npm install
```

### Step 2: Configure Environment
1. Copy `.env` file and fill in your credentials:
   - Instagram Access Token
   - Instagram Business Account ID
   - Instagram App ID
   - PumpPortal API Key
   - Neon Database URL

### Step 3: Test Instagram API
```bash
npm run test-instagram
```

This will verify:
- ✅ Your Instagram credentials are valid
- ✅ You can access account information
- ✅ You can fetch media (Reels/Posts)
- ✅ You can access comments
- ✅ Token expiry status

### Step 4: Test PumpPortal API
```bash
npm run test-pumpportal
```

### Step 5: Set Up Database
```bash
npx prisma generate
npx prisma db push
```

### Step 6: Run the Application
```bash
npm run dev
```

## 📋 Current Status

See [MVP-README.md](../MVP-README.md) for full development plan.

## 🛠️ Project Structure

```
mvp/
├── scripts/           # Test scripts
├── prisma/            # Database schema
├── services/          # Business logic
├── workers/           # Background workers
└── index.js          # Main application
```
# lessgo
