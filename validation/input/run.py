#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK-062 键盘 rollover / 组合技术验证 —— 可复现模型脚本（TASK-062）。

范围（模型级，不是引擎/玩家实测）：
1. NKRO / 6KRO / 2KRO 键盘模型下，TASK-062 brief 要求的组合同时可按键数矩阵；
2. 组合解析器（3f=50ms 新鲜方向窗口、方向已按住>3f 回退基础版、C+X 防御优先、
   Z+X+C 必杀优先、Z tap/hold、顺序输入回退 Z→X→C / Z→方向→C/X）；
3. 合成时序用例：pass / fail / edge（规范张力/缓冲假设）；
4. 固定种子的模糊回放：确定性检查。

依赖：Python 标准库 + numpy（numpy 仅用于固定种子随机源）。不联网。
运行：python run.py
产物（写入本文件所在目录）：
  combo_matrix.csv     组合 × 键盘模型矩阵
  context_matrix.csv   移动/跳跃/斜向等上下文扩展矩阵
  timing_cases.csv     组合解析器合成时序用例结果
退出码：0 = 无 FAIL；1 = 存在 FAIL。
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# 0. 基线常数（来源：docs/00 §4.1/§4.3、docs/02 §3.2/§3.4、docs/03 §4.1/§4.3）
# ---------------------------------------------------------------------------

FRAME_MS = 1000.0 / 60.0                    # 60fps 一帧 = 16.666...ms
DIR_WINDOW_MS = 3.0 * FRAME_MS              # 3f = 50.0ms（方向新鲜窗口）
GUARD_WINDOW_MS = 40.0                      # docs/03 §4.1 优先级表：C+X ±40ms
GUARD_WINDOW_ALT_MS = 50.0                  # docs/03 §4.3：C+X 时间窗 ±50ms（冲突，见报告）
ULTIMATE_SEQ_WINDOW_MS = 250.0              # docs/00 §4.1：顺序必杀 Z→X→C ≤250ms
Z_TAP_MAX_MS = 150.0                        # docs/03 §4.1：Z tap ≤150ms
ATTACK_BUFFER_MS = 3.0 * FRAME_MS           # 2–3 帧输入缓冲（docs/03 §4.4），这里取 3f=50ms
OUT_DIR = Path(__file__).resolve().parent

SINGLE_KEYS = ("Z", "X", "C", "V", "Space", "Shift")
DIRECTION_KEYS = frozenset({"Up", "Down", "Left", "Right"})
MODIFIER_KEYS = frozenset({"Shift", "Ctrl", "Alt", "Meta"})
ATTACK_KEYS = ("Z", "X", "C")
LOGICAL_DIRECTION = "Direction"
KNOWN_ACTIONS = frozenset({
    "GUARD", "ULTIMATE",
    "SPECIAL_1", "SPECIAL_2", "SPECIAL_3", "SPECIAL_4",
    "SKILL_1", "SKILL_2", "SKILL_3", "SKILL_4",
    "LIGHT_ATTACK", "HEAVY_ATTACK", "SOFT_LOCK",
})

# 键盘模型：(名称, 非修饰键同时按上限；None = 不限)
KEYBOARD_MODELS = (
    ("NKRO", None),
    ("6KRO", 6),
    ("2KRO", 2),
)


# ---------------------------------------------------------------------------
# 1. 组合清单（TASK-062 brief + docs/00 §4.1 + docs/02 §3.3）
# ---------------------------------------------------------------------------

COMBOS = [
    {
        "id": "K01", "combo": "Z", "keys": ("Z",), "layout": "classic / modern",
        "command": "经典：软锁 tap / 特殊技修饰 hold；现代：轻击",
        "note": "单键；所有键盘模型可输入。tap/hold 见 timing_cases C01–C03。",
    },
    {
        "id": "K02", "combo": "X", "keys": ("X",), "layout": "classic / modern",
        "command": "重击", "note": "单键。",
    },
    {
        "id": "K03", "combo": "C", "keys": ("C",), "layout": "classic / modern",
        "command": "经典：轻击；现代：技能 1",
        "note": "单键；经典布局 C 只攻击，不拾取（拾取改 F）。",
    },
    {
        "id": "K04", "combo": "V", "keys": ("V",), "layout": "classic / modern",
        "command": "跳跃（V+C / V+X 空中攻击的组合前缀）",
        "note": "单键；V+C 等上下文组合见 context_matrix.csv X04/X05。",
    },
    {
        "id": "K05", "combo": "Space", "keys": ("Space",), "layout": "classic / modern",
        "command": "防御/格挡替代键（C+X 的低 rollover 替代）",
        "note": "Space 是非修饰键，计 1；修饰键假设见报告。",
    },
    {
        "id": "K06", "combo": "Shift", "keys": ("Shift",), "layout": "classic / modern",
        "command": "冲刺替代键（双击方向之外的替代）",
        "note": "修饰键，不计入 6KRO/2KRO 的非修饰键上限（假设）。",
    },
    {
        "id": "K07", "combo": "C+X", "keys": ("C", "X"), "layout": "classic",
        "command": "防御/格挡（完美格挡 100ms；Space 为文档既定替代）",
        "note": "2 键；移动中防御实为方向+C+X=3 键（见 context X01）。",
    },
    {
        "id": "K08", "combo": "Z+C", "keys": ("Z", "C"), "layout": "classic",
        "command": "特殊技 1", "note": "2 键；Z 按住作修饰。",
    },
    {
        "id": "K09", "combo": "Z+X", "keys": ("Z", "X"), "layout": "classic",
        "command": "特殊技 2", "note": "2 键；Z 按住作修饰。",
    },
    {
        "id": "K10", "combo": "Z+X+C", "keys": ("Z", "X", "C"), "layout": "classic / modern",
        "command": "必杀（消耗必杀槽）",
        "note": "3 键；经典布局受 C+X 防御优先级影响（见 C16/C24），并支持顺序输入。",
    },
    {
        "id": "K11", "combo": "Direction+C", "keys": (LOGICAL_DIRECTION, "C"),
        "layout": "modern（经典布局下为移动轻击，不是技能）",
        "command": "现代技能 3",
        "note": "2 键（正交）；斜向 +1 键。",
    },
    {
        "id": "K12", "combo": "Direction+Z+C", "keys": (LOGICAL_DIRECTION, "Z", "C"),
        "layout": "classic",
        "command": "特殊技 3（方向在 C 前 ≤3f 新鲜输入）",
        "note": "3 键；支持顺序输入 Z→方向→C。",
    },
    {
        "id": "K13", "combo": "Direction+Z+X", "keys": (LOGICAL_DIRECTION, "Z", "X"),
        "layout": "classic",
        "command": "特殊技 4（方向在 X 前 ≤3f 新鲜输入）",
        "note": "3 键；支持顺序输入 Z→方向→X。",
    },
    {
        "id": "K14", "combo": "Direction+Z+X+C",
        "keys": (LOGICAL_DIRECTION, "Z", "X", "C"),
        "layout": "启动自检（非战斗指令）",
        "command": "启动键位测试的 4 键极限组合（docs/03 §4.3）",
        "note": "4 键（正交）/ 5 键（斜向）；用来暴露低 rollover 键盘丢键。",
    },
    {
        "id": "K15", "combo": "Direction+X+C", "keys": (LOGICAL_DIRECTION, "X", "C"),
        "layout": "modern（经典布局下等价于 X+C 防御）",
        "command": "现代技能 4",
        "note": "3 键；顺序回退与 3f 方向窗口冲突，建议改键（见报告 §4.3）。",
    },
]

