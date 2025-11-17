"""Self-check utilities for Xtremetools deployments."""
from __future__ import annotations

import time
from typing import Any

from ..alias import NODE_CLASS_MAPPINGS
from ..generator import get_structured_mode_flag
from ..node_discovery import get_last_fetch_timestamp
from ..workflow_validator import get_last_validation_passed
from ..base.node_base import XtremetoolsUtilityNode
from ..base.info import InfoFormatter


class XtremetoolsSelfCheck(XtremetoolsUtilityNode):
    CATEGORY = "🤖 Xtremetools/Diagnostics"

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status_report",)
    FUNCTION = "run_check"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:  # pragma: no cover - no inputs for diagnostics
        return {"required": {}, "optional": {}}

    def run_check(self) -> tuple[str]:
        info = InfoFormatter("Self-Check")
        node_count = len(NODE_CLASS_MAPPINGS)
        last_fetch_ts = get_last_fetch_timestamp()
        structured_active = get_structured_mode_flag()
        last_validation_passed = get_last_validation_passed()

        human_ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_fetch_ts)) if last_fetch_ts else "never"

        info.add(f"Nodes discovered: {node_count}")
        info.add(f"Last /object_info fetch: {human_ts}")
        info.add(f"Structured JSON mode active: {'yes' if structured_active else 'no'}")
        if last_validation_passed is None:
            info.add("Last export validation: unknown")
        else:
            info.add(f"Last export validation passed: {'yes' if last_validation_passed else 'no'}")

        return self.ensure_tuple(info.render())


NODE_CLASS_MAPPINGS = {
    "XtremetoolsSelfCheck": XtremetoolsSelfCheck,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XtremetoolsSelfCheck": "Diagnostics | Self-Check",
}
