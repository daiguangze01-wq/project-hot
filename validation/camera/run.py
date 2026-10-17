#!/usr/bin/env python3
"""TASK-060 -- 2.5D camera / readability validation (model math + synthetic renders).

WHAT THIS IS
    A deterministic, dependency-light mathematical model of the shipped 2.5D
    orthographic camera baseline (docs/00 section 3.1, docs/02 section 3.1,
    docs/04 section 4), plus synthetic PIL renders of what that projection looks
    like at ortho size 7 / 8 / 9, pitch 50 deg, yaw 45 deg, 1920x1080.
    THIS IS NOT UNITY, NOT URP, AND NOT A PLAYER PLAYTEST.  It only answers
    geometric questions: how many screen pixels a character is, where the ground
    viewport edges are, and which combat distances fall inside the frame.

CAMERA MODEL (exactly the model specified in the TASK-060 brief)
    right   = ( cos(yaw),            -sin(yaw),            0          )
    up      = ( sin(yaw)sin(pitch),   cos(yaw)sin(pitch),   cos(pitch) )
    forward = ( sin(yaw)cos(pitch),   cos(yaw)cos(pitch),  -sin(pitch) )
    u = dot(p, right);  v = dot(p, up)
    screen_x = W/2 + u*scale;  screen_y = H/2 - v*scale
    scale = 1080 / (2 * orthoSize)          [px per metre, 1080p]

    Derived (verified by asserts at the end of main):
      character screen height (effective 1.8 m) = 1.8 * cos(pitch) * scale
      visible ground half-width  = S * W / H  (= 1.7778*S at 16:9)
      visible ground half-depth  = S / sin(pitch)   [camera-forward axis]
      screen-margin half-depth ahead = S/sin(pitch) (same behind; symmetric)

OUTPUTS (written to --out-dir, default = this directory)
    metrics.csv                     15 rows: size 7/8/9 x pitch 45/50/55 for the
                                    shipped viewport, plus the 20 m / 30 m
                                    zoom-out sizes 15 / 23 (docs/02 section 3.1).
    render_size7.png                synthetic renders, 1920x1080, size 7/8/9.
    render_size8.png
    render_size9.png

REPRODUCE
    C:\\Users\\dai\\.dsh\\dsh-runtimes\\dsh-primary-runtime\\dependencies\\python\\python.exe \
        validation\\camera\\run.py

    Deterministic: fixed constants, numpy RNG seeded with 20261017 (ground
    specks only; no other randomness).  Only stdlib + numpy + Pillow are used.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------- #
# Constants -- all numbers in this file are the TASK-060 / docs baseline.
# --------------------------------------------------------------------------- #
SCRIPT_DIR = Path(__file__).resolve().parent

SEED = 20261017
SCREEN_W = 1920
SCREEN_H = 1080
YAW_DEG = 45.0
PITCHES = (45.0, 50.0, 55.0)
SHIPPED_SIZES = (7.0, 8.0, 9.0)
ZOOM_CASES = ((15.0, 20.0), (23.0, 30.0))   # (ortho size, nominal distance m)
H_EFF = 1.8                                 # effective silhouette height (hat/weapon)
H_BODY = 1.5                                # body-only height (docs/00 "1.5m baseline")
TARGET_PX = (70.0, 90.0)                    # character screen-height target @1080p
DISTANCES = (6.0, 10.0, 14.0, 20.0, 30.0)
SUPERSAMPLE = 2                             # render at 2x then downscale (readable edges)

OX = np.array([1.0, 0.0, 0.0])              # world axes
OY = np.array([0.0, 1.0, 0.0])
OZ = np.array([0.0, 0.0, 1.0])


# --------------------------------------------------------------------------- #
# Camera math
# --------------------------------------------------------------------------- #
def camera_basis(pitch_deg: float, yaw_deg: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the orthonormal orthographic camera basis (right, up, forward)."""
    p = math.radians(pitch_deg)
    y = math.radians(yaw_deg)
    right = np.array([math.cos(y), -math.sin(y), 0.0])
    up = np.array([math.sin(y) * math.sin(p), math.cos(y) * math.sin(p), math.cos(p)])
    forward = np.array([math.sin(y) * math.cos(p), math.cos(y) * math.cos(p), -math.sin(p)])
    return right, up, forward


