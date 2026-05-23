# 🚀 Deploy Bharat Intelligence — Free on Render.com

## One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Shivamkole1969/bharat-intelligence)

Click the button above, or follow the manual steps below.

---

## Manual Deploy Steps

### 1. Sign Up on Render
1. Go to **[render.com](https://render.com)**
2. Click **"Get Started for Free"**
3. **Sign up with GitHub** (this auto-connects your repos)

### 2. Create PostgreSQL Database
1. Click **"New +"** → **"PostgreSQL"**
2. Name: `bharat-db`
3. Plan: **Free**
4. Click **"Create Database"**
5. Copy the **Internal Database URL** (starts with `postgres://...`)

### 3. Create Web Service (Backend + Frontend)
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repo: `Shivamkole1969/bharat-intelligence`
3. Settings:
   - **Name**: `bharat-intelligence`
   - **Runtime**: **Docker**
   - **Dockerfile Path**: `./Dockerfile`
   - **Plan**: **Free**
4. Add **Environment Variables**:
   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | *(paste the Internal Database URL from step 2)* |
   | `APP_ENV` | `production` |
   | `HOST` | `0.0.0.0` |
   | `PORT` | `8000` |
   | `CORS_ORIGINS` | `*` |
   | `GROQ_API_KEYS` | *(your Groq API key — needed for AI Chat)* |
5. Click **"Create Web Service"**

### 4. Wait for Build (~5 min)
Render builds the Docker image and deploys. Once green, your app is live at:

**`https://bharat-intelligence.onrender.com`**

---

## Features Available (All Free)

✅ Search any NSE Top 500 company  
✅ Live TradingView charts, fundamentals, technicals  
✅ AI prediction meter with bullish/bearish gauge  
✅ Multi-timeframe stock ratings (1D / 1W / 1M / 3M)  
✅ 28 candlestick patterns with projected candles  
✅ Live intelligence dashboard with market clock  
✅ Bullish & bearish watchlists  
✅ AI Chat (needs Groq API key)  
✅ 3D market map  
✅ Audit trail  
✅ User Guide (📖 button in navbar)  

## Free Tier Notes

- Backend **spins down** after 15 min inactivity → first load takes ~30s
- PostgreSQL free for **90 days**
- No Redis needed — uses in-memory cache
