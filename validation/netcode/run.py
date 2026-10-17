#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TASK-061 -- Perfect guard / lag-compensation technical validation (Monte Carlo model).

This script is the single source of every number in ``REPORT.md``.  It is a
**synthetic discrete-event model**, NOT a Unity/Fusion measurement and NOT a
player study.  It exists to answer three decision questions at M0-prep level:

1. Is a 100 ms perfect-guard window at 30 Hz tick + ~200 ms rewind + 2-3 frame
   input buffer fair/viable online?
2. Is a 150 ms online window + 1 server tick grace enough?
3. Is a 60 Hz ranked tick rate necessary?

Model summary (see ``REPORT.md`` section 2 and the function docstring of
``simulate`` for the full assumption list A1-A16):

* Light attack: startup 8 f + active 3 f @ 60 fps; the hit lands at
  startup + active/2 = 158.333 ms after the attack starts (docs/00 §3.5,
  docs/02 §4.4).
* The defender is an expert who makes the guard input coincide with the hit
  **as they perceive it** (one-way delay + interpolation/snapshot delay),
  plus a Gaussian human timing error (sigma = 0 / 25 / 50 ms; 0 = perfect-timing
  control) and 0-1 frame of 60 Hz client sampling delay.
* The guard edge is sent redundantly and arrives after one-way delay + jitter;
  an input buffer of B frames absorbs up to B client frames of positive jitter
  and provides B+1 redundant copies (packet loss survives unless all copies are
  lost).  A server-side input buffer delays both players' inputs and the hit
  resolution equally, so it cancels in relative timing; this is assumption A6.
* The server resolves the hit at its next tick (30 or 60 Hz) with a random tick
  phase => hit-detection delay delta ~ U(0, 1 tick).
* Defender-favoring ON: (a) server reconstructs the guard timestamp in the
  defender's perceived timeline (subtracts one-way + interpolation), (b) a guard
  input may be applied retroactively to an already-resolved hit within the
  lag-compensation cap (150/200 ms), (c) +1 server tick of window grace.
  Defender-favoring OFF: raw per-server-time timestamps, no retroactive
  application, no grace (the "strict realtime" policy that REV-002 B2 warns
  about).
* Determinism: master seed 20261017; configs are evaluated in a fixed nested
  loop order with one numpy Generator; default 10,000 trials per config.

Outputs (written next to this script by default):

* ``results.csv``          -- full factorial matrix, one row per config.
* ``guard_success.svg``    -- success rate (and false-positive rate) vs RTT.
* ``sensitivity.csv``      -- extra scenarios (half-tick grace, arrival-time
                              judging, enlarged window) used in REPORT.md §5.
* ``sanity_checks.csv``    -- model sanity checks with pass/fail.
* ``summary_tables.md``    -- markdown tables of the key slices used by REPORT.

Run:
    python run.py                 # full run, ~1 min, fixed seed
    python run.py --quick         # 2,000 trials/config (debug only)
    python run.py --trials 50000  # more precision (not the shipped deliverable)
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Baseline constants (docs/00 §3.5, docs/02 §4.4, docs/03 §5.4)
# ---------------------------------------------------------------------------
MASTER_SEED = 20261017
DT_CLIENT_MS = 1000.0 / 60.0          # 16.666... ms, client input/sampling rate 60 Hz
STARTUP_FRAMES = 8.0                  # light attack startup, 60 fps frames
ACTIVE_FRAMES = 3.0                   # light attack active frames
HIT_OFFSET_MS = (STARTUP_FRAMES + ACTIVE_FRAMES / 2.0) * DT_CLIENT_MS  # 158.333 ms
BASE_DAMAGE = 30.0                    # docs/00 §3.5 light attack damage
NORMAL_BLOCK_DAMAGE_FACTOR = 0.2      # docs/02 §4.5: guard => HP damage x0.2

DEFAULT_TRIALS = 10_000

# Full factorial axes required by validation/README.md TASK-061 + two extra
# modelling axes (interpolation delay 0/33 ms, human sigma 0/25/50 ms).
TICKS: Tuple[int, ...] = (30, 60)
BUFFERS: Tuple[int, ...] = (0, 1, 2, 3)
RTTS: Tuple[int, ...] = (0, 50, 80, 100, 150, 200)
JITTERS: Tuple[int, ...] = (0, 10)
LOSSES: Tuple[float, ...] = (0.0, 2.0)
WINDOWS: Tuple[int, ...] = (100, 150)
CAPS: Tuple[int, ...] = (150, 200)
DEFENDERS: Tuple[bool, ...] = (False, True)
INTERPS: Tuple[int, ...] = (0, 33)
SIGMAS: Tuple[int, ...] = (0, 25, 50)


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Params:
    """One point of the factorial matrix."""

    tick_hz: int
    input_buffer_frames: int
    rtt_ms: int
    jitter_ms: int
    loss_pct: float
    window_ms: int
    cap_ms: int
    defender_favoring: bool
    interp_ms: int
    human_sigma_ms: int


def wilson_half_width(p: float, n: int, z: float = 1.96) -> float:
    """95 % Wilson score interval half-width for a binomial proportion."""
    if n <= 0:
        return float("nan")
    denom = 1.0 + z * z / n
    half = z * math.sqrt(max(p * (1.0 - p), 0.0) / n + z * z / (4.0 * n * n)) / denom
    return float(half)


