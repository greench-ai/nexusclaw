"""
NexusClaw config — simple provider-based config like OpenClaw.
No LiteLLM. Direct provider API calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


@dataclass
class ProviderConfig:
    """A provider with API credentials and available models."""
    name: str
    api_key: str | None = None
    base_url: str | None = None
    api_mode: str = "openai-chat"  # openai-chat | anthropic-chat | auto-detect
    models: list[str] = field(default_factory=list)
    enabled: bool = True


class NexusClawConfig(BaseModel):
    version: str = "1.0.0"
    default_provider: str = "ollama"
    default_model: str = "ollama/llama3"
    providers: dict[str, ProviderConfig] = field(default_factory=dict)

    def get_provider_for_model(self, model: str) -> ProviderConfig | None:
        """Find the provider that owns a model."""
        prefix = model.split("/")[0] if "/" in model else model
        return self.providers.get(prefix)

    def model_list(self) -> list[str]:
        """All configured models."""
        models = []
        for provider in self.providers.values():
            if provider.enabled:
                models.extend(provider.models)
        return models


def load_config(path: Path) -> NexusClawConfig:
    if not path.exists():
        return NexusClawConfig()
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    # Deserialize ProviderConfig objects
    providers = {}
    for name, pdata in data.get("providers", {}).items():
        if isinstance(pdata, dict):
            pdata = dict(pdata)
            pdata.pop("name", None)  # avoid duplicate 'name' kwarg
            providers[name] = ProviderConfig(name=name, **pdata)
        else:
            providers[name] = pdata
    data["providers"] = providers
    return NexusClawConfig(**data)


def save_config(config: NexusClawConfig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Serialize to YAML-friendly dict (ProviderConfig → dict)
    data = config.model_dump(mode="json")
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def get_config_path() -> Path:
    return Path.home() / ".nexusclaw" / "config.yaml"
