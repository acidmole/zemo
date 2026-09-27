"""Hand-traced board definition; generates backend/app/data/board.json.

Every coordinate is a pixel in frontend/public/board.webp (see build_board.py).
The data was traced from the original board: straight hallways sit on a
22 x 13 grid, the diagonal corridors and striped belts were measured along
their centerlines, and doors were located from the red hatches in the art.

Usage (from the repo root):
    python tools/board_trace.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "backend" / "app" / "data" / "board.json"

IMAGE = {"src": "/board.webp", "width": 2874, "height": 2199}

# --- Straight hallways: a regular grid ------------------------------------

GRID_X0, GRID_Y0 = 322.0, 318.0
PITCH_X, PITCH_Y = 107.9, 108.5
SQUARE = 104  # drawn size, slightly smaller than the pitch


def _run(axis: str, fixed: int, start: int, end: int) -> list[tuple[int, int]]:
    if axis == "row":
        return [(c, fixed) for c in range(start, end + 1)]
    return [(fixed, r) for r in range(start, end + 1)]


# Runs overlap where corridors cross; dict.fromkeys drops the repeats
GRID_CELLS: list[tuple[int, int]] = list(dict.fromkeys([
    *_run("row", 0, 3, 9), *_run("row", 0, 12, 19),     # top corridor, split by Control Room
    *_run("col", 0, 1, 10),                             # left corridor
    *_run("col", 3, 1, 5),                              # upper-left inner corridor
    *_run("row", 6, 0, 8), *_run("row", 6, 12, 21),     # middle corridor, split by the pod
    *_run("col", 18, 1, 3), *_run("col", 18, 7, 12),    # right inner corridor
    *_run("row", 3, 19, 21),
    (21, 1), (21, 2), *_run("col", 21, 4, 5), *_run("col", 21, 7, 10),  # right corridor
    (1, 9), (2, 9), *_run("col", 3, 9, 11),             # lower-left inner corridor
    *_run("row", 12, 2, 9), *_run("row", 12, 12, 18),   # bottom corridor, split by the Airlock
]))

# The first bottom-row square is stretched where it meets Code Room 2
GRID_OVERRIDES: dict[tuple[int, int], dict] = {
    (2, 12): {"x": 520, "w": 136},
}


def grid_id(c: int, r: int) -> str:
    return f"h_{c}_{r}"


# --- Diagonal corridors: squares along a measured centerline ---------------

def _along(p0: tuple[float, float], angle_deg: float, spans: list[tuple[float, float]],
           width: float = 104) -> list[dict]:
    """Rectangles centred between successive dividers, measured as distance along the centerline."""
    dx, dy = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    out = []
    for s0, s1 in spans:
        s = (s0 + s1) / 2
        out.append({"x": round(p0[0] + dx * s), "y": round(p0[1] + dy * s),
                    "w": round(s1 - s0 - 4), "h": width, "angle": round(angle_deg, 1)})
    return out


# name -> (squares from the pod end outwards, tags)
CORRIDORS: dict[str, tuple[list[dict], list[str]]] = {
    # Pod ring -> top corridor
    "ne": (_along((1557, 857), -58.8, [(24, 160), (160, 268), (268, 376), (376, 484), (484, 556)]), []),
    # Branch off ne_3, between the Brig (above) and the Armory (below)
    "brig": (_along((1711, 573), 28.8, [(66, 168), (168, 280), (280, 376)]), []),
    # Pod ring -> bottom corridor
    "sw": (_along((1366, 1112), 131.0, [(26, 118), (118, 224), (224, 332), (332, 440), (440, 580)]), []),
    # Striped belts: three segments each, split by the purple bars
    "nwbelt": (_along((1340, 820), -107.9, [(0, 133), (133, 345), (345, 473)], 112), ["striped_belt"]),
    "sebelt": (_along((1555, 1100), 70.5, [(0, 131), (131, 351), (351, 494)], 112), ["striped_belt"]),
}

# --- Escape Pod ring: six sectors around the pod --------------------------

POD_CENTER = (1438, 970)
POD_RADIUS = 98
RING_OUTER = 187
# (id, from_deg, to_deg, tags); screen angles, 0 = east, clockwise
RING = [
    ("ring_nw", -142, -100, []),
    ("ring_ne", -100, -24, []),
    ("ring_e", -24, 40, ["x_ray"]),
    ("ring_se", 40, 97, []),
    ("ring_sw", 97, 138, []),
    ("ring_w", 138, 218, ["x_ray"]),
]
# Rules: "you can enter it from any of the four surrounding spaces"
POD_APPROACHES = ["ring_nw", "ring_ne", "ring_se", "ring_sw"]


def _sector(a0: float, a1: float) -> list[list[int]]:
    pts = []
    steps = max(4, int(abs(a1 - a0) / 6))
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        pts.append([round(POD_CENTER[0] + RING_OUTER * math.cos(a)),
                    round(POD_CENTER[1] + RING_OUTER * math.sin(a))])
    for i in range(steps, -1, -1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        pts.append([round(POD_CENTER[0] + POD_RADIUS * math.cos(a)),
                    round(POD_CENTER[1] + POD_RADIUS * math.sin(a))])
    return pts


# --- Rooms -----------------------------------------------------------------

# id -> (name, type, x, y, radius). x, y is the most open floor spot, used for
# tokens; the circle is the highlight and click area.
ROOMS: dict[str, tuple[str | None, str, int, int, int]] = {
    "1": (None, "room", 469, 465, 54),
    "2": (None, "room", 500, 680, 46),
    "3": (None, "room", 457, 833, 59),
    "4": (None, "room", 700, 222, 41),
    "5": (None, "room", 908, 448, 70),
    "6": (None, "room", 800, 625, 70),
    "7": ("Reactor Room", "room", 800, 835, 60),
    "8": (None, "room", 969, 805, 40),
    "9": (None, "room", 1153, 662, 70),
    "10": (None, "room", 1432, 563, 60),
    "11": ("Security", "room", 2034, 488, 60),
    "12": (None, "room", 2421, 482, 62),
    "13": ("The Brig", "room", 1969, 595, 45),
    "14": (None, "room", 2356, 787, 53),
    "15": (None, "room", 2213, 855, 56),
    "16": (None, "room", 1738, 861, 41),
    "17": ("The Armory", "room", 1794, 773, 40),
    "18": (None, "room", 2135, 1065, 50),
    "19": (None, "room", 2433, 1084, 59),
    "20": (None, "room", 2417, 1200, 52),
    "21": ("Vending Machines", "room", 2445, 1386, 43),
    "22": ("Lavatory", "room", 2375, 1610, 45),
    "23": ("Lost and Found", "room", 2000, 1485, 50),
    "24": (None, "room", 1870, 1144, 80),
    "25": ("Casino", "room", 1424, 1261, 70),
    "26": ("The Zemo Zoo", "room", 1145, 1148, 63),
    "27": (None, "room", 837, 1176, 70),
    "28": (None, "room", 810, 1450, 60),
    "29": ("Kitchen", "room", 485, 1460, 60),
    "30": (None, "room", 611, 1161, 60),
    "31": (None, "room", 465, 1095, 60),
    "32": ("Command Control", "room", 1442, 301, 125),
    "code_room_1": ("Code Room 1", "code_room", 324, 311, 124),
    "code_room_2": ("Code Room 2", "code_room", 325, 1612, 124),
    "code_room_3": ("Code Room 3", "code_room", 2556, 1614, 122),
    "bio_vat": ("Bio-Vat", "bio_vat", 2566, 298, 108),
    "airlock": ("Airlock", "airlock", 1443, 1614, 116),
    "escape_pod": ("Escape Pod", "escape_pod", POD_CENTER[0], POD_CENTER[1], POD_RADIUS),
}

# --- Connections -------------------------------------------------------------

# Doors: room -> hallway spaces it opens onto (one entry per red hatch)
DOORS: dict[str, list[str]] = {
    "1": ["h_3_0", "h_0_2"],
    "2": ["h_3_3"],
    "3": ["h_1_6"],
    "4": ["h_4_0"],
    "5": ["h_6_0"],
    "6": ["h_3_3"],
    "7": ["h_3_5"],
    "8": ["h_7_6"],
    "9": ["nwbelt_2"],
    "10": ["nwbelt_1"],
    "11": ["ne_5"],
    "12": ["h_18_1"],
    "13": ["brig_1"],
    "14": ["h_21_4"],
    "15": ["h_18_6"],
    "16": ["ne_1"],
    "17": ["brig_3"],
    "18": ["h_18_8"],
    "19": ["h_19_6"],
    "20": ["h_18_8"],
    "21": ["h_18_10", "h_21_10"],
    "22": ["h_18_12"],
    "23": ["h_16_12"],
    "24": ["h_14_6"],
    "25": ["sebelt_2"],
    "26": ["sw_2"],
    "27": ["h_5_6"],
    "28": ["h_4_12"],
    "29": ["h_3_10"],
    "30": ["h_3_9"],
    "31": ["h_0_7"],
    "32": ["h_9_0", "h_12_0"],
    "code_room_1": ["h_0_1"],
    "code_room_2": ["h_0_10", "h_2_12"],
    "code_room_3": ["h_21_10"],
    "bio_vat": ["h_19_0", "h_21_1"],
    "airlock": ["h_9_12", "h_12_12"],
    "escape_pod": POD_APPROACHES,
}

# Where corridors, the ring and the grid meet (grid-to-grid steps are derived)
LINKS: list[tuple[str, str, list[str]]] = [
    ("ring_w", "h_8_6", []),
    ("ring_e", "h_12_6", []),
    ("ring_nw", "nwbelt_1", []),
    ("ring_ne", "ne_1", []),
    ("ring_se", "sebelt_1", []),
    ("ring_sw", "sw_1", []),
    ("ne_5", "h_14_0", []),
    ("sw_5", "h_6_12", []),
    ("nwbelt_3", "h_8_0", []),
    ("sebelt_3", "h_13_12", []),
    # The blue field across the Brig branch
    ("ne_3", "brig_1", ["security_field"]),
]


def build() -> dict:
    spaces: list[dict] = []
    edges: list[dict] = []

    cells = set(GRID_CELLS)
    for c, r in GRID_CELLS:
        sq = {"x": round(GRID_X0 + PITCH_X * c), "y": round(GRID_Y0 + PITCH_Y * r),
              "w": SQUARE, "h": SQUARE, "angle": 0}
        sq.update(GRID_OVERRIDES.get((c, r), {}))
        spaces.append({"id": grid_id(c, r), "type": "hallway", "name": "Hallway",
                       "x": sq["x"], "y": sq["y"],
                       "shape": {"kind": "rect", "w": sq["w"], "h": sq["h"], "angle": sq["angle"]}})
        for nc, nr in ((c + 1, r), (c, r + 1)):
            if (nc, nr) in cells:
                edges.append({"a": grid_id(c, r), "b": grid_id(nc, nr)})

    for name, (squares, tags) in CORRIDORS.items():
        for i, sq in enumerate(squares, start=1):
            space = {"id": f"{name}_{i}", "type": "hallway", "name": "Hallway", "x": sq["x"], "y": sq["y"],
                     "shape": {"kind": "rect", "w": sq["w"], "h": sq["h"], "angle": sq["angle"]}}
            if tags:
                space["tags"] = tags
            spaces.append(space)
            if i > 1:
                edges.append({"a": f"{name}_{i - 1}", "b": f"{name}_{i}"})

    for i, (rid, a0, a1, tags) in enumerate(RING):
        mid = math.radians((a0 + a1) / 2)
        rr = (POD_RADIUS + RING_OUTER) / 2
        space = {"id": rid, "type": "hallway", "name": "Pod Ring",
                 "x": round(POD_CENTER[0] + rr * math.cos(mid)), "y": round(POD_CENTER[1] + rr * math.sin(mid)),
                 "shape": {"kind": "polygon", "points": _sector(a0, a1)}}
        if tags:
            space["tags"] = tags
        spaces.append(space)
        edges.append({"a": rid, "b": RING[(i + 1) % len(RING)][0]})

    for rid, (name, rtype, x, y, radius) in ROOMS.items():
        spaces.append({"id": rid, "type": rtype, "name": name or f"Room {rid}", "x": x, "y": y,
                       "shape": {"kind": "circle", "r": radius}})
        for hallway in DOORS[rid]:
            edges.append({"a": rid, "b": hallway, "door": True})

    for a, b, tags in LINKS:
        edge = {"a": a, "b": b}
        if tags:
            edge["tags"] = tags
        edges.append(edge)

    ids = {s["id"] for s in spaces}
    for e in edges:
        assert e["a"] in ids and e["b"] in ids, f"unknown space in edge {e}"
    return {"image": IMAGE, "spaces": spaces, "edges": edges}


def main() -> None:
    board = build()
    OUT.write_text(json.dumps(board, indent=1) + "\n")
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(board['spaces'])} spaces, {len(board['edges'])} edges")


if __name__ == "__main__":
    main()
