# AI Health Mall | Fun Game | AI Merchants Brawl

[English](README.md) | [简体中文](README_CN.md)

AI Health Mall is a health supplement e-commerce competition simulator. Five AI merchants each manage a different product line. A platform AI dynamically allocates customer traffic every day, and the merchants independently decide pricing, promotions, audience targeting, and restocking. A probability engine then turns those decisions into orders and rankings.

## Highlights

- Five independent AI merchants, each connected to a different OpenAI-compatible model
- A platform AI that distributes 500 simulated customer leads every day
- Merchant AIs that decide pricing, promotions, target demographics, selling points, and restocking
- A probability engine that combines discounts, promotions, and category affinity to generate orders
- Admin workflows for advancing the simulation, viewing rankings, analyzing performance, and managing the market

## The 5 AI Merchants

| AI | Product | Category | Starting Price | MSRP | Target Demographic |
|---|---|---|---|---|---|
| DeepSeek | Whey Protein Powder | Protein | ¥168 | ¥228 | Young Adults |
| GPT-4o | Multivitamin & Mineral Tablets | Vitamins | ¥168 | ¥218 | All Ages |
| Doubao | Liquid Calcium Softgels | Calcium | ¥128 | ¥168 | Seniors |
| MiMo | Probiotic Freeze-dried Powder | Probiotics | ¥138 | ¥178 | Children |
| Qwen | Deep Sea Fish Oil Omega-3 | Fish Oil | ¥128 | ¥198 | Seniors |

Each AI runs independently through its own API calls, with no shared strategy or data coordination.

## Customer Pool

The system ships with a 5,000+ simulated customer pool, including 18 named star users and a large number of statistically generated users.

Each customer has independent attributes:

- Category preference vector
- Price sensitivity
- Brand loyalty
- Time-based behavior pattern

## Daily Simulation Flow

Click "Advance Day" or call `POST /api/v1/admin/advance-day` to trigger a complete daily competition cycle.

1. Platform AI allocates traffic based on merchant performance and demographic ratios.
2. Five merchant AIs make pricing, promotion, targeting, selling-point, and restocking decisions in parallel.
3. A probability engine converts those decisions into orders.
4. Rankings and platform advisories update at the end of the day.

## Admin Console

Admins can:

- Advance the simulation day by day
- View rankings, pricing, promotions, and targeting at a glance
- Inspect AI decision logs
- Review platform advisories
- Track R&D projects
- Manage inventory
- Reset the whole simulation

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python / FastAPI / Async SQLAlchemy / SQLite |
| Frontend | Vue 3 / TypeScript / Vite / Ant Design Vue / ECharts |
| AI | DeepSeek / GPT-4o / Doubao / MiMo / Qwen (OpenAI-compatible protocol) |
| State Management | Pinia / Axios interceptor for unified error handling |

## Project Structure

```text
backend/
  main.py              FastAPI entrypoint
  config.py            Configuration
  constants.py         Shared constants
  core/database.py     Database initialization
  models/              ORM models
  api/                 API routes
  services/            Business services
  ai/                  AI providers and graph execution
  data/                Seed data

frontend/
  src/App.vue          Application entrypoint
  src/pages/           Pages
  src/api/             API wrappers
  src/stores/          Pinia stores
  src/components/      Components
  src/router/          Vue Router
  vite.config.ts       Local proxy config
```

## Quick Start

```bash
# 1. Backend (port 8000)
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 2. Frontend (port 5174, proxies /api to 8000)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5174`, then go to the admin console and click "Advance Day" to start the simulation.

## API Reference

Common admin endpoints:

- `POST /api/v1/admin/advance-day`: advance one day
- `GET /api/v1/admin/advance-day-status`: check progress
- `POST /api/v1/admin/generate-strategies`: generate marketing strategies
- `POST /api/v1/admin/reset`: reset the simulation

## License

This project is open source under the [MIT License](LICENSE).
