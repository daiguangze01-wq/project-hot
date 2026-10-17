# Project Hot — 2.5D 键盘竞技场 MVP

> 目标：用最小可运行原型验证「2.5D 固定斜俯视 + 全键盘 ZXCV + 装备=招式 + 服务器权威 + 多人房间」的核心循环。
> 这是 **Web 技术栈的 MVP**，不是 Unity/Fusion 生产实现；用于手感/规则/联机形态验证，不替代 M0 引擎验证。

## 运行

```powershell
# 在仓库根目录
& "C:\Users\dai\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe" mvp\server.js
# 或：cd mvp; node server.js
```

打开：

- 单屏试玩：<http://127.0.0.1:3000/>
- 双人：再开一个浏览器标签/窗口，访问同一 URL（最多 4 人；默认 p1 剑豪、p2 拳师）
- 指定战斗核心：`?core=blade`（剑豪）或 `?core=fist`（拳师）
- 自动演示/截图：<http://127.0.0.1:3000/?demo=1>

## 操作（全键盘，无鼠标）

| 键 | 功能 |
|---|---|
| WASD / 方向键 | 8 方向移动 |
| C | 轻击（可 3 连；70ms 组合缓冲） |
| X | 重击 |
| V | 跳跃 |
| Z+C | 技能 1（突进斩） |
| Z+X | 技能 2（直线冲击） |
| Z+方向+C | 技能 3 |
| Z+方向+X | 技能 4（AoE） |
| Z+X+C | 必杀（需 100 能量） |
| Space / C+X | 防御（按住） |
| 移动 + C/X | 边移动边攻击 |

> MVP 的输入组合在**客户端做 70ms 缓冲后**发给服务器；服务器仍权威计算命中/伤害/冷却/资源。生产版按 `docs/03` 把组合解析移回服务器/输入时间戳。
>
> **安全/范围**：每个 `/events` 连接下发一次性 session token，`/input` 必须带 token 且只能操作绑定玩家；默认只监听 `127.0.0.1`。**不要设置 `HOST=0.0.0.0` 暴露到局域网/公网**——MVP 无账号/限速/反作弊，仅本机可信环境。

## 已实现

- **30Hz 服务器权威 tick**：`process.hrtime` 固定步进 + 追帧（Windows 定时器粒度下仍按墙钟 30Hz），SSE 状态广播 + HTTP 输入（零依赖）。
- 2.5D 固定斜俯视渲染（Canvas，isometric 投影；地面/影子/高度/朝向/攻击弧/受击数字）。
- 1–4 人房间 + 训练木桩；PvP 开启；死亡 3 秒重生；击杀/死亡计分。
- HP 500 / MP 100 / Guard 300 / Ultimate 100；轻/重/4 技能/必杀；V 跳跃；防御减伤/完美格挡/破防。
- **4 个战斗核心**（剑豪/拳师/枪兵/术士）：`?core=blade|fist|spear|staff`，由 `mvp/cores.json` 数据驱动；技能伤害/范围/MP/冷却/武器外观不同，验证「换核心→换招式表」的最小形态。
- 木桩 5000 HP，2 秒重置；HUD/技能冷却/计分板/连接状态。
- 截图：`screenshots/mvp-demo.png`（剑豪）、`screenshots/mvp-demo-staff.png`（术士）。
- 无外部依赖；`node --test` 单测 + CDP 截图脚本。

## 测试

```powershell
cd mvp
node --test test/*.test.js
```

覆盖：移动/边界、轻击命中、防御/完美格挡、MP/冷却/必杀资源、死亡/重生、SSE 加入 + 输入 + 健康检查。

## 架构

```text
Browser (Canvas + DOM HUD)
  │  SSE /events  (30Hz state)
  │  POST /input   (33ms held + buffered actions + session token)
  ▼
Node http server (mvp/server.js)
  │  authoritative 30Hz sim (mvp/sim.js)
  │  no DB; in-memory room
  ▼
Training dummy + players
```

## 与正式基线的关系

- 2.5D 固定 pitch50/yaw45、全键盘、服务器权威：遵循 `docs/00` v0.3.0。
- 装备=招式：MVP 只实现 **4 个战斗核心的招式表差异**（`mvp/cores.json` 数据驱动）；防具/符文/外观/1.0 全量资产不在 MVP，不能据此说「装备=招式」已完整验证。
- 角色占屏/正交尺寸：MVP 为 Web Canvas 视觉近似，**不用于验收** 70–90px；验收仍走 URP M0。
- 联网：MVP 用 HTTP/SSE 验证形态；生产用 Fusion 2 Server Mode + 预测/校正/200ms 回放。
- 输入：MVP 客户端组合缓冲；生产按 `docs/03` 的 60Hz InputFrame/时间戳/服务器解析。
- 美术：几何占位，不是最终像素资产。

## 已知限制

- 无客户端预测/回滚；本地 33ms 输入 + 30Hz 快照，远程会有延迟。
- 无房间列表/匹配/账号/持久化；刷新即新角色。
- PvP 无平衡/排位/反作弊；只验证形态。
- 组合缓冲 70ms 会让轻击略有延迟；生产需按帧数据/输入时间戳重做。
- 训练木桩不攻击；PvE AI/副本不在 MVP 范围。
- 跳跃已实现，但命中判定暂不检查 Z 高度（跳不能躲招）；2.5D 空中判定留给 M0 设计/引擎验证。
- 防具/符文/外观/装备槽未实现；只有 2 个核心的招式表差异。
- 默认仅 localhost；生产需要账号/会话/限速/Origin/反作弊后才可暴露。

## 下一步（M0 引擎）

1. Unity URP 相机对账：size8/pitch50/yaw45、1.8m 78px、6/10m 可见性、14m 边缘指示。
2. Fusion 2：ClientTimeMs/defender-favoring/cap200/0.5 tick；C1/C2 负对照 + 150ms 矩阵。
3. 3 款键盘 QA（`validation/input/manual_test.html`）。
4. 把 MVP 的招式表/冷却/伤害映射到 `docs/00`/`docs/02` 数据驱动资产。
