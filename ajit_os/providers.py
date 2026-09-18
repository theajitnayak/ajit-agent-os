"""OpenAI-compatible chat clients, standard library only.

Every provider below exposes the same `/chat/completions` shape, so one client
reaches all of them. Base URLs were checked against vendor documentation on
2026-09-19. Vendors move endpoints, so `ajit_os.providers --check` reprints them
and `custom` lets you supply your own without editing this file.

Only the message text you pass is sent. This module never reads your files,
environment or history beyond the single API key it needs.
"""
import json
import os
import urllib.error
import urllib.request

#: base_url values verified against vendor docs on 2026-09-19.
PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "key_env": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-flash",
        "weights": "MIT licensed open weights",
        "note": "Free signup credit has been offered; confirm current terms before relying on it.",
    },
    "dashscope": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "key_env": "DASHSCOPE_API_KEY",
        "default_model": "qwen-plus",
        "weights": "Qwen ships Apache-2.0 checkpoints; larger models use a separate licence",
        "note": "Alibaba runs separate international regions. Check your region's host in the Model Studio docs.",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "key_env": "ZHIPU_API_KEY",
        "default_model": "glm-4-flash",
        "weights": "GLM publishes open weights under its own permissive licence",
        "note": "Some GLM Flash tiers have been offered at no cost; confirm before depending on it.",
    },
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "key_env": "SILICONFLOW_API_KEY",
        "default_model": "Qwen/Qwen2.5-7B-Instruct",
        "weights": "Hosts many open-weight models from several labs",
        "note": "Useful for comparing several open models through one key.",
    },
    "minimax": {
        "base_url": "https://api.minimax.chat/v1",
        "key_env": "MINIMAX_API_KEY",
        "default_model": "abab6.5s-chat",
        "weights": "Mixed; check the specific model",
        "note": "",
    },
    "volcengine": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "key_env": "ARK_API_KEY",
        "default_model": "",
        "weights": "Hosts Doubao and third-party open models",
        "note": "Model names are endpoint ids you create in the console.",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "default_model": "",
        "weights": "Router across many providers",
        "note": "Carries free-tier variants of several open models, usually rate limited.",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "key_env": "",
        "default_model": "qwen2.5:7b",
        "weights": "Whatever you pull locally",
        "note": "Fully offline and free. No key needed. Start with `ollama serve`.",
    },
    "custom": {
        "base_url": "",
        "key_env": "AJIT_OS_API_KEY",
        "default_model": "",
        "weights": "Unknown",
        "note": "Set AJIT_OS_BASE_URL to any OpenAI-compatible endpoint.",
    },
}


class ProviderError(RuntimeError):
    """A provider could not be reached or replied in an unusable shape."""


def resolve(provider, model=None, base_url=None, api_key=None):
    """Turn a provider name plus overrides into concrete connection settings."""
    if provider not in PROVIDERS:
        raise ProviderError(f"Unknown provider {provider!r}. Known: {', '.join(sorted(PROVIDERS))}")
    config = PROVIDERS[provider]
    resolved_url = base_url or os.environ.get("AJIT_OS_BASE_URL") or config["base_url"]
    if not resolved_url:
        raise ProviderError(f"No base_url for {provider!r}. Pass base_url or set AJIT_OS_BASE_URL.")
    key_env = config["key_env"]
    resolved_key = api_key or (os.environ.get(key_env) if key_env else "")
    if key_env and not resolved_key:
        raise ProviderError(f"Set {key_env} to use {provider!r}.")
    resolved_model = model or config["default_model"]
    if not resolved_model:
        raise ProviderError(f"No default model for {provider!r}. Pass model explicitly.")
    return {"base_url": resolved_url.rstrip("/"), "api_key": resolved_key, "model": resolved_model}


def chat(prompt, provider="ollama", model=None, base_url=None, api_key=None,
         timeout=60, temperature=0.0, opener=None):
    """Send one prompt and return the reply text.

    `opener` is injected in tests so the suite never touches the network.
    """
    settings = resolve(provider, model, base_url, api_key)
    body = json.dumps({
        "model": settings["model"],
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if settings["api_key"]:
        headers["Authorization"] = f"Bearer {settings['api_key']}"
    request = urllib.request.Request(
        settings["base_url"] + "/chat/completions", data=body, headers=headers, method="POST")
    send = opener or urllib.request.urlopen
    try:
        with send(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ProviderError(f"{provider} returned HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ProviderError(f"Could not reach {provider}: {exc}") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ProviderError(f"{provider} returned a non-JSON body") from None
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise ProviderError(f"{provider} returned no message content") from None


def describe():
    """Human-readable provider table."""
    rows = ["Provider      Base URL", "-" * 72]
    for name in sorted(PROVIDERS):
        config = PROVIDERS[name]
        rows.append(f"{name:<13} {config['base_url'] or '(set AJIT_OS_BASE_URL)'}")
        key_env = config["key_env"] or "(none)"
        rows.append(f"{'':<13} key env: {key_env}   weights: {config['weights']}")
        if config["note"]:
            rows.append(f"{'':<13} {config['note']}")
    rows.append("")
    rows.append("Endpoints verified 2026-09-19. Confirm pricing and free tiers with the vendor.")
    return "\n".join(rows)


if __name__ == "__main__":
    print(describe())
