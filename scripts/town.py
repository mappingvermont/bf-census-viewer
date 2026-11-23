"""Per-town settings and paths, read from <town>/town.json.

Every script takes the town folder name (e.g. `bellows-falls`, `winooski`) as its first argument and is
run from the repo root:  python3 -I scripts/build_csv.py winooski
"""
import json
import os
from types import SimpleNamespace

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Fractions of page height for the centres of lines 1 and 50, measured on FamilySearch 1900 scans, and how
# many extra lines each tile band takes in above and below. A town's town.json can override any of these.
DEFAULT_LAYOUT = {"line1": 0.269, "line50": 0.961, "overlap": 1}


def load(name):
    root = os.path.join(REPO, name)
    path = os.path.join(root, "town.json")
    if not os.path.exists(path):
        towns = sorted(d for d in os.listdir(REPO) if os.path.exists(os.path.join(REPO, d, "town.json")))
        raise SystemExit(f"no town.json in {root}; towns: {', '.join(towns)}")
    with open(path) as f:
        cfg = json.load(f)
    data = os.path.join(root, "data")
    return SimpleNamespace(
        **{k: v for k, v in cfg.items() if k not in ("layout", "examples")},
        layout={**DEFAULT_LAYOUT, **cfg.get("layout", {})},
        root=root,
        img=os.path.join(data, "img"),
        transcribed=os.path.join(data, "transcribed"),
        output=os.path.join(data, "output"),
        site_data=os.path.join(root, "site", "data"),
        examples=[os.path.join(REPO, p) for p in cfg["examples"]],
    )