OVER_LIMIT_FALLBACK = {
    "K10": "顺序输入 Z→X→C（≤250ms，先按后放，任意时刻≤2 键）；自检失败时提示改键",
    "K12": "顺序输入 Z→方向→C（≤250ms，先按后放）；或改键",
    "K13": "顺序输入 Z→方向→X（≤250ms，先按后放）；或改键",
    "K15": "顺序输入 X→C 且方向在 C 前 ≤3f；该顺序与 3f 窗口冲突 → 建议改键/专用键位",
    "K14": "非战斗指令（仅启动自检）；自检失败 → 提示顺序输入/改键/降级键盘档位",
}

WITHIN_LIMIT_FALLBACK = {
    "K07": "none（Space 为文档既定替代；移动中防御 = 方向+C+X = 3 键，2KRO 下必须改按 Space）",
}


def non_modifier_count(keys) -> int:
    """组合中「非修饰键」个数；逻辑方向按 1 个方向键计（斜向另 +1）。"""
    return sum(1 for k in keys if k not in MODIFIER_KEYS)


def has_direction(keys) -> bool:
    return LOGICAL_DIRECTION in keys


def risk_level(limit, count: int) -> str:
    """计数模型下的残余风险等级。

    - NKRO：计数无上限 → none；
    - 6KRO：≤2 键 none，≥3 键 low（厂商「6KRO」标称区域差异/矩阵 ghosting 未建模）；
    - 2KRO：≤2 键 low（2 键不成 ghosting 回路；缺陷/修饰键行共享未建模），>2 键 high。
    """
    if limit is None:
        return "none"
    if count > limit:
        return "high"
    if limit >= 6:
        if count <= 2:
            return "none"
        if count >= limit:
            return "medium"  # 用满 6KRO 上限，无余量
        return "low"
    return "low" if count <= 2 else "high"


def verdict_for(combo: dict, limit, count: int, diag_count: int) -> str:
    cid = combo["id"]
    if cid == "K14":
        return "not_a_command"
    if limit is None:
        return "ok"
    if count > limit:
        return "sequential_or_remap" if cid == "K15" else "sequential_required"
    if diag_count > limit:
        return "ok_cardinal_only"
    if cid == "K07":
        return "ok_space_optional"
    return "ok"


def fallback_for(combo: dict, limit, count: int, diag_count: int) -> str:
    cid = combo["id"]
    if limit is None:
        return "none"
    if count > limit:
        return OVER_LIMIT_FALLBACK[cid]
    if diag_count > limit:
        if cid == "K11":
            return "仅正交方向可用（斜向 = 3 键，超 2KRO 上限）；或改键"
        return "仅正交方向可用；斜向超限 → 用正交方向或改键"
    if cid == "K07":
        if limit >= 6:
            return "none（Space 为文档既定替代；移动中防御见 context_matrix.csv X01）"
        return WITHIN_LIMIT_FALLBACK["K07"]
    return "none"


def note_for(combo: dict, model: str, limit) -> str:
    notes = []
    if model == "6KRO" and non_modifier_count(combo["keys"]) >= 3:
        notes.append("6KRO 标称值依赖厂商/键区，≥3 键组合建议用 manual_test.html 实测")
    if model == "2KRO" and non_modifier_count(combo["keys"]) <= 2:
        notes.append("2 键可同时按住；矩阵 ghosting/修饰键行未建模")
    if has_direction(combo["keys"]):
        notes.append("斜向方向需 2 个方向键，额外 +1 键")
    if combo["id"] == "K10":
        notes.append("文档优先级 C+X 防御 > Z+X+C 必杀；X/C 间隔 ≤40ms 时可能被防御抢判")
        if model == "2KRO":
            notes.append("顺序回退须先按后放，且 X 抬起后 3f 内按 C，否则普攻先提交（见 timing_cases C18/C19）")
    if combo["id"] == "K15":
        notes.append("顺序回退与 3f 新鲜方向窗口冲突")
    if combo["id"] == "K14":
        notes.append("仅启动自检；4/5 键用于暴露低 rollover 键盘丢键")
    return "；".join(notes)


