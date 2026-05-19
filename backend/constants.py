"""共享常量 — 避免在多个模块间重复定义"""

# 品类对人群的天然吸引力（0-1）
CATEGORY_DEMO_AFFINITY: dict[str, dict[str, float]] = {
    "蛋白粉": {"child": 0.3, "youth": 0.8, "middle": 0.6, "elderly": 0.4},
    "维生素": {"child": 0.6, "youth": 0.5, "middle": 0.7, "elderly": 0.8},
    "钙片":   {"child": 0.7, "youth": 0.3, "middle": 0.6, "elderly": 0.9},
    "益生菌": {"child": 0.6, "youth": 0.7, "middle": 0.5, "elderly": 0.4},
    "鱼油":   {"child": 0.3, "youth": 0.4, "middle": 0.7, "elderly": 0.8},
    "胶原蛋白": {"child": 0.1, "youth": 0.8, "middle": 0.7, "elderly": 0.3},
    "褪黑素": {"child": 0.1, "youth": 0.6, "middle": 0.7, "elderly": 0.5},
    "枸杞":   {"child": 0.2, "youth": 0.3, "middle": 0.7, "elderly": 0.9},
}

# 真实人口比例基准
DEMOGRAPHIC_RATIO: dict[str, float] = {
    "child": 0.18,
    "youth": 0.30,
    "middle": 0.35,
    "elderly": 0.17,
}

# AI Provider API Key 映射
API_KEY_MAP: dict[str, str] = {
    "GLM":      "DEEPSEEK_API_KEY",
    "gpt":      "GPT_API_KEY",
    "MiniMax":  "DOUBAO_API_KEY",
    "Kimi":     "DEEPSEEK_API_KEY",
    "qwen":     "QWEN_API_KEY",
}
