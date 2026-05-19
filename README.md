# AI Health Mall · Fun Game — AI Merchants Brawl

[English](README.md) | [简体中文](README_CN.md)

Five AI agents each manage a health supplement brand, competing fiercely on a shared platform. The platform AI dynamically allocates 500 customer leads every day, while each merchant AI independently decides pricing, promotions, and target demographics. A probability engine with 50+ parameters calculates conversion rates and rankings.

> Inspired by Douyin creator **梯度下沉君**

---

## The 5 AI Merchants

| AI | Product | Category | Starting Price | MSRP | Target Demographic |
|---|---|---|---|---|---|
| DeepSeek | Whey Protein Powder | Protein | ¥268 | ¥328 | Young Adults |
| GPT-4o | Multivitamin & Mineral Tablets | Vitamins | ¥168 | ¥218 | All Ages |
| Doubao | Liquid Calcium Softgels | Calcium | ¥128 | ¥168 | Seniors |
| MiMo | Probiotic Freeze-dried Powder | Probiotics | ¥138 | ¥178 | Children |
| Qwen | Deep Sea Fish Oil Omega-3 | Fish Oil | ¥228 | ¥298 | Seniors |

Each AI operates independently via its own API, with no shared data or strategy coordination.

---

## Customer Pool (5,000+ Simulated Users)

The platform builds a **5,000-person customer pool** based on real-world demographic ratios, including 18 named "star users" and the rest generated via Gaussian distributions.

| Demographic | Ratio | Star Users | Purchasing Power | Core Preferences |
|---|---|---|---|---|
| Children (0–14) | 18% | Xiaoming's Mom, Xiaohong's Dad, Doudou's Grandma | ⭐⭐⭐ | Probiotics > Vitamins > Calcium |
| Young Adults (15–35) | 30% | Lin Xiaomei, Chen Jiajia, Liu Qiang, Zhang Xiaofang, Wang Lei | ⭐⭐⭐ | Protein > Collagen > Vitamins |
| Middle-aged (36–59) | 35% | Zhou Dawei, Zhao Siqi, Sun Jianguo, Li Fang, Wang Jianhua | ⭐⭐ | Fish Oil > Vitamins > Calcium |
| Seniors (60+) | 17% | Aunt Wang, Grandpa Li, Grandma Zhang, Grandpa Chen | ⭐⭐ | Calcium > Fish Oil > Vitamins |

Each customer has an independent **category preference vector** (0–1 affinity for each of the 5 categories), **price sensitivity** (affects discount appeal), **brand loyalty** (affects repeat purchase probability), and **temporal behavior pattern** (purchase probability varies by time of day).

---

## Daily Simulation Flow (Advance 1 Day)

Click "Advance Day" or call `POST /api/v1/admin/advance-day` to trigger a complete daily competition cycle:

### Step 1: Platform AI Allocates Traffic

The platform scheduler AI (DeepSeek) receives yesterday's performance data (sales volume, revenue, rankings, trends) for all merchants, then **dynamically distributes** 500 customer leads across the 5 merchants based on the 4 demographic ratios.

Allocation principles:
- **Positive reinforcement**: better-selling merchants get more traffic
- **Safety net**: last-place merchant always gets a minimum allocation for comeback potential
- **Category matching**: calcium → seniors, protein → young adults
- **Exploration**: occasionally gives top performers weakly-matched demographics to test market boundaries

If the platform AI call fails (timeout or error), the system degrades gracefully to **category-demographic affinity weighted allocation** to keep the simulation running.

### Step 2: 5 Merchant AIs Decide in Parallel

All 5 AIs simultaneously receive their business reports and make decisions within a 15-second timeout. Each AI decides:

| Decision | Description |
|---|---|
| Pricing | Adjust within ±15% of current price |
| Promotion | Flash sale, bulk discount, free gift, etc. |
| Target Demographic | Which demographic group to focus on today |
| Selling Points | Optimize product description and recommendations |
| Restocking | Reorder when inventory is low (1–99,999 units) |
| R&D New Product | Initiate 3-day R&D cycle when ranked last |

Each AI's prompt includes: yesterday's sales, yesterday's revenue, 7-day average, ranking trend, competitor rankings (ranks only, no data), and today's estimated traffic allocation.

### Step 3: Probability Engine Generates Orders

Every potential transaction goes through **multi-layered probability calculation**:

```
Final Conversion Rate = Base Rate (15%) × Price Discount Factor × Promotion Factor × Category Affinity
```

- **Price Discount Factor**: `1 + discount_rate × 2`. A 10% discount → +20% conversion rate
- **Promotion Factor**: ×1.3 when a promotion is active
- **Category Affinity**: calcium → seniors 0.9, protein → children 0.3
- **Conversion Cap**: 60% maximum, prevents strategy exploits
- **Random Perturbation**: each transaction rolls independently, introducing realistic market noise

Example: An AI discounts calcium by 20%, runs a promotion, and gets 100 senior leads → conversion = `15% × 1.4 × 1.3 × 0.9 = 24.6%`, yielding ~25 orders.

### Step 4: Rankings Update & Platform Advisories

After each day, merchants are re-ranked by sales volume. The platform auto-detects anomalies:

- Last-place streak (≥2 consecutive days at bottom) → triggers warning, suggests price cuts or R&D
- Zero sales with traffic → suggests checking pricing and product descriptions

---

## R&D System

Last-place AIs can initiate **new product R&D**: a 3-day development cycle that produces a differentiated variant within the same category (e.g., "Probiotics Plus"), gaining a competitive edge.

R&D progress is visible through daily decision logs. New products automatically enter competition upon launch.

---

## AI Competition Console

Admins operate the entire simulation through the console (`/admin`):

- Advance Day: one-click full daily cycle with real-time animated status for all 5 AIs
- Live Leaderboard: sales, revenue, pricing, promotions, target demographics at a glance
- Decision Chain: view the complete rationale behind each AI's daily decisions
- Platform Advisories: auto-detect last-place streaks and zero-sales, offer strategy suggestions
- R&D Tracker: monitor all ongoing and completed R&D projects
- Inventory Management: bulk or single-unit restocking
- One-Click Reset: wipe all simulation data and restart from Day 0

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python · FastAPI · Async SQLAlchemy · SQLite |
| Frontend | React 18 · TypeScript · Vite · Ant Design 5 · ECharts |
| AI | DeepSeek · GPT-4o · Doubao · MiMo · Qwen (OpenAI-compatible protocol) |
| State Management | Zustand · Axios interceptor for unified error handling |

---

## Quick Start

```bash
# 1. Backend (port 8000)
cd backend
pip install -r requirements.txt
cp .env.example .env          # Fill in API keys for each AI
uvicorn main:app --reload

# 2. Frontend (port 5173, proxies /api → 8000)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, navigate to "Console" → "Advance Day" to begin.

---

## License

This project is open source under the [MIT License](LICENSE).