def build_matrix_rows():
    rows = []
    for combo in COMBOS:
        count = non_modifier_count(combo["keys"])
        diag = count + 1 if has_direction(combo["keys"]) else count
        for model, limit in KEYBOARD_MODELS:
            within = limit is None or count <= limit
            within_diag = limit is None or diag <= limit
            rows.append({
                "combo": combo["combo"],
                "combo_id": combo["id"],
                "layout_scope": combo["layout"],
                "keyboard_model": model,
                "keyboard_limit": "unlimited" if limit is None else str(limit),
                "simultaneous_non_modifier_keys": str(count),
                "within_limit": "TRUE" if within else "FALSE",
                "risk": risk_level(limit, count),
                "required_fallback": fallback_for(combo, limit, count, diag),
                "diagonal_non_modifier_keys": str(diag),
                "within_limit_diagonal": "TRUE" if within_diag else "FALSE",
                "verdict": verdict_for(combo, limit, count, diag),
                "notes": note_for(combo, model, limit),
            })
    return rows


# 上下文扩展：移动/跳跃/斜向/修饰键，回答「实战里多按一个方向/跳跃键会怎样」
CONTEXT_CASES = [
    {
        "id": "X01", "combo": "Direction+C+X（移动中防御）",
        "keys": ("Direction", "C", "X"), "cardinal": 3, "diagonal": 4,
        "command": "移动中格挡（经典 C+X；Space 替代）",
        "over_limit_fallback": "2KRO：停步防御或改按 Space（Space+正交方向=2 键）；斜向仍超限",
        "note": "移动中防御是人类最高频的 3 键叠加场景之一。",
    },
    {
        "id": "X02", "combo": "Direction+Z+C（移动中特殊技 3）",
        "keys": ("Direction", "Z", "C"), "cardinal": 3, "diagonal": 4,
        "command": "移动中特殊技 3（方向新鲜 ≤3f）",
        "over_limit_fallback": "2KRO：顺序输入 Z→方向→C（≤250ms）；或停步",
        "note": "与主矩阵 K12 同键数，这里是「移动中」语义。",
    },
    {
        "id": "X03", "combo": "Direction+Z+X（移动中特殊技 4）",
        "keys": ("Direction", "Z", "X"), "cardinal": 3, "diagonal": 4,
        "command": "移动中特殊技 4（方向新鲜 ≤3f）",
        "over_limit_fallback": "2KRO：顺序输入 Z→方向→X（≤250ms）；或停步",
        "note": "与主矩阵 K13 同键数，这里是「移动中」语义。",
    },
    {
        "id": "X04", "combo": "V+C（跳跃轻击）",
        "keys": ("V", "C"), "cardinal": 2, "diagonal": 2,
        "command": "空中攻击前缀（docs/00 §4.1 V+C / V+X）",
        "over_limit_fallback": "none",
        "note": "2 键，2KRO 可。",
    },
    {
        "id": "X05", "combo": "V+Direction+C（跳跃+方向+轻击）",
        "keys": ("V", "Direction", "C"), "cardinal": 3, "diagonal": 4,
        "command": "带方向空中攻击",
        "over_limit_fallback": "2KRO：先跳后按方向+C（V 按下后可松开）或改键",
        "note": "跳跃键 V 是非修饰键，计入 rollover。",
    },
    {
        "id": "X06", "combo": "Direction(斜向)+Z+X+C",
        "keys": ("Direction", "Direction2", "Z", "X", "C"), "cardinal": 5, "diagonal": 5,
        "command": "斜向必杀（启动自检极限）",
        "over_limit_fallback": "2KRO：不可同按（5 键）→ 顺序输入/改键；6KRO 下 5 键仅剩 1 键余量",
        "note": "斜向 = 2 个方向键。6KRO 仅剩 1 键余量。",
    },
    {
        "id": "X07", "combo": "V+Direction(斜向)+Z+X+C",
        "keys": ("V", "Direction", "Direction2", "Z", "X", "C"),
        "cardinal": 6, "diagonal": 6,
        "command": "跳跃+斜向+必杀（极限叠加）",
        "over_limit_fallback": "2KRO：不可能；6KRO 下恰好用满 6 键，任何额外按键都会丢",
        "note": "6 键 = 6KRO 上限，无余量；仅 NKRO 可保证。",
    },
    {
        "id": "X08", "combo": "Shift+C+X（冲刺+防御）",
        "keys": ("Shift", "C", "X"), "cardinal": 2, "diagonal": 2,
        "command": "Shift 冲刺 + 防御",
        "over_limit_fallback": "none",
        "note": "Shift 为修饰键，按模型不计入非修饰键上限（假设）。",
    },
]


def build_context_rows():
    rows = []
    for ctx in CONTEXT_CASES:
        for model, limit in KEYBOARD_MODELS:
            within = limit is None or ctx["cardinal"] <= limit
            within_diag = limit is None or ctx["diagonal"] <= limit
            rows.append({
                "context": ctx["combo"],
                "context_id": ctx["id"],
                "keyboard_model": model,
                "keyboard_limit": "unlimited" if limit is None else str(limit),
                "simultaneous_non_modifier_keys": str(ctx["cardinal"]),
                "within_limit": "TRUE" if within else "FALSE",
                "risk": risk_level(limit, ctx["cardinal"]),
                "required_fallback": "none" if within else ctx["over_limit_fallback"],
                "diagonal_non_modifier_keys": str(ctx["diagonal"]),
                "within_limit_diagonal": "TRUE" if within_diag else "FALSE",
                "notes": ctx["note"],
            })
    return rows


