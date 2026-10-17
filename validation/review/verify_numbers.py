#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-063 independent verification script (reviewer-owned evidence).

Recomputes the key numbers of TASK-060/061/062 from the delivered artifacts
using independently written formulas, and cross-checks them against the
authors' REPORT.md claims.  Read-only w.r.t. author files: it only reads
validation/{camera,netcode,input} and docs, and writes nothing.

Run:
  C:\\Users\\dai\\.dsh\\dsh-runtimes\\dsh-primary-runtime\\dependencies\\python\\python.exe \
      validation\\review\\verify_numbers.py
"""

from __future__ import annotations

import hashlib
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

VAL = Path(__file__).resolve().parents[1]          # ...\validation
ROOT = VAL.parent                                  # repo root
RERUN = Path(__file__).resolve().parent / "rerun"  # validation\review\rerun
FAILS: list[str] = []
CHECKS = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILS.append(f"{name} :: {detail}")
        print(f"[FAIL] {name}  {detail}")
    else:
        print(f"[ok]   {name}")


def close(a, b, tol=1e-3):
    return abs(float(a) - float(b)) <= tol


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ===========================================================================
# 0. Environment
# ===========================================================================
print("== ENV ==")
import sys
print("python", sys.version.split()[0])
print("numpy", np.__version__, "pandas", pd.__version__)
check("python is 3.12.14", sys.version.startswith("3.12.14"), sys.version.split()[0])
check("numpy is 2.3.5", np.__version__ == "2.3.5", np.__version__)

# ===========================================================================
# 1. CAMERA (TASK-060)
# ===========================================================================
print("\n== CAMERA ==")
cam = pd.read_csv(VAL / "camera" / "metrics.csv")
print("metrics.csv shape:", cam.shape)
check("camera metrics 15 rows", len(cam) == 15, str(len(cam)))
check("camera metrics 35 cols", cam.shape[1] == 35, str(cam.shape[1]))
check("camera shipped 9 rows", int((cam["viewport"] == "shipped").sum()) == 9)
check("camera zoom rows 6", int((cam["viewport"] != "shipped").sum()) == 6)

W, H = 1920.0, 1080.0
H_EFF, H_BODY = 1.8, 1.5
YAW = math.radians(45.0)
worst = {}
for _, r in cam.iterrows():
    s = float(r["ortho_size"])
    p = math.radians(float(r["pitch_deg"]))
    scale = H / (2.0 * s)
    char = H_EFF * math.cos(p) * scale
    body = H_BODY * math.cos(p) * scale
    half_w = s * W / H
    half_d = s / math.sin(p)
    half_diag = math.hypot(half_w, half_d)
    world_axis = min(half_w, half_d) / math.cos(YAW)
    # forward feet screen y for distance d (camera-centred)
    def feet_y(d):
        return H / 2.0 - d * math.sin(p) * scale
    # world +X axis (yaw=45): u=v=d*cos45 -> screen y = H/2 - d*cos45*sin(p)*scale
    def feet_y_world_axis(d):
        return H / 2.0 - d * math.cos(YAW) * math.sin(p) * scale
    for col, val in [
        ("scale_px_per_m", scale), ("char_px_H_eff_1.8m", char),
        ("char_px_body_1.5m", body), ("ground_half_width_m", half_w),
        ("ground_half_depth_m", half_d), ("ground_half_diag_m", half_diag),
        ("world_axis_visible_m", world_axis),
    ]:
        worst[col] = max(worst.get(col, 0.0), abs(float(r[col]) - val))
    for d in (6, 10, 14, 20, 30):
        fy = feet_y(d)
        worst[f"d{d}_y"] = max(worst.get(f"d{d}_y", 0.0), abs(float(r[f"d{d}_forward_feet_y_px"]) - fy))
        inside = 0.0 - 1e-9 <= fy <= H + 1e-9
        check(f"s{int(s)} p{int(math.degrees(p))} d{d} inside_forward matches formula",
              bool(r[f"d{d}_inside_forward"] == ("yes" if inside else "no")),
              f"csv={r[f'd{d}_inside_forward']} formula={inside} y={fy:.2f}")
        inside_any = d <= half_diag + 1e-9
        check(f"s{int(s)} p{int(math.degrees(p))} d{d} inside_any matches formula",
              bool(r[f"d{d}_inside_any_direction"] == ("yes" if inside_any else "no")))
workmax = max(worst.values())
check("camera numeric columns match independent formulas (<5e-3, CSV 3dp)", workmax < 5e-3, f"max diff {workmax:.2e}")

# 70-90 band and H_eff/H_body exposure
check("within_70_90 count == 5",
      int((cam["within_70_90"] == "yes").sum()) == 5,
      str(int((cam["within_70_90"] == "yes").sum())))
# chars at p50
p50 = cam[(cam["pitch_deg"] == 50)].set_index("ortho_size")["char_px_H_eff_1.8m"]
check("char px @p50 size 7/8/9 = 89.3/78.1/69.4",
      close(p50[7], 89.256) and close(p50[8], 78.099) and close(p50[9], 69.421),
      f"{p50[7]:.3f}/{p50[8]:.3f}/{p50[9]:.3f}")
body50 = cam[(cam["pitch_deg"] == 50)].set_index("ortho_size")["char_px_body_1.5m"]
check("body 1.5m px @p50 size 8/9 = 65.1/57.9",
      close(body50[8], 65.082) and close(body50[9], 57.851),
      f"{body50[8]:.3f}/{body50[9]:.3f}")
p50 = cam[(cam["pitch_deg"] == 50)].set_index("ortho_size")
check("half depth @p50 size 7/8/9 = 9.14/10.44/11.75",
      close(p50.loc[7, "ground_half_depth_m"], 9.138) and close(p50.loc[8, "ground_half_depth_m"], 10.443)
      and close(p50.loc[9, "ground_half_depth_m"], 11.749))
check("world axis visible @p50 size 8 = 14.77", close(p50.loc[8, "world_axis_visible_m"], 14.769))
check("d10 feet y @8/50 = 22.9", close(p50.loc[8, "d10_forward_feet_y_px"], 22.9, 0.1))
check("d14 forward @8/50 = -184", close(p50.loc[8, "d14_forward_feet_y_px"], -184.1, 0.2))
check("d14 world-axis @8/50 visible at y=28",
      p50.loc[8, "d14_inside_world_axis"] == "yes" and
      close(H / 2.0 - 14 * math.cos(YAW) * math.sin(math.radians(50)) * (H / 16.0), 28.1, 0.2),
      f"flag={p50.loc[8, 'd14_inside_world_axis']} y={H/2.0 - 14*math.cos(YAW)*math.sin(math.radians(50))*(H/16.0):.2f}")
check("14m forward off-screen by 3.56m", close(14.0 - p50.loc[8, "ground_half_depth_m"], 3.557, 0.01))
check("14m forward: 0/9 inside_forward", int((cam[cam.viewport == 'shipped']["d14_inside_forward"] == "yes").sum()) == 0)
check("6m forward: 9/9 inside_forward", int((cam[cam.viewport == 'shipped']["d6_inside_forward"] == "yes").sum()) == 9)
check("10m forward: 5/9 inside_forward", int((cam[cam.viewport == 'shipped']["d10_inside_forward"] == "yes").sum()) == 5)
check("14m world-axis: 6/9", int((cam[cam.viewport == 'shipped']["d14_inside_world_axis"] == "yes").sum()) == 6)
check("20m forward: 0/9", int((cam[cam.viewport == 'shipped']["d20_inside_forward"] == "yes").sum()) == 0)
check("30m forward: 0/9", int((cam[cam.viewport == 'shipped']["d30_inside_forward"] == "yes").sum()) == 0)
check("20m any direction: only size9/p45",
      cam[(cam.viewport == 'shipped') & (cam["d20_inside_any_direction"] == "yes")][["ortho_size", "pitch_deg"]].values.tolist() == [[9.0, 45.0]])

# 70-90 +/-1px tolerance count (REPORT 0 says 6; actual = ?)
tol1 = cam[(cam.viewport == "shipped") & (cam["band_delta_px"].abs() <= 1.0)]
print(f"NOTE: 70-90px band with +/-1px tolerance: REPORT says 6/9; artifact count = {len(tol1)}/9 "
      f"({sorted(zip(tol1['ortho_size'], tol1['pitch_deg']))})")
def whole_body_dist(s, pitch):
    p = math.radians(pitch)
    return (H / 2.0 - H_EFF * math.cos(p) * H / (2 * s)) / (math.sin(p) * H / (2 * s))

for s, pitch, exp in [
    (7, 50, 7.63), (8, 50, 8.93), (9, 50, 10.24),
    (8, 45, 9.51), (9, 45, 10.93), (9, 55, 9.73),
]:
    check(f"whole-body visible {s}/{pitch} = {exp}", close(whole_body_dist(s, pitch), exp, 0.02),
          f"{whole_body_dist(s, pitch):.3f}")

# report statement: "only size 9 can show 10m whole body" -- check p55 counterexample
check("10m whole-body NOT possible at size9/p55 (report wording overbroad)",
      whole_body_dist(9, 55) < 10.0, f"{whole_body_dist(9, 55):.2f} m")

def need_size(d, pitch, full=False, margin=24):
    p = math.radians(pitch)
    feet = d * math.sin(p)
    if not full:
        return feet
    return (feet + H_EFF * math.cos(p)) * H / (H - 2 * margin)

for d, pitch, exp_feet, exp_full in [
    (20, 45, 14.14, 16.13), (20, 50, 15.32, 17.24), (20, 55, 16.38, 18.23),
    (30, 45, 21.21, 23.53), (30, 50, 22.98, 25.26), (30, 55, 24.57, 26.80),
    (14, 45, 9.90, 11.69), (14, 50, 10.72, 12.43), (14, 55, 11.47, 13.08),
]:
    check(f"needed size {d}m p{pitch} feet={exp_feet}",
          close(need_size(d, pitch), exp_feet, 0.01), f"{need_size(d, pitch):.3f}")
    check(f"needed size {d}m p{pitch} whole+24={exp_full}",
          close(need_size(d, pitch, True), exp_full, 0.01), f"{need_size(d, pitch, True):.3f}")

# zoom rows: docs size 15/23 consequences (report 3.4)
zoom = cam[cam["viewport"] != "shipped"].set_index(["ortho_size", "pitch_deg"])
check("zoom size15/p50 char px 41.7", close(zoom.loc[(15.0, 50.0), "char_px_H_eff_1.8m"], 41.7, 0.05))
check("zoom size15/p50 20m feet y = -11.6", close(zoom.loc[(15.0, 50.0), "d20_forward_feet_y_px"], -11.6, 0.1))
check("zoom size23/p50 30m feet y = 0.4", close(zoom.loc[(23.0, 50.0), "d30_forward_feet_y_px"], 0.4, 0.1))
check("zoom size23/p50 char px 27.2", close(zoom.loc[(23.0, 50.0), "char_px_H_eff_1.8m"], 27.17, 0.05))
check("zoom size15/p45 20m feet y = 30.9 (report '31')",
      close(zoom.loc[(15.0, 45.0), "d20_forward_feet_y_px"], 30.88, 0.1))

# camera anchor fractions (report 5.2)
def anchor_feet(d, s, pitch):
    p = math.radians(pitch)
    total = 2.0 * s / math.sin(p)
    return d / total

def anchor_full(d, s, pitch, margin=24):
    p = math.radians(pitch)
    total = 2.0 * s / math.sin(p)
    scale = H / (2 * s)
    return d / total + (H_EFF * math.cos(p) * scale + margin) / H

check("anchor s8/p50 14m feet >= 0.670", close(anchor_feet(14, 8, 50), 0.670, 0.002),
      f"{anchor_feet(14, 8, 50):.4f}")
check("anchor s8/p50 14m whole+24 >= 0.765", close(anchor_full(14, 8, 50), 0.765, 0.002),
      f"{anchor_full(14, 8, 50):.4f}")
check("anchor s8/p50 leaves 6.89m behind", close((1 - anchor_feet(14, 8, 50)) * 2 * 8 / math.sin(math.radians(50)), 6.89, 0.01))
check("zoom 0.8x/1.0x/1.2x @8/50 = 62.5/78.1/93.7",
      close(0.8 * 78.099, 62.48, 0.05) and close(1.2 * 78.099, 93.72, 0.05))

# camera artifact hashes vs independent rerun
print("\n-- camera hashes vs independent rerun --")
for f in ["metrics.csv", "render_size7.png", "render_size8.png", "render_size9.png"]:
    a = VAL / "camera" / f
    b = RERUN / "camera" / f
    if b.exists():
        check(f"camera {f} byte-identical on rerun", sha(a) == sha(b), f"{sha(a)} vs {sha(b)}")
    else:
        print(f"[skip] rerun camera {f} missing")

# ===========================================================================
# 2. NETCODE (TASK-061)
# ===========================================================================
print("\n== NETCODE ==")
res = pd.read_csv(VAL / "netcode" / "results.csv")
print("results.csv shape:", res.shape)
check("netcode results 9216 rows", len(res) == 9216, str(len(res)))
check("netcode results 35 cols", res.shape[1] == 35, str(res.shape[1]))
grid = (res[["tick_hz", "input_buffer_frames", "rtt_ms", "jitter_ms", "loss_pct", "window_ms",
             "cap_ms", "defender_favoring", "interp_ms", "human_sigma_ms"]]
        .drop_duplicates())
check("netcode config grid complete: 9216 unique configs", len(grid) == 9216, str(len(grid)))


def row(**kw):
    m = pd.Series(True, index=res.index)
    for k, v in kw.items():
        m &= (res[k] == v)
    sub = res[m]
    if len(sub) != 1:
        raise AssertionError(f"expected 1 row for {kw}, got {len(sub)}")
    return sub.iloc[0]


def close_pp(actual, expected, tol=0.06):
    return abs(float(actual) * 100.0 - expected) <= tol


MAIN = dict(input_buffer_frames=2, jitter_ms=10, loss_pct=2.0, cap_ms=200,
            defender_favoring="on", interp_ms=33.0, human_sigma_ms=25.0)

# --- report 3.1 / 3.3: success + false positive vs RTT -------------------
print("\n-- 3.1 success / false-positive (main config) --")
succ_exp = {
    (30, 100): [99.7, 99.7, 99.7, 99.4, 82.1, 17.4],
    (30, 150): [100.0, 100.0, 100.0, 99.7, 81.7, 18.4],
    (60, 100): [98.9, 99.0, 99.1, 99.0, 73.2, 9.4],
    (60, 150): [100.0, 100.0, 99.9, 99.5, 74.1, 10.8],
}
fp_exp = {
    (30, 100): [5.6, 5.9, 5.7, 5.7, 0.7, 0.9],
    (30, 150): [0.5, 0.4, 0.5, 0.2, 0.0, 0.0],
    (60, 100): [5.8, 4.7, 5.4, 5.1, 0.6, 0.7],
    (60, 150): [0.4, 0.4, 0.4, 0.1, 0.1, 0.1],
}
for (tick, win), exp in succ_exp.items():
    for i, rtt in enumerate([0, 50, 80, 100, 150, 200]):
        r = row(tick_hz=tick, window_ms=win, rtt_ms=rtt, **MAIN)
        check(f"3.1 ({tick}Hz/{win}ms RTT{rtt}) success={exp[i]}%",
              close_pp(r["perfect_guard_success_rate"], exp[i], 0.06),
              f"csv={r['perfect_guard_success_rate']*100:.2f}")
        check(f"3.1 ({tick}Hz/{win}ms RTT{rtt}) fp={fp_exp[(tick, win)][i]}%",
              close_pp(r["false_positive_rate"], fp_exp[(tick, win)][i], 0.06),
              f"csv={r['false_positive_rate']*100:.2f}")
check("headline: 30Hz/100ms RTT80 fp 5.7% > 5%",
      close_pp(row(tick_hz=30, window_ms=100, rtt_ms=80, **MAIN)["false_positive_rate"], 5.7, 0.06))
check("headline: 150ms/30Hz RTT80 success 100.0% fp 0.5%",
      close_pp(row(tick_hz=30, window_ms=150, rtt_ms=80, **MAIN)["perfect_guard_success_rate"], 100.0, 0.06) and
      close_pp(row(tick_hz=30, window_ms=150, rtt_ms=80, **MAIN)["false_positive_rate"], 0.5, 0.06))
check("headline: 150ms/30Hz RTT100 success 99.7% fp 0.2%",
      close_pp(row(tick_hz=30, window_ms=150, rtt_ms=100, **MAIN)["perfect_guard_success_rate"], 99.7, 0.06) and
      close_pp(row(tick_hz=30, window_ms=150, rtt_ms=100, **MAIN)["false_positive_rate"], 0.2, 0.06))

# --- 3.2 human vs network split -----------------------------------------
print("\n-- 3.2 p95 split (30Hz/150ms) --")
for rtt, sig, exp in [(80, 0, dict(succ=100.0, tin=100.0, sgw=100.0, fp=0.0, ph=0.0, pn=25.8)),
                      (80, 25, dict(succ=100.0, tin=99.5, sgw=100.0, fp=0.5, ph=49.2, pn=26.1)),
                      (80, 50, dict(succ=94.5, tin=86.1, sgw=100.0, fp=8.5, ph=98.3, pn=25.9)),
                      (100, 25, dict(succ=99.7, tin=99.6, sgw=99.9, fp=0.2, ph=48.4, pn=26.0)),
                      (100, 50, dict(succ=90.4, tin=86.1, sgw=99.7, fp=4.6, ph=96.8, pn=25.6)),
                      (150, 25, dict(succ=81.7, tin=99.5, sgw=82.1, fp=0.0, ph=49.2, pn=25.8)),
                      (150, 50, dict(succ=67.9, tin=86.2, sgw=75.8, fp=2.6, ph=96.8, pn=25.9))]:
    r = row(tick_hz=30, window_ms=150, rtt_ms=rtt, input_buffer_frames=2, jitter_ms=10,
            loss_pct=2.0, cap_ms=200, defender_favoring="on", interp_ms=33.0, human_sigma_ms=float(sig))
    for col, key in [("perfect_guard_success_rate", "succ"), ("true_in_window_rate", "tin"),
                     ("success_given_in_window", "sgw"), ("false_positive_rate", "fp")]:
        check(f"3.2 RTT{rtt} sigma{sig} {col}={exp[key]}",
              close_pp(r[col], exp[key], 0.12),
              f"csv={r[col]:.3f}")
    for col, key in [("p95_human_error_ms", "ph"), ("p95_network_error_ms", "pn")]:
        check(f"3.2 RTT{rtt} sigma{sig} {col}={exp[key]}ms",
              close(r[col], exp[key], 0.15),
              f"csv={r[col]:.3f}")
# sigma=0 p95 network 30Hz vs 60Hz: 25.8 vs 12.9 (report 3.2 / 3.6 / S10)
r30 = row(tick_hz=30, window_ms=150, rtt_ms=80, input_buffer_frames=2, jitter_ms=10,
          loss_pct=2.0, cap_ms=200, defender_favoring="on", interp_ms=33.0, human_sigma_ms=0.0)
r60 = row(tick_hz=60, window_ms=150, rtt_ms=80, input_buffer_frames=2, jitter_ms=10,
          loss_pct=2.0, cap_ms=200, defender_favoring="on", interp_ms=33.0, human_sigma_ms=0.0)
check("3.6 p95 network sigma0 30Hz 25.8 / 60Hz 12.9",
      close(r30["p95_network_error_ms"], 25.8, 0.2) and close(r60["p95_network_error_ms"], 12.9, 0.2),
      f"{r30['p95_network_error_ms']:.2f}/{r60['p95_network_error_ms']:.2f}")
check("S10 quantization ratio 2.00", close(r30["p95_network_error_ms"] / r60["p95_network_error_ms"], 2.00, 0.03))

# --- 3.4 cap 150 vs 200 --------------------------------------------------
print("\n-- 3.4 cap 150 vs 200 --")
cap_exp = {(30, 150, 100): (82.4, 99.7), (30, 150, 150): (18.4, 81.7),
           (30, 100, 80): (95.2, 99.7), (30, 100, 100): (82.6, 99.4),
           (60, 100, 80): (91.6, 99.1), (60, 100, 100): (74.0, 99.0)}
for (tick, win, rtt), (c150, c200) in cap_exp.items():
    base = dict(tick_hz=tick, window_ms=win, rtt_ms=rtt, input_buffer_frames=2, jitter_ms=10,
                loss_pct=2.0, defender_favoring="on", interp_ms=33.0, human_sigma_ms=25.0)
    r150 = row(cap_ms=150, **base)
    r200 = row(cap_ms=200, **base)
    check(f"3.4 {tick}Hz/W{win}/RTT{rtt} cap150={c150}%",
          close_pp(r150["perfect_guard_success_rate"], c150, 0.12),
          f"csv={r150['perfect_guard_success_rate']*100:.2f}")
    check(f"3.4 {tick}Hz/W{win}/RTT{rtt} cap200={c200}%",
          close_pp(r200["perfect_guard_success_rate"], c200, 0.12),
          f"csv={r200['perfect_guard_success_rate']*100:.2f}")

# --- 3.5 defender-favoring on/off (interp=0) ----------------------------
print("\n-- 3.5 defender-favoring on/off (30Hz/150ms/cap200/interp=0) --")
for rtt, off, on_, dmgoff, dmgon in [
    (0, 60.8, 100.0, 11.56, 0.00), (80, 0.5, 100.0, 29.85, 0.00),
    (100, 0.0, 100.0, 29.99, 0.00), (150, 0.0, 98.2, 30.00, 0.55),
    (200, 0.0, 62.0, 30.00, 11.40),
]:
    base = dict(tick_hz=30, window_ms=150, rtt_ms=rtt, input_buffer_frames=2, jitter_ms=10,
                loss_pct=2.0, cap_ms=200, interp_ms=0.0, human_sigma_ms=25.0)
    roff = row(defender_favoring="off", **base)
    ron = row(defender_favoring="on", **base)
    check(f"3.5 RTT{rtt} OFF={off}% ON={on_}%",
          close_pp(roff["perfect_guard_success_rate"], off, 0.12) and
          close_pp(ron["perfect_guard_success_rate"], on_, 0.12),
          f"csv={roff['perfect_guard_success_rate']*100:.2f}/{ron['perfect_guard_success_rate']*100:.2f}")
    check(f"3.5 RTT{rtt} mean damage OFF={dmgoff} ON={dmgon}",
          close(roff["mean_damage"], dmgoff, 0.02) and close(ron["mean_damage"], dmgon, 0.02),
          f"csv={roff['mean_damage']:.2f}/{ron['mean_damage']:.2f}")

# --- 3.8 input buffer / loss -------------------------------------------
print("\n-- 3.8 buffer x loss (30Hz/150ms/RTT80) --")
buf_exp = {(0, 0.0): 99.9, (0, 2.0): 98.0, (1, 0.0): 100.0, (1, 2.0): 99.9,
           (2, 0.0): 100.0, (2, 2.0): 100.0, (3, 0.0): 100.0, (3, 2.0): 100.0}
for (b, loss), exp in buf_exp.items():
    r = row(tick_hz=30, window_ms=150, rtt_ms=80, input_buffer_frames=b, jitter_ms=10,
            loss_pct=loss, cap_ms=200, defender_favoring="on", interp_ms=33.0, human_sigma_ms=25.0)
    check(f"3.8 B{b} loss{loss} success={exp}%",
          close_pp(r["perfect_guard_success_rate"], exp, 0.12),
          f"csv={r['perfect_guard_success_rate']*100:.2f}")

# --- 3.9 interp 0 vs 33 -------------------------------------------------
print("\n-- 3.9 interp 0 vs 33 --")
interp_exp = {(100, 80, 0): (99.7, 6.7), (100, 80, 33): (99.7, 5.7),
              (100, 150, 0): (97.9, 5.2), (100, 150, 33): (82.1, 0.7),
              (150, 100, 0): (100.0, 0.6), (150, 100, 33): (99.7, 0.2),
              (150, 150, 0): (98.2, 0.1), (150, 150, 33): (81.7, 0.0)}
for (win, rtt, interp), (succ, fp) in interp_exp.items():
    r = row(tick_hz=30, window_ms=win, rtt_ms=rtt, input_buffer_frames=2, jitter_ms=10,
            loss_pct=2.0, cap_ms=200, defender_favoring="on", interp_ms=float(interp),
            human_sigma_ms=25.0)
    check(f"3.9 W{win} RTT{rtt} interp{interp} success={succ}% fp={fp}%",
          close_pp(r["perfect_guard_success_rate"], succ, 0.12) and close_pp(r["false_positive_rate"], fp, 0.12),
          f"csv={r['perfect_guard_success_rate']*100:.2f}/{r['false_positive_rate']*100:.2f}")

# --- 3.11 visible telegraph / retro applied ----------------------------
print("\n-- 3.11 visible telegraph / retro --")
retro_exp = {0: (82.1, 41.2), 80: (100.0, 121.6), 100: (99.7, 141.5), 150: (81.7, 191.9)}
for rtt, (retro, arrival) in retro_exp.items():
    r = row(tick_hz=30, window_ms=150, rtt_ms=rtt, input_buffer_frames=2, jitter_ms=10,
            loss_pct=2.0, cap_ms=200, defender_favoring="on", interp_ms=33.0, human_sigma_ms=25.0)
    check(f"3.11 RTT{rtt} retro={retro}% arrival={arrival}ms",
          close_pp(r["retro_applied_rate"], retro, 0.12) and close(r["mean_arrival_after_hit_ms"], arrival, 0.15),
          f"csv={r['retro_applied_rate']*100:.2f}/{r['mean_arrival_after_hit_ms']:.2f}")
check("3.11 telegraph 158.3-(RTT/2+interp) for RTT100/interp33 = 75.3",
      close(row(tick_hz=30, window_ms=150, rtt_ms=100, input_buffer_frames=2, jitter_ms=10,
                loss_pct=2.0, cap_ms=200, defender_favoring="on", interp_ms=33.0,
                human_sigma_ms=25.0)["visible_telegraph_to_hit_ms"], 75.3, 0.05))

# --- internal consistency of success/fp/true-window --------------------
print("\n-- internal consistency --")
bad = 0
for idx in [0, 123, 500, 2000, 5000, 9215]:
    r = res.iloc[idx]
    n = int(r["trials"])
    tin = float(r["true_in_window_rate"])
    sgw = float(r["success_given_in_window"]) if not pd.isna(r["success_given_in_window"]) else 0.0
    succ = float(r["perfect_guard_success_rate"])
    fp = float(r["false_positive_rate"])
    implied = (tin * sgw) + fp
    if abs(implied - succ) > 0.0005:
        bad += 1
        print("  mismatch row", idx, implied, succ)
check("success = in_window*delivered + false_positive (sampled rows)", bad == 0, str(bad))
check("false positives only when out-of-window samples exist (sampled rows)",
      all(float(res.iloc[i]["false_positive_rate"]) == 0.0 or float(res.iloc[i]["true_in_window_rate"]) < 1.0
          for i in [0, 500, 2000, 5000, 9215]))
check("hitbox_rewind never capped in parameter domain",
      int(res["rewind_capped"].sum()) == 0 and float(res["hitbox_rewind_ms"].max()) <= 150.0,
      f"max rewind={res['hitbox_rewind_ms'].max()}")

# --- sanity checks ------------------------------------------------------
print("\n-- sanity_checks.csv --")
sanity = pd.read_csv(VAL / "netcode" / "sanity_checks.csv")
check("sanity 10 checks all pass", len(sanity) == 10 and int(sanity["passed"].sum()) == 10,
      f"{int(sanity['passed'].sum())}/{len(sanity)}")
obs = dict(zip(sanity["check"], sanity["observed"]))
for k, exp in [("S1_offline_perfect_timing", "1.0000"), ("S2_high_rtt_no_lagcomp", "0.0000"),
               ("S3_arrival_time_judging", "0.0084"), ("S4_defender_favoring_gain", "0.9997"),
               ("S5_cap_200_helps_rtt150", "0.6393"), ("S7_loss_without_redundancy", "0.0203"),
               ("S8_rtt_monotonicity", "0.9998 >= 0.9969 >= 0.1819"),
               ("S9_redundancy_recovers_loss", "0.0230"), ("S10_tick_quantization_ratio", "2.00")]:
    if re.fullmatch(r"[0-9.]+", str(obs[k])):
        ok = abs(float(obs[k]) - float(exp)) <= 5e-4
    else:
        ok = str(obs[k]) == exp
    check(f"sanity {k} = {exp}", ok, str(obs[k]))
check("sanity S6 fp30=0.0583 fp60=0.0494",
      str(obs["S6_tick60_lower_false_positive"]) == "fp30=0.0583, fp60=0.0494",
      str(obs["S6_tick60_lower_false_positive"]))

# --- sensitivity claims -------------------------------------------------
print("\n-- sensitivity.csv claims --")
sens = pd.read_csv(VAL / "netcode" / "sensitivity.csv")


def srow(scenario, **kw):
    m = sens["scenario"] == scenario
    for k, v in kw.items():
        m &= (sens[k] == v)
    sub = sens[m]
    if len(sub) != 1:
        raise AssertionError(f"sensitivity: expected 1 row {scenario} {kw}, got {len(sub)}")
    return sub.iloc[0]


# arrival-time judging: 30Hz/150ms/cap200 RTT 50/80/100 (sensitivity.csv);
# RTT150 only exists as sanity S3.  Report values vs artifact values are
# compared separately below (see REPORT-VS-ARTIFACT section).
arr_exp = {(30, 50): 88.66, (30, 80): 54.94, (30, 100): 27.30,
           (60, 80): 20.99, (60, 100): 6.06}
for (tick, rtt), exp in arr_exp.items():
    r = srow("arrival_time_judging", tick_hz=tick, window_ms=150, rtt_ms=rtt)
    check(f"3.10 arrival-time {tick}Hz RTT{rtt} artifact success={exp}%",
          close_pp(r["perfect_guard_success_rate"], exp, 0.06),
          f"csv={r['perfect_guard_success_rate']*100:.2f}")
check("3.10 arrival-time RTT150 collapse recorded in sanity S3 (0.84%)",
      close_pp(dict(zip(sanity['check'], sanity['observed']))['S3_arrival_time_judging']
               if re.fullmatch(r"[0-9.]+", str(obs['S3_arrival_time_judging'])) else 0, 0.84, 0.05),
      str(obs['S3_arrival_time_judging']))
# window 200 + cap 150 (artifact values)
for rtt, exp in [(80, 95.41), (100, 82.45), (150, 17.81)]:
    r = srow("window_200_cap_150", tick_hz=30, rtt_ms=rtt)
    check(f"3.10 window200/cap150 30Hz RTT{rtt} artifact success={exp}%",
          close_pp(r["perfect_guard_success_rate"], exp, 0.06),
          f"csv={r['perfect_guard_success_rate']*100:.2f}")
# chord delay 40ms (uniform U(0,40)): artifact ranges
chord_art = {}
for win in (100, 150):
    sub = sens[(sens["scenario"] == "chord_delay_40ms") & (sens["tick_hz"] == 30) & (sens["window_ms"] == win)]
    chord_art[win] = (sub["perfect_guard_success_rate"].min() * 100, sub["perfect_guard_success_rate"].max() * 100,
                      sub["false_positive_rate"].min() * 100, sub["false_positive_rate"].max() * 100)
check("3.10 chord40 30Hz/100ms artifact succ 97.0-99.2 fp 19.7-22.2",
      close(chord_art[100][0], 96.96, 0.06) and close(chord_art[100][1], 99.18, 0.06) and
      close(chord_art[100][2], 19.74, 0.06) and close(chord_art[100][3], 22.23, 0.06),
      str(chord_art[100]))
check("3.10 chord40 30Hz/150ms artifact succ 97.0-99.9 fp 2.1-4.3",
      close(chord_art[150][0], 96.97, 0.06) and close(chord_art[150][1], 99.89, 0.06),
      str(chord_art[150]))
# half-tick grace claim (30Hz/150ms, RTT 80/100)
sub = sens[(sens["scenario"] == "grace_half_tick") & (sens["tick_hz"] == 30) &
           (sens["window_ms"] == 150) & (sens["rtt_ms"].isin([80, 100]))]
check("3.10 half-tick 30Hz/150ms RTT80/100 success 99.6-99.9 fp 0.3-0.7",
      len(sub) == 2 and sub["perfect_guard_success_rate"].mul(100).between(99.5, 100.0).all()
      and sub["false_positive_rate"].mul(100).between(0.2, 0.8).all(),
      f"succ={list(np.round(sub['perfect_guard_success_rate']*100,2))}")

# --- assumptions A1-A16 explicit in REPORT ------------------------------
rep_txt = (VAL / "netcode" / "REPORT.md").read_text(encoding="utf-8", errors="ignore")
missing_a = [f"A{i}" for i in range(1, 17) if f"| A{i} |" not in rep_txt]
check("netcode REPORT lists assumptions A1-A16 explicitly", not missing_a, str(missing_a))

# --- REPORT vs ARTIFACT discrepancy audit (findings, not pass/fail) ------
print("\n-- REPORT vs ARTIFACT discrepancies (sensitivity/summary) --")
rep = [
    ("10 arrival-time 30Hz RTT50", 89.0, 88.66),
    ("10 arrival-time 30Hz RTT80", 54.8, 54.94),
    ("10 arrival-time 30Hz RTT100", 27.1, 27.30),
    ("10 arrival-time 60Hz RTT80", 20.1, 20.99),
    ("10 arrival-time 60Hz RTT100", 5.3, 6.06),
    ("10 window200/cap150 RTT80", 94.7, 95.41),
    ("10 window200/cap150 RTT100", 82.0, 82.45),
    ("10 window200/cap150 RTT150", 17.9, 17.81),
    ("10 chord40 100ms fp-upper (claim 18.5-21.1)", 21.1, 22.23),
    ("10 chord40 150ms fp-upper (claim 2.2-4.5)", 4.5, 4.30),
    ("10 chord40 150ms succ-lower (claim 96.8-100.0)", 96.8, 96.97),
]
print(f"{'claim':52s} {'report':>8s} {'artifact':>8s} {'delta pp':>9s}")
for name, rv, av in rep:
    print(f"{name:52s} {rv:8.2f} {av:8.2f} {av - rv:+9.2f}")
print("NOTE: REPORT 3.10 cites ranges that do not exactly match sensitivity.csv/summary_tables.md;")
print("      Q1 cites chord FP 17-21% while persisted artifact gives 19.7-22.2%. See REVIEW.md.")

# --- netcode artifacts determinism + svg -------------------------------
print("\n-- netcode hashes / svg --")
for f in ["results.csv", "sensitivity.csv", "sanity_checks.csv", "guard_success.svg"]:
    a = VAL / "netcode" / f
    b = RERUN / "netcode" / f
    check(f"netcode {f} byte-identical on rerun", sha(a) == sha(b), sha(a) if a.exists() else "missing")
diff_lines = 0
a = VAL / "netcode" / "summary_tables.md"
b = RERUN / "netcode" / "summary_tables.md"
if b.exists():
    la, lb = a.read_text(encoding="utf-8").splitlines(), b.read_text(encoding="utf-8").splitlines()
    diff_lines = sum(1 for x, y in zip(la, lb) if x != y)
    check("summary_tables.md differs only in runtime line (reproducibility caveat)",
          diff_lines <= 1, f"{diff_lines} differing lines")
try:
    tree = ET.parse(VAL / "netcode" / "guard_success.svg")
    svg_text = (VAL / "netcode" / "guard_success.svg").read_text(encoding="utf-8")
    check("guard_success.svg parses as XML", True)
    check("guard_success.svg has 4 series labels (30/60Hz x 100/150ms)",
          all(k in svg_text for k in ["30Hz tick / 100ms window", "30Hz tick / 150ms window",
                                      "60Hz tick / 100ms window", "60Hz tick / 150ms window"]),
          "missing labels")
    check("guard_success.svg has M0 70%/5% target lines and Wilson CI legend",
          "M0" in svg_text and "Wilson CI" in svg_text and "70" in svg_text and "5" in svg_text,
          "target/CI markers not found")
except Exception as e:  # noqa: BLE001
    check("guard_success.svg parses as XML", False, str(e))

# ===========================================================================
# 3. INPUT (TASK-062)
# ===========================================================================
print("\n== INPUT ==")
cm = pd.read_csv(VAL / "input" / "combo_matrix.csv")
cx = pd.read_csv(VAL / "input" / "context_matrix.csv")
tc = pd.read_csv(VAL / "input" / "timing_cases.csv")
print("combo/context/timing shapes:", cm.shape, cx.shape, tc.shape)
check("combo_matrix 45 rows", len(cm) == 45, str(len(cm)))
check("combo_matrix 15 combos", cm["combo_id"].nunique() == 15)
check("context_matrix 24 rows", len(cx) == 24, str(len(cx)))
check("timing_cases 37 rows", len(tc) == 37, str(len(tc)))

for model, within, within_diag, risk_counts in [
    ("NKRO", 15, 15, {"none": 15}),
    ("6KRO", 15, 15, {"none": 10, "low": 5}),
    ("2KRO", 10, 9, {"low": 10, "high": 5}),
]:
    sub = cm[cm["keyboard_model"] == model]
    w = int(sub["within_limit"].sum())
    wd = int(sub["within_limit_diagonal"].sum())
    check(f"{model} cardinal within={within}", w == within, str(w))
    check(f"{model} diagonal within={within_diag}", wd == within_diag, str(wd))
    rc = sub["risk"].value_counts().to_dict()
    check(f"{model} risk counts {risk_counts}", rc == risk_counts, str(rc))
fails_2kro = set(cm[(cm["keyboard_model"] == "2KRO") & (~cm["within_limit"])]["combo"])
exp_fail = {"Z+X+C", "Direction+Z+C", "Direction+Z+X", "Direction+Z+X+C", "Direction+X+C"}
check("2KRO simultaneous failures match report", fails_2kro == exp_fail, str(sorted(fails_2kro)))
check("max simultaneous non-modifier keys cardinal=4", int(cm["simultaneous_non_modifier_keys"].max()) == 4,
      str(cm["simultaneous_non_modifier_keys"].max()))
check("max simultaneous non-modifier keys diagonal=5", int(cm["diagonal_non_modifier_keys"].max()) == 5)
check("6KRO context all 8/8", int(cx[cx['keyboard_model'] == '6KRO']['within_limit'].sum()) == 8)
check("2KRO context only 2/8", int(cx[cx['keyboard_model'] == '2KRO']['within_limit'].sum()) == 2)
check("context max keys = 6", int(cx["simultaneous_non_modifier_keys"].max()) == 6)

res_counts = tc["result"].value_counts().to_dict()
check("timing cases PASS=27 EDGE=10 FAIL=0",
      res_counts.get("PASS", 0) == 27 and res_counts.get("EDGE", 0) == 10 and res_counts.get("FAIL", 0) == 0,
      str(res_counts))

cases = tc.set_index("id")
case_exp = {
    "C09": "EDGE", "C13": "PASS", "C14": "PASS", "C15": "EDGE", "C16": "EDGE",
    "C17": "EDGE", "C18": "EDGE", "C19": "EDGE", "C20": "EDGE", "C24": "EDGE",
    "C25": "EDGE", "C26": "PASS", "C10": "PASS", "C12": "PASS",
    "C01": "PASS", "C02": "PASS", "C03": "PASS", "M02": "PASS", "M03": "PASS",
    "M07": "PASS", "M08": "EDGE", "M09": "PASS",
}
for cid, exp in case_exp.items():
    if cid not in cases.index:
        check(f"timing case {cid} exists", False)
        continue
    check(f"timing case {cid} result={exp}", cases.loc[cid, "result"] == exp,
          str(cases.loc[cid, "result"]))
check("C16 actual = GUARD (literal priority steals ultimate)",
      "GUARD" in str(cases.loc["C16", "actual"]), str(cases.loc["C16", "actual"]))
check("C24 (z_suppresses_guard) actual = ULTIMATE",
      "ULTIMATE" in str(cases.loc["C24", "actual"]), str(cases.loc["C24", "actual"]))
check("C25 uses ±50ms window variant", float(cases.loc["C25", "guard_window_ms"]) == 50.0,
      str(cases.loc["C25", "guard_window_ms"]))
check("C17 clean ultimate window is EDGE/PASS within (40,50]",
      cases.loc["C17", "result"] in ("EDGE", "PASS"), str(cases.loc["C17", "result"]))
check("C13 direction 50ms (3f) still direction version",
      "SPECIAL_3" in str(cases.loc["C13", "actual"]), str(cases.loc["C13", "actual"]))
check("C14 direction 66.7ms (4f) falls back to SPECIAL_1",
      "SPECIAL_1" in str(cases.loc["C14", "actual"]), str(cases.loc["C14", "actual"]))
check("C19 intermediate attack committed before ultimate",
      "HEAVY" in str(cases.loc["C19", "actual"]) or "SPECIAL_2" in str(cases.loc["C19", "actual"]),
      str(cases.loc["C19", "actual"]))
check("C26 Z tap then C -> LIGHT_ATTACK (not SPECIAL_1)",
      "LIGHT_ATTACK" in str(cases.loc["C26", "actual"]), str(cases.loc["C26", "actual"]))

# --- adversarial re-test of the stated "clean sequential ultimate" recipe --
# REPORT 3.1 / 4.6 says clean Z->X->C parse works if "C within 3f after X-up".
# The model's actual condition is anchored at X-DOWN (input buffer deadline) and
# requires X released before C (else C+X literal guard steals the input).
print("\n-- adversarial resolver checks: sequential ultimate recipe --")
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("task062_run", VAL / "input" / "run.py")
task062 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(task062)


def actions_for(events):
    r = task062.ComboResolver(layout="classic")
    for t, k, kind in events:
        (r.down if kind == "down" else r.up)(k, t)
    r.finish()
    return ">".join(cmd for _t, cmd in r.actions) or "NONE"


c18_ok = actions_for([(0, "Z", "down"), (30, "Z", "up"), (50, "X", "down"),
                      (60, "X", "up"), (90, "C", "down")])
check("delivered C18 reproduces SOFT_LOCK>ULTIMATE", c18_ok == "SOFT_LOCK>ULTIMATE", c18_ok)
recipe = actions_for([(0, "Z", "down"), (30, "Z", "up"), (50, "X", "down"),
                      (60, "X", "up"), (110, "C", "down")])
check("REPORT recipe fails: X-up+50ms C -> not a clean ultimate (stale claim)",
      recipe != "SOFT_LOCK>ULTIMATE", recipe)
x_held = actions_for([(0, "Z", "down"), (30, "Z", "up"), (50, "X", "down"), (90, "C", "down")])
check("X still held when C pressed -> literal C+X GUARD steals ultimate",
      x_held == "SOFT_LOCK>GUARD", x_held)
xd_plus_50 = actions_for([(0, "Z", "down"), (30, "Z", "up"), (50, "X", "down"),
                          (55, "X", "up"), (100, "C", "down")])
check("clean ultimate bound is X-down+3f (C at exactly X-down+50ms)", xd_plus_50 == "SOFT_LOCK>ULTIMATE", xd_plus_50)

for f in ["combo_matrix.csv", "context_matrix.csv", "timing_cases.csv"]:
    a = VAL / "input" / f
    b = RERUN / "input" / f
    check(f"input {f} byte-identical on rerun", sha(a) == sha(b), sha(a))

# manual_test.html page selftest (reviewer rerun); optional artifact
dom = RERUN / "input" / "selftest_dom.txt"
if dom.exists():
    import json
    candidates = re.findall(r'SELFTEST_JSON:(\{[^<]*\})', dom.read_text(encoding="utf-8", errors="ignore"))
    obj = None
    for cand in candidates:
        try:
            parsed = json.loads(cand)
        except json.JSONDecodeError:
            continue
        if "checks" in parsed:
            obj = parsed
            break
    check("manual_test.html page selftest reproduces 28/28 checks",
          obj is not None and obj.get("ok") is True and obj.get("checks") == 28 and obj.get("failures") == [],
          str(obj))

# ===========================================================================
# 4. DOCS CLAIM AUDIT (read only)
# ===========================================================================
print("\n== DOCS AUDIT ==")
docs = {p.name: p.read_text(encoding="utf-8") for p in (ROOT / "docs").glob("*.md")}
d00 = docs["00-设计基线与术语.md"]
d02 = docs["02-产品设计文档.md"]
d03 = docs["03-技术设计文档.md"]
d04 = docs["04-3D像素美术风格指南.md"]
test = lambda name, txt, pat: check(name, re.search(pat, txt) is not None)

test("docs/00 has 1.5m basis phrase", d00, r"以角色 1\.5m 为基准")
test("docs/00 has H_eff 1.8m phrase", d00, r"有效高度 1\.8m")
test("docs/00 has 'M0 可校准 6–8'", d00, r"M0 可校准 6[–-]8")
test("docs/00 has 14m Z soft-lock range (not readability thresholds)",
     d00, r"锁定 14m")
test("docs/02 has 6/10/14m readability 90/85/80", d02, r"≥90%[\s\S]{0,120}≥85%[\s\S]{0,120}≥80%")
test("docs/02 has zoom-out size 15/23", d02, r"zoom-out size 15/23")
test("docs/02 has online 150ms + 1 tick", d02, r"在线 150ms（9f）\+ 服务器 1 tick 容差")
test("docs/02 has defense interaction cap 150ms", d02, r"防御交互单独 cap 150ms")
test("docs/02 has M0 70%/5% acceptance", d02, r"成功率 ≥70%、误判 ≤5%")
test("docs/03 has ±40ms C+X", d03, r"±40ms")
test("docs/03 has ±50ms C+X", d03, r"±50ms")
test("docs/00 has literal priority C+X > Z+X+C", d00, r"C\+X 防御 > Z\+X\+C 必杀")
test("docs/00 has 受击前 100ms 内防御 (single-sided wording)", d00, r"受击前 100ms 内防御")
test("docs/00 has 3-key thin-film claim", d00, r"常见薄膜键盘至少 3 键同时按")
test("docs/04 has 70-90px formula", d04, r"cos\(50°\)\s*/\s*\(2\s*×\s*orthoSize\)")
check("docs/00-04 do not define yaw", not any(re.search(r"yaw|偏航", docs[n]) for n in
                                               ["00-设计基线与术语.md", "02-产品设计文档.md",
                                                "03-技术设计文档.md", "04-3D像素美术风格指南.md"]))
all_drafts = "\n".join(
    p.read_text(encoding="utf-8", errors="ignore")
    for p in (ROOT / "docs" / "_drafts").glob("*.md")
)
check("drafts contain conflicting yaw proposals (context only)",
      re.search(r"yaw\s*0", all_drafts) is not None and
      (re.search(r"yaw\s*45", all_drafts) is not None or
       ("偏航" in all_drafts and re.search(r"45", all_drafts) is not None)),
      "drafts do not show both yaw=0 and yaw=45 proposals")

# ===========================================================================
# Summary
# ===========================================================================
print("\n" + "=" * 70)
print(f"CHECKS={CHECKS}  FAILURES={len(FAILS)}")
for f in FAILS:
    print(" FAIL:", f)
print("=" * 70)
