"""CLI helper to refresh the Xtremetools type registry."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Xtremetools" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from comfyui_xtremetools.node_discovery import refresh_types_command


def main() -> None:
    summary = refresh_types_command()
    print(summary)


if __name__ == "__main__":
    main()