# ---------------------------------------------------------------------------
# 2. 组合解析器（软件层优先级/窗口；模型级，不是引擎状态机）
# ---------------------------------------------------------------------------

class ComboResolver:
    """按 docs 规则的组合解析器。

    设计取舍（报告 §4 记录）：
    - 所有攻击类动作带 3f（50ms）输入缓冲延迟，组合在缓冲内完成时按更高优先级
      取消低优先级待提交动作。这是对 docs/03 §4.4「输入缓冲 2–3 帧」的建模；
    - 防御 C+X：两键都按住且间隔 ≤ guard_window_ms 才成立（避免「先按后放」的
      顺序输入被误判为防御）；
    - 经典布局 C+X 防御优先级最高（literal，规范字面）；policy
      "z_suppresses_guard" 为「Z 按住时防御让位」的候选修正（报告建议）；
    - Z tap ≤150ms → 软锁；Z 按住 >150ms 作为修饰键等待 X/C；Z 已被组合消费时
      松开不再产生软锁；
    - 方向新鲜：方向键按住且 keydown 距 C/X keydown ≤3f（50ms）→ 方向版；
      方向已按住 >3f → 基础版；顺序回退 Z→方向→C/X 允许 Z 已松开；
    - 顺序必杀：Z→X→C 三个 keydown 按序、总跨度 ≤250ms（允许各键先按后放）；
    - 现代布局防御 = Space（按住），Space 按住时 C/X 不触发攻击。
    """

    def __init__(
        self,
        layout: str = "classic",
        guard_window_ms: float = GUARD_WINDOW_MS,
        guard_policy: str = "literal",
        dir_window_ms: float = DIR_WINDOW_MS,
        ultimate_window_ms: float = ULTIMATE_SEQ_WINDOW_MS,
        z_tap_ms: float = Z_TAP_MAX_MS,
        buffer_ms: float = ATTACK_BUFFER_MS,
    ):
        assert layout in ("classic", "modern")
        assert guard_policy in ("literal", "z_suppresses_guard")
        self.layout = layout
        self.guard_window_ms = guard_window_ms
        self.guard_policy = guard_policy
        self.dir_window_ms = dir_window_ms
        self.ultimate_window_ms = ultimate_window_ms
        self.z_tap_ms = z_tap_ms
        self.buffer_ms = buffer_ms

        self.held: set[str] = set()
        self.down_log: list[tuple[str, float]] = []
        self.actions: list[tuple[float, str]] = []
        self.pending: list[dict] = []
        self.seq = 0
        self.last_t = 0.0
        self.z_down_t: float | None = None
        self.z_used = False

    # -- 内部工具 ---------------------------------------------------------

    def _last_down(self, key: str) -> float:
        for k, t in reversed(self.down_log):
            if k == key:
                return t
        return -1e18

    def _record_down(self, key: str, t: float) -> None:
        self.down_log.append((key, t))
        if len(self.down_log) > 256:
            del self.down_log[:-256]

    def _flush_before(self, t: float) -> None:
        if not self.pending:
            return
        due = [p for p in self.pending if p["deadline"] < t - 1e-9]
        if not due:
            return
        due.sort(key=lambda p: (p["deadline"], p["seq"]))
        for p in due:
            self.pending.remove(p)
            self.actions.append((p["deadline"], p["cmd"]))

    def _schedule(self, t: float, priority: int, cmd: str) -> None:
        # 更高优先级的组合取消尚未提交的低优先级动作
        self.pending = [p for p in self.pending if p["priority"] >= priority]
        self.seq += 1
        self.pending.append({
            "deadline": t + self.buffer_ms,
            "priority": priority,
            "cmd": cmd,
            "seq": self.seq,
        })

    def _fresh_direction(self, t: float):
        best = None
        best_age = None
        for key in sorted(DIRECTION_KEYS):
            if key not in self.held:
                continue
            age = t - self._last_down(key)
            if 0.0 <= age <= self.dir_window_ms + 1e-9:
                if best is None or age < best_age:
                    best, best_age = key, age
        return best

    def _sequential_z_direction(self, t: float, direction: str) -> bool:
        """顺序输入 Z→方向→C/X：Z 的 keydown 在方向 keydown 之前，总跨度 ≤250ms。"""
        d_t = self._last_down(direction)
        if d_t < 0:
            return False
        for key, ts in reversed(self.down_log):
            if key == "Z" and ts < d_t:
                return (t - ts) <= self.ultimate_window_ms + 1e-9
        return False

    def _sequential_ultimate(self, t: float) -> bool:
        """顺序输入 Z→X→C：三个 keydown 按序、总跨度 ≤250ms（允许先按后放）。"""
        c_t = self._last_down("C")
        if abs(c_t - t) > 1e-9:
            return False
        for key, xt in reversed(self.down_log):
            if key == "X" and xt < c_t:
                for k2, zt in reversed(self.down_log):
                    if k2 == "Z" and zt < xt:
                        return (t - zt) <= self.ultimate_window_ms + 1e-9
        return False

    # -- 分类（优先级：GUARD 4 > ULTIMATE 3 > 新鲜方向 2 > 基础特殊 1 > 普攻 0）--

    def _classify(self, key: str, t: float):
        if "Space" in self.held:
            return None  # 防御按住时 C/X 不攻击（Space 防御，两布局通用替代）

        if self.layout == "classic":
            other = "X" if key == "C" else "C"
            if other in self.held:
                gap = t - self._last_down(other)
                if gap <= self.guard_window_ms + 1e-9:
                    if self.guard_policy == "literal" or "Z" not in self.held:
                        return (4, "GUARD")
            if all(k in self.held for k in ("Z", "X", "C")):
                return (3, "ULTIMATE")
            if self._sequential_ultimate(t):
                return (3, "ULTIMATE")
            direction = self._fresh_direction(t)
            if direction is not None:
                if "Z" in self.held:
                    return (2, "SPECIAL_3" if key == "C" else "SPECIAL_4")
                if self._sequential_z_direction(t, direction):
                    return (2, "SPECIAL_3" if key == "C" else "SPECIAL_4")
            if "Z" in self.held:
                return (1, "SPECIAL_1" if key == "C" else "SPECIAL_2")
            return (0, "LIGHT_ATTACK" if key == "C" else "HEAVY_ATTACK")

        # modern：Z=轻击、C=技能1、X=重击、X+C=技能2、
        #          方向+C=技能3、方向+X+C=技能4、Z+X+C=必杀、Space=防御
        if all(k in self.held for k in ("Z", "X", "C")):
            return (3, "ULTIMATE")
        direction = self._fresh_direction(t)
        if key == "C":
            if "X" in self.held:
                if direction is not None:
                    return (2, "SKILL_4")
                return (1, "SKILL_2")
            if direction is not None:
                return (2, "SKILL_3")
            return (0, "SKILL_1")
        return (0, "HEAVY_ATTACK")

    # -- 事件入口 ---------------------------------------------------------

    def down(self, key: str, t: float) -> None:
        assert t >= self.last_t - 1e-9, f"non-monotonic event: {key}@{t}"
        self.last_t = t
        self._flush_before(t)
        self.held.add(key)
        self._record_down(key, t)

        if key == "Z":
            self.z_down_t = t
            self.z_used = False
            if self.layout == "modern":
                self._schedule(t, 0, "LIGHT_ATTACK")
            return
        if key == "Space":
            self._schedule(t, 4, "GUARD")
            return
        if key in ("C", "X"):
            result = self._classify(key, t)
            if result is None:
                return
            priority, cmd = result
            if cmd in ("SPECIAL_1", "SPECIAL_2", "SPECIAL_3", "SPECIAL_4", "ULTIMATE"):
                self.z_used = True
            if cmd == "GUARD" and "Z" in self.held:
                self.z_used = True
            self._schedule(t, priority, cmd)

    def up(self, key: str, t: float) -> None:
        assert t >= self.last_t - 1e-9, f"non-monotonic event: {key}@{t}"
        self.last_t = t
        self._flush_before(t)
        self.held.discard(key)
        if key == "Z" and self.layout == "classic" and self.z_down_t is not None:
            duration = t - self.z_down_t
            if duration <= self.z_tap_ms + 1e-9 and not self.z_used:
                self.actions.append((t, "SOFT_LOCK"))
                self.z_used = True
            self.z_down_t = None

    def finish(self) -> list[tuple[float, str]]:
        while self.pending:
            self.pending.sort(key=lambda p: (p["deadline"], p["seq"]))
            p = self.pending.pop(0)
            self.actions.append((p["deadline"], p["cmd"]))
        return self.actions