def simulate(
    p: Params,
    trials: int,
    rng: np.random.Generator,
    *,
    grace_override_ms: Optional[float] = None,
    timestamp_mode: str = "client_ts",
    chord_delay_ms: float = 0.0,
    press_bias_ms: float = 0.0,
    hit_quantum_override_ms: Optional[float] = None,
) -> Dict[str, float]:
    """Run ``trials`` Monte Carlo trials of one configuration.

    Ground-truth timeline (all times are relative, in ms; A1 = perfect clock
    sync / zero clock-estimation error, which makes this a model, not an
    engine measurement):

    * ``t_hit``        = 158.333 ms (attack hit offset, docs/00 §3.5).
    * ``delta ~ U(0, 1 tick)``
                       = server hit-detection delay (next tick boundary);
                         ``t_detect = t_hit + delta``.
    * ``e_h ~ N(0, sigma)``
                       = human timing error (0 = perfect-timing control).
    * ``q_c ~ U(0, 16.67)``
                       = 60 Hz client sampling delay of the guard edge.
    * ``j_view = U(-J, J)`` when interpolation delay is 0, else 0
                       = view jitter; a 33 ms interpolation buffer absorbs the
                         +/-10 ms packet jitter, raw (0 ms) rendering does not.
    * ``t_press = t_hit + OW + interp + j_view + e_h + q_c``
                       = wall-clock press time; the expert defender aligns with
                         the perceived hit (one-way + interpolation late), so
                         this is the model of "按下时机 = 看到的命中时刻 + 误差".
    * ``OW = RTT/2``   = one-way delay (symmetric assumption A4).
    * ``j_up ~ U(-J, J)``, ``late_j = max(0, j_up - B*frame)``
                       = up-link jitter not absorbed by the B-frame input
                         buffer (A6).
    * ``t_arr = t_press + OW + late_j``
                       = guard input arrival at the server.
    * Loss: guard is sent B+1 redundant copies; all-lost prob = loss^(B+1).
    * Server-evaluated guard time:
        - client_ts + defender-favoring ON:
          ``t_guard_ev = t_press - (OW + interp)`` (reconstructed perceived
          timeline) and the input may retroactively convert a resolved hit
          if ``t_arr <= t_detect + cap``; window = W/2 + 1 tick grace.
        - client_ts + OFF: ``t_guard_ev = t_press``; must arrive before the
          hit resolution (``t_arr <= t_detect``); no grace.
        - arrival_ts (sensitivity only): ``t_guard_ev = t_arr``; shows what
          happens if the server ignores ``ClientTimeMs`` (REV-002 B2 concern).
    * Perfect guard granted iff the input is not lost, arrives within the
      policy deadline and ``|t_guard_ev - t_detect| <= W/2 + grace``.
    * Ground truth for fairness: ``actual_err = j_view + e_h + q_c``; "should
      have been perfect" iff ``|actual_err| <= W/2`` (omniscient judge, so
      false positives = server grants perfect outside the true window).
    * Damage illustration: perfect 0; normal guard (accepted and arrived
      *before* hit resolution) = 30 x 0.2 = 6; otherwise 30 (A15).

    Optional sensitivity knobs (used only by ``run_sensitivity``; the main
    matrix keeps both at 0): ``chord_delay_ms`` adds a uniform 0..x ms C+X
    chord-recognition delay (docs/03 §4.1: C+X window ±40 ms), and
    ``press_bias_ms`` shifts the expert's press (e.g. -8 ms to compensate the
    60 Hz sampling delay).
    """
    n = int(trials)
    if n <= 0:
        raise ValueError("trials must be positive")

    tick_ms = 1000.0 / p.tick_hz
    ow = p.rtt_ms / 2.0
    jitter = float(p.jitter_ms)
    loss = p.loss_pct / 100.0
    window = float(p.window_ms)
    cap = float(p.cap_ms)
    sigma = float(p.human_sigma_ms)
    interp = float(p.interp_ms)
    buffer_frames = int(p.input_buffer_frames)

    t_hit = np.full(n, HIT_OFFSET_MS, dtype=np.float64)

    # Server hit detection at the next tick boundary: random tick phase.
    # ``hit_quantum_override_ms`` explores docs/03 §5.1's 60 Hz combat substep
    # hit timing even when the network tick is 30 Hz.
    hit_quantum = tick_ms if hit_quantum_override_ms is None else float(hit_quantum_override_ms)
    delta = rng.uniform(0.0, hit_quantum, n)
    t_detect = t_hit + delta

    # Human timing error (0 ms = perfect-timing control).
    if sigma > 0.0:
        e_h = rng.normal(0.0, sigma, n)
    else:
        e_h = np.zeros(n, dtype=np.float64)

    # 60 Hz client sampling: the press is captured on the next input sample.
    q_c = rng.uniform(0.0, DT_CLIENT_MS, n)

    # View jitter is absorbed only when an interpolation buffer exists.
    if jitter > 0.0 and interp <= 0.0:
        j_view = rng.uniform(-jitter, jitter, n)
    else:
        j_view = np.zeros(n, dtype=np.float64)

    t_press = t_hit + ow + interp + j_view + e_h + q_c + press_bias_ms
    if chord_delay_ms > 0.0:
        # C+X chord recognition: the second key must arrive inside the chord
        # window before the guard edge is emitted.
        t_press = t_press + rng.uniform(0.0, chord_delay_ms, n)

    # Up-link jitter; the server input buffer absorbs up to B client frames.
    if jitter > 0.0:
        j_up = rng.uniform(-jitter, jitter, n)
        late_j = np.maximum(0.0, j_up - buffer_frames * DT_CLIENT_MS)
    else:
        late_j = np.zeros(n, dtype=np.float64)

    t_arr = t_press + ow + late_j

    # Redundant input send: B+1 copies; only all-copies-lost kills the input.
    p_all_lost = loss ** (buffer_frames + 1) if loss > 0.0 else 0.0
    if p_all_lost > 0.0:
        lost = rng.random(n) < p_all_lost
    else:
        lost = np.zeros(n, dtype=bool)

    if grace_override_ms is not None:
        grace = float(grace_override_ms)
    else:
        grace = tick_ms if p.defender_favoring else 0.0

    arrival_budget = cap if p.defender_favoring else 0.0
    accepted = (~lost) & (t_arr <= (t_detect + arrival_budget))

    if timestamp_mode == "arrival_ts":
        t_guard_ev = t_arr
    else:
        view_comp = (ow + interp) if p.defender_favoring else 0.0
        t_guard_ev = t_press - view_comp

    err = t_guard_ev - t_detect
    half_window_eff = window / 2.0 + grace
    perfect = accepted & (np.abs(err) <= half_window_eff)

    actual_err = t_press - (t_hit + ow + interp)  # j_view + e_h + q_c
    true_in_window = np.abs(actual_err) <= window / 2.0
    # Human/execution quality without network view jitter (skills + sampling).
    human_in_window = np.abs(e_h + q_c) <= window / 2.0

    false_positive = perfect & (~true_in_window)
    out_of_window = ~true_in_window

    # Illustrative damage economy (A15): perfect parry negates; a normal block
    # only works if the server had the guard before the hit was resolved.
    damage = np.full(n, BASE_DAMAGE, dtype=np.float64)
    normal_block = accepted & (~perfect) & (t_arr <= t_detect)
    damage[normal_block] = BASE_DAMAGE * NORMAL_BLOCK_DAMAGE_FACTOR
    damage[perfect] = 0.0

    # Perfect guards that were granted retroactively after hit resolution: from
    # the attacker's client view the hit was cancelled after the fact.
    retro = perfect & (t_arr > t_detect)

    success = float(perfect.mean())
    fp = float(false_positive.mean())
    n_true = int(true_in_window.sum())
    n_out = int(out_of_window.sum())

    return {
        "trials": n,
        "perfect_guard_success_rate": success,
        "perfect_guard_success_ci95": wilson_half_width(success, n),
        "true_in_window_rate": float(true_in_window.mean()),
        "human_in_window_rate": float(human_in_window.mean()),
        "success_given_in_window": (
            float(perfect[true_in_window].mean()) if n_true > 0 else float("nan")
        ),
        "false_positive_rate": fp,
        "false_positive_ci95": wilson_half_width(fp, n),
        "false_positive_given_out_window": (
            float(false_positive.sum() / n_out) if n_out > 0 else float("nan")
        ),
        "mean_damage": float(damage.mean()),
        "p95_timing_error_ms": float(np.percentile(np.abs(err), 95.0)),
        "p95_human_error_ms": float(np.percentile(np.abs(e_h), 95.0)),
        "p95_network_error_ms": float(np.percentile(np.abs(err - e_h), 95.0)),
        "mean_signed_error_ms": float(err.mean()),
        "mean_abs_error_ms": float(np.abs(err).mean()),
        "acceptance_rate": float(accepted.mean()),
        "retro_applied_rate": float(retro.mean()),
        "mean_arrival_after_hit_ms": float((t_arr - t_hit).mean()),
        "grace_ms": grace,
        "effective_half_window_ms": half_window_eff,
        "hitbox_rewind_ms": min(ow + interp, cap),
        "rewind_capped": int((ow + interp) > cap),
        "all_lost_probability": p_all_lost,
        "n_true_in_window": n_true,
        # Reaction-time feasibility diagnostic (static per config): how long is
        # the visible warning window between perceiving the attack start and the
        # true hit?  Perception is delayed by one-way + interpolation, so this
        # shrinks with latency.  Even at 0 ms RTT it is only 158 ms (< typical
        # 200-250 ms visual reaction), i.e. perfect guard is anticipatory.
        "visible_telegraph_to_hit_ms": HIT_OFFSET_MS - (ow + interp),
    }


# ---------------------------------------------------------------------------
# Matrix + auxiliary runs
# ---------------------------------------------------------------------------
CONFIG_COLUMNS = [
    "tick_hz",
    "input_buffer_frames",
    "rtt_ms",
    "jitter_ms",
    "loss_pct",
    "window_ms",
    "cap_ms",
    "defender_favoring",
    "interp_ms",
    "human_sigma_ms",
]

METRIC_COLUMNS = [
    "trials",
    "perfect_guard_success_rate",
    "perfect_guard_success_ci95",
    "true_in_window_rate",
    "human_in_window_rate",
    "success_given_in_window",
    "false_positive_rate",
    "false_positive_ci95",
    "false_positive_given_out_window",
    "mean_damage",
    "p95_timing_error_ms",
    "p95_human_error_ms",
    "p95_network_error_ms",
    "mean_signed_error_ms",
    "mean_abs_error_ms",
    "acceptance_rate",
    "retro_applied_rate",
    "mean_arrival_after_hit_ms",
    "grace_ms",
    "effective_half_window_ms",
    "hitbox_rewind_ms",
    "rewind_capped",
    "all_lost_probability",
    "n_true_in_window",
    "visible_telegraph_to_hit_ms",
]

CSV_COLUMNS = CONFIG_COLUMNS + METRIC_COLUMNS


def config_dict(p: Params) -> Dict[str, object]:
    d: Dict[str, object] = {
        "tick_hz": p.tick_hz,
        "input_buffer_frames": p.input_buffer_frames,
        "rtt_ms": p.rtt_ms,
        "jitter_ms": p.jitter_ms,
        "loss_pct": p.loss_pct,
        "window_ms": p.window_ms,
        "cap_ms": p.cap_ms,
        "defender_favoring": "on" if p.defender_favoring else "off",
        "interp_ms": p.interp_ms,
        "human_sigma_ms": p.human_sigma_ms,
    }
    return d


