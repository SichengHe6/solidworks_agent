from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


@dataclass(frozen=True)
class ModelRoute:
    provider: str
    match_prefixes: tuple[str, ...]
    base_url: str
    api_key_env: str


MODEL_ROUTE_TABLE: tuple[ModelRoute, ...] = (
    ModelRoute(
        provider="gpt",
        match_prefixes=("gpt", "openai/"),
        base_url=OPENROUTER_BASE_URL,
        api_key_env="OPENROUTER_API_KEY",
    ),
    ModelRoute(
        provider="claude",
        match_prefixes=("claude", "anthropic/"),
        base_url=OPENROUTER_BASE_URL,
        api_key_env="OPENROUTER_API_KEY",
    ),
    ModelRoute(
        provider="gemini",
        match_prefixes=("gemini", "google/"),
        base_url=OPENROUTER_BASE_URL,
        api_key_env="OPENROUTER_API_KEY",
    ),
    ModelRoute(
        provider="deepseek",
        match_prefixes=("deepseek", "deepseek/"),
        base_url=DEEPSEEK_BASE_URL,
        api_key_env="DEEPSEEK_API_KEY",
    ),
    ModelRoute(
        provider="qwen",
        match_prefixes=("qwen", "qwen-", "qwen/", "qwq", "qvq"),
        base_url=DASHSCOPE_BASE_URL,
        api_key_env="DASHSCOPE_API_KEY",
    ),
)

DEFAULT_MODEL_ROUTE = ModelRoute(
    provider="openrouter",
    match_prefixes=(),
    base_url=OPENROUTER_BASE_URL,
    api_key_env="OPENROUTER_API_KEY",
)

PLANNING_MODEL_NAME = "deepseek-v4-flash"
CODING_MODEL_NAME = "deepseek-v4-flash"
IMAGE_REVIEW_MODEL_NAME = "qwen3.6-flash"

MODEL_PROFILES = {
    "planning": PLANNING_MODEL_NAME,
    "coding": CODING_MODEL_NAME,
    "image_review": IMAGE_REVIEW_MODEL_NAME,
    "requirement": PLANNING_MODEL_NAME,
    "requirement_review": PLANNING_MODEL_NAME,
    "assembly_planning": PLANNING_MODEL_NAME,
    "assembly_review": PLANNING_MODEL_NAME,
    "part_modeling_plan": PLANNING_MODEL_NAME,
    "part_code": CODING_MODEL_NAME,
    "part_code_repair": CODING_MODEL_NAME,
    "part_static_review": PLANNING_MODEL_NAME,
    "part_image_review": IMAGE_REVIEW_MODEL_NAME,
    "assembly_modeling_plan": PLANNING_MODEL_NAME,
    "assembly_code": CODING_MODEL_NAME,
    "assembly_code_repair": CODING_MODEL_NAME,
}

MODEL_PROFILE_LABELS = {
    "planning": "通用规划默认",
    "coding": "通用编码默认",
    "image_review": "通用图像审查默认",
    "requirement": "需求补全",
    "requirement_review": "需求评审",
    "assembly_planning": "装配协议规划",
    "assembly_review": "装配协议评审",
    "part_modeling_plan": "零件建模思路",
    "part_code": "零件代码生成",
    "part_code_repair": "零件代码返修",
    "part_static_review": "零件静态评审",
    "part_image_review": "零件图像审查",
    "assembly_modeling_plan": "装配建模思路",
    "assembly_code": "装配代码生成",
    "assembly_code_repair": "装配代码返修",
}

MODEL_PROFILE_ORDER = tuple(MODEL_PROFILE_LABELS)

USE_LEGACY_KNOWLEDGE_BASE = os.getenv("MULTI_AGENT_USE_LEGACY_KB", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

AGENT_OUTPUT_ROOT = Path(r"D:\a_src\python\sw_agent\agent_output")
KNOWLEDGE_BASE_ROOT = PACKAGE_ROOT / "knowledge_base"
SKILLS_ROOT = PACKAGE_ROOT / "skills"
STANDARD_LIBRARY_ROOT = PACKAGE_ROOT / "standard_library"


_clients: dict[tuple[str, str, str], OpenAI] = {}
_client_lock = threading.Lock()


def get_model_name(profile: str = "planning") -> str:
    """Return the model configured for a logical agent profile."""
    return MODEL_PROFILES.get(profile, MODEL_PROFILES["planning"])


def infer_model_route(model_name: str) -> ModelRoute:
    """Infer provider route from an official or OpenRouter-style model name."""
    normalized = str(model_name or "").strip().lower()
    for route in MODEL_ROUTE_TABLE:
        if any(normalized.startswith(prefix) for prefix in route.match_prefixes):
            return route
    return DEFAULT_MODEL_ROUTE


def get_model_client_config(profile: str = "planning") -> dict[str, str]:
    """Resolve model, base_url and API key for a logical agent profile."""
    model_name = get_model_name(profile)
    route = infer_model_route(model_name)
    api_key = os.getenv(route.api_key_env) or "your-api-key"
    return {
        "profile": profile,
        "model": model_name,
        "provider": route.provider,
        "base_url": route.base_url,
        "api_key_env": route.api_key_env,
        "api_key_source": route.api_key_env if api_key != "your-api-key" else "missing",
        "api_key": api_key,
    }


def ensure_model_profile_ready(profile: str = "planning") -> dict[str, str]:
    """Validate that a logical profile has enough config to make an API request."""
    config = get_model_client_config(profile)
    if config["api_key"] == "your-api-key":
        raise RuntimeError(
            f"模型配置缺少 API Key：profile={profile}, model={config['model']}, "
            f"provider={config['provider']}, base_url={config['base_url']}。"
            f"请设置 {config['api_key_env']}。"
        )
    return config


def get_client(profile: str = "planning"):
    """Return the shared LLM client configured for a logical agent profile."""
    config = ensure_model_profile_ready(profile)
    cache_key = (profile, config["base_url"], config["api_key_env"])
    if cache_key in _clients:
        return _clients[cache_key]

    with _client_lock:
        if cache_key in _clients:
            return _clients[cache_key]

        if OpenAI is None:
            raise RuntimeError(
                "缺少 `openai` 依赖，无法初始化多智能体模型客户端。"
                "请先安装 openai 包后再运行 multi_agent_src_v3。"
            )

        _clients[cache_key] = OpenAI(
            base_url=config["base_url"],
            api_key=config["api_key"],
        )

    return _clients[cache_key]