# ---------------------------------------------------------------------------
# 3. 合成时序用例
# ---------------------------------------------------------------------------

def case(cid, title, events, expected, *, layout="classic", policy="literal",
         guard_window=GUARD_WINDOW_MS, edge=False, note=""):
    return {
        "id": cid, "title": title, "events": events, "expected": expected,
        "layout": layout, "policy": policy, "guard_window": guard_window,
        "edge": edge, "note": note,
    }


TIMING_CASES = [
    # ---- 经典布局：Z tap/hold、单键、基础特殊 ----
    case("C01", "Z tap 100ms → 软锁", [(0.0, "Z", "down"), (100.0, "Z", "up")],
         "SOFT_LOCK", note="docs/03 §4.1：tap ≤150ms。"),
    case("C02", "Z tap 150ms（边界，≤150 成立）",
         [(0.0, "Z", "down"), (150.0, "Z", "up")], "SOFT_LOCK",
         note="150ms = 9f，闭区间边界。"),
    case("C03", "Z hold 166.7ms（10f）→ 无动作",
         [(0.0, "Z", "down"), (166.7, "Z", "up")], "NONE",
         note=">150ms 视为按住修饰，不产生软锁。"),
    case("C04", "Z+C（间隔 100ms，Z 按住）→ 特殊技 1",
         [(0.0, "Z", "down"), (100.0, "C", "down")], "SPECIAL_1"),
    case("C05", "Z+X（间隔 100ms，Z 按住）→ 特殊技 2",
         [(0.0, "Z", "down"), (100.0, "X", "down")], "SPECIAL_2"),
    case("C06", "C+X 间隔 30ms → 防御",
         [(0.0, "C", "down"), (30.0, "X", "down")], "GUARD"),
    case("C07", "X+C 间隔 30ms → 防御（顺序无关）",
         [(0.0, "X", "down"), (30.0, "C", "down")], "GUARD"),
    case("C08", "C+X 间隔 40ms（±40ms 边界）→ 防御",
         [(0.0, "C", "down"), (40.0, "X", "down")], "GUARD",
         note="docs/03 §4.1 优先级表 ±40ms，闭区间。"),
    case("C09", "C+X 间隔 41.7ms（超 ±40ms）→ 两次普攻",
         [(0.0, "C", "down"), (41.7, "X", "down")],
         "LIGHT_ATTACK>HEAVY_ATTACK", edge=True,
         note="边界外：C 先按普通轻击、X 判重击；若采用 docs/03 §4.3 的 ±50ms 则为 GUARD。"),
    case("C10", "Z+方向+C，方向领先 C 40ms（新鲜）→ 特殊技 3",
         [(0.0, "Z", "down"), (100.0, "Up", "down"), (140.0, "C", "down")],
         "SPECIAL_3"),
    case("C11", "Z+方向+X，方向领先 X 30ms（新鲜）→ 特殊技 4",
         [(0.0, "Z", "down"), (100.0, "Up", "down"), (130.0, "X", "down")],
         "SPECIAL_4"),
    case("C12", "Z+方向+C，方向已按住 100ms（>3f）→ 基础特殊技 1",
         [(0.0, "Z", "down"), (100.0, "Up", "down"), (200.0, "C", "down")],
         "SPECIAL_1", note="方向 >3f = 移动中，回退基础版。"),
    case("C13", "Z+方向+C，方向领先正好 50ms（3f 边界）→ 特殊技 3",
         [(0.0, "Z", "down"), (100.0, "Up", "down"), (150.0, "C", "down")],
         "SPECIAL_3", note="3f = 50.0ms，闭区间。"),
    case("C14", "Z+方向+C，方向领先 66.7ms（4f）→ 基础特殊技 1",
         [(0.0, "Z", "down"), (100.0, "Up", "down"), (166.7, "C", "down")],
         "SPECIAL_1", note="60Hz 采样下，50–66.7ms 之间不存在整帧间隔。"),
    case("C15", "Z+X+C，X→C 间隔 60ms（>3f 缓冲）→ 必杀前先提交特殊技 2",
         [(0.0, "Z", "down"), (100.0, "X", "down"), (160.0, "C", "down")],
         "SPECIAL_2>ULTIMATE", edge=True,
         note="中间动作已提交；引擎需状态机取消或更长意图缓冲才能干净必杀。"),
    case("C16", "Z+X+C，X→C 间隔 20ms → 防御优先（规范字面）",
         [(0.0, "Z", "down"), (100.0, "X", "down"), (120.0, "C", "down")],
         "GUARD", edge=True,
         note="文档优先级 C+X 防御 > 必杀：Z 按住时 X/C 间隔≤40ms 会被防御抢判（规范张力）。"),
    case("C17", "Z+X+C，X→C 间隔 50ms（3f 缓冲内完成）→ 只用必杀",
         [(0.0, "Z", "down"), (100.0, "X", "down"), (150.0, "C", "down")],
         "ULTIMATE", edge=True,
         note="干净必杀仅在 X→C ∈ (40ms, 50ms] 的窄带内成立（依赖缓冲模型）。"),
    case("C18", "顺序必杀 Z→X→C（X 抬起后 3f 内按 C，总 90ms）→ 软锁+必杀",
         [(0.0, "Z", "down"), (30.0, "Z", "up"), (50.0, "X", "down"),
          (60.0, "X", "up"), (90.0, "C", "down")],
         "SOFT_LOCK>ULTIMATE", edge=True,
         note="2KRO 顺序回退可行条件：X 抬起后 ≤3f 内按 C；Z tap 会先产生软锁（无害）。"),
    case("C19", "顺序必杀 Z→X→C 但 C 迟到（总 180ms）→ 普攻先提交",
         [(0.0, "Z", "down"), (30.0, "Z", "up"), (50.0, "X", "down"),
          (60.0, "X", "up"), (180.0, "C", "down")],
         "SOFT_LOCK>HEAVY_ATTACK>ULTIMATE", edge=True,
         note="超过 3f 缓冲后中间普通攻击已提交；实际引擎需定义取消/抑制。"),
    case("C20", "顺序特殊技 3：Z→方向→C（总 80ms）→ 软锁+特殊技 3",
         [(0.0, "Z", "down"), (30.0, "Z", "up"), (60.0, "Up", "down"),
          (80.0, "C", "down")],
         "SOFT_LOCK>SPECIAL_3", edge=True,
         note="2KRO 特殊技 3/4 顺序回退；软锁与特殊技可能双动作。"),
    case("C21", "顺序特殊技 3 超过 250ms → 普通轻击",
         [(0.0, "Z", "down"), (30.0, "Z", "up"), (250.0, "Up", "down"),
          (280.0, "C", "down")],
         "SOFT_LOCK>LIGHT_ATTACK",
         note="Z→C 总跨度 280ms >250ms，不判顺序特殊技。"),
    case("C22", "经典布局：方向+C（无 Z）→ 普通轻击（不是技能）",
         [(0.0, "Up", "down"), (30.0, "C", "down")], "LIGHT_ATTACK",
         note="方向+C 是「现代技能 3」；经典布局只是移动轻击。"),
    case("C23", "经典布局：方向+X+C → 仍判防御",
         [(0.0, "Up", "down"), (50.0, "X", "down"), (70.0, "C", "down")],
         "GUARD", note="同样的键在现代布局是技能 4；经典布局由 X+C 防御抢占。"),
    case("C24", "候选修正：Z 按住时防御让位 → Z+X+C 判必杀",
         [(0.0, "Z", "down"), (100.0, "X", "down"), (120.0, "C", "down")],
         "ULTIMATE", policy="z_suppresses_guard", edge=True,
         note="建议方案：Z 按住时 C+X 防御让位（需改 docs/00 §4.1 优先级，Human 门）。"),
    case("C25", "C+X 间隔 41.7ms，若采用 ±50ms 窗口 → 防御",
         [(0.0, "C", "down"), (41.7, "X", "down")], "GUARD",
         guard_window=GUARD_WINDOW_ALT_MS, edge=True,
         note="docs/03 §4.3 写 ±50ms，与 §4.1 的 ±40ms 冲突；本模型默认 40ms。"),
    case("C26", "Z tap 软锁后再按 C → 软锁+普通轻击（顺序特殊 1 不成立）",
         [(0.0, "Z", "down"), (100.0, "Z", "up"), (150.0, "C", "down")],
         "SOFT_LOCK>LIGHT_ATTACK",
         note="顺序输入仅承诺特殊 3/4 与必杀；Z→C 松手顺序不判特殊 1。"),
    case("C27", "方向+Z+X+C（4 键同时，X→C 间隔 50ms）→ 必杀",
         [(0.0, "Up", "down"), (50.0, "Z", "down"), (100.0, "X", "down"),
          (150.0, "C", "down")],
         "ULTIMATE", note="NKRO/6KRO 可 4 键同按；2KRO 不可能（须顺序输入）。"),
    case("C28", "Space 替代防御（经典布局）：Space 按住 + C → 防御",
         [(0.0, "Space", "down"), (50.0, "C", "down")], "GUARD",
         note="docs/00 §4.1：C+X 防御的 Space 替代；2KRO 移动中防御的关键回退。"),

    # ---- 现代布局 ----
    case("M01", "现代：Z 单键 → 轻击",
         [(0.0, "Z", "down"), (100.0, "Z", "up")], "LIGHT_ATTACK", layout="modern"),
    case("M02", "现代：方向领先 C 30ms → 技能 3",
         [(0.0, "Up", "down"), (30.0, "C", "down")], "SKILL_3", layout="modern"),
    case("M03", "现代：方向已按住 100ms → 技能 1（基础版）",
         [(0.0, "Up", "down"), (100.0, "C", "down")], "SKILL_1", layout="modern",
         note="方向 >3f = 移动中，回退基础技能。"),
    case("M04", "现代：X+C（X 先，间隔 30ms）→ 技能 2",
         [(0.0, "X", "down"), (30.0, "C", "down")], "SKILL_2", layout="modern"),
    case("M05", "现代：方向+X+C（X 先，C 距方向 45ms）→ 技能 4",
         [(0.0, "Up", "down"), (20.0, "X", "down"), (45.0, "C", "down")],
         "SKILL_4", layout="modern"),
    case("M06", "现代：C 单键 → 技能 1",
         [(0.0, "C", "down")], "SKILL_1", layout="modern"),
    case("M07", "现代：Space 按住防御时按 C → 防御，不攻击",
         [(0.0, "Space", "down"), (50.0, "C", "down")], "GUARD",
         layout="modern"),
    case("M08", "现代：C 先 X 后（非文档顺序）→ 技能 1 + 重击",
         [(0.0, "C", "down"), (20.0, "X", "down")],
         "SKILL_1>HEAVY_ATTACK", layout="modern", edge=True,
         note="现代 X+C 顺序敏感：C 先于 X 不代表技能 2；实现需明确顺序或加缓冲。"),
    case("M09", "现代：Z+X+C 近同时（X→C 20ms）→ 必杀（无 C+X 防御冲突）",
         [(0.0, "Z", "down"), (20.0, "X", "down"), (40.0, "C", "down")],
         "ULTIMATE", layout="modern",
         note="现代布局防御是 Space，因此必杀没有经典布局的防御抢判问题。"),
]


