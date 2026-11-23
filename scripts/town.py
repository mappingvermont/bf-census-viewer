"""Per-town settings and paths, read from <town>/town.json.

Every script takes the town folder name (e.g. `bellows-falls`, `winooski`) as its first argument and is
run from the repo root:  python3 -I scripts/build_csv.py winooski
"""
import json
import os
from types import SimpleNamespace

import schedules

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Where things sit on a FamilySearch 1900 scan, as fractions of page height (y) or width (x): the centres of
# lines 1 and 50, how many extra lines each tile band takes in above and below, where the left (L) tiles end
# and the right (R) tiles start, the street column, and the number + name columns used for the N tiles.
# A town's town.json can override any of these.
DEFAULT_LAYOUT = {"line1": 0.269, "line50": 0.961, "overlap": 1,
                  "left_x1": 0.67, "right_x0": 0.63, "street_x": [0.04, 0.075], "names_x": [0.06, 0.40]}


def load(name):
    root = os.path.join(REPO, name)
    path = os.path.join(root, "town.json")
    if not os.path.exists(path):
        towns = sorted(d for d in os.listdir(REPO) if os.path.exists(os.path.join(REPO, d, "town.json")))
        raise SystemExit(f"no town.json in {root}; towns: {', '.join(towns)}")
    with open(path) as f:
        cfg = json.load(f)
    data = os.path.join(root, "data")
    year = cfg.get("year", 1900)
    return SimpleNamespace(
        **{k: v for k, v in cfg.items() if k not in ("layout", "examples", "year")},
        year=year,
        schedule=schedules.get(year),
        layout={**DEFAULT_LAYOUT, **cfg.get("layout", {})},
        root=root,
        img=os.path.join(data, "img"),
        transcribed=os.path.join(data, "transcribed"),
        output=os.path.join(data, "output"),
        site_data=os.path.join(root, "site", "data"),
        examples=[os.path.join(REPO, p) for p in cfg["examples"]],
    )
