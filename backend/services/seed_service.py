import json
import os
import random
from sqlalchemy import select, func
from core.database import async_session
from models.merchant import Merchant
from models.product import Product
from models.customer import Customer
from models.marketing import PurchaseSimulationConfig, SimulationState


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


async def seed_data_if_empty():
    async with async_session() as db:
        result = await db.execute(select(func.count()).select_from(Merchant))
        count = result.scalar()
        if count and count > 0:
            return

        with open(os.path.join(DATA_DIR, "seed_merchants.json"), encoding="utf-8") as f:
            merchants_data = json.load(f)
        with open(os.path.join(DATA_DIR, "seed_products.json"), encoding="utf-8") as f:
            products_data = json.load(f)
        with open(os.path.join(DATA_DIR, "seed_demographics.json"), encoding="utf-8") as f:
            customers_data = json.load(f)

        # 创建唯一的商家
        for m in merchants_data:
            db.add(Merchant(**m))
        await db.flush()

        merchant = (await db.execute(select(Merchant))).scalars().first()

        # 创建 5 个产品，每个产品绑定自己的 AI
        for p in products_data:
            db.add(Product(
                merchant_id=merchant.id,
                name=p["name"],
                description=p["description"],
                ai_model=p["ai_model"],
                target_demographic=p.get("demographic", "all"),
                category=p.get("category", ""),
                price=p["price"],
                original_price=p["original_price"],
                stock=200,
                ai_selling_points=[],
            ))
        await db.flush()

        # 创建明星用户（18个手写角色）
        for c in customers_data:
            db.add(Customer(**c, is_star=True))

        # 读取用户生成配置，批量生成统计用户
        gen_config_path = os.path.join(DATA_DIR, "user_generation_config.json")
        if os.path.exists(gen_config_path):
            with open(gen_config_path, encoding="utf-8") as f:
                gen_config = json.load(f)
            stat_users = _generate_statistical_users(gen_config, len(customers_data))
            for u in stat_users:
                db.add(Customer(**u, is_star=False))
            print(f"✅ 批量生成 {len(stat_users)} 个统计用户")

        # 购买模拟配置（新的人群分类）
        configs = [
            {"demographic": "child", "base_purchase_rate": 0.06,
             "category_preferences": {"维生素": 0.9, "钙片": 0.8, "益生菌": 0.85, "鱼油": 0.5, "蛋白粉": 0.3, "胶原蛋白": 0.2},
             "price_sensitivity": 0.3, "brand_loyalty": 0.6,
             "time_pattern": {"9": 0.7, "10": 0.9, "14": 0.8, "15": 0.9, "19": 0.6, "20": 0.4}},
            {"demographic": "youth", "base_purchase_rate": 0.08,
             "category_preferences": {"蛋白粉": 0.9, "胶原蛋白": 0.85, "维生素": 0.6, "益生菌": 0.7, "鱼油": 0.4, "钙片": 0.3},
             "price_sensitivity": 0.5, "brand_loyalty": 0.4,
             "time_pattern": {"10": 0.6, "12": 0.8, "15": 0.7, "20": 1.0, "21": 0.9, "22": 0.7}},
            {"demographic": "middle", "base_purchase_rate": 0.09,
             "category_preferences": {"鱼油": 0.9, "维生素": 0.8, "钙片": 0.7, "蛋白粉": 0.5, "胶原蛋白": 0.6, "益生菌": 0.5},
             "price_sensitivity": 0.4, "brand_loyalty": 0.6,
             "time_pattern": {"8": 0.7, "9": 0.9, "12": 0.8, "18": 0.7, "21": 0.6}},
            {"demographic": "elderly", "base_purchase_rate": 0.10,
             "category_preferences": {"钙片": 0.95, "鱼油": 0.9, "维生素": 0.85, "益生菌": 0.6, "蛋白粉": 0.4, "胶原蛋白": 0.3},
             "price_sensitivity": 0.6, "brand_loyalty": 0.7,
             "time_pattern": {"7": 0.8, "8": 1.0, "9": 1.0, "10": 0.9, "14": 0.8, "15": 0.7, "16": 0.5}},
        ]
        for cfg in configs:
            db.add(PurchaseSimulationConfig(**cfg))

        # 初始化模拟状态
        db.add(SimulationState(current_day=0, is_running=False))

        await db.commit()
        print("✅ 种子数据初始化完成（5 AI 竞争模式）")


def _generate_statistical_users(config: dict, existing_count: int) -> list[dict]:
    """按 user_generation_config.json 配置批量生成统计用户"""
    target = config["total_users"] - existing_count
    total_configured = sum(d["count"] for d in config["demographics"].values())
    rng = random.Random(config.get("random_seed", 42))

    users = []
    for demo_name, demo_cfg in config["demographics"].items():
        count = round(demo_cfg["count"] * target / total_configured)
        pw_cfg = demo_cfg["purchase_weight"]

        for _ in range(count):
            pw = rng.gauss(pw_cfg["mean"], pw_cfg["std"])
            pw = round(max(0.5, min(3.0, pw)), 2)

            prefs = {}
            for cat, dist in demo_cfg["preferences"].items():
                val = rng.gauss(dist["mean"], dist["std"])
                prefs[cat] = round(max(0.1, min(1.0, val)), 2)

            users.append({
                "name": None,
                "demographic": demo_name,
                "age_range": rng.choice(demo_cfg["age_range"]),
                "purchase_weight": pw,
                "preferences": prefs,
            })

    return users