def run_timing_cases():
    results = []
    for c in TIMING_CASES:
        resolver = ComboResolver(
            layout=c["layout"],
            guard_window_ms=c["guard_window"],
            guard_policy=c["policy"],
        )
        for t, key, kind in c["events"]:
            if kind == "down":
                resolver.down(key, t)
            else:
                resolver.up(key, t)
        resolver.finish()
        actual = ">".join(cmd for _t, cmd in resolver.actions) or "NONE"
        if actual != c["expected"]:
            result = "FAIL"
        elif c["edge"]:
            result = "EDGE"
        else:
            result = "PASS"
        timeline = "; ".join(
            f"{t:g} {key}{'↓' if kind == 'down' else '↑'}" for t, key, kind in c["events"]
        )
        results.append({
            "id": c["id"],
            "layout": c["layout"],
            "guard_policy": c["policy"],
            "guard_window_ms": f"{c['guard_window']:g}",
            "case": c["title"],
            "timeline": timeline,
            "expected": c["expected"],
            "actual": actual,
            "result": result,
            "notes": c["note"],
        })
    return results


# ---------------------------------------------------------------------------
# 4. 固定种子模糊回放（确定性/健壮性）
# ---------------------------------------------------------------------------

def run_fuzz(n: int = 500, seed: int = 20261017) -> dict:
    rng = np.random.default_rng(seed)
    keys = ("Z", "X", "C", "Up", "Down", "Left", "Right", "Space")
    deterministic_fail = 0
    unknown_action = 0
    non_monotonic = 0
    soft_locks = 0
    guards = 0
    ultimates = 0

    for _ in range(n):
        timeline: list[tuple[float, str, str]] = []
        t = 0.0
        for _ in range(int(rng.integers(4, 10))):
            t += float(rng.uniform(5.0, 120.0))
            key = keys[int(rng.integers(len(keys)))]
            timeline.append((round(t, 3), key, "down"))
            t += float(rng.uniform(5.0, 120.0))
            timeline.append((round(t, 3), key, "up"))
        timeline.sort(key=lambda e: (e[0], 0 if e[2] == "up" else 1))

        def replay() -> list[tuple[float, str]]:
            r = ComboResolver(layout="classic")
            for tt, key, kind in timeline:
                if kind == "down":
                    r.down(key, tt)
                else:
                    r.up(key, tt)
            return r.finish()

        first = replay()
        second = replay()
        if first != second:
            deterministic_fail += 1
        last_t = -1e18
        for tt, cmd in first:
            if cmd not in KNOWN_ACTIONS:
                unknown_action += 1
            if tt < last_t - 1e-9:
                non_monotonic += 1
            last_t = tt
            if cmd == "SOFT_LOCK":
                soft_locks += 1
            elif cmd == "GUARD":
                guards += 1
            elif cmd == "ULTIMATE":
                ultimates += 1

    return {
        "sequences": n,
        "seed": seed,
        "deterministic_fail": deterministic_fail,
        "unknown_action": unknown_action,
        "non_monotonic": non_monotonic,
        "soft_locks": soft_locks,
        "guards": guards,
        "ultimates": ultimates,
    }


