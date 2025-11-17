"""Environment and configuration helpers for Xtremetools."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

# Copilot: prefer explicit type hints for new helpers.

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ENV_PATH = _REPO_ROOT / ".env"


def _load_dotenv(env_path: Path) -> None:
    """Populate os.environ with key/value pairs from the .env file."""
    if not env_path.exists():  # no-op when users skip .env
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(slots=True)
class EnvironmentConfig:
    """Holds environment-derived configuration values."""

    comfyui_server_url: str = "http://localhost:8188"
    lm_studio_server_url: str = "http://localhost:1234"
    lm_studio_model: str | None = None
    supported_models_path: Path = _REPO_ROOT / "Xtremetools" / "config" / "supported_models.json"
    workflow_schema_path: Path = _REPO_ROOT / "Xtremetools" / "workflow_schema.json"

    @property
    def as_dict(self) -> dict[str, Any]:
        return {
            "comfyui_server_url": self.comfyui_server_url,
            "lm_studio_server_url": self.lm_studio_server_url,
            "lm_studio_model": self.lm_studio_model,
            "supported_models_path": str(self.supported_models_path),
            "workflow_schema_path": str(self.workflow_schema_path),
        }


@lru_cache(maxsize=1)
def get_environment_config(env_path: Path | None = None) -> EnvironmentConfig:
    """Load .env settings once and expose typed configuration."""

    _load_dotenv(env_path or _DEFAULT_ENV_PATH)

    supported_override = os.getenv("XTREMETOOLS_SUPPORTED_MODELS")
    schema_override = os.getenv("XTREMETOOLS_WORKFLOW_SCHEMA")

    supported_models_path = Path(supported_override) if supported_override else _REPO_ROOT / "Xtremetools" / "config" / "supported_models.json"
    workflow_schema_path = Path(schema_override) if schema_override else _REPO_ROOT / "Xtremetools" / "workflow_schema.json"

    return EnvironmentConfig(
        comfyui_server_url=os.getenv("COMFYUI_SERVER_URL", "http://localhost:8188"),
        lm_studio_server_url=os.getenv("LM_STUDIO_SERVER_URL", "http://localhost:1234"),
        lm_studio_model=os.getenv("LM_STUDIO_MODEL"),
        supported_models_path=supported_models_path,
        workflow_schema_path=workflow_schema_path,
    )


__all__ = ["EnvironmentConfig", "get_environment_config"]
