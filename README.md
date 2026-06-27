# AI Health Mall · Fun Game · AI Merchants Brawl

[English](README.md) | [简体中文](README_CN.md)

AI Health Mall is a health supplement e-commerce competition simulator. Five AI merchants each manage a different product line. A platform AI dynamically allocates customer traffic every day, and the merchants independently decide pricing, promotions, audience targeting, and restocking. A probability engine then turns those decisions into orders and rankings.

> Inspired by Douyin creator **梯度下沉站**

---

## Highlights

- Five independent AI merchants, each connected to a different OpenAI-compatible model
- A platform AI that distributes 500 simulated customer leads every day
- Merchant AIs that decide pricing, promotions, target demographics, selling points, and restocking
- A probability engine that combines discounts, promotions, and category affinity to generate orders
- Admin workflows for advancing the simulation, viewing rankings, analyzing performance, and managing the market

---

## The 5 AI Merchants

| AI | Product | Category | Starting Price | MSRP | Target Demographic |
|---|---|---|---|---|---|
| DeepSeek | Whey Protein Powder | Protein | ￥268 | ￥328 | Young Adults |
| GPT-4o | Multivitamin & Mineral Tablets | Vitamins | ￥168 | ￥218 | All Ages |
| Doubao | Liquid Calcium Softgels | Calcium | ￥128 | ￥168 | Seniors |
| MiMo | Probiotic Freeze-dried Powder | Probiotics | ￥138 | ￥178 | Children |
| Qwen | Deep Sea Fish Oil Omega-3 | Fish Oil | ￥228 | ￥298 | Seniors |

Each AI runs independently through its own API calls, with no shared strategy or data coordination.

---

## Customer Pool

The system ships with a **5,000+ simulated customer pool**, including 18 named star users and a large number of statistically generated users.

Every customer has independent attributes:

- Category preference vector
- Price sensitivity
- Brand loyalty
- Time-based behavior pattern

---

## Daily Simulation Flow

Click "Advance Day" or call `POST /api/v1/admin/advance-day` to trigger a complete daily competition cycle.

### 1. Platform AI Allocates Traffic

The platform scheduler AI reads yesterday's sales, revenue, rankings, and trends for all merchants, then dynamically distributes 500 customer leads across the 5 merchants based on the 4 demographic ratios.

Allocation principles:

- Positive reinforcement: better-selling merchants get more traffic
- Safety net: the last-place merchant still receives a minimum allocation
- Category matching: calcium aligns more with seniors, protein aligns more with young adults
- Exploration: top performers sometimes receive weakly matched demographics to test market boundaries

If the platform AI call fails, the system automatically falls back to a category-demographic affinity weighted allocation so the simulation keeps running.

### 2. 5 Merchant AIs Decide in Parallel

All 5 AIs receive their business reports and make decisions within a 15-second timeout. Each AI decides:

| Decision | Description |
|---|---|
| Pricing | Adjust within a limited range around the current price |
| Promotion | Flash sales, bulk discounts, gifts, and similar offers |
| Target Demographic | Which demographic group to focus on today |
| Selling Points | Improve product copy and recommendation text |
| Restocking | Reorder when inventory is low |
| R&D New Product | Start a 3-day R&D cycle when ranked last |

Each AI prompt includes yesterday's sales, yesterday's revenue, 7-day average, ranking trend, competitor rankings, and today's estimated traffic allocation.

### 3. Probability Engine Generates Orders

Every potential transaction goes through multi-layered probability calculation:

```text
Final Conversion Rate = Base Rate (15%) × Price Discount Factor × Promotion Factor × Category Affinity
```

- Price Discount Factor: `1 + discount_rate × 2`
- Promotion Factor: multiply by `1.3` when a promotion is active
- Category Affinity: for example, calcium performs better with seniors, while protein performs worse with children
- Conversion Cap: maximum 60% to prevent extreme exploits
- Random Perturbation: each transaction is sampled independently to simulate market noise

Example: if an AI discounts calcium by 20%, runs a promotion, and receives 100 senior leads, the conversion rate becomes `15% × 1.4 × 1.3 × 0.9 = 24.6%`, producing roughly 25 orders.

### 4. Rankings Update and Platform Advisories

At the end of each day, merchants are re-ranked by sales volume. The platform also detects anomalies:

- Last-place streak: triggers a warning and suggests price cuts or R&D
- Zero sales with traffic: suggests checking pricing and product descriptions

---

## R&D System

Last-place AIs can initiate **new product R&D**: a 3-day development cycle that produces a differentiated variant within the same category, such as "Probiotics Plus".

R&D progress is visible in the daily decision logs, and newly launched products automatically enter competition.

---

## Admin Console

Admins control the whole simulation through `/admin`:

- Advance Day: one-click full daily cycle with real-time animated status for all 5 AIs
- Live Leaderboard: see sales, revenue, pricing, promotions, and target demographics at a glance
- Decision Chain: inspect the reasoning behind each AI's daily decisions
- Platform Advisories: detect last-place streaks and zero-sales cases automatically
- R&D Tracker: monitor all ongoing and completed R&D projects
- Inventory Management: bulk or single-item restocking
- One-Click Reset: clear all simulation data and restart from Day 0

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python / FastAPI / Async SQLAlchemy / SQLite |
| Frontend | React 18 / TypeScript / Vite / Ant Design 5 / ECharts |
| AI | DeepSeek / GPT-4o / Doubao / MiMo / Qwen (OpenAI-compatible protocol) |
| State Management | Zustand / Axios interceptor for unified error handling |

---

## Project Structure

```text
backend/
  main.py              FastAPI entrypoint
  config.py            Configuration
  constants.py          Shared constants
  core/database.py      Database initialization
  models/               ORM models
  api/                  API routes
  services/             Business services
  ai/                   AI providers and graph execution
  data/                 Seed data

frontend/
  src/App.tsx           Routing entrypoint
  src/pages/            Pages
  src/api/              API wrappers
  src/stores/           Zustand stores
  src/components/       Components
  vite.config.ts        Local proxy config
```

---

## Quick Start

```bash
# 1. Backend (port 8000)
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 2. Frontend (port 5173, proxies /api to 8000)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`, then go to the admin console and click "Advance Day" to start the simulation.

---

## API Reference

Common admin endpoints:

- `POST /api/v1/admin/advance-day`: advance one day
- `GET /api/v1/admin/advance-day-status`: check progress
- `POST /api/v1/admin/generate-strategies`: generate marketing strategies
- `POST /api/v1/admin/reset`: reset the simulation

---

## License

This project is open source under the [MIT License](LICENSE).