# ---------------------------------------------------------------------------
# 5. 输出
# ---------------------------------------------------------------------------

MATRIX_FIELDS = [
    "combo", "combo_id", "layout_scope", "keyboard_model", "keyboard_limit",
    "simultaneous_non_modifier_keys", "within_limit", "risk", "required_fallback",
    "diagonal_non_modifier_keys", "within_limit_diagonal", "verdict", "notes",
]
CONTEXT_FIELDS = [
    "context", "context_id", "keyboard_model", "keyboard_limit",
    "simultaneous_non_modifier_keys", "within_limit", "risk",
    "required_fallback", "diagonal_non_modifier_keys", "within_limit_diagonal",
    "notes",
]
TIMING_FIELDS = [
    "id", "layout", "guard_policy", "guard_window_ms", "case", "timeline",
    "expected", "actual", "result", "notes",
]


def write_csv(name: str, fields: list[str], rows: list[dict]) -> Path:
    path = OUT_DIR / name
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def summarise_matrix(rows: list[dict]) -> None:
    print(f"combo_matrix: {len(rows)} 行 = {len(COMBOS)} 组合 × {len(KEYBOARD_MODELS)} 键盘模型")
    max_cardinal = max(int(r["simultaneous_non_modifier_keys"]) for r in rows)
    max_diag = max(int(r["diagonal_non_modifier_keys"]) for r in rows)
    print(f"  主矩阵最大同时非修饰键：正交 {max_cardinal} 键 / 斜向 {max_diag} 键")
    for model, limit in KEYBOARD_MODELS:
        subset = [r for r in rows if r["keyboard_model"] == model]
        ok = [r for r in subset if r["within_limit"] == "TRUE"]
        ok_diag = [r for r in subset if r["within_limit_diagonal"] == "TRUE"]
        risks = {}
        for r in subset:
            risks[r["risk"]] = risks.get(r["risk"], 0) + 1
        risk_text = "，".join(f"{k}={v}" for k, v in sorted(risks.items()))
        print(f"  {model}: 正交可同时按 {len(ok)}/{len(subset)}；斜向 {len(ok_diag)}/{len(subset)}；risk: {risk_text}")
        if len(ok) != len(subset):
            failed = [r["combo"] for r in subset if r["within_limit"] == "FALSE"]
            print(f"    不可同按: {', '.join(failed)}")
        if len(ok_diag) != len(ok):
            diag_failed = [r["combo"] for r in subset
                           if r["within_limit"] == "TRUE" and r["within_limit_diagonal"] == "FALSE"]
            print(f"    正交可、斜向不可: {', '.join(diag_failed)}")


