# NSE F&O Scanner — Deployment Guide

## Current Status
- ✅ All 34 unit tests passing
- ✅ Frontend builds cleanly (Vite + TypeScript)
- ✅ Docker images ready (backend + frontend multi-stage)
- ✅ render.yaml configured for one-click Render deploy
- ✅ GitHub Actions CI/CD pipeline ready
- ❌ **Not yet deployed** — needs a GitHub repo + Render account

---

## Option 1: Render.com (Recommended — ~$21/mo, simplest)

### Step 1 — Push to GitHub
```bash
cd /path/to/nse-scanner
git remote add origin https://github.com/YOUR_USERNAME/nse-scanner.git
git push -u origin main
```

### Step 2 — Deploy on Render
1. Go to https://render.com → New → Blueprint
2. Connect your GitHub repo
3. Render reads `render.yaml` and auto-creates:
   - `nse-scanner-backend` (web service, Docker)
   - `nse-scanner-frontend` (web service, Docker)
   - `nse-scanner-db` (PostgreSQL, Starter plan)
4. Add Redis: Dashboard → New → Redis → Free plan → copy URL

### Step 3 — Set environment variables in Render dashboard
```
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY   (optional — enables AI summaries)
REDIS_URL=redis://...               (from Redis service above)
```

### Step 4 — Verify deployment
```bash
# Backend health
curl https://nse-scanner-backend.onrender.com/health

# Scanner signals
curl https://nse-scanner-backend.onrender.com/api/v1/scanner/signals

# Trigger first scan
curl -X POST https://nse-scanner-backend.onrender.com/api/v1/scanner/trigger
```

**Expected URLs:**
- Frontend: `https://nse-scanner-frontend.onrender.com`
- Backend API: `https://nse-scanner-backend.onrender.com`

---

## Option 2: Railway (~$5/mo, even cheaper)

```bash
npm install -g @railway/cli
railway login
cd /path/to/nse-scanner/backend
railway init
railway add --plugin postgresql
railway add --plugin redis
railway up
```

Then deploy frontend separately:
```bash
cd /path/to/nse-scanner/frontend
npm run build
# Deploy dist/ to Vercel (free): npx vercel --prod
```

---

## Option 3: Local Docker Compose (for testing)

```bash
cd /path/to/nse-scanner
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD and optionally ANTHROPIC_API_KEY

docker compose up -d
# Wait ~30s for services to start

# Verify
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/scanner/trigger

# Frontend at http://localhost
```

---

## GitHub Actions CI/CD Setup

Add these secrets to your GitHub repo (Settings → Secrets → Actions):

| Secret | Value |
|--------|-------|
| `RENDER_API_KEY` | From Render → Account → API Keys |
| `RENDER_BACKEND_SERVICE_ID` | From Render service URL: `srv-XXXX` |
| `RENDER_FRONTEND_SERVICE_ID` | From Render service URL: `srv-XXXX` |
| `RENDER_BACKEND_URL` | `nse-scanner-backend.onrender.com` |
| `RENDER_FRONTEND_URL` | `nse-scanner-frontend.onrender.com` |

On every push to `main`, GitHub Actions will:
1. Run 34 unit tests
2. TypeScript type-check and build frontend
3. Build and push Docker images to GHCR
4. Deploy to Render
5. Wait for health check
6. Auto-rollback if health check fails

---

## Architecture

```
Internet
    │
    ├── Frontend (nginx:alpine)     port 80
    │   └── React SPA (Vite build)
    │       └── Proxies /api/ and /ws → Backend
    │
    ├── Backend (Python 3.12)       port 8000
    │   ├── FastAPI + Uvicorn
    │   ├── APScheduler (scan every 60s)
    │   ├── WebSocket server
    │   ├── NSE data fetcher (httpx + yfinance)
    │   └── Indicator engine (pandas/numpy, deterministic)
    │
    ├── PostgreSQL 16               port 5432
    │   └── Stores quotes, indicators, signals, watchlists
    │
    └── Redis 7                     port 6379
        ├── Cache (signal data, historical OHLCV)
        └── Pub/Sub (scanner → WebSocket broadcast)
```

---

## Database Schema

Tables auto-created by SQLAlchemy on startup (`init_db()`):
- `stocks` — F&O symbol registry
- `quotes` — Live price ticks
- `candles` — OHLCV history
- `indicators` — Computed EMA/MACD/RSI/ATR/VWAP/S&R per scan
- `signals` — BUY/SELL signals with entry/SL/targets
- `watchlists` — User-defined symbol lists (JSON)

---

## Scanner Logic Summary

**Data flow (every 60s):**
1. Fetch live quotes from NSE API (httpx with cookie session)
2. Fall back to Yahoo Finance if NSE rate-limits
3. Cache 1-year historical OHLCV in Redis (TTL 1hr)
4. Compute indicators in pandas (pure math, no AI)
5. Score each symbol on 6 factors (max ±10 per factor):
   - EMA100 position (+/-2)
   - MACD crossover (+/-3) or momentum (+/-1)
   - Volume >1.5x avg (+/-2)
   - Support/resistance breakout (+/-2)
   - RSI extremes (+/-1)
   - EMA alignment (+/-1)
6. Map score → STRONG_BUY (≥7) / BUY (≥4) / NEUTRAL / SELL (≤-4) / STRONG_SELL (≤-7)
7. Generate entry, stoploss (1.5–2x ATR), targets (1.2–3x ATR)
8. Cache result in Redis, broadcast via WebSocket pub/sub

**AI usage (minimal):**
- Market summary: 1 Claude call per 15 min (cached)
- Stock detail: 1 Claude call per symbol per 10 min (cached)
- Everything else: deterministic math

---

## Monitoring

Once deployed on Render:
- Render dashboard: https://dashboard.render.com
- Backend logs: `railway logs` or Render → Service → Logs
- Health: `GET /health` returns `{"status": "ok"}`
- Metrics: `GET /api/v1/market/breadth` — real-time scanner health

---

## Backup

PostgreSQL backup (run daily via cron or Render's backup feature):
```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

Redis is ephemeral cache — no backup needed (rebuilds on restart).