def ground_axes(yaw_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """Ground-plane camera axes: g = camera-forward projected to z=0, r = camera-right."""
    y = math.radians(yaw_deg)
    g = np.array([math.sin(y), math.cos(y), 0.0])
    r = np.array([math.cos(y), -math.sin(y), 0.0])
    return g, r


def scale_px_per_m(ortho_size: float, screen_h: int = SCREEN_H) -> float:
    return screen_h / (2.0 * ortho_size)


def project(points, pitch_deg: float, yaw_deg: float, ortho_size: float,
            width: int = SCREEN_W, height: int = SCREEN_H):
    """Orthographic project world points (metres) to screen pixels.

    Returns (sx, sy, depth) where depth = dot(p, forward) (larger = farther from camera).
    """
    pts = np.asarray(points, dtype=float)
    right, up, forward = camera_basis(pitch_deg, yaw_deg)
    scale = height / (2.0 * ortho_size)
    u = pts @ right
    v = pts @ up
    depth = pts @ forward
    return width / 2.0 + u * scale, height / 2.0 - v * scale, depth


def cast_screen_point_to_ground(sx: float, sy: float, pitch_deg: float, yaw_deg: float,
                                ortho_size: float, width: int = SCREEN_W,
                                height: int = SCREEN_H) -> np.ndarray:
    """Cast an orthographic screen pixel along `forward` onto the ground plane z=0."""
    right, up, forward = camera_basis(pitch_deg, yaw_deg)
    scale = height / (2.0 * ortho_size)
    u = (sx - width / 2.0) / scale
    v = (height / 2.0 - sy) / scale
    p0 = u * right + v * up                      # point on the image plane
    t = -p0[2] / forward[2]                      # z=0 intersection (pitch != 0)
    return p0 + t * forward


def visible_ground_polygon(ortho_size: float, pitch_deg: float, yaw_deg: float,
                           width: int = SCREEN_W, height: int = SCREEN_H):
    """Visible ground (z=0) polygon by casting the four screen corners along forward.

    Returns (polygon_xyz, half_width_m, half_depth_m) with the extents measured in
    ground-plane camera axes (r = right, g = forward).
    """
    corners = [(0.0, 0.0), (width, 0.0), (width, height), (0.0, height)]
    poly = np.array([
        cast_screen_point_to_ground(sx, sy, pitch_deg, yaw_deg, ortho_size, width, height)
        for sx, sy in corners
    ])
    g, r = ground_axes(yaw_deg)
    half_width = float(np.max(np.abs(poly @ r)))
    half_depth = float(np.max(np.abs(poly @ g)))
    return poly, half_width, half_depth


def visible_distance_along(pitch_deg: float, yaw_deg: float, ortho_size: float,
                           direction_xy) -> float:
    """Largest ground distance from the screen centre visible along a ground direction."""
    _, half_w, half_d = visible_ground_polygon(ortho_size, pitch_deg, yaw_deg)
    g, r = ground_axes(yaw_deg)
    d = np.array([direction_xy[0], direction_xy[1], 0.0], dtype=float)
    d /= np.linalg.norm(d)
    limits = []
    ur = abs(float(d @ r))
    ug = abs(float(d @ g))
    if ur > 1e-12:
        limits.append(half_w / ur)
    if ug > 1e-12:
        limits.append(half_d / ug)
    return min(limits)


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #
BASE_COLUMNS = [
    "viewport",
    "ortho_size",
    "pitch_deg",
    "yaw_deg",
    "screen",
    "scale_px_per_m",
    "char_px_H_eff_1.8m",
    "char_pct_H_eff_1.8m",
    "within_70_90",
    "band_delta_px",
    "char_px_body_1.5m",
    "ground_half_width_m",
    "ground_half_depth_m",
    "ground_half_diag_m",
    "world_axis_visible_m",
]
DIST_COLUMNS = [
    f"d{int(d)}_{suffix}"
    for d in DISTANCES
    for suffix in ("forward_feet_y_px", "inside_forward", "inside_world_axis", "inside_any_direction")
]
COLUMNS = BASE_COLUMNS + DIST_COLUMNS


def build_metric_row(viewport: str, ortho_size: float, pitch_deg: float,
                     yaw_deg: float = YAW_DEG) -> dict:
    """One metrics.csv row for one viewport (size, pitch, yaw) combination."""
    pitch = math.radians(pitch_deg)
    scale = scale_px_per_m(ortho_size)
    char_px = H_EFF * math.cos(pitch) * scale
    body_px = H_BODY * math.cos(pitch) * scale
    _, half_w, half_d = visible_ground_polygon(ortho_size, pitch_deg, yaw_deg)
    half_diag = math.hypot(half_w, half_d)

    within = TARGET_PX[0] <= char_px <= TARGET_PX[1]
    if char_px < TARGET_PX[0]:
        band_delta = char_px - TARGET_PX[0]
    elif char_px > TARGET_PX[1]:
        band_delta = char_px - TARGET_PX[1]
    else:
        band_delta = 0.0

    y = math.radians(yaw_deg)
    row = {
        "viewport": viewport,
        "ortho_size": ortho_size,
        "pitch_deg": pitch_deg,
        "yaw_deg": yaw_deg,
        "screen": f"{SCREEN_W}x{SCREEN_H}",
        "scale_px_per_m": scale,
        "char_px_H_eff_1.8m": char_px,
        "char_pct_H_eff_1.8m": 100.0 * char_px / SCREEN_H,
        "within_70_90": within,
        "band_delta_px": band_delta,
        "char_px_body_1.5m": body_px,
        "ground_half_width_m": half_w,
        "ground_half_depth_m": half_d,
        "ground_half_diag_m": half_diag,
        "world_axis_visible_m": visible_distance_along(pitch_deg, yaw_deg, ortho_size, (1.0, 0.0)),
    }

    for d in DISTANCES:
        key = f"d{int(d)}"
        # a) straight ahead from the screen centre, along camera-forward on the ground;
        #    such points always project onto the vertical centre line: sy = H/2 - d*sin(p)*scale
        feet_y = SCREEN_H / 2.0 - d * math.sin(pitch) * scale
        inside_forward = 0.0 <= feet_y <= SCREEN_H
        # b) along world +X (a classic 8-way combat direction; yaw=45 makes this a
        #    "diagonal" of the viewport footprint)
        u = d * math.cos(y)
        v = d * math.sin(y) * math.sin(pitch)
        sx = SCREEN_W / 2.0 + u * scale
        sy = SCREEN_H / 2.0 - v * scale
        inside_world = 0.0 <= sx <= SCREEN_W and 0.0 <= sy <= SCREEN_H
        # c) is a point at that ground distance visible in ANY ground direction?
        inside_any = d <= half_diag + 1e-9
        row[f"{key}_forward_feet_y_px"] = feet_y
        row[f"{key}_inside_forward"] = inside_forward
        row[f"{key}_inside_world_axis"] = inside_world
        row[f"{key}_inside_any_direction"] = inside_any
    return row


def build_metrics() -> list[dict]:
    rows: list[dict] = []
    for size in SHIPPED_SIZES:
        for pitch in PITCHES:
            rows.append(build_metric_row("shipped", size, pitch))
    for size, nominal in ZOOM_CASES:
        for pitch in PITCHES:
            rows.append(build_metric_row(f"zoom{int(nominal)}m_size{int(size)}", size, pitch))
    return rows


def fmt_cell(value) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def write_metrics_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: fmt_cell(row[key]) for key in COLUMNS})


# --------------------------------------------------------------------------- #
# Fonts / small drawing helpers
# --------------------------------------------------------------------------- #
def _font_candidates(bold: bool) -> list[Path]:
    windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    fonts = windir / "Fonts"
    names = (["seguisb.ttf", "segoeuib.ttf", "arialbd.ttf", "calibrib.ttf"]
             if bold else
             ["segoeui.ttf", "arial.ttf", "calibri.ttf", "segoeuil.ttf"])
    return [fonts / n for n in names]


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for path in _font_candidates(bold):
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    try:
        return ImageFont.load_default(size=size)          # Pillow >= 10.1
    except TypeError:                                     # pragma: no cover
        return ImageFont.load_default()


def rgba(color, alpha: int) -> tuple[int, int, int, int]:
    return (int(color[0]), int(color[1]), int(color[2]), int(alpha))


def pill(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str,
         font: ImageFont.FreeTypeFont, fg=(240, 245, 250, 255),
         bg=(8, 12, 18, 215), pad: tuple[int, int] = (6, 3), radius: int = 4,
         outline=None, anchor: str = "lt") -> tuple[float, float, float, float]:
    """Text with a translucent rounded background. Returns the pill bbox."""
    x, y = xy
    bbox = draw.textbbox((x, y), text, font=font, anchor=anchor)
    box = (bbox[0] - pad[0], bbox[1] - pad[1], bbox[2] + pad[0], bbox[3] + pad[1])
    draw.rounded_rectangle(box, radius=radius, fill=bg, outline=outline)
    draw.text((x, y), text, font=font, fill=fg, anchor=anchor)
    return box


def draw_lines(draw: ImageDraw.ImageDraw, point_pairs, fill, width: int = 1) -> None:
    for a, b in point_pairs:
        draw.line([a, b], fill=fill, width=width)


def _norm(vec: np.ndarray) -> np.ndarray:
    return vec / np.linalg.norm(vec)


def shade(color: tuple[int, int, int], normal: np.ndarray) -> tuple[int, int, int]:
    """Flat-shade a face colour with one fixed light (camera-ish top-left)."""
    light = _norm(np.array([-0.35, -0.60, 1.00]))
    k = 0.58 + 0.42 * max(0.0, float(normal @ light))
    return tuple(max(0, min(255, int(round(c * k)))) for c in color)