def iter_matrix() -> Iterable[Params]:
    """Fixed nested-loop order -> deterministic RNG stream (A14)."""
    for tick in TICKS:
        for buffer_frames in BUFFERS:
            for rtt in RTTS:
                for jitter in JITTERS:
                    for loss in LOSSES:
                        for window in WINDOWS:
                            for cap in CAPS:
                                for defender in DEFENDERS:
                                    for interp in INTERPS:
                                        for sigma in SIGMAS:
                                            yield Params(
                                                tick_hz=tick,
                                                input_buffer_frames=buffer_frames,
                                                rtt_ms=rtt,
                                                jitter_ms=jitter,
                                                loss_pct=loss,
                                                window_ms=window,
                                                cap_ms=cap,
                                                defender_favoring=defender,
                                                interp_ms=interp,
                                                human_sigma_ms=sigma,
                                            )


MATRIX_SIZE = (
    len(TICKS)
    * len(BUFFERS)
    * len(RTTS)
    * len(JITTERS)
    * len(LOSSES)
    * len(WINDOWS)
    * len(CAPS)
    * len(DEFENDERS)
    * len(INTERPS)
    * len(SIGMAS)
)


def run_matrix(trials: int, seed: int) -> List[Dict[str, object]]:
    rng = np.random.default_rng(seed)
    rows: List[Dict[str, object]] = []
    t0 = time.time()
    for i, p in enumerate(iter_matrix(), start=1):
        res = simulate(p, trials, rng)
        row: Dict[str, object] = dict(config_dict(p))
        row.update(res)
        rows.append(row)
        if i % 1024 == 0 or i == MATRIX_SIZE:
            elapsed = time.time() - t0
            print(
                f"  matrix {i}/{MATRIX_SIZE} configs, {elapsed:6.1f}s elapsed",
                flush=True,
            )
    return rows


def run_sensitivity(trials: int, seed: int) -> List[Dict[str, object]]:
    """Extra scenarios for REPORT.md discussion (not part of results.csv)."""
    rng = np.random.default_rng(seed)
    rows: List[Dict[str, object]] = []

    def add(scenario: str, p: Params, **kwargs: object) -> None:
        res = simulate(p, trials, rng, **kwargs)  # type: ignore[arg-type]
        row: Dict[str, object] = {"scenario": scenario}
        row.update(config_dict(p))
        row.update(res)
        rows.append(row)

    # S1: half-tick grace instead of 1 full tick (fairness trade-off).
    for tick in (30, 60):
        for window in (100, 150):
            for rtt in (80, 100, 150):
                p = Params(tick, 2, rtt, 10, 2.0, window, 200, True, 33, 25)
                add("grace_half_tick", p, grace_override_ms=(1000.0 / tick) / 2.0)

    # S1b: zero grace -- isolates the fairness cost of the 1-tick tolerance.
    for tick in (30, 60):
        for window in (100, 150):
            for rtt in (80, 100):
                for sigma in (25, 50):
                    p = Params(tick, 2, rtt, 10, 2.0, window, 200, True, 33, sigma)
                    add("grace_zero", p, grace_override_ms=0.0)

    # S1c: half-tick grace with a casual player (sigma = 50 ms).
    for tick in (30, 60):
        for window in (100, 150):
            for rtt in (80, 100):
                p = Params(tick, 2, rtt, 10, 2.0, window, 200, True, 33, 50)
                add("grace_half_tick_sigma50", p, grace_override_ms=(1000.0 / tick) / 2.0)

    # S1d: hit time resolved at 60 Hz combat substeps (docs/03 §5.1) even when
    # the network tick is 30 Hz.  This isolates the tick-quantization cost.
    for window in (100, 150):
        for rtt in (80, 100):
            for sigma in (25, 50):
                p = Params(30, 2, rtt, 10, 2.0, window, 200, True, 33, sigma)
                add("substep_60hz_hit", p, hit_quantum_override_ms=DT_CLIENT_MS)

    # S2: server ignores ClientTimeMs and judges the arrival time (REV-002 B2).
    for tick in (30, 60):
        for rtt in (0, 50, 80, 100):
            p = Params(tick, 2, rtt, 10, 2.0, 150, 200, True, 33, 25)
            add("arrival_time_judging", p, timestamp_mode="arrival_ts")

    # S4b: C+X chord-recognition delay (docs/03 §4.1: C+X window ±40 ms).
    for tick in (30, 60):
        for window in (100, 150):
            for rtt in (0, 80, 100):
                p = Params(tick, 2, rtt, 10, 2.0, window, 200, True, 33, 25)
                add("chord_delay_40ms", p, chord_delay_ms=40.0)

    # S4c: expert learns to pre-press ~8 ms to compensate 60 Hz sampling delay.
    for tick in (30, 60):
        for rtt in (80, 100):
            p = Params(tick, 2, rtt, 10, 2.0, 100, 200, True, 33, 25)
            add("press_bias_minus_8ms", p, press_bias_ms=-DT_CLIENT_MS / 2.0)

    # S3: enlarge the window to 200 ms -- does that fix high-RTT delivery?
    for tick in (30, 60):
        for rtt in (80, 100, 150):
            p = Params(tick, 2, rtt, 10, 2.0, 200, 150, True, 33, 25)
            add("window_200_cap_150", p)

    # S4: defender-favoring OFF (strict realtime) at the M0 target RTTs.
    for rtt in (0, 80, 100, 150):
        p = Params(30, 2, rtt, 10, 2.0, 150, 200, False, 33, 25)
        add("defender_favoring_off", p)

    return rows