def main() -> int:
    # 统一 stdout 为 UTF-8，避免 Windows 控制台代码页导致中文输出乱码。
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    matrix_rows = build_matrix_rows()
    context_rows = build_context_rows()
    timing_rows = run_timing_cases()
    fuzz = run_fuzz()

    paths = [
        write_csv("combo_matrix.csv", MATRIX_FIELDS, matrix_rows),
        write_csv("context_matrix.csv", CONTEXT_FIELDS, context_rows),
        write_csv("timing_cases.csv", TIMING_FIELDS, timing_rows),
    ]

    print("=== TASK-062 keyboard rollover / combo validation ===")
    print(f"frame: 1f = {FRAME_MS:.4f}ms；方向窗口 {DIR_WINDOW_MS:.1f}ms(3f)；"
          f"C+X 默认 {GUARD_WINDOW_MS:.0f}ms；顺序必杀 ≤{ULTIMATE_SEQ_WINDOW_MS:.0f}ms；"
          f"输入缓冲 {ATTACK_BUFFER_MS:.1f}ms(3f)")
    summarise_matrix(matrix_rows)
    print(f"context_matrix: {len(context_rows)} 行")
    max_ctx = max(int(r["simultaneous_non_modifier_keys"]) for r in context_rows)
    print(f"  上下文矩阵最大同时非修饰键：{max_ctx} 键")
    for model, _limit in KEYBOARD_MODELS:
        subset = [r for r in context_rows if r["keyboard_model"] == model]
        ok = [r for r in subset if r["within_limit"] == "TRUE"]
        print(f"  {model}: 上下文组合可同时按 {len(ok)}/{len(subset)}")

    counts = {"PASS": 0, "EDGE": 0, "FAIL": 0}
    for row in timing_rows:
        counts[row["result"]] += 1
    print(f"timing_cases: {len(timing_rows)} 例；PASS={counts['PASS']} "
          f"EDGE={counts['EDGE']} FAIL={counts['FAIL']}")
    for row in timing_rows:
        if row["result"] == "FAIL":
            print(f"  FAIL {row['id']}: expected={row['expected']} actual={row['actual']} "
                  f"({row['case']})")
    print(f"fuzz: {fuzz['sequences']} 序列，seed={fuzz['seed']}；"
          f"deterministic_fail={fuzz['deterministic_fail']}，"
          f"unknown_action={fuzz['unknown_action']}，non_monotonic={fuzz['non_monotonic']}；"
          f"soft_lock={fuzz['soft_locks']} guard={fuzz['guards']} ultimate={fuzz['ultimates']}")
    for path in paths:
        print(f"wrote: {path.name}")

    fuzz_ok = (fuzz["deterministic_fail"] == 0 and fuzz["unknown_action"] == 0
               and fuzz["non_monotonic"] == 0)
    ok = counts["FAIL"] == 0 and fuzz_ok
    print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
