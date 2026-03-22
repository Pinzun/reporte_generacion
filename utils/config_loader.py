import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent / "config.json"

_cfg: dict | None = None


def get_config() -> dict:
    global _cfg
    if _cfg is None:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _cfg = json.load(f)
    return _cfg