def run_sanity_checks(trials: int, seed: int) -> List[Dict[str, object]]:
    """Sanity checks: the model must reproduce basic expected behaviour."""
    checks: List[Dict[str, object]] = []

    def check(
        name: str,
        description: str,
        metric: str,
        expected: str,
        observed: object,
        passed: bool,
        note: str = "",
    ) -> None:
        checks.append(
            {
                "check": name,
                "description": description,
                "metric": metric,
                "expected": expected,
                "observed": observed,
                "passed": int(bool(passed)),
                "note": note,
            }
        )

    # 1. Offline, perfect timing (sigma=0), no jitter/loss/interp: near 100 %.
    rng = np.random.default_rng(seed + 101)
    p = Params(30, 0, 0, 0, 0.0, 100, 150, True, 0, 0)
    r = simulate(p, max(trials, 20_000), rng)
    check(
        "S1_offline_perfect_timing",
        "RTT 0 / loss 0 / jitter 0 / sigma 0 (perfect timing control) must yield near-100 %.",
        "perfect_guard_success_rate",
        ">= 0.999",
        f"{r['perfect_guard_success_rate']:.4f}",
        r["perfect_guard_success_rate"] >= 0.999,
    )

    # 2. 200 ms RTT, 100 ms window, no lag compensation (defender-favoring off).
    rng = np.random.default_rng(seed + 102)
    p = Params(60, 0, 200, 0, 0.0, 100, 200, False, 0, 0)
    r = simulate(p, trials, rng)
    check(
        "S2_high_rtt_no_lagcomp",
        "RTT 200 / W=100 / no lag-comp (strict realtime) must be poor.",
        "perfect_guard_success_rate",
        "<= 0.02",
        f"{r['perfect_guard_success_rate']:.4f}",
        r["perfect_guard_success_rate"] <= 0.02,
    )

    # 3. Judging guard by arrival time (not ClientTimeMs) destroys online play.
    rng = np.random.default_rng(seed + 103)
    p = Params(30, 2, 150, 10, 2.0, 150, 200, True, 33, 25)
    r = simulate(p, trials, rng, timestamp_mode="arrival_ts")
    check(
        "S3_arrival_time_judging",
        "Arrival-time judging instead of input timestamps at RTT 150 must collapse (<= 0.05).",
        "perfect_guard_success_rate",
        "<= 0.05",
        f"{r['perfect_guard_success_rate']:.4f}",
        r["perfect_guard_success_rate"] <= 0.05,
    )

    # 4. Defender-favoring must materially help at RTT 80.
    rng = np.random.default_rng(seed + 104)
    base = Params(30, 2, 80, 10, 2.0, 150, 200, False, 33, 25)
    off = simulate(base, trials, rng)
    on = simulate(Params(30, 2, 80, 10, 2.0, 150, 200, True, 33, 25), trials, rng)
    gain = on["perfect_guard_success_rate"] - off["perfect_guard_success_rate"]
    check(
        "S4_defender_favoring_gain",
        "Defender-favoring ON must gain >= 0.20 success at RTT 80 (retro + timestamp compensation).",
        "success(ON) - success(OFF)",
        ">= 0.20",
        f"{gain:.4f}",
        gain >= 0.20,
    )

    # 5. Raising the defense cap 150 -> 200 must help at RTT 150.
    rng = np.random.default_rng(seed + 105)
    r150 = simulate(Params(30, 2, 150, 10, 2.0, 150, 150, True, 33, 25), trials, rng)
    r200 = simulate(Params(30, 2, 150, 10, 2.0, 150, 200, True, 33, 25), trials, rng)
    gain_cap = r200["perfect_guard_success_rate"] - r150["perfect_guard_success_rate"]
    check(
        "S5_cap_200_helps_rtt150",
        "Cap 200 must gain >= 0.20 success over cap 150 at RTT 150.",
        "success(cap200) - success(cap150)",
        ">= 0.20",
        f"{gain_cap:.4f}",
        gain_cap >= 0.20,
    )

    # 6. 60 Hz tick must produce fewer false positives than 30 Hz (smaller tick).
    rng = np.random.default_rng(seed + 106)
    p30 = Params(30, 2, 80, 10, 2.0, 100, 200, True, 33, 25)
    p60 = Params(60, 2, 80, 10, 2.0, 100, 200, True, 33, 25)
    fp30 = simulate(p30, trials, rng)["false_positive_rate"]
    fp60 = simulate(p60, trials, rng)["false_positive_rate"]
    check(
        "S6_tick60_lower_false_positive",
        "60 Hz tick false-positive rate <= 30 Hz tick at RTT 80/W=100.",
        "fp(60Hz) - fp(30Hz)",
        "<= 0.0",
        f"fp30={fp30:.4f}, fp60={fp60:.4f}",
        fp60 <= fp30,
    )

    # 7. 2 % loss without redundancy costs ~2 % success.
    rng = np.random.default_rng(seed + 107)
    r_loss0 = simulate(Params(30, 0, 0, 0, 0.0, 100, 150, True, 0, 0), trials, rng)
    r_loss2 = simulate(Params(30, 0, 0, 0, 2.0, 100, 150, True, 0, 0), trials, rng)
    loss_drop = r_loss0["perfect_guard_success_rate"] - r_loss2["perfect_guard_success_rate"]
    check(
        "S7_loss_without_redundancy",
        "2 % loss with buffer 0 must cost roughly 2 % success.",
        "success(loss0) - success(loss2)",
        "0.01 .. 0.03",
        f"{loss_drop:.4f}",
        0.01 <= loss_drop <= 0.03,
    )

    # 8. Success must be monotone non-increasing in RTT for the baseline config.
    rng = np.random.default_rng(seed + 108)
    vals = []
    for rtt in (0, 100, 200):
        r = simulate(Params(30, 2, rtt, 10, 2.0, 150, 200, True, 33, 25), trials, rng)
        vals.append(r["perfect_guard_success_rate"])
    monotone = vals[0] >= vals[1] >= vals[2]
    check(
        "S8_rtt_monotonicity",
        "Success must not increase with RTT (0 -> 100 -> 200 ms).",
        "s(0) >= s(100) >= s(200)",
        "monotone",
        f"{vals[0]:.4f} >= {vals[1]:.4f} >= {vals[2]:.4f}",
        monotone,
    )

    # 9. Redundancy (buffer >= 1) must recover most of the packet loss.
    rng = np.random.default_rng(seed + 109)
    b0_loss2 = simulate(Params(30, 0, 0, 0, 2.0, 100, 150, True, 0, 25), trials, rng)
    b2_loss2 = simulate(Params(30, 2, 0, 0, 2.0, 100, 150, True, 0, 25), trials, rng)
    recovery = b2_loss2["perfect_guard_success_rate"] - b0_loss2["perfect_guard_success_rate"]
    check(
        "S9_redundancy_recovers_loss",
        "Buffer 2 (redundant copies) must recover most of the 2 % loss penalty.",
        "success(B2) - success(B0) at loss 2 %",
        ">= 0.015",
        f"{recovery:.4f}",
        recovery >= 0.015,
    )

    # 10. Server tick quantization is ~2x smaller at 60 Hz than 30 Hz.
    rng = np.random.default_rng(seed + 110)
    e30 = simulate(Params(30, 0, 0, 0, 0.0, 100, 150, True, 0, 0), trials, rng)
    e60 = simulate(Params(60, 0, 0, 0, 0.0, 100, 150, True, 0, 0), trials, rng)
    ratio = e30["p95_timing_error_ms"] / max(e60["p95_timing_error_ms"], 1e-9)
    check(
        "S10_tick_quantization_ratio",
        "p95 timing error at 30 Hz must be clearly larger than at 60 Hz.",
        "p95(30Hz) / p95(60Hz)",
        ">= 1.5",
        f"{ratio:.2f}",
        ratio >= 1.5,
    )

    return checks


# ---------------------------------------------------------------------------
# CSV / SVG / summary writers
# ---------------------------------------------------------------------------
def fmt_float(value: float, digits: int = 6) -> float:
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return float("nan")
    return float(f"{float(value):.{digits}g}")