# --------------------------------------------------------------------------- #
# Character model (simplified low-poly figure: legs, torso, shoulder pads, head,
# hat (brim+crown), weapon (blade+guard+grip), shadow). Total height = 1.80 m.
# --------------------------------------------------------------------------- #
BOX_CORNERS = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
               (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
# (corner indices, local outward normal)
BOX_FACES = [
    ((0, 3, 2, 1), (0.0, 0.0, -1.0)),
    ((4, 5, 6, 7), (0.0, 0.0, 1.0)),
    ((0, 1, 5, 4), (0.0, -1.0, 0.0)),
    ((3, 7, 6, 2), (0.0, 1.0, 0.0)),
    ((0, 4, 7, 3), (-1.0, 0.0, 0.0)),
    ((1, 2, 6, 5), (1.0, 0.0, 0.0)),
]
# (name, centre (right, facing, z), size, colour key)
CHAR_PARTS = [
    ("leg_l", (-0.12, 0.00, 0.36), (0.17, 0.20, 0.72), "pants"),
    ("leg_r", (0.12, 0.00, 0.36), (0.17, 0.20, 0.72), "pants"),
    ("torso", (0.00, 0.00, 1.03), (0.44, 0.26, 0.62), "armor"),
    ("shoulder_l", (-0.29, 0.00, 1.27), (0.22, 0.26, 0.22), "accent"),
    ("shoulder_r", (0.29, 0.00, 1.27), (0.22, 0.26, 0.22), "accent"),
    ("head", (0.00, -0.01, 1.50), (0.26, 0.26, 0.28), "skin"),
    ("hat_brim", (0.00, -0.02, 1.67), (0.52, 0.50, 0.06), "hat"),
    ("hat_crown", (0.00, -0.02, 1.75), (0.30, 0.30, 0.10), "hat"),
    ("weapon_blade", (0.44, 0.06, 1.36), (0.06, 0.06, 0.66), "steel"),
    ("weapon_guard", (0.44, 0.06, 1.01), (0.06, 0.26, 0.06), "gold"),
    ("weapon_grip", (0.44, 0.06, 0.92), (0.06, 0.06, 0.18), "wood"),
]

PALETTES = [
    {  # 6 m figure
        "armor": (62, 140, 190), "pants": (58, 62, 78), "accent": (232, 186, 84),
        "skin": (235, 192, 152), "hat": (38, 58, 88), "steel": (206, 216, 232),
        "gold": (222, 178, 94), "wood": (138, 98, 62), "dot": (86, 190, 245),
    },
    {  # 10 m figure
        "armor": (188, 72, 68), "pants": (62, 56, 66), "accent": (238, 218, 126),
        "skin": (230, 184, 146), "hat": (78, 42, 52), "steel": (208, 208, 220),
        "gold": (226, 186, 96), "wood": (132, 94, 60), "dot": (240, 120, 108),
    },
    {  # 14 m figure
        "armor": (116, 172, 88), "pants": (58, 62, 58), "accent": (206, 226, 240),
        "skin": (228, 188, 150), "hat": (48, 70, 52), "steel": (204, 214, 226),
        "gold": (218, 178, 96), "wood": (128, 92, 60), "dot": (150, 224, 130),
    },
]
DIST_COLORS = {6.0: (86, 220, 150), 10.0: (255, 212, 92), 14.0: (255, 138, 84),
               20.0: (140, 152, 172), 30.0: (108, 118, 138)}


# --------------------------------------------------------------------------- #
# Renderer
# --------------------------------------------------------------------------- #
class SceneRenderer:
    """Synthetic 1920x1080 render of the projected 2.5D camera view."""

    def __init__(self, ortho_size: float, pitch_deg: float = 50.0, yaw_deg: float = YAW_DEG):
        self.ortho_size = float(ortho_size)
        self.pitch = float(pitch_deg)
        self.yaw = float(yaw_deg)
        self.ss = SUPERSAMPLE
        self.w = SCREEN_W * self.ss
        self.h = SCREEN_H * self.ss
        self.scale = scale_px_per_m(self.ortho_size)          # 1x px/m
        self.char_px = H_EFF * math.cos(math.radians(self.pitch)) * self.scale
        self.g, self.r = ground_axes(self.yaw)
        self.right, self.up, self.forward = camera_basis(self.pitch, self.yaw)
        self._half_w = None
        self._half_d = None

    # -- projection helpers ------------------------------------------------ #
    def proj(self, points):
        """Project world points -> 1x screen pixels."""
        return project(points, self.pitch, self.yaw, self.ortho_size)

    def proj2(self, points):
        """Project world points -> supersampled screen pixels (for geometry drawing)."""
        sx, sy, _ = self.proj(points)
        return [tuple(map(float, xy)) for xy in zip(sx * self.ss, sy * self.ss)]

    def poly2(self, points, fill, outline=None, width: int = 1):
        xy = self.proj2(points)
        self.draw.polygon(xy, fill=fill, outline=outline, width=width)

    def line2(self, points, fill, width: int = 1):
        xy = self.proj2(points)
        self.draw.line(xy, fill=fill, width=width)

    # -- ground ------------------------------------------------------------ #
    def draw_ground(self, rng: np.random.Generator) -> None:
        d = self.draw
        d.rectangle([0, 0, self.w, self.h], fill=(34, 40, 48, 255))
        # deterministic soil specks (the only use of the RNG; seed = 20261017)
        n = 700
        world = np.column_stack([
            rng.uniform(-34.0, 34.0, n),
            rng.uniform(-34.0, 34.0, n),
            np.zeros(n),
        ])
        radii = rng.uniform(0.10, 0.32, n)
        alphas = rng.integers(16, 42, n)
        sx, sy, _ = self.proj(world)
        for x, y, rad, alpha in zip(sx, sy, radii, alphas):
            if -40 <= x <= SCREEN_W + 40 and -40 <= y <= SCREEN_H + 40:
                rx = max(1.0, rad * self.scale * self.ss)
                d.ellipse([x * self.ss - rx, y * self.ss - rx,
                           x * self.ss + rx, y * self.ss + rx],
                          fill=(96, 108, 122, int(alpha)))
        # 1 m grid; every 5 m brighter (lines are straight under linear projection)
        for coord in range(-40, 41):
            major = coord % 5 == 0
            color = (128, 152, 178, 108) if major else (86, 104, 124, 52)
            w = (2 if major else 1) * (self.ss // 2 if self.ss > 1 else 1)
            w = max(1, w)
            self.line2(np.array([[coord, -60.0, 0.0], [coord, 60.0, 0.0]]), color, w)
            self.line2(np.array([[-60.0, coord, 0.0], [60.0, coord, 0.0]]), color, w)
        # faint dotted camera-forward ground axis
        ts = np.arange(0.0, 16.0 + 1e-9, 0.25)
        axis = np.column_stack([self.g[0] * ts, self.g[1] * ts, np.zeros_like(ts)])
        seg = self.proj2(axis)
        for i in range(0, len(seg) - 1, 2):
            d.line([seg[i], seg[i + 1]], fill=(150, 190, 220, 70), width=1)

    # -- distance rings ----------------------------------------------------- #
    def draw_ring(self, radius: float, color, width: int = 2, dashed: bool = False,
                  dash_segments: int = 14) -> None:
        n = 480
        t = np.linspace(0.0, 2.0 * math.pi, n + 1)
        pts = np.column_stack([radius * np.cos(t), radius * np.sin(t), np.zeros_like(t)])
        xy = self.proj2(pts)
        for i in range(n):
            if dashed and (i // max(1, dash_segments // 2)) % 2 == 1:
                continue
            self.draw.line([xy[i], xy[i + 1]], fill=rgba(color, 235), width=width)

    # -- character ---------------------------------------------------------- #
    def character_origin(self, distance: float) -> np.ndarray:
        return self.g * float(distance)

    def origin_for_screen(self, sx: float, sy: float) -> np.ndarray:
        """Ground point whose projection is the given 1x screen pixel (linear model inverse)."""
        u = (sx - SCREEN_W / 2.0) / self.scale
        v = (SCREEN_H / 2.0 - sy) / self.scale
        return u * self.r + (v / math.sin(math.radians(self.pitch))) * self.g

    def world_from_local(self, origin: np.ndarray, local: tuple[float, float, float]) -> np.ndarray:
        """Character local frame: +x = character right, +y = character facing, +z = up.

        The figure faces down-screen (toward the camera/player), i.e. local +y = -g.
        """
        return origin + self.r * local[0] + (-self.g) * local[1] + OZ * local[2]

    def draw_character(self, origin: np.ndarray, palette: dict) -> None:
        # ground shadow (radius 0.42 m ellipse on z=0)
        t = np.linspace(0.0, 2.0 * math.pi, 40)
        shadow = (origin[None, :]
                  + np.column_stack([0.42 * np.cos(t), 0.42 * np.sin(t), np.zeros_like(t)]))
        self.poly2(shadow, fill=(0, 0, 0, 96))

        faces = []
        for _name, centre, size, colour_key in CHAR_PARTS:
            base = palette[colour_key]
            corners_local = [
                (centre[0] + cx * size[0] / 2.0,
                 centre[1] + cy * size[1] / 2.0,
                 centre[2] + cz * size[2] / 2.0)
                for cx, cy, cz in BOX_CORNERS
            ]
            corners_world = [self.world_from_local(origin, c) for c in corners_local]
            for indices, normal_local in BOX_FACES:
                quad = np.array([corners_world[i] for i in indices])
                normal_world = _norm(
                    self.r * normal_local[0] + (-self.g) * normal_local[1] + OZ * normal_local[2]
                )
                depth = float(quad.mean(axis=0) @ self.forward)
                faces.append((depth, quad, shade(base, normal_world)))
        # painter's algorithm: farthest (largest depth) first
        faces.sort(key=lambda item: -item[0])
        for _depth, quad, colour in faces:
            self.poly2(quad, fill=rgba(colour, 255), outline=(10, 14, 20, 120), width=1)

    def draw_figure_cutout(self) -> None:
        """1:1 figure strip (bottom left): same screen px at 6/10/14 m.

        Orthographic projection makes a character's screen size independent of
        ground distance, so this strip isolates anatomy readability from the
        viewport-clipping question answered by the main frame.
        """
        x0, y0, x1, y1 = 32, 800, 532, 1010
        ss = self.ss
        self.draw.rounded_rectangle([x0 * ss, y0 * ss, x1 * ss, y1 * ss], radius=8 * ss,
                                    fill=(8, 12, 18, 218), outline=(90, 110, 132, 160))
        self.draw.line([(70 * ss, 948 * ss), (500 * ss, 948 * ss)],
                       fill=(90, 110, 132, 120), width=max(1, ss))
        for sx, palette in ((130.0, PALETTES[0]), (280.0, PALETTES[1]), (430.0, PALETTES[2])):
            self.draw_character(self.origin_for_screen(sx, 948.0), palette)

    def draw_height_bar(self, distance: float) -> None:
        origin = self.character_origin(distance)
        feet_sx, feet_sy, _ = self.proj(origin[None, :])
        head_sx, head_sy, _ = self.proj(self.world_from_local(origin, (0.0, 0.0, H_EFF))[None, :])
        feet_sx, feet_sy = float(feet_sx[0]), float(feet_sy[0])
        head_sy = float(head_sy[0])
        bar_x = feet_sx - 86.0
        top = head_sy * self.ss
        bottom = feet_sy * self.ss
        bx = bar_x * self.ss
        col = (238, 242, 250, 220)
        self.draw.line([(bx, top), (bx, bottom)], fill=col, width=max(1, self.ss))
        for z in (0.0, 0.5, 1.0, 1.5, 1.8):
            y = (feet_sy - (z / H_EFF) * (feet_sy - head_sy)) * self.ss
            half = 5 * self.ss
            self.draw.line([(bx - half, y), (bx + half, y)], fill=col, width=max(1, self.ss))
        # short connector to the figure
        self.draw.line([(bx, bottom), ((feet_sx - 22) * self.ss, bottom)],
                       fill=rgba((238, 242, 250), 120), width=1)

    # -- one full frame ----------------------------------------------------- #
    def render(self, out_path: Path) -> None:
        rng = np.random.default_rng(SEED)
        self.img = Image.new("RGB", (self.w, self.h), (34, 40, 48))
        self.draw = ImageDraw.Draw(self.img, "RGBA")

        self.draw_ground(rng)
        for radius in (20.0, 30.0):                      # far rings (dim, usually off-frame)
            self.draw_ring(radius, DIST_COLORS[radius], width=1, dashed=True)
        for radius in (6.0, 10.0, 14.0):
            self.draw_ring(radius, DIST_COLORS[radius], width=max(1, self.ss))
        # figures ordered far -> near (they do not overlap, but keep painter order sane)
        for distance, palette in ((14.0, PALETTES[2]), (10.0, PALETTES[1]), (6.0, PALETTES[0])):
            self.draw_character(self.character_origin(distance), palette)
        for distance in (6.0, 10.0, 14.0):
            self.draw_height_bar(distance)
        self.draw_figure_cutout()

        # downscale -> crisp 1x frame, then draw text/UI in 1x space
        frame = self.img.resize((SCREEN_W, SCREEN_H), Image.Resampling.LANCZOS)
        overlay = ImageDraw.Draw(frame, "RGBA")
        self._draw_annotations(frame, overlay)
        frame.save(out_path, format="PNG", optimize=False)
        self.frame = frame

    # -- 1x annotation layer ------------------------------------------------- #
    def _char_screen(self, distance: float) -> tuple[float, float]:
        sx, sy, _ = self.proj(self.character_origin(distance)[None, :])
        return float(sx[0]), float(sy[0])

    def _draw_annotations(self, frame: Image.Image, d: ImageDraw.ImageDraw) -> None:
        self._half_w, self._half_d = visible_ground_polygon(self.ortho_size, self.pitch, self.yaw)[1:]
        f_title = load_font(25, bold=True)
        f_big = load_font(22, bold=True)
        f_body = load_font(18)
        f_small = load_font(15)
        f_tiny = load_font(13)

        # ----- camera centre / player marker (0 m) -----
        zero_sx, zero_sy, _ = self.proj(np.array([[0.0, 0.0, 0.0]]))
        cxp, cyp = float(zero_sx[0]), float(zero_sy[0])
        t = np.linspace(0.0, 2.0 * math.pi, 64)
        ring = np.column_stack([0.55 * np.cos(t), 0.55 * np.sin(t), np.zeros_like(t)])
        sx, sy, _ = self.proj(ring)
        d.line([(float(x), float(y)) for x, y in zip(sx, sy)],
               fill=(120, 220, 255, 220), width=2)
        d.line([(cxp - 9, cyp), (cxp + 9, cyp)], fill=(120, 220, 255, 230), width=2)
        d.line([(cxp, cyp - 9), (cxp, cyp + 9)], fill=(120, 220, 255, 230), width=2)
        pill(d, (cxp + 14, cyp + 12), "player 0 m / camera centre", f_small,
             fg=(190, 232, 250, 255), bg=(6, 16, 24, 190))

        # ----- distance ring labels (6 / 10 / 14 m) -----
        figure_screen = {distance: self._char_screen(distance) for distance in (6.0, 10.0, 14.0)}
        for radius, colour in ((6.0, DIST_COLORS[6.0]), (10.0, DIST_COLORS[10.0]),
                                (14.0, DIST_COLORS[14.0])):
            self._ring_label(d, radius, colour, f_small, figure_screen)

        # ----- figure distance labels + part call-outs (6 m figure only) -----
        for distance, palette in ((6.0, PALETTES[0]), (10.0, PALETTES[1]),
                                  (14.0, PALETTES[2])):
            fsx, fsy = figure_screen[distance]
            if fsy < 0.0:
                continue                      # off-viewport; the notice below says why
            if fsy > 96.0:
                pill(d, (fsx - 70.0, fsy + 10.0), f"{distance:.0f} m figure", f_small,
                     fg=(238, 242, 248, 255), bg=(8, 12, 18, 200),
                     outline=rgba(palette["dot"], 200))
            else:                             # near the top edge: label right of the feet
                pill(d, (fsx + 16.0, fsy + 4.0), f"{distance:.0f} m figure", f_small,
                     fg=(238, 242, 248, 255), bg=(8, 12, 18, 200),
                     outline=rgba(palette["dot"], 200))
        self._part_callouts(d, f_small)
        self._bar_label(d, f_small)

        # ----- off-viewport / clipping notices (right side, under the inset) -----
        notices = []
        for distance, palette in ((10.0, PALETTES[1]), (14.0, PALETTES[2])):
            _, feet_y = figure_screen[distance]
            if feet_y < 0.0:
                notices.append((palette["dot"],
                                f"{distance:.0f} m figure: OFF-VIEWPORT, feet {-feet_y:.0f} px above top edge"))
            elif feet_y - self.char_px < 0.0:
                notices.append((palette["dot"],
                                f"{distance:.0f} m figure: body clipped, head "
                                f"{self.char_px - feet_y:.0f} px above top edge"))
        y = 440.0
        for colour, text in notices:
            d.polygon([(1408, y + 10), (1420, y + 10), (1414, y - 2)], fill=rgba(colour, 235))
            pill(d, (1424.0, y), text, f_small, fg=(245, 240, 230, 255),
                 bg=(10, 10, 14, 205), outline=rgba(colour, 200))
            y += 36.0

        # ----- main HUD panel (top left) -----
        self._hud(d, f_title, f_big, f_body, f_small)

        # ----- top-down schematic inset (top right) -----
        self._inset(d, f_small, f_tiny)

        # ----- figure cut-out labels (bottom left; geometry drawn in render) -----
        self._cutout_labels(d, f_small, f_tiny)

        # ----- character px ruler (right, below inset) -----
        self._px_ruler(d, f_small, f_tiny)

        # ----- footers -----
        footer = ("synthetic model render, not Unity  -  fixed orthographic projection model math only "
                  "(no URP / occlusion / AA / post-processing)  -  validation/camera/run.py  -  seed 20261017")
        d.text((32, SCREEN_H - 34), footer, font=f_small, fill=(150, 160, 175, 255))
        right = f"TASK-060  -  ortho size {self.ortho_size:g}  -  pitch {self.pitch:g} deg  -  yaw {self.yaw:g} deg"
        tw = d.textlength(right, font=f_big)
        d.text((SCREEN_W - 32 - tw, SCREEN_H - 36), right, font=f_big, fill=(225, 230, 240, 255))

    def _ring_label(self, d, radius: float, colour, font, figure_screen: dict) -> None:
        """Place the ring's distance label on a visible part of the ring, avoiding figures."""
        candidates = [self.r * radius, -self.r * radius, self.g * radius, -self.g * radius]
        sx, sy, _ = self.proj(np.array(candidates))
        figure_points = [p for p in figure_screen.values() if p[1] >= 0.0]
        for x, y in zip(sx, sy):
            x, y = float(x), float(y)
            if not (6.0 <= x <= SCREEN_W - 6.0 and 20.0 <= y <= SCREEN_H - 20.0):
                continue
            if any(math.hypot(x - fx, y - fy) < 80.0 for fx, fy in figure_points):
                continue
            anchor = "mm"
            if x > SCREEN_W - 160.0:
                anchor, x = "rm", SCREEN_W - 18.0
            elif x < 160.0:
                anchor, x = "lm", 18.0
            pill(d, (x, y), f"{radius:.0f} m", font, fg=(240, 245, 250, 255),
                 bg=(8, 12, 18, 205), outline=rgba(colour, 220), anchor=anchor)
            return
        # fallback: only an arc of the ring is on screen (e.g. the 14 m ring at
        # size 7) -- label the most comfortably visible point of that arc.
        n = 720
        t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
        ring_pts = np.column_stack([radius * np.cos(t), radius * np.sin(t),
                                    np.zeros_like(t)])
        sx, sy, _ = self.proj(ring_pts)
        best = None
        for x, y in zip(sx, sy):
            x, y = float(x), float(y)
            if not (60.0 <= x <= SCREEN_W - 60.0 and 40.0 <= y <= SCREEN_H - 40.0):
                continue
            if any(math.hypot(x - fx, y - fy) < 80.0 for fx, fy in figure_points):
                continue
            margin = min(x, SCREEN_W - x, y, SCREEN_H - y)
            if best is None or margin > best[2]:
                best = (x, y, margin)
        if best is not None:
            pill(d, (best[0], best[1]), f"{radius:.0f} m", font, fg=(240, 245, 250, 255),
                 bg=(8, 12, 18, 205), outline=rgba(colour, 220), anchor="mm")

    def _part_callouts(self, d, font) -> None:
        origin = self.character_origin(6.0)
        anchors = [
            ("hat", self.world_from_local(origin, (0.0, -0.02, 1.76)), (34, -28)),
            ("shoulder pad", self.world_from_local(origin, (0.29, 0.0, 1.27)), (46, 8)),
            ("weapon", self.world_from_local(origin, (0.44, 0.06, 1.52)), (74, -12)),
            ("shadow", origin + np.array([0.0, 0.0, 0.02]), (-18, 30)),
        ]
        for text, point, (dx, dy) in anchors:
            sx, sy, _ = self.proj(np.array([point]))
            x, y = float(sx[0]), float(sy[0])
            if not (0 <= x <= SCREEN_W and 0 <= y <= SCREEN_H):
                continue
            tx, ty = x + dx, y + dy
            d.line([(x, y), (tx - 2, ty + 6)], fill=(235, 240, 248, 150), width=1)
            pill(d, (tx, ty), text, font, fg=(236, 242, 250, 255),
                 bg=(8, 12, 18, 200), pad=(4, 2))

    def _bar_label(self, d, font) -> None:
        """Screen-px label on the 6 m figure's 1.8 m height bar."""
        fsx, fsy = self._char_screen(6.0)
        bar_x = fsx - 86.0
        head_y = fsy - self.char_px
        pill(d, (bar_x + 10.0, head_y - 16.0), f"1.8 m = {self.char_px:.0f} px", font,
             fg=(236, 242, 250, 255), bg=(8, 12, 18, 205))

    def _hud(self, d, f_title, f_big, f_body, f_small) -> None:
        x0, y0 = 32, 32
        within = TARGET_PX[0] <= self.char_px <= TARGET_PX[1]
        pct = 100.0 * self.char_px / SCREEN_H
        hw, hd = self._half_w, self._half_d
        lines = [
            f"ortho size {self.ortho_size:g}   pitch {self.pitch:g} deg   yaw {self.yaw:g} deg   "
            f"1920x1080 (16:9)   seed 20261017",
            f"scale = 1080/(2*size) = {self.scale:.1f} px/m   fixed orthographic (no perspective)",
            f"visible ground: half-width {hw:.2f} m, half-depth {hd:.2f} m, "
            f"ground diagonal half {math.hypot(hw, hd):.2f} m",
            "grid 1 m  -  rings 6/10/14 m  -  figures at 6/10/14 m along camera-forward  -  height bars",
        ]
        flags = []
        for distance in (6.0, 10.0, 14.0):
            _, feet_y = self._char_screen(distance)
            flags.append(f"{distance:.0f} m " + ("yes" if 0.0 <= feet_y <= SCREEN_H else "NO"))
        lines.append("in viewport (feet point):  " + "   ".join(flags))

        verdict1 = f"character H_eff 1.8 m = {self.char_px:.1f} px ({pct:.2f}% of screen height)"
        verdict2 = "target 70-90 px @1080p at default zoom: "
        if within:
            verdict2_status = "PASS"
        else:
            delta = self.char_px - (TARGET_PX[0] if self.char_px < TARGET_PX[0] else TARGET_PX[1])
            verdict2_status = f"FAIL ({delta:+.1f} px)"
        lead_note = (f"14 m lock range: {max(0.0, 14.0 - hd):.2f} m beyond the straight-ahead "
                     f"ground depth ({hd:.2f} m) -> camera lead or zoom-out")
        note = ("figure = legs/torso/shoulder pads/head/hat/weapon + 1.8 m height bar "
                "(model anatomy, not final art)")

        widths = [d.textlength(s, font=f_big) for s in (verdict1, verdict2 + verdict2_status)]
        widths += [d.textlength(s, font=f_body) for s in lines]
        widths += [d.textlength(s, font=f_small) for s in (note, lead_note)]
        widths.append(d.textlength("TASK-060  2.5D camera readability", font=f_title))
        widths.append(d.textlength("SYNTHETIC MODEL RENDER - NOT UNITY", font=f_big))
        panel_w = min(830, max(660, int(max(widths)) + 32))
        panel_h = 344

        y = y0 + 12
        d.rounded_rectangle([x0, y0, x0 + panel_w, y0 + panel_h], radius=8,
                            fill=(8, 12, 18, 218), outline=(90, 110, 132, 160))
        d.text((x0 + 16, y), "TASK-060  2.5D camera readability", font=f_title,
               fill=(240, 244, 250, 255))
        y += 36
        d.text((x0 + 16, y), "SYNTHETIC MODEL RENDER - NOT UNITY", font=f_big,
               fill=(255, 170, 90, 255))
        y += 32
        for line in lines:
            d.text((x0 + 16, y), line, font=f_body, fill=(206, 214, 226, 255))
            y += 24
        y += 8
        d.text((x0 + 16, y), verdict1, font=f_big, fill=(240, 244, 250, 255))
        y += 27
        d.text((x0 + 16, y), verdict2, font=f_big, fill=(240, 244, 250, 255))
        px = x0 + 16 + d.textlength(verdict2, font=f_big)
        d.text((px, y), verdict2_status, font=f_big,
               fill=(110, 235, 165, 255) if within else (255, 125, 110, 255))
        y += 26
        d.text((x0 + 16, y), lead_note, font=f_small, fill=(240, 196, 130, 255))
        y += 21
        d.text((x0 + 16, y), note, font=f_small, fill=(168, 178, 192, 255))

    def _inset(self, d, f_small, f_tiny) -> None:
        x0, y0, w, h = SCREEN_W - 32 - 470, 32, 470, 388
        d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=8,
                            fill=(8, 12, 18, 218), outline=(90, 110, 132, 160))
        d.text((x0 + 14, y0 + 10), "TOP-DOWN SCHEMATIC - not the rendered view",
               font=f_small, fill=(214, 222, 234, 255))
        px0, py0 = x0 + 16, y0 + 40
        pw, ph = w - 32, h - 40 - 34
        scale = min(pw / 80.0, ph / 60.0)       # about +-40 m x +-30 m
        cx, cy = px0 + pw / 2.0, py0 + ph / 2.0
        d.rectangle([px0, py0, px0 + pw, py0 + ph], fill=(14, 19, 25, 220),
                    outline=(70, 84, 100, 200))
        # viewport footprint (camera-aligned rectangle)
        hw, hd = self._half_w, self._half_d
        rect = [cx - hw * scale, cy - hd * scale, cx + hw * scale, cy + hd * scale]
        d.rectangle(rect, fill=(70, 130, 170, 60), outline=(120, 205, 245, 235), width=2)
        d.text((max(px0 + 2, rect[0]), rect[3] + 4), "shipped viewport footprint",
               font=f_tiny, fill=(150, 220, 250, 255))
        # distance rings (same colours as the main view)
        for radius, colour in ((6.0, DIST_COLORS[6.0]), (10.0, DIST_COLORS[10.0]),
                                (14.0, DIST_COLORS[14.0]),
                                (20.0, DIST_COLORS[20.0]), (30.0, DIST_COLORS[30.0])):
            r = radius * scale
            dashed = radius >= 20.0
            step = 0.20 if dashed else 0.9
            t = np.arange(0.0, 2.0 * math.pi + step, step)
            xy = [(cx + r * math.cos(a), cy - r * math.sin(a)) for a in t]
            for i in range(len(xy) - 1):
                if dashed and i % 2 == 1:
                    continue
                d.line([xy[i], xy[i + 1]], fill=rgba(colour, 210), width=1)
        # figures + player
        labels = ((6.0, PALETTES[0], "right"), (10.0, PALETTES[1], "left"),
                  (14.0, PALETTES[2], "right"))
        for distance, palette, side in labels:
            fy = cy - distance * scale
            d.ellipse([cx - 3, fy - 3, cx + 3, fy + 3], fill=rgba(palette["dot"], 255))
            if side == "right":
                d.text((cx + 8, fy - 7), f"{distance:.0f} m", font=f_tiny,
                       fill=rgba(palette["dot"], 255))
            else:
                d.text((cx - 8, fy - 7), f"{distance:.0f} m", font=f_tiny,
                       fill=rgba(palette["dot"], 255), anchor="rt")
        d.line([(cx - 6, cy), (cx + 6, cy)], fill=(120, 220, 255, 255), width=2)
        d.line([(cx, cy - 6), (cx, cy + 6)], fill=(120, 220, 255, 255), width=2)
        d.text((cx + 8, cy + 4), "0 m player", font=f_tiny, fill=(120, 220, 255, 255))
        d.text((px0 + 4, py0 + ph - 17), "rings 6/10/14 m (solid) - 20/30 m (dashed) - "
               "camera forward = up", font=f_tiny, fill=(150, 160, 175, 255))

    def _cutout_labels(self, d, f_small, f_tiny) -> None:
        d.text((46, 810), "FIGURE CUT-OUT - 1:1 at every distance",
               font=f_small, fill=(214, 222, 234, 255))
        d.text((46, 830), "orthographic: screen px does not shrink with ground distance",
               font=f_tiny, fill=(160, 170, 185, 255))
        for sx, distance, palette in ((130.0, 6.0, PALETTES[0]),
                                      (280.0, 10.0, PALETTES[1]),
                                      (430.0, 14.0, PALETTES[2])):
            label = f"{distance:.0f} m"
            tw = d.textlength(label, font=f_small)
            d.text((sx - tw / 2.0, 960.0), label, font=f_small,
                   fill=rgba(palette["dot"], 255))
        d.text((46, 988), "model anatomy only - not final art / playtest readability",
               font=f_tiny, fill=(160, 170, 185, 255))

    def _px_ruler(self, d, f_small, f_tiny) -> None:
        x0, y0, w, h = SCREEN_W - 32 - 200, 600, 200, 360
        d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=8,
                            fill=(8, 12, 18, 218), outline=(90, 110, 132, 160))
        d.text((x0 + 12, y0 + 9), "character screen height", font=f_small,
               fill=(214, 222, 234, 255))
        d.text((x0 + 12, y0 + 29), "(H_eff 1.8 m, model math)", font=f_tiny,
               fill=(160, 170, 185, 255))
        d.text((x0 + 12, y0 + 46), f"actual = {self.char_px:.1f} px", font=f_tiny,
               fill=(255, 214, 92, 255))
        axis_x = x0 + 74
        top = y0 + 72
        def y_of(char_px: float) -> float:
            return top + (char_px / 120.0) * 240.0
        axis_bottom = y_of(120.0)
        d.line([(axis_x, y_of(0.0)), (axis_x, axis_bottom)], fill=(200, 208, 220, 220), width=2)
        # 70-90 px target band
        band = [x0 + 34, y_of(TARGET_PX[1]), x0 + w - 14, y_of(TARGET_PX[0])]
        d.rectangle([band[0], min(band[1], band[3]), band[2], max(band[1], band[3])],
                    fill=(80, 200, 140, 60), outline=(100, 225, 160, 170), width=1)
        for value in (0.0, 30.0, 60.0, 90.0, 120.0):
            y = y_of(value)
            d.line([(axis_x - 5, y), (axis_x + 5, y)], fill=(210, 218, 230, 220), width=1)
            d.text((axis_x - 38, y - 7), f"{value:.0f}", font=f_tiny,
                   fill=(190, 198, 212, 255))
        d.text((axis_x + 10, y_of(TARGET_PX[0]) - 18), "target 70-90 px",
               font=f_tiny, fill=(100, 225, 160, 255))
        y_char = y_of(self.char_px)
        d.line([(axis_x - 8, y_char), (axis_x + 8, y_char)], fill=(255, 214, 92, 255), width=3)
        d.text((x0 + 14, y0 + h - 34), "vertical scale: 120 px = 240 screen px",
               font=f_tiny, fill=(150, 160, 175, 255))
        d.text((x0 + 14, y0 + h - 18), "at default zoom (1.0x)", font=f_tiny,
               fill=(150, 160, 175, 255))


# --------------------------------------------------------------------------- #
# Console summary + self checks
# --------------------------------------------------------------------------- #
def run_self_checks(rows: list[dict]) -> None:
    for row in rows:
        size = row["ortho_size"]
        pitch = row["pitch_deg"]
        scale = row["scale_px_per_m"]
        expected_hw = SCREEN_W * size / SCREEN_H
        expected_hd = size / math.sin(math.radians(pitch))
        expected_char = H_EFF * math.cos(math.radians(pitch)) * scale
        assert abs(row["ground_half_width_m"] - expected_hw) < 1e-9, row["viewport"]
        assert abs(row["ground_half_depth_m"] - expected_hd) < 1e-9, row["viewport"]
        assert abs(row["char_px_H_eff_1.8m"] - expected_char) < 1e-9, row["viewport"]
        # screen corner cast ground polygon must lie on z=0
        poly, _, _ = visible_ground_polygon(size, pitch, row["yaw_deg"])
        assert np.max(np.abs(poly[:, 2])) < 1e-9
        # forward feet formula must match direct projection of the ground point
        if row["viewport"] == "shipped":
            g, _ = ground_axes(row["yaw_deg"])
            d = 10.0
            sx, sy, _ = project(g[None, :] * d, pitch, row["yaw_deg"], size)
            assert abs(float(sy[0]) - row["d10_forward_feet_y_px"]) < 1e-9
            assert abs(float(sx[0]) - SCREEN_W / 2.0) < 1e-9
    assert len(rows) == 15
    print("self-checks: OK (corner cast, half-width/half-depth, char px, forward projection)")


def print_summary(rows: list[dict]) -> None:
    shipped = [r for r in rows if r["viewport"] == "shipped"]
    zoom = [r for r in rows if r["viewport"] != "shipped"]
    print()
    print("shipped viewport (H_eff=1.8 m, 1920x1080, yaw=45 deg)")
    header = ("size pitch | char_px within | half_w half_d |  6m  10m  14m fwd/axis/any")
    print(header)
    print("-" * len(header))
    for r in shipped:
        def _flag(value: bool) -> str:
            return "Y" if value else "n"
        flags = "  ".join(
            f"{_flag(r[f'd{int(d)}_inside_forward'])}/"
            f"{_flag(r[f'd{int(d)}_inside_world_axis'])}/"
            f"{_flag(r[f'd{int(d)}_inside_any_direction'])}"
            for d in (6.0, 10.0, 14.0)
        )
        print(f"{r['ortho_size']:4.0f} {r['pitch_deg']:5.0f} | "
              f"{r['char_px_H_eff_1.8m']:7.1f} {str(r['within_70_90']):>6} | "
              f"{r['ground_half_width_m']:6.2f} {r['ground_half_depth_m']:6.2f} | {flags}")
    print()
    print("zoom-out rows (docs/02 section 3.1 nominal sizes 15 m / 23 m)")
    for r in zoom:
        d_target = 20.0 if "size15" in r["viewport"] else 30.0
        key = f"d{int(d_target)}"
        print(f"  {r['viewport']:<18} pitch {r['pitch_deg']:4.0f}  char {r['char_px_H_eff_1.8m']:5.1f} px  "
              f"half_depth {r['ground_half_depth_m']:6.2f}  "
              f"{d_target:.0f}m ahead feet_y={r[key + '_forward_feet_y_px']:7.1f} "
              f"inside_fwd={r[key + '_inside_forward']}  "
              f"inside_world_axis={r[key + '_inside_world_axis']}")
    print()
    n_pass = sum(1 for r in shipped if r["within_70_90"])
    print(f"70-90 px target: {n_pass}/9 shipped (size,pitch) combos pass strictly")
    for d in (6.0, 10.0, 14.0):
        n = sum(1 for r in shipped if r[f"d{int(d)}_inside_forward"])
        print(f"  {d:.0f} m straight ahead inside viewport (feet): {n}/9 combos")
    # size 6 / 8 M0 calibration note
    for size in (6.0, 8.0):
        px = H_EFF * math.cos(math.radians(50.0)) * scale_px_per_m(size)
        print(f"  M0 calibration check: size {size:g} @ pitch 50 deg -> {px:.1f} px "
              f"({'inside' if TARGET_PX[0] <= px <= TARGET_PX[1] else 'OUTSIDE'} 70-90 px)")
    # required zoom sizes for straight-ahead feet visibility
    for distance in (20.0, 30.0):
        for pitch in PITCHES:
            need = distance * math.sin(math.radians(pitch))
            print(f"  size needed for {distance:.0f} m ahead feet at top edge, pitch {pitch:.0f} deg: "
                  f"{need:.2f}")


def print_report_facts() -> None:
    """Numbers quoted in REPORT.md, all derived from the same model constants."""
    print()
    print("REPORT FACTS (same model; quoted in REPORT.md)")
    print("  [A] straight-ahead forward distance at which the WHOLE 1.8 m figure")
    print("      (feet + head) is still inside the frame, whole-body max ahead (m):")
    for size in SHIPPED_SIZES:
        for pitch in PITCHES:
            p = math.radians(pitch)
            scale = scale_px_per_m(size)
            char_px = H_EFF * math.cos(p) * scale
            body_max = (SCREEN_H / 2.0 - char_px) / (math.sin(p) * scale)
            print(f"      size {size:.0f} pitch {pitch:.0f} deg: feet-visible to "
                  f"{size / math.sin(p):5.2f} m, whole-body visible to {body_max:5.2f} m")
    print("  [B] ortho size needed so a figure at a given straight-ahead distance has its")
    print("      whole body inside with a 24 px top margin (centred camera, yaw does not matter):")
    for distance in (14.0, 20.0, 30.0):
        for pitch in PITCHES:
            p = math.radians(pitch)
            need = (distance * math.sin(p) + H_EFF * math.cos(p)) * SCREEN_H / (SCREEN_H - 48.0)
            print(f"      {distance:.0f} m, pitch {pitch:.0f} deg -> size >= {need:5.2f}")
    print("  [C] zoom factor vs character px (H_eff 1.8 m, size 8, pitch 50 deg):")
    p = math.radians(50.0)
    base_px = H_EFF * math.cos(p) * scale_px_per_m(8.0)
    for factor in (0.8, 1.0, 1.2):
        print(f"      zoom {factor:.1f}x -> {base_px * factor:.1f} px")
    print("  [D] camera forward lead (player anchored lower than screen centre) needed to")
    print("      bring the 14 m straight-ahead point into the frame, default size 8 pitch 50 deg:")
    for size in SHIPPED_SIZES:
        for pitch in PITCHES:
            p = math.radians(pitch)
            total_ahead = 2.0 * size / math.sin(p)
            print(f"      size {size:.0f} pitch {pitch:.0f} deg: total visible forward depth "
                  f"{total_ahead:5.2f} m -> player anchor fraction from top >= "
                  f"{14.0 / total_ahead:.3f} for 14 m")
    print("  [E] forward/behind split if the player is anchored at a given fraction of screen height")
    print("      (default size 8, pitch 50 deg; total forward depth 20.88 m):")
    for anchor in (0.55, 0.60, 0.65, 0.67, 0.70):
        total_ahead = 2.0 * 8.0 / math.sin(math.radians(50.0))
        print(f"      anchor {anchor:.2f} from top -> {anchor * total_ahead:5.2f} m ahead, "
              f"{(1.0 - anchor) * total_ahead:5.2f} m behind")
    print("  [F] player anchor fraction from top needed so a 14 m straight-ahead figure has")
    print("      its whole body inside with a 24 px top margin (feet y - char_px >= 24):")
    for size in SHIPPED_SIZES:
        for pitch in PITCHES:
            p = math.radians(pitch)
            scale = scale_px_per_m(size)
            char_px = H_EFF * math.cos(p) * scale
            need_px = 14.0 * math.sin(p) * scale + char_px + 24.0
            fraction = need_px / SCREEN_H
            behind = (1.0 - fraction) * 2.0 * size / math.sin(p)
            print(f"      size {size:.0f} pitch {pitch:.0f} deg: anchor >= {fraction:.3f}, "
                  f"leaves ~{behind:4.2f} m visible behind the player")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TASK-060 2.5D camera validation (model math + renders)")
    parser.add_argument("--out-dir", type=Path, default=SCRIPT_DIR,
                        help="output directory (default: directory containing run.py)")
    parser.add_argument("--seed", type=int, default=SEED, help="ground-speck RNG seed")
    parser.add_argument("--skip-renders", action="store_true", help="only write metrics.csv")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    global SEED
    args = parse_args(argv)
    SEED = int(args.seed)
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"TASK-060 2.5D camera validation | seed={SEED} | out={out_dir}")
    rows = build_metrics()
    run_self_checks(rows)
    print_summary(rows)
    print_report_facts()

    metrics_path = out_dir / "metrics.csv"
    write_metrics_csv(metrics_path, rows)
    print(f"\nwrote {metrics_path}  ({len(rows)} rows x {len(COLUMNS)} columns)")

    written = [metrics_path]
    if not args.skip_renders:
        for size in SHIPPED_SIZES:
            path = out_dir / f"render_size{size:g}.png"
            renderer = SceneRenderer(size, pitch_deg=50.0, yaw_deg=YAW_DEG)
            renderer.render(path)
            written.append(path)
            print(f"wrote {path}  (1920x1080)")

    print("\nsha256:")
    for path in written:
        print(f"  {path.name}  {sha256_of(path)}")
    print("\nDONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