def write_csv(path: Path, rows: Sequence[Dict[str, object]], columns: Sequence[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_svg(index: Dict[Tuple[object, ...], Dict[str, object]], path: Path) -> None:
    """Render guard_success.svg from the matrix rows (no third-party libs).

    Left panel: perfect-guard success rate vs RTT.
    Right panel: false-positive rate vs RTT (same curves).
    Curves: 30/60 Hz tick x 100/150 ms window; cap 200, defender-favoring ON,
    buffer 2, jitter 10 ms, loss 2 %, interp 33 ms, human sigma 25 ms.
    """
    curves = [
        ("30Hz tick / 100ms window", 30, 100, "#c0392b"),
        ("30Hz tick / 150ms window", 30, 150, "#e67e22"),
        ("60Hz tick / 100ms window", 60, 100, "#2c6fb5"),
        ("60Hz tick / 150ms window", 60, 150, "#16a085"),
    ]

    def get_row(tick: int, window: int, rtt: int) -> Dict[str, object]:
        key = (tick, 2, rtt, 10, 2.0, window, 200, "on", 33, 25)
        if key not in index:
            raise KeyError(f"missing SVG data row: {key}")
        return index[key]

    width, height = 1000, 730
    p1x, p1y, p1w, p1h = 78, 146, 392, 380
    p2x, p2y, p2w, p2h = 558, 146, 392, 380

    def x_coord(panel_x: int, panel_w: int, rtt: float) -> float:
        return panel_x + (rtt / 200.0) * panel_w

    def y_success(value: float) -> float:
        return p1y + p1h - max(0.0, min(1.0, value)) * p1h

    def y_fp(value: float) -> float:
        return p2y + p2h - max(0.0, min(0.20, value)) / 0.20 * p2h

    def txt(
        x: float,
        y: float,
        text: str,
        size: float = 12.0,
        anchor: str = "start",
        fill: str = "#222222",
        weight: str = "normal",
        rotate: Optional[float] = None,
    ) -> str:
        rot = f' transform="rotate({rotate:.1f} {x:.1f} {y:.1f})"' if rotate else ""
        return (
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="Microsoft YaHei, Noto Sans CJK SC, '
            f'Segoe UI, sans-serif" font-size="{size:.1f}" text-anchor="{anchor}" '
            f'fill="{fill}" font-weight="{weight}"{rot}>{text}</text>'
        )

    def line(
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: str,
        sw: float = 1.0,
        dash: Optional[str] = None,
        opacity: float = 1.0,
    ) -> str:
        d = f' stroke-dasharray="{dash}"' if dash else ""
        return (
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{sw:.1f}" opacity="{opacity:.2f}"{d}/>'
        )

    def polyline(points: Sequence[Tuple[float, float]], color: str) -> str:
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        return (
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.4" '
            f'stroke-linejoin="round" stroke-linecap="round"/>'
        )

    parts: List[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
    )
    parts.append(
        '<title id="title">TASK-061 perfect guard success rate vs RTT (synthetic Monte Carlo model)</title>'
    )
    parts.append(
        '<desc id="desc">Discrete-event Monte Carlo model, seed 20261017, 10,000 trials per point. '
        "Light attack startup 8f + active 3f at 60 fps; hit judged at 30 or 60 Hz server tick; "
        "guard edge sent with 60 Hz client sampling, redundant input copies (buffer 2), jitter 10 ms, "
        "loss 2 %; interpolation/snapshot delay 33 ms; human timing error sigma 25 ms; "
        "defense-interaction lag-compensation cap 200 ms; defender-favoring ON (client-timestamp "
        "reconstruction + retroactive guard evaluation + 1 tick window grace). "
        "Synthetic model, not a Unity/Fusion measurement and not a player study.</desc>"
    )

    # Background + titles.
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>')
    parts.append(
        txt(40, 44, "TASK-061 · 完美格挡成功率 vs RTT（Monte Carlo 模型，非引擎实测）", 21, fill="#1a1a1a", weight="bold")
    )
    parts.append(
        txt(
            40,
            70,
            "窗口 100/150ms（以真实命中为中心）· tick 30/60Hz · cap 200ms · defender-favoring ON · "
            "输入缓冲 2 帧 · 抖动 10ms · 丢包 2% · 插值 33ms · 人类时序 sigma=25ms · 每点 1 万次",
            12.5,
            fill="#555555",
        )
    )

    # Panel 1: success rate.
    parts.append(
        txt(p1x, p1y - 36, "完美格挡成功率", 15, fill="#1a1a1a", weight="bold")
    )
    parts.append(
        txt(p1x, p1y - 19, "（越高越好；M0 验收目标 ≥70% @ RTT 80/100ms）", 11.5, fill="#666666")
    )
    for pct in range(0, 101, 20):
        y = y_success(pct / 100.0)
        parts.append(line(p1x, y, p1x + p1w, y, "#e6e6e6", 1.0))
        parts.append(txt(p1x - 10, y + 4, f"{pct}%", 11, anchor="end", fill="#666666"))
    for rtt in (0, 50, 100, 150, 200):
        x = x_coord(p1x, p1w, rtt)
        parts.append(line(x, p1y, x, p1y + p1h, "#f0f0f0", 1.0))
        parts.append(txt(x, p1y + p1h + 20, f"{rtt}", 11, anchor="middle", fill="#666666"))
    parts.append(line(p1x, p1y + p1h, p1x + p1w, p1y + p1h, "#999999", 1.2))
    parts.append(line(p1x, p1y, p1x, p1y + p1h, "#999999", 1.2))
    parts.append(txt(p1x + p1w / 2, p1y + p1h + 42, "RTT (ms)", 12.5, anchor="middle", fill="#444444"))
    parts.append(
        txt(p1x - 48, p1y + p1h / 2, "成功率", 12.5, anchor="middle", fill="#444444", rotate=-90)
    )
    y70 = y_success(0.70)
    parts.append(line(p1x, y70, p1x + p1w, y70, "#888888", 1.4, dash="6,4"))
    parts.append(txt(p1x + p1w - 4, y70 - 6, "M0 ≥70%", 10.5, anchor="end", fill="#777777"))

    # Panel 2: false positives.
    parts.append(
        txt(p2x, p2y - 36, "误判率（真实时序不在窗口内却被判完美）", 15, fill="#1a1a1a", weight="bold")
    )
    parts.append(
        txt(p2x, p2y - 19, "（越低越好；M0 验收目标 ≤5%）", 11.5, fill="#666666")
    )
    for pct in (0, 5, 10, 15, 20):
        y = y_fp(pct / 100.0)
        parts.append(line(p2x, y, p2x + p2w, y, "#e6e6e6", 1.0))
        parts.append(txt(p2x - 10, y + 4, f"{pct}%", 11, anchor="end", fill="#666666"))
    for rtt in (0, 50, 100, 150, 200):
        x = x_coord(p2x, p2w, rtt)
        parts.append(line(x, p2y, x, p2y + p2h, "#f0f0f0", 1.0))
        parts.append(txt(x, p2y + p2h + 20, f"{rtt}", 11, anchor="middle", fill="#666666"))
    parts.append(line(p2x, p2y + p2h, p2x + p2w, p2y + p2h, "#999999", 1.2))
    parts.append(line(p2x, p2y, p2x, p2y + p2h, "#999999", 1.2))
    parts.append(txt(p2x + p2w / 2, p2y + p2h + 42, "RTT (ms)", 12.5, anchor="middle", fill="#444444"))
    parts.append(
        txt(p2x - 48, p2y + p2h / 2, "误判率", 12.5, anchor="middle", fill="#444444", rotate=-90)
    )
    y5 = y_fp(0.05)
    parts.append(line(p2x, y5, p2x + p2w, y5, "#888888", 1.4, dash="6,4"))
    parts.append(txt(p2x + p2w - 4, y5 - 6, "M0 ≤5%", 10.5, anchor="end", fill="#777777"))

    # Curves with markers and 95 % CI whiskers.
    for label, tick, window, color in curves:
        pts_s: List[Tuple[float, float]] = []
        pts_f: List[Tuple[float, float]] = []
        for rtt in RTTS:
            row = get_row(tick, window, rtt)
            succ = float(row["perfect_guard_success_rate"])
            sci = float(row["perfect_guard_success_ci95"])
            fp = float(row["false_positive_rate"])
            fci = float(row["false_positive_ci95"])
            x1 = x_coord(p1x, p1w, rtt)
            y1 = y_success(succ)
            pts_s.append((x1, y1))
            x2 = x_coord(p2x, p2w, rtt)
            y2 = y_fp(fp)
            pts_f.append((x2, y2))
            # CI whiskers.
            parts.append(
                line(x1, y_success(succ - sci), x1, y_success(succ + sci), color, 1.0, opacity=0.55)
            )
            parts.append(
                line(x1 - 3, y_success(succ - sci), x1 + 3, y_success(succ - sci), color, 1.0, opacity=0.55)
            )
            parts.append(
                line(x1 - 3, y_success(succ + sci), x1 + 3, y_success(succ + sci), color, 1.0, opacity=0.55)
            )
            parts.append(
                line(x2, y_fp(fp - fci), x2, y_fp(fp + fci), color, 1.0, opacity=0.55)
            )
        parts.append(polyline(pts_s, color))
        parts.append(polyline(pts_f, color))
        for x, y in pts_s:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="{color}"/>')
        for x, y in pts_f:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{color}"/>')

    # Note the overlapping high-success region at low RTT.
    parts.append(
        txt(p1x + 6, p1y + p1h - 10,
            "RTT ≤100ms 时四条曲线重叠在 98.9%–100%（见 REPORT.md T1）", 10.5, fill="#777777")
    )

    # Legend + footer notes.
    legend_y = 598
    parts.append(
        txt(40, legend_y - 12, "图例（实线；带 95% Wilson CI 须）：", 12, fill="#333333", weight="bold")
    )
    for i, (label, _tick, _window, color) in enumerate(curves):
        col = i % 2
        row_i = i // 2
        lx = 40 + col * 470
        ly = legend_y + 10 + row_i * 24
        parts.append(line(lx, ly - 4, lx + 34, ly - 4, color, 3.0))
        parts.append(txt(lx + 42, ly, label, 12, fill="#333333"))
    parts.append(
        txt(40, 676,
            "模型假设（详见 REPORT.md §2）：对称网络（双方 RTT 相同）、时钟/时间戳映射无误差、防御者按“看到命中时刻 + 人因误差”出手、",
            11, fill="#666666")
    )
    parts.append(
        txt(40, 694,
            "服务器下一次 tick 判定命中（delta~U(0,1 tick)）、defender-favoring = 客户端时间戳 + 回放 cap 内追溯 + 1 tick 窗口容差；",
            11, fill="#666666")
    )
    parts.append(
        txt(40, 712,
            "非 Fusion/Unity 实测、非玩家实测；真实引擎/手感的偏差必须由 M0 测试矩阵验证。",
            11, fill="#a33a3a")
    )
    parts.append("</svg>")

    svg_text = "".join(parts)
    ET.fromstring(svg_text)  # validate well-formed XML
    path.write_text(svg_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Summary tables (markdown; REPORT.md copies these numbers)
# ---------------------------------------------------------------------------
def build_index(rows: Sequence[Dict[str, object]]) -> Dict[Tuple[object, ...], Dict[str, object]]:
    index: Dict[Tuple[object, ...], Dict[str, object]] = {}
    for row in rows:
        key = (
            row["tick_hz"],
            row["input_buffer_frames"],
            row["rtt_ms"],
            row["jitter_ms"],
            row["loss_pct"],
            row["window_ms"],
            row["cap_ms"],
            row["defender_favoring"],
            row["interp_ms"],
            row["human_sigma_ms"],
        )
        index[key] = row
    return index


def get_row(
    index: Dict[Tuple[object, ...], Dict[str, object]],
    tick: int,
    buffer_frames: int,
    rtt: int,
    jitter: int,
    loss: float,
    window: int,
    cap: int,
    defender: str,
    interp: int,
    sigma: int,
) -> Dict[str, object]:
    key = (tick, buffer_frames, rtt, jitter, loss, window, cap, defender, interp, sigma)
    if key not in index:
        raise KeyError(f"missing results.csv row for {key}")
    return index[key]


def f_pct(value: object) -> str:
    return f"{100.0 * float(value):.1f}%"


def f_pct_ci(value: object, ci: object) -> str:
    return f"{100.0 * float(value):.1f}% ±{100.0 * float(ci):.1f}"


def f_ms(value: object) -> str:
    return f"{float(value):.1f}"


def f_dmg(value: object) -> str:
    return f"{float(value):.2f}"


def md_table(header: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |"]
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def emit_summary(
    path: Path,
    rows: Sequence[Dict[str, object]],
    sensitivity_rows: Sequence[Dict[str, object]],
    sanity_rows: Sequence[Dict[str, object]],
    trials: int,
    runtime_s: float,
    seed: int,
) -> None:
    idx = build_index(rows)
    out: List[str] = []
    out.append("# TASK-061 汇总表（run.py 自动生成）\n")
    out.append(
        f"> 模型：离散事件 Monte Carlo（合成模型，非 Unity/Fusion 实测、非玩家实测）。"
        f"seed={seed}，每配置 {trials} 次，矩阵 {len(rows)} 行，运行 {runtime_s:.1f}s。"
        f"完整数据：`results.csv`；敏感性：`sensitivity.csv`；自检：`sanity_checks.csv`。\n"
    )

    # T1: main configuration success / false positive / p95 / damage pivots.
    main_configs = [(30, 100), (30, 150), (60, 100), (60, 150)]
    base = dict(buffer_frames=2, jitter=10, loss=2.0, cap=200, defender="on", interp=33, sigma=25)

    def main_row(tick: int, window: int, rtt: int) -> Dict[str, object]:
        return get_row(idx, tick, base["buffer_frames"], rtt, base["jitter"], base["loss"],
                       window, base["cap"], base["defender"], base["interp"], base["sigma"])

    out.append("## T1 主配置：成功率 vs RTT\n")
    out.append(
        "配置：cap=200ms、defender-favoring=on、输入缓冲 2 帧、抖动 10ms、丢包 2%、插值 33ms、人因 sigma=25ms。\n"
    )
    header = ["tick/窗口"] + [f"RTT {r}" for r in RTTS]
    t1rows = []
    for tick, window in main_configs:
        cells = [f"{tick}Hz/{window}ms"]
        for rtt in RTTS:
            row = main_row(tick, window, rtt)
            cells.append(f_pct_ci(row["perfect_guard_success_rate"], row["perfect_guard_success_ci95"]))
        t1rows.append(cells)
    out.append(md_table(header, t1rows) + "\n")

    out.append("## T2 主配置：误判率 vs RTT（真实时序不在窗口内却被判完美）\n")
    t2rows = []
    for tick, window in main_configs:
        cells = [f"{tick}Hz/{window}ms"]
        for rtt in RTTS:
            row = main_row(tick, window, rtt)
            cells.append(f_pct(row["false_positive_rate"]))
        t2rows.append(cells)
    out.append(md_table(header, t2rows) + "\n")

    out.append("## T3 主配置：服务器观测 p95 时序误差 / 平均伤害\n")
    t3rows = []
    for tick, window in main_configs:
        cells = [f"{tick}Hz/{window}ms"]
        for rtt in RTTS:
            row = main_row(tick, window, rtt)
            cells.append(f"{f_ms(row['p95_timing_error_ms'])} / {f_dmg(row['mean_damage'])}")
        t3rows.append(cells)
    out.append("单元格：p95 |T_guard_ev − T_detect| (ms) / 平均伤害（30 基础伤害，完美 0、普通格挡 6、未挡 30）。\n")
    out.append(md_table(header, t3rows) + "\n")

    # T4: M0 acceptance check at RTT 80/100.
    out.append("## T4 M0 验收对照（RTT 80/100ms：成功率 ≥70%、误判 ≤5%）\n")
    out.append("配置：cap=200、defender-favoring=on、缓冲 2、抖动 10、丢包 2%、插值 33ms。\n")
    header4 = ["tick/窗口", "sigma(ms)", "RTT", "成功率", "误判率", "判定"]
    t4rows = []
    for tick, window in main_configs:
        for sigma in SIGMAS:
            for rtt in (80, 100):
                row = get_row(idx, tick, 2, rtt, 10, 2.0, window, 200, "on", 33, sigma)
                ok = (
                    float(row["perfect_guard_success_rate"]) >= 0.70
                    and float(row["false_positive_rate"]) <= 0.05
                )
                verdict = "PASS" if ok else "FAIL"
                if sigma != 25:
                    verdict += "（参考）"
                t4rows.append(
                    [
                        f"{tick}Hz/{window}ms",
                        str(sigma),
                        f"{rtt}",
                        f_pct_ci(row["perfect_guard_success_rate"], row["perfect_guard_success_ci95"]),
                        f_pct(row["false_positive_rate"]),
                        verdict,
                    ]
                )
    out.append(md_table(header4, t4rows) + "\n")

    # T5: tick rate comparison.
    out.append("## T5 tick 30Hz vs 60Hz（成功率 / 误判率 / p95 误差）\n")
    t5rows = []
    for window in (100, 150):
        for rtt in (80, 100, 150):
            r30 = main_row(30, window, rtt)
            r60 = main_row(60, window, rtt)
            t5rows.append(
                [
                    f"{window}ms",
                    str(rtt),
                    f_pct(r30["perfect_guard_success_rate"]),
                    f_pct(r60["perfect_guard_success_rate"]),
                    f_pct(r30["false_positive_rate"]),
                    f_pct(r60["false_positive_rate"]),
                    f_ms(r30["p95_timing_error_ms"]),
                    f_ms(r60["p95_timing_error_ms"]),
                ]
            )
    out.append(
        md_table(
            ["窗口", "RTT", "30Hz 成功", "60Hz 成功", "30Hz 误判", "60Hz 误判", "30Hz p95", "60Hz p95"],
            t5rows,
        )
        + "\n"
    )

    # T6: cap 150 vs 200.
    out.append("## T6 回放 cap 150ms vs 200ms（成功率）\n")
    t6rows = []
    for window in (100, 150):
        for tick in (30, 60):
            cells = [f"{window}ms", f"{tick}Hz"]
            for rtt in (80, 100, 150, 200):
                r150 = get_row(idx, tick, 2, rtt, 10, 2.0, window, 150, "on", 33, 25)
                r200 = get_row(idx, tick, 2, rtt, 10, 2.0, window, 200, "on", 33, 25)
                cells.append(
                    f"{f_pct(r150['perfect_guard_success_rate'])} / "
                    f"{f_pct(r200['perfect_guard_success_rate'])}"
                )
            t6rows.append(cells)
    out.append(
        md_table(["窗口", "tick", "RTT 80 (cap150/cap200)", "RTT 100", "RTT 150", "RTT 200"], t6rows) + "\n"
    )

    # T7: defender-favoring on/off.
    out.append("## T7 defender-favoring on/off（严格实时 vs 偏防御，30Hz、窗口 150ms、cap 200ms、插值 0ms）\n")
    t7rows = []
    for rtt in (0, 80, 100, 150, 200):
        off = get_row(idx, 30, 2, rtt, 10, 2.0, 150, 200, "off", 0, 25)
        on = get_row(idx, 30, 2, rtt, 10, 2.0, 150, 200, "on", 0, 25)
        t7rows.append(
            [
                str(rtt),
                f_pct(off["perfect_guard_success_rate"]),
                f_pct(on["perfect_guard_success_rate"]),
                f_dmg(off["mean_damage"]),
                f_dmg(on["mean_damage"]),
            ]
        )
    out.append(md_table(["RTT", "OFF 成功率", "ON 成功率", "OFF 平均伤害", "ON 平均伤害"], t7rows) + "\n")
    out.append(
        "注：OFF = 严格实时（不看客户端时间戳、不允许追溯、无容差），ON = 客户端时间戳 + 视图延迟补偿 + cap 内追溯 + 1 tick 容差。"
        "插值/快照延迟本身也会造成“看到命中再按”在服务器时序上偏晚（见 T10/T11），因此防御时序不能只靠严格实时。\n"
    )

    # T8: buffer / loss / jitter (30Hz, window 150ms, cap 200, sigma 25).
    out.append("## T8 输入缓冲/丢包/抖动（30Hz、窗口 150ms、cap 200ms、RTT 80ms）\n")
    t8rows = []
    for buffer_frames in BUFFERS:
        cells = [str(buffer_frames)]
        for loss in (0.0, 2.0):
            row = get_row(idx, 30, buffer_frames, 80, 10, loss, 150, 200, "on", 33, 25)
            cells.append(f_pct(row["perfect_guard_success_rate"]))
        t8rows.append(cells)
    out.append(md_table(["输入缓冲(帧)", "丢包 0% 成功率", "丢包 2% 成功率"], t8rows) + "\n")
    out.append("注：输入缓冲在模型中为服务器侧对称缓冲——相对时序不因缓冲改变（A6）；其作用为抖动吸收与冗余重传（B+1 份）。\n")

    # T9: sigma decomposition (human vs network).
    out.append("## T9 人因误差 vs 网络/量化误差分解（30Hz、窗口 150ms、cap 200ms、缓冲 2、抖动 10、丢包 2%、插值 33ms）\n")
    header9 = ["RTT", "sigma", "成功率", "真实在窗率", "窗口内交付率", "误判率", "p95 人类误差", "p95 网络/量化误差"]
    t9rows = []
    for rtt in (80, 100, 150):
        for sigma in SIGMAS:
            row = get_row(idx, 30, 2, rtt, 10, 2.0, 150, 200, "on", 33, sigma)
            t9rows.append(
                [
                    str(rtt),
                    str(sigma),
                    f_pct(row["perfect_guard_success_rate"]),
                    f_pct(row["true_in_window_rate"]),
                    f_pct(row["success_given_in_window"]),
                    f_pct(row["false_positive_rate"]),
                    f_ms(row["p95_human_error_ms"]),
                    f_ms(row["p95_network_error_ms"]),
                ]
            )
    out.append(md_table(header9, t9rows) + "\n")

    # T10: interpolation sensitivity.
    out.append("## T10 插值/快照延迟 0 vs 33ms（成功率 / 误判率）\n")
    t10rows = []
    for tick, window in main_configs:
        for rtt in (80, 100, 150):
            r0 = get_row(idx, tick, 2, rtt, 10, 2.0, window, 200, "on", 0, 25)
            r33 = get_row(idx, tick, 2, rtt, 10, 2.0, window, 200, "on", 33, 25)
            t10rows.append(
                [
                    f"{tick}Hz/{window}ms",
                    str(rtt),
                    f_pct(r0["perfect_guard_success_rate"]),
                    f_pct(r33["perfect_guard_success_rate"]),
                    f_pct(r0["false_positive_rate"]),
                    f_pct(r33["false_positive_rate"]),
                ]
            )
    out.append(md_table(["配置", "RTT", "插值0 成功", "插值33 成功", "插值0 误判", "插值33 误判"], t10rows) + "\n")

    # T11: retroactive grant rate (attacker fairness).
    out.append("## T11 追溯授予率（命中已被服务器判定后、由追溯格挡撤销的比例）\n")
    t11rows = []
    for rtt in (0, 50, 80, 100, 150):
        row = main_row(30, 150, rtt)
        t11rows.append(
            [
                str(rtt),
                f_pct(row["perfect_guard_success_rate"]),
                f_pct(row["retro_applied_rate"]),
                f_ms(row["mean_arrival_after_hit_ms"]),
            ]
        )
    out.append(
        md_table(["RTT", "成功率", "追溯授予率", "输入到达-真实命中(均值ms)"], t11rows) + "\n"
    )
    out.append(
        "注：追溯授予率 = 守卫输入到达服务器时命中已被判定、随后被追溯改判为完美格挡的比例。"
        "插值/快照延迟 33ms 会让输入天然晚于服务器命中判定，所以 RTT=0 时追溯率也高；这意味着防御时序必须用输入时间戳回溯，"
        "同时攻击方会在本地先看到命中、随后被服务器撤销（观感公平问题，需 UI/打击反馈设计，M0 实测）。\n"
    )

    # T12: sensitivity scenarios.
    out.append("## T12 敏感性场景（sensitivity.csv）\n")
    header12 = ["场景", "tick/窗口", "RTT", "sigma", "成功率", "误判率", "备注"]
    sens_index: Dict[Tuple[object, ...], Dict[str, object]] = {}
    for row in sensitivity_rows:
        key = (
            row["scenario"],
            row["tick_hz"],
            row["window_ms"],
            row["rtt_ms"],
            row["human_sigma_ms"],
        )
        sens_index[key] = row
    note_map = {
        "grace_half_tick": "0.5 tick 容差（对比矩阵内 1 tick）",
        "grace_zero": "0 容差（隔离 1 tick 容差的代价）",
        "grace_half_tick_sigma50": "0.5 tick 容差 + sigma50（休闲玩家）",
        "substep_60hz_hit": "30Hz tick 但命中时刻按 60Hz 战斗子步解析",
        "arrival_time_judging": "忽略客户端时间戳、按到达时间判",
        "chord_delay_40ms": "额外 C+X chord 识别延迟 0–40ms",
        "press_bias_minus_8ms": "高手预压 8ms 补偿 60Hz 采样",
        "window_200_cap_150": "窗口放大到 200ms 但 cap=150",
        "defender_favoring_off": "严格实时（无追溯）",
    }
    scenario_order = [
        "grace_half_tick",
        "grace_zero",
        "grace_half_tick_sigma50",
        "substep_60hz_hit",
        "arrival_time_judging",
        "chord_delay_40ms",
        "press_bias_minus_8ms",
        "window_200_cap_150",
        "defender_favoring_off",
    ]
    t12rows = []
    for scenario in scenario_order:
        for tick in (30, 60):
            for window in (100, 150, 200):
                for rtt in (0, 50, 80, 100, 150):
                    key = (scenario, tick, window, rtt, 25)
                    if key not in sens_index:
                        continue
                    row = sens_index[key]
                    t12rows.append(
                        [
                            scenario,
                            f"{tick}Hz/{window}ms",
                            str(rtt),
                            "25",
                            f_pct(row["perfect_guard_success_rate"]),
                            f_pct(row["false_positive_rate"]),
                            note_map[scenario],
                        ]
                    )
    out.append(md_table(header12, t12rows) + "\n")

    # T14: visible warning window (anticipation vs reaction) + chord latency.
    out.append("## T14 可见预警窗口（能否“看到起手再格挡”）\n")
    t14rows = []
    for interp in (0, 33):
        for rtt in RTTS:
            visible = HIT_OFFSET_MS - (rtt / 2.0 + interp)
            t14rows.append(
                [
                    f"{rtt}",
                    str(interp),
                    f"{visible:.1f}",
                    "否（<200ms 典型视觉反应）" if visible < 200 else "理论上可能",
                ]
            )
    out.append(
        md_table(["RTT", "插值延迟(ms)", "可见预警→真实命中(ms)", "靠“看到再反应”可行？"], t14rows)
        + "\n"
    )

    out.append("## T15 C+X chord 延迟与预压补偿（窗口 100ms、cap 200ms、sigma=25、30/60Hz 对照）\n")
    t15rows = []
    for scenario, label in (
        ("chord_delay_40ms", "chord +0–40ms"),
        ("press_bias_minus_8ms", "预压 -8ms"),
    ):
        for tick in (30, 60):
            for rtt in (80, 100):
                key = (scenario, tick, 100, rtt, 25)
                if key not in sens_index:
                    continue
                row = sens_index[key]
                t15rows.append(
                    [
                        label,
                        f"{tick}Hz",
                        str(rtt),
                        f_pct(row["perfect_guard_success_rate"]),
                        f_pct(row["false_positive_rate"]),
                    ]
                )
    out.append(md_table(["场景", "tick", "RTT", "成功率", "误判率"], t15rows) + "\n")

    # T16: tolerance (grace) trade-off, sigma 25 -- 0 / 0.5 tick / 1 tick.
    out.append("## T16 服务器容差（grace）取舍：成功率 / 误判率（sigma=25、cap 200、插值 33ms、RTT 80/100）\n")
    t16rows = []
    for tick in (30, 60):
        for window in (100, 150):
            for rtt in (80, 100):
                g0 = sens_index.get(("grace_zero", tick, window, rtt, 25))
                gh = sens_index.get(("grace_half_tick", tick, window, rtt, 25))
                g1 = get_row(idx, tick, 2, rtt, 10, 2.0, window, 200, "on", 33, 25)
                if g0 is None or gh is None:
                    continue
                t16rows.append(
                    [
                        f"{tick}Hz/{window}ms",
                        str(rtt),
                        f"{f_pct(g0['perfect_guard_success_rate'])} / {f_pct(g0['false_positive_rate'])}",
                        f"{f_pct(gh['perfect_guard_success_rate'])} / {f_pct(gh['false_positive_rate'])}",
                        f"{f_pct(g1['perfect_guard_success_rate'])} / {f_pct(g1['false_positive_rate'])}",
                    ]
                )
    out.append(
        md_table(
            ["tick/窗口", "RTT", "容差 0", "容差 0.5 tick", "容差 1 tick"],
            t16rows,
        )
        + "\n"
    )
    out.append("单元格：成功率 / 误判率。M0 验收：成功率 ≥70% 且误判 ≤5%。\n")

    # T16b: tolerance trade-off for a casual player (sigma 50).
    out.append("## T16b 容差取舍：休闲玩家 sigma=50（1 tick vs 0.5 tick，cap 200、插值 33ms）\n")
    t16brows = []
    for tick in (30, 60):
        for window in (100, 150):
            for rtt in (80, 100):
                g1 = get_row(idx, tick, 2, rtt, 10, 2.0, window, 200, "on", 33, 50)
                gh = sens_index.get(("grace_half_tick_sigma50", tick, window, rtt, 50))
                if gh is None:
                    continue
                t16brows.append(
                    [
                        f"{tick}Hz/{window}ms",
                        str(rtt),
                        f"{f_pct(gh['perfect_guard_success_rate'])} / {f_pct(gh['false_positive_rate'])}",
                        f"{f_pct(g1['perfect_guard_success_rate'])} / {f_pct(g1['false_positive_rate'])}",
                    ]
                )
    out.append(
        md_table(["tick/窗口", "RTT", "容差 0.5 tick：成功 / 误判", "容差 1 tick：成功 / 误判"], t16brows) + "\n"
    )

    # T16c: 30 Hz network tick but 60 Hz substep hit-time resolution.
    out.append(
        "## T16c 30Hz tick 下命中时刻按 60Hz 战斗子步解析（docs/03 §5.1）"
        "对比“按 30Hz tick 边界判定”（cap 200、插值 33ms、1 tick 容差）\n"
    )
    t16crows = []
    for window in (100, 150):
        for sigma in (25, 50):
            for rtt in (80, 100):
                matrix_row = get_row(idx, 30, 2, rtt, 10, 2.0, window, 200, "on", 33, sigma)
                sub = sens_index.get(("substep_60hz_hit", 30, window, rtt, sigma))
                if sub is None:
                    continue
                t16crows.append(
                    [
                        f"30Hz tick / {window}ms",
                        str(sigma),
                        str(rtt),
                        f"{f_pct(matrix_row['perfect_guard_success_rate'])} / {f_pct(matrix_row['false_positive_rate'])}",
                        f"{f_pct(sub['perfect_guard_success_rate'])} / {f_pct(sub['false_positive_rate'])}",
                    ]
                )
    out.append(
        md_table(
            ["配置", "sigma", "RTT", "30Hz tick 边界判定：成功 / 误判", "60Hz 子步命中解析：成功 / 误判"],
            t16crows,
        )
        + "\n"
    )

    # T17: sanity checks.
    out.append("## T17 模型自检结果\n")
    header13 = ["检查", "指标", "期望", "观测", "通过"]
    t13rows = []
    for row in sanity_rows:
        t13rows.append(
            [
                str(row["check"]),
                str(row["metric"]),
                str(row["expected"]),
                str(row["observed"]),
                "PASS" if int(row["passed"]) else "FAIL",
            ]
        )
    out.append(md_table(header13, t13rows) + "\n")
    failed = [row for row in sanity_rows if not int(row["passed"])]
    out.append(
        f"自检结论：{'全部通过' if not failed else '存在失败项（见上）'}。\n"
    )

    path.write_text("\n".join(out), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="TASK-061 perfect guard / lag-comp Monte Carlo model")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS, help="trials per config (default 10000)")
    parser.add_argument("--seed", type=int, default=MASTER_SEED, help="master RNG seed (default 20261017)")
    parser.add_argument("--outdir", type=Path, default=Path(__file__).resolve().parent, help="output directory")
    parser.add_argument("--quick", action="store_true", help="quick mode: 2000 trials/config (debug only)")
    args = parser.parse_args(argv)

    trials = 2000 if args.quick else args.trials
    outdir: Path = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    print(f"TASK-061 Monte Carlo model: seed={args.seed}, trials/config={trials}, outdir={outdir}")
    print(f"matrix size = {MATRIX_SIZE} configs; run mode = {'quick' if args.quick else 'full'}")

    rows = run_matrix(trials, args.seed)
    index = build_index(rows)
    results_path = outdir / "results.csv"
    write_csv(results_path, rows, CSV_COLUMNS)
    print(f"wrote {results_path} ({len(rows)} rows)")

    sensitivity_rows = run_sensitivity(trials, args.seed + 7)
    sensitivity_columns = ["scenario"] + CONFIG_COLUMNS + METRIC_COLUMNS
    sensitivity_path = outdir / "sensitivity.csv"
    write_csv(sensitivity_path, sensitivity_rows, sensitivity_columns)
    print(f"wrote {sensitivity_path} ({len(sensitivity_rows)} rows)")

    sanity_rows = run_sanity_checks(trials, args.seed)
    sanity_columns = ["check", "description", "metric", "expected", "observed", "passed", "note"]
    sanity_path = outdir / "sanity_checks.csv"
    write_csv(sanity_path, sanity_rows, sanity_columns)
    failed = [row["check"] for row in sanity_rows if not int(row["passed"])]
    print(f"wrote {sanity_path}; sanity failures: {failed if failed else 'none'}")

    svg_path = outdir / "guard_success.svg"
    write_svg(index, svg_path)
    print(f"wrote {svg_path}")

    runtime = time.time() - started
    summary_path = outdir / "summary_tables.md"
    emit_summary(summary_path, rows, sensitivity_rows, sanity_rows, trials, runtime, args.seed)
    print(f"wrote {summary_path}")

    # Headline numbers for the console / handoff.
    def headline(tick: int, window: int, rtt: int, sigma: int = 25) -> str:
        row = get_row(index, tick, 2, rtt, 10, 2.0, window, 200, "on", 33, sigma)
        return (
            f"tick={tick}Hz, W={window}ms, RTT={rtt}ms, sigma={sigma}ms -> "
            f"success={100 * float(row['perfect_guard_success_rate']):.1f}% "
            f"(CI +/-{100 * float(row['perfect_guard_success_ci95']):.1f}), "
            f"false_pos={100 * float(row['false_positive_rate']):.1f}%, "
            f"p95_err={float(row['p95_timing_error_ms']):.1f}ms, "
            f"mean_dmg={float(row['mean_damage']):.2f}"
        )

    print("\nHeadline (cap=200ms, defender-favoring on, buffer 2, jitter 10ms, loss 2%, interp 33ms):")
    for tick, window in ((30, 100), (30, 150), (60, 100), (60, 150)):
        for rtt in (0, 80, 100, 150, 200):
            print("  " + headline(tick, window, rtt))
    print(f"\nDone in {runtime:.1f}s")

    if failed:
        print(f"WARNING: {len(failed)} sanity check(s) failed: {failed}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
