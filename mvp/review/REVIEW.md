---
id: REV-071
type: review
task: TASK-071
subject: Project Hot — Web MVP（mvp/）独立评审
version: 1.0
status: final
owner: mvp-reviewer
reviewers: [lead]
depends_on: [TASK-070]
last_reviewed: 2026-10-18
scope: mvp/
verdict: pass-with-fixes（本机可玩；未达"可交给外部试玩"标准）
blockers: 2
majors: 5
minors: 18
---

# REV-071 — Project Hot Web MVP 独立评审

> Reviewer 不得直接修改源文件；本报告只是评审产出，未修改 `mvp/sim.js`、`mvp/server.js`、`mvp/public/`、`mvp/test/`、`mvp/README.md`、`mvp/screenshots/` 或 `docs/`。
> 评审方式：读源码 + 独立重跑测试 + 自起服务（PORT=3100）+ 真 SSE 客户端 + 无头 Chrome 键盘 E2E + 攻击性输入探针 + 截图核对。所有临时脚本/日志均位于 `mvp/review/`，评审结束后已删除，仅保留本文件。

---

## 0. 结论（TL;DR）

| 问题 | 结论 |
|---|---|
| **用户现在能玩吗？** | **能**：本机 `node mvp/server.js` 后打开 `http://127.0.0.1:3000/`，**纯键盘**可完成移动/轻击/重击/技能/防御/必杀，木桩掉血、HUD 实时更新、双标签页可互相看见并 PvP（击杀/死亡/计分/3 秒重生全部实测通过）。无 JS 异常。 |
| **是可信的 MVP 吗？** | **方向可信、证据不完整**：服务器权威 sim 是真的（伤害/MP/冷却/Ult/复活均由服务器裁决，客户端只发 `held`+`actions`）；2.5D 斜俯视、全键盘、4 人房、木桩、计分、HUD 都真实跑通。但存在 **2 个 blocker**（一次畸形请求即可杀死整个服务进程；`/input` 未绑定连接身份）、**5 个 major**（声明 30Hz 实测仅 21.4Hz 导致全部时序/手感失真 1.4×；V 跳跃是静默 no-op；动作白名单走原型链可把玩家永久卡死；seq 无上界可永久冻结输入；"装备=招式"核心差异点并未真正实现）。 |
| **能否作为"已通过时序/手感验证"的依据？** | **不能**。在当前 Windows 环境下 tick 为 21.3–21.4Hz，所有前摇/冷却/完美格挡窗口/移速在墙钟上放慢约 1.4×，README 的「30Hz」与 REQ-TECH-002 的 30Hz 基线在本机不成立。 |
| **是否可对外试玩/暴露到非 localhost？** | **不可**，直至 blocker 关闭。 |
| **是否替代 M0 引擎验证？** | **完全不替代**，见 §7。 |

**问题计数：blocker 2 · major 5 · minor 18。**

---

## 1. Verdict 详述

### 1.1 能不能玩（独立 E2E 结论）

**能玩，且是"真联机"而非单机假象**（全部为我独立执行，不采信作者的测试）：

- 无头 Chrome 只用 `Input.dispatchKeyEvent` 键盘事件驱动页面：W 键使服务器侧玩家 `y: 4.8 → 1.68`；C 键触发服务器侧 `action: light`；木桩 HP `4940 → 4910`（轻击 30 伤害）；Z+C 使服务器扣 20 MP（`100 → 80`，`action: skill1`）；按住 Space 服务器 `guarding: true`，松开回到 `false`。页面无未捕获 JS 异常。
- 第二个独立 SSE 连接（不发送任何输入）可看到浏览器玩家及其权威状态，证明状态确实来自服务器广播。
- 双客户端 PvP：一方重击命中另一方，伤害 80（格挡后 16）、击杀后 `kills/deaths` 记账正确、3 秒后在出生点满血满蓝满防复活。

### 1.2 是不是可信的 MVP

**是"可演示的形态 MVP"，还不是"可采信的验证 MVP"**：

- **可信的部分**（我逐项验过）：服务器权威裁决、零依赖单文件服务、SSE 状态广播、输入接口、房间容量、静态资源、玩家名转义、路径穿越防护、资源门控、PvP 击杀/重生、HUD 与 sim 数据一致、截图与代码自洽。
- **不可信的部分**：
  1. 一次畸形 HTTP 请求可让整个进程退出（任何 tab/脚本/网页都能触发）；
  2. `/input` 只认 `playerId`（p1–p4 可猜），不认连接身份，任意客户端可操控任意玩家；
  3. Windows 上实测 tick ≈ 21.4Hz 而声称 30Hz，**"手感/时序"类结论目前不可采信**；
  4. README/HUD 宣称的 V 跳跃在服务器不存在；
  5. 「装备=招式」这个项目最核心的差异点没有出现在 MVP 里（只有一套固定 7 招，没有装备/配装/切换）。

### 1.3 结论等级

**pass-with-fixes**：可以作为"本地演示/内部评审"的 MVP；**不算**可交给外部试玩者的"可玩版本"，更不是 M0 引擎验证。建议 Lead 按 §6 的修复清单决定是否先修 blocker+major 再进入试玩。

---

## 2. 独立证据（命令、环境、结果）

### 2.1 环境与命令

| 项 | 值 |
|---|---|
| OS | Windows（`docs`/运行均在 `D:\workspace\project-hot`） |
| Node | `C:\Users\dai\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe` → **v24.21.0** |
| 我的服务 | `$env:PORT='3100'; node mvp/server.js`（未动 Lead 的 3000 端口服务；仅只读探测过其 `/health`） |
| 浏览器 | 本机 Chrome `--headless=new` + CDP，1280×720，**只派发键盘事件，无鼠标事件** |

### 2.2 单元/集成测试（作者测试，独立重跑）

```powershell
cd mvp
& "C:\Users\dai\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe" --test test/*.test.js
```

结果：**10 tests / 10 pass / 0 fail / 0 skipped / 122.6ms**；连续重跑 **5 次均 10/10 通过**（无 flake）。命令在 PowerShell 下可直接执行（Node 24 自解析 glob），README 的测试命令可用。

> 注意：测试全绿**不代表输入边界安全**——下面 3 个"一发崩溃"场景没有任何测试覆盖。这是测试信心的边界，不是测试失败的证据。

### 2.3 服务器独立功能/协议探针（33 项全过，另 6 项发现）

我在 `PORT=3100` 自起服务，用脚本化 SSE 客户端 + 原生 HTTP 探针，结果摘要：

| 类别 | 结果 |
|---|---|
| `/health` | `{"ok":true,"tick":...,"players":0,"clients":0,"uptimeSec":...}` ✅ |
| 两个 SSE 客户端互相可见 | welcome 返回 `p1/p2`；两端 state 均含 2 名玩家且名字正确；350ms 内收到 9 帧 ✅ |
| 输入→服务器权威状态变化 | POST 204；右移 450ms 后另一客户端看到 `x: 0 → 1.56`；light 动作出现在对端 state（`t:0.067, duration:0.34`）；木桩 `5000 → 4970` ✅ |
| 协议负例 | 旧 seq→409；未知 playerId→409；坏 JSON→400；9 个 actions→400；actions 非数组→400；缺 playerId→400；>8KB body→**413** ✅ |
| 房间容量 | 第 4 人 200；第 5 人 **503 "Room is full (max 4 players)."**；`/health` players=4 ✅ |
| 清理 | 客户端关闭 SSE 后 300–500ms 内 `players:0, clients:0`；关一个客户端后名额可立即复用（503→200） ✅ |
| 静态资源/方法 | `/` 200（2024B，含 `game.js`）；`/style.css` 正确 MIME；`POST /`→405；`HEAD /`→200；`GET /input`→404；`POST /events`→405 ✅ |
| **路径穿越（8 个 payload，raw socket 绕过 fetch 归一化）** | `/../server.js`、`/../../AGENTS.md`、`/%2e%2e/server.js`、`/%2e%2e%2fserver.js`、`/..%5cserver.js`、`/..%2fserver.js`、`/....//server.js`、`/..%252fserver.js` → **全部 404，无源码泄漏**；对照 `/game.js` 200 ✅ |
| **XSS（无头浏览器真实执行）** | `?name=<img src=x onerror="window.__pwn=1"><svg onload="window.__pwn=2">` → `window.__pwn=null`、`#scoreList` 中 `img/svg` 元素数 **0**、`#pname.textContent` 为字面量文本、无 JS 异常 → **未发现 XSS** ✅ |

**探针发现的漏洞（不是 PASS 项）**：见 §5 的 B-2 / M-3 / M-4 / m-2 / m-15。

### 2.4 "一发崩溃"隔离探针（安全关键，独立子进程复现）

每个场景都新起一个独立 server 子进程、保持 1 个 SSE 玩家在线、先发一条**合法**输入（返回 204，作为对照），再发**一条**畸形请求：

| 场景（单次 POST /input） | 结果 | 证据 |
|---|---|---|
| 对照：合法输入 | 204，服务器存活（3s 后 `/health` 正常） | `ALIVE {"ok":true,"tick":67,"players":1,...}` |
| Body 为 JSON `null` | **进程自杀，退出码 1** | `TypeError: Cannot read properties of null (reading 'playerId') at IncomingMessage.<anonymous> (mvp/server.js:136:20)` |
| `{"playerId":"p1","held":5}` | **进程自杀，退出码 1** | `TypeError: Cannot use 'in' operator to search for 'up' in 5 at Sim.applyInput (mvp/sim.js:169:13)` |
| `{"playerId":"p1","held":"up"}` | **进程自杀，退出码 1** | `TypeError: Cannot use 'in' operator to search for 'up' in up at Sim.applyInput (mvp/sim.js:169:13)` |

结论：**任何能向本机回环发 POST 的进程/网页脚本都能在这局游戏进行中把服务打挂**。这不是"作者测试没开"的问题，而是一个未捕获异常 = 整局玩家全部掉线。

### 2.5 无头 Chrome 键盘 E2E（12/12）

只用键盘事件驱动，结果：

| 检查 | 实测 |
|---|---|
| 页面加载 + SSE 连接 | `connected · p1`，canvas 存在 |
| 键盘玩家名 | HUD `BrowserProbe` |
| 7 个技能槽渲染 | 7 |
| 观察者（第二连接）可见浏览器玩家 | `["BrowserProbe","Observer"]` |
| W 移动到达服务器 | `y: 4.8 → 1.68` |
| C 触发服务器 light 动作 | 对端 state 捕获 `action.type=light` |
| 轻击木桩掉血（端到端） | `4940 → 4910`（30 伤害） |
| Z+C 技能1 扣 20 MP | `100 → 80`，`action=skill1` |
| Space 防御开关 | `guarding: true → false` |
| **V 跳跃** | **`maxZ=0`、从未出现 jump action（no-op）** |
| HUD 随服务器状态更新 | 木桩 HP 文本 4910，pstate 合法 |
| 客户端未捕获异常 | **0** |

### 2.6 PvP 端到端（击杀/计分/重生，6/6）

| 检查 | 实测 |
|---|---|
| 格挡减伤 20% | 重击 80 → **16** 伤害；GUARD `300 → 256`（-44 = 55%） |
| 连续重击击杀 | HP 轨迹 `404 → 324 → 244 → 164 → 84 → 4 → 0`（3 下格挡外 + 6 下命中） |
| 记分 | `deaths: 1`，`kills: 1`，死亡后 `alive:false`，`respawnIn ≈ 2.5` |
| 3 秒重生 + 资源恢复 | 5.6s 后 `alive:true, hp:500, mp:100, guard:300, ult:0`，回到出生点 `(0,-4.8)` |

### 2.7 资源门控（真实线协议，4/4）

| 检查 | 实测 |
|---|---|
| Ult=0 时必杀被拒 | POST 204 但无 ultimate 动作，ult 仍 0 ✅ |
| 技能1 消耗 20 MP + 进入冷却 | MP `100 → 80`，`cooldown.skill1 = 3.7s` ✅ |
| 冷却中再放技能1 | MP 保持 80（未扣费、未出招）✅ |
| 技能2 消耗 30 MP | MP `80 → 50`，`cooldown.skill2 = 5.7s` ✅ |

### 2.8 Tick 率与时钟漂移（**major 证据**）

| 测量 | 结果 |
|---|---|
| 运行中的 MVP `/health` tick 增量 | 3.034s 墙钟走 **65 tick = 21.42 Hz**（声明 30Hz） |
| 长期一致性 | `tick 4893 / uptime 228s = 21.5 Hz` |
| 对照：纯 Node `setInterval(1000/30)` | 3.003s / 64 tick = **21.31 Hz**（非 server.js 独有，是 Windows 定时器粒度问题） |
| 对照：`setInterval(1000/60)` / `(50)` | 35.5Hz / 15.98Hz（均非请求值） |
| 客户端 `setInterval(sendInput, 50)` 实际 | **16 Hz**（非 20Hz） |
| **有效移动速度** | 按住右 1.002s 位移 3.64 单位 → **3.63 u/s，仅为声明 `SPEED=5.2` 的 0.699×** |
| 影响 | 因为 `sim.tick(1/30)` 用**固定 dt**（[server.js:178](D:/workspace/project-hot/mvp/server.js)），sim 时钟以 **0.71× 墙钟**前进：前摇/冷却/复活/0.16s 完美格挡窗口/2s 木桩重置在真实时间里全部被放慢约 1.4×。 |

### 2.9 视觉证据（两张截图）

| 截图 | 内容核对 |
|---|---|
| `mvp/screenshots/mvp-demo.png`（作者提供，read-only 查看） | 1280×720；HUD：HP 500 / MP 50 / GUARD 300 / ULT 24；技能 CD 数字可见；计分板 `PixelKnight 0/0`；木桩 `4802/5000`；等距菱形场地 + 网格 + 中心环 + 四角灯柱 + 玩家/木桩/影子/武器/选中环；底部键盘说明；右下 `connected · p1`。**与 sim 数值自洽**：轻击 30 + 连段轻击 38 + 技能1 70 + 技能2 60 = 198 → 5000-198 = 4802；MP 100-20-30 = 50；ULT 0.12×198 ≈ 24。说明 HUD 不是摆拍。 |
| 我在键盘 E2E 中另拍的 live 截图（临时文件，已删除） | 双人同屏：`BrowserProbe`（HP 500 / MP 80 / GUARD 300 / ULT 4）与 `Observer`；木桩 4910；计分板两人各 0/0；技能1 冷却遮罩可见；证明真实运行画面与截图一致。 |

---

## 3. 代码审计（逐项）

| # | 审计项 | 结论 | 证据/说明 |
|---|---|---|---|
| 3.1 | **服务器权威** | ⚠️ 部分通过 | `sim.js` 是唯一状态源：客户端只能发 `held`+`actions`，伤害/HP/MP/Ult/冷却/命中/复活全部服务器计算；我用"只发输入的第二个客户端"验证另一客户端看到的是服务器裁决状态。**但输入通道没有身份**：`POST /input` 只校验 `playerId` 字符串存在（[server.js:136-146](D:/workspace/project-hot/mvp/server.js)），不校验"这条连接是否就是该玩家"→ 任意 HTTP 客户端可伪造成 p1–p4（实测把 B 移动了 0.218 并触发 heavy，返回 204）。 |
| 3.2 | **输入/序列校验** | ❌ 有 blocker | 好的部分：JSON 解析 400、`playerId` 必需、`actions` 必须为数组且 ≤8、8KB body 上限（413）、每玩家单调 seq。**坏的**：`body=null`/`held` 非对象直接抛未捕获异常杀进程（B-1）；`MOVES[type]` 未做 own-property 校验，`'constructor'` 可通过并产生 `duration=NaN` 的永卡 action（M-3）；seq 无上界，`seq=1e15` 被接受后该玩家后续输入永久 409（M-4，需刷新页面）。 |
| 3.3 | **房间容量/清理** | ✅ 通过 | `MAX_PLAYERS=4`（[server.js:21](D:/workspace/project-hot/mvp/server.js)），满了返回 503 文本；SSE `req/res` 的 close/error 都注册了 `cleanup`（[server.js:104-113](D:/workspace/project-hot/mvp/server.js)），`clients.delete + sim.removePlayer` 幂等；实测关闭后 300–500ms 归零、名额可复用。 |
| 3.4 | **SSE 错误路径** | ⚠️ 部分通过 | 有：双事件清理解绑、15s heartbeat 且 `unref`、`X-Accel-Buffering:no`、广播循环里 try/catch + 删除失效客户端。缺：忽略 `res.write()` 返回的背压信号、未注册 `res.on('error')`、没有慢客户端内存上限、没有基于 `lastSeen` 的空闲超时（`lastSeen` 写了但从不读）。本地小房间风险低，不能带到生产。 |
| 3.5 | **静态路径穿越** | ✅ 通过 | `path.resolve(publicDir, '.'+rel)` + `startsWith(publicDir+sep)` 白名单（[server.js:153-159](D:/workspace/project-hot/mvp/server.js)）；8 种编码/反斜杠 payload 实测全部 404，未泄漏源码。 |
| 3.6 | **XSS（玩家名）** | ✅ 通过 | 服务端只做长度截断、原样进 JSON（正确，JSON 不等于 HTML）；客户端在唯一 `innerHTML` 位置 `#scoreList` 用 `escapeHtml`（[game.js:672-674, 703-705](D:/workspace/project-hot/mvp/public/game.js)），其余全部 `textContent`/canvas `fillText`；`p.color` 来自服务器常量而非用户输入。浏览器实测 payload 全部被转义、没有元素注入、无脚本执行。 |
| 3.7 | **内存泄漏** | ⚠️ 部分通过 | `players`/`clients` 随 SSE 关闭删除；`fx`/`events` 每 tick 按 TTL 过滤；heartbeat 每个客户端 clearInterval。风险点：无空闲超时（静默连接占满 4 席）、慢客户端可无限堆积广播缓冲、满房重连只有 `reconnecting…` 没有提示（[game.js:246-248](D:/workspace/project-hot/mvp/public/game.js)）。 |
| 3.8 | **冷却/MP/必杀资源** | ✅ 通过 | 服务器端 `tryAction` 逐项校验 Ult（`p.ult < 100` 拒绝）、MP、冷却（[sim.js:191-223](D:/workspace/project-hot/mvp/sim.js)）；真实线协议 4/4 验证（§2.7）。资源只在施放成功时扣。 |
| 3.9 | **防御/完美格挡** | ⚠️ 基本通过 | 长按格挡 = 80→16（20%）且 GUARD -44（55%）；0.16s 内起防 = 完美格挡 0 伤害 + 回 20 GUARD（单测覆盖 + [sim.js:373-389](D:/workspace/project-hot/mvp/sim.js)）。**风险**：完美窗口锚点是"本次起防时刻"，重新起防无代价，脚本化客户端可读取广播的 `action.t/duration` 精确对齐起防时刻实现"自动完美格挡"；人类玩家这是正常防反，但反作弊/严肃 PvP 前需要服务器侧输入时序或起防成本。另：完美格挡 FX 被重复 push 两次。 |
| 3.10 | **重生** | ✅ 通过 | 死亡清 action/guard、`respawnAt = time+3`、`deaths++`、攻击者 `kills++`；重生恢复满 HP/MP/GUARD、清空 ult/冷却/连段并回出生点（[sim.js:409-437](D:/workspace/project-hot/mvp/sim.js)）；PvP 端到端验证（§2.6）。缺：重生保护帧/固定出生点可被蹲点（minor）。 |
| 3.11 | **Tick 率** | ❌ 不通过（major） | 见 §2.8：声明 30Hz，本机实测 21.3–21.4Hz；`dt` 仍固定 `1/30` → 全系统慢 0.7×。 |
| 3.12 | **测试确定性** | ✅ 通过（覆盖不足另计） | 5 次重跑全绿；sim 测试用固定 `1/30` 步进、无随机影响断言（`Math.random` 只用于 fx id）；无网络抖动依赖（server 测试有 3s deadline 但本地稳定）。**覆盖不足**：无 B-1/M-3/M-4/B-2 类负例、无"两个客户端互相可见"、完美格挡只测内部函数不测输入时序。 |
| 3.13 | **全键盘/无鼠标** | ✅ 通过（V 除外） | 客户端只注册 `keydown`/`keyup`/`blur`（无 pointer/mouse/click 监听），`preventDefault` 阻止方向键/空格滚动；无头 Chrome 仅用键盘事件完成全部操作；帮助面板列出键位。**但 V 跳跃是 no-op**（major，见 M-2）。 |
| 3.14 | **2.5D 斜俯视渲染** | ✅ 通过（原型级） | `project()` 使用 pitch 50°/yaw 45° 等距投影（[game.js:14-30](D:/workspace/project-hot/mvp/public/game.js)），地面 X/Y 平面战斗、Z 仅用于高度；菱形地面/网格/环/灯柱/影子/攻击弧都在。仅视觉近似，不能用于验收 70–90px 角色占屏（README 已声明）。 |

**其它静态审计结论**：零外部依赖（无 npm 包、无第三方资产，原创几何占位，无竞品 IP 迹象）；服务默认只监听 `127.0.0.1`（好），但 `HOST` 可被改成 0.0.0.0 且 README 未警告无鉴权服务不可暴露；`GET /input` 落到静态 404 而非 405（小语义问题）；`process.on('SIGINT')` 只 `server.close`+500ms 强退，不主动结束 SSE 通知客户端。

---

## 4. 视觉检查

**结论：作为原型可读、可理解，核心画面有 1 个明显可读性缺陷。**

| 检查项 | 结果 |
|---|---|
| HUD 四资源 | HP/MP/GUARD/ULT 四条 + 数值 + 技能槽 + 冷却数字/遮罩，肉眼可读；与服务器数据一致 |
| 场地 | 等距菱形 + 网格 + 中心三环 + 四角灯柱，方向感成立；边界即 arena（±8） |
| 木桩 | 中心草人造型 + 独立血条 + `木桩 4802` 数字，重置 2s 逻辑存在 |
| 角色名 | 头顶名字 + 血条；自己青色、他人红色可区分 |
| 双人画面 | 两个玩家按 `x+y` 深度排序，遮挡关系正确；计分板各自颜色点 |
| 顶部/底部灯柱 | 场地菱形在 1280×720 下上下略微贴边/裁切（顶部灯柱接近画布顶端），属取景问题非缺陷 |
| **缺陷：名字/血条与木桩标签重叠** | 近战距离（也就是核心战斗距离）下，玩家名字与木桩血条/`木桩 xxxx` 文字互相叠字（两张截图都能看到），自己血条压在木桩身体上。原型可接受，但"能不能看清对方 HP/自己 HP"是动作游戏可读性底线，建议加名字/血条防重叠或缩短名字标签。 |
| 非 16:9 窗口 | canvas 用 `object-fit: contain` 自适应，但 HUD 用 viewport 绝对定位（`#hud{inset:0}`），非 16:9 时 HUD 不与画面对齐（minor）。 |

---

## 5. 问题清单（AGENTS.md Review 格式）

### Blocker（2）

```text
SEVERITY: blocker
ID: B-1
LOCATION: mvp/server.js:128-151（handleInput 的 end 回调，尤其 L132 解析后 L136 直接读 payload.playerId、L145 调 applyInput）；mvp/sim.js:159-189（L169 `if (k in h)`）
ISSUE: 未捕获异常可被单条 HTTP 请求触发并杀死整个服务进程。三种独立复现：
  1) body=`null` → TypeError: Cannot read properties of null (reading 'playerId') @ server.js:136 → 进程 exit 1；
  2) body={"playerId":"p1","held":5} → TypeError: Cannot use 'in' operator to search for 'up' in 5 @ sim.js:169 → 进程 exit 1；
  3) body={"playerId":"p1","held":"up"} → 同上 @ sim.js:169 → 进程 exit 1。
  对照：合法输入 204 且服务持续存活。任何本机进程、或用户访问的任意网页（/input 不校验 Origin/Content-Type，简单 POST 即可跨源发送）都能在 4 人局进行中把服务器打挂。
FIX: ① handleInput 入口先做 `payload !== null && typeof payload === 'object'` 的校验，非法即 400；② applyInput 里要求 `held` 为普通对象（`typeof held === 'object' && held !== null && !Array.isArray(held)`），缺失键一律视为 false；③ 包一层 request 级 try/catch + 顶层 `uncaughtException` 兜底并以 500 返回；④ 补 3 条对应负例测试（body null / held 数字 / held 字符串）。
STATUS: open
```

```text
SEVERITY: blocker
ID: B-2
LOCATION: mvp/server.js:63-114（/events）、116-151（/input）、78-114（无 token 的 welcome）
ISSUE: POST /input 不绑定连接身份。服务器只校验 playerId 字符串存在，playerId 是顺序可猜的 p1–p4；welcome 事件也不下发任何会话密钥。实测：A 的 HTTP 客户端 POST {"playerId": B 的 id, seq: 9000, held:{right:true}, actions:['heavy']} → 204，B 被移动 0.218 单位并触发 heavy（B 自己没发过任何输入）。这意味着"服务器权威"只成立于状态计算，不成立于输入归属：任意客户端可操控/冒名其他玩家；配合 B-1 可由任意网页把本地局打挂（CSRF/DNS rebinding 面）。MVP 是 localhost、无账号，真实曝光面小，但"服务器权威"是 AGENTS.md 不可协商约束 #7，且这是 5–10 行可修问题，必须在对外试玩前关闭。
FIX: /events 的 welcome 下发生成的随机 sessionToken（不入广播状态）；客户端所有 /input 带上 token（Header 或 body），服务器维护 token→playerId 映射并拒绝不匹配；同时校验 Origin 或要求自定义 Header 防跨源简单请求；增加每 token 输入限速。若 Lead 明确接受"仅 localhost、单人可信环境"的临时风险，可降级为 major 并写入 README 已知限制——但仍不得把服务暴露到 0.0.0.0。
STATUS: open
```

### Major（5）

```text
SEVERITY: major
ID: M-1
LOCATION: mvp/server.js:44、176-190（`tickMs=1000/TICK_RATE`、`setInterval` 内 `sim.tick(1/30)` 固定 dt）；mvp/README.md:40（"30Hz 服务器权威 tick"）
ISSUE: 声明 30Hz，Windows 本机实测 21.42Hz（3.034s/65 tick；长期 4893 tick/228s=21.5Hz）。对照纯 Node setInterval(33.33ms)=21.31Hz，确认是 Windows 定时器粒度（~46.9ms）而非业务代码偶发；但服务器用固定 dt=1/30，导致 sim 时钟只有 0.71× 墙钟：实测按住右 1.002s 位移 3.64 单位 = 3.63 u/s（声明 SPEED 5.2 的 0.699×）。所有可感知时序（前摇 0.12–0.42s、冷却 4–20s、完美格挡 0.16s、复活 3s、木桩 2s）在真实时间上被放慢约 1.4×；客户端输入定时器 50ms 实测也只有 16Hz。→ 任何"手感/节奏/冷却是否合适"的试玩结论在当前环境都不成立，也与 REQ-TECH-002 的 30Hz 基线不符。
FIX: tick 用 monotonic 时间（`process.hrtime.bigint()`）计算真实 elapsed 作为 dt，并做追帧（累计余量、单次 dt clamp，例如 ≤100ms）；不要用固定 1/30。客户端发送/插值同样用真实 elapsed。补一个 tick 率回归测试（例如 3s 内 tick 数在 28–32 之间的容差断言或至少记录）。若暂时不修，README 必须明确"Windows 本机实测约 21Hz，时序数值未按真实时间校准，不可用于手感验收"，且试玩时把招式时长按实测系数解释。
STATUS: open
```

```text
SEVERITY: major
ID: M-2
LOCATION: mvp/README.md:27（操作表 "V 跳跃"）、mvp/public/index.html:36（HUD 帮助 "V 跳跃"）、mvp/public/game.js:154-155（按 V 推入 'jump' action）；mvp/sim.js（MOVES 无 jump；L14-15 JUMP_V/GRAVITY 未被用于输入入口）
ISSUE: V 跳跃是静默 no-op。客户端把 'jump' 放进 actions，服务器 tryAction 查 `MOVES['jump']` 为 undefined 直接 return false（HTTP 仍 204），z 永远 0。无头浏览器实测：按住 V 后连续采样 8 次 `maxZ=0`，广播中从未出现 jump action。用户看到帮助里写着跳跃、按了没反应——这是"标称功能未实现"，会直接误导试玩反馈。
FIX: 二选一：① 在 sim 里实现 jump（MOVES.jump 或独立入口：校验 alive/action/冷却后 `p.vz = JUMP_V`；tickPlayer 已有 z/重力物理与落地逻辑，只需接线，并补"跳起→落地"单测）；② 从 README/HUD/客户端按键中删除跳跃并写入已知限制。推荐 ①（成本低，且 V 键已在布局里）。
STATUS: open
```

```text
SEVERITY: major
ID: M-3
LOCATION: mvp/sim.js:191-197（`if (!MOVES[type]) return false; const m = MOVES[type];`），影响 L219 duration 与 L281 tickPlayer 的 `MOVES[p.action.type]`
ISSUE: 动作白名单用原型链查找，未做 own-property 校验。实测 POST actions:['constructor'] → 204；服务器把 Object 构造函数当招式：`duration = undefined+undefined+undefined = NaN`，`p.action` 永不结束（t>=NaN 恒 false），玩家被永久卡在 action（实测 600ms 后 action 仍为 constructor、再发 light 也被忽略；1.7s 后仍卡死）。配合 B-2，攻击者可对任意/全部玩家下发该动作，把对局软锁（所有人不能行动）；respwn 也不重置 seq 所以输入可能继续被拒。同类可用键还有 'toString'、'__proto__' 等。普通玩家界面不会触发，但它暴露了"服务器信任字符串动作名"的边界。
FIX: `if (typeof type !== 'string' || !Object.prototype.hasOwnProperty.call(MOVES, type)) return false;`；对 `MOVES` 用 `Object.create(null)` 或 Map 亦可。补负例测试：constructor/toString/__proto__/空串/数字。
STATUS: open
```

```text
SEVERITY: major
ID: M-4
LOCATION: mvp/sim.js:159-165（`if (typeof payload.seq === 'number' && payload.seq <= p.seq) return false; p.seq = payload.seq;`）；mvp/server.js:136-146
ISSUE: 客户端可把 seq 直接推到任意大；一旦接受一次 `seq=1e15`，该玩家所有后续输入永久 409（实测：normal=204 → huge(1e15)=204 → 后续正常 seq=409）。玩家在界面上表现为完全失去控制，且刷新前无法恢复（respawn 不清 seq）。配合 B-2 可冻结任意/全部玩家。非数值 seq（如 "abc"）则被静默忽略（204 但 seq 不更新），校验语义不完整。
FIX: 要求 seq 为有限整数；只接受 `p.seq < seq <= p.seq + 窗口`（例如 +300，约 5s@60Hz）或 `seq <= p.seq` 时拒绝但记录；异常大跳直接 400/409 并保留旧 seq。补负例测试（1e15、Infinity、字符串、负数）。
STATUS: open
```

```text
SEVERITY: major
ID: M-5
LOCATION: mvp/sim.js:17-46（固定 MOVES 表）、mvp/README.md:3（目标声称验证"装备=招式"）、MVP 无任何装备/配装/武器切换概念
ISSUE: 项目最核心的差异点「装备 = 招式（武器原型 + 战斗核心 + 防具 + 符文 + 外观）」在 MVP 中不存在：只有角色绑定的固定 7 招（轻/重/4 技能/必杀），没有装备槽、没有配装选择、没有招式随装备变化、也没有数据驱动的招式资产。README 目标句把"装备=招式"列为要验证的核心循环之一，但当前实现只能验证"一套固定 ZXCV 招式表 + 2.5D + 服务端权威 + 多人房间"。如果不澄清，试玩反馈会误以为该差异点已被验证。
FIX: 二选一：① 最小化实现"装备=招式"形态：至少 2 套武器/招式表可选（URL/按键切换），招式表从 `docs/00`/`docs/02` 数据驱动，验证"换装备→换键位招式→再打一轮"；② 在 README 明确写"MVP 不覆盖装备=招式，待 M0 数据驱动资产阶段验证"，并把 §5 的结论口径改为"招式表形态验证"。
STATUS: open
```

### Minor（18）

| ID | LOCATION | ISSUE | FIX | STATUS |
|---|---|---|---|---|
| m-1 | `sim.js:167-170` | `held` 是局部更新：payload 省略的键保留旧值。官方客户端总发全量所以没暴露，但任何"只发改动键"的客户端/重连会粘住移动键（我的探针亲测会把玩家一直推到场边）。 | 要求 `held` 全量 5 键或缺失一律置 false；加测试。 | open |
| m-2 | `server.js:104-113`、`sim.js:165`、`game.js:246-248` | 无空闲/半开连接超时；`lastSeen` 写了但从不使用；静默 SSE 连接可占满 4 席。房间满时客户端只显示 `reconnecting…`，用户不知道原因。 | 用 lastSeen 做 30–60s 无输入踢除（但保留观战可另设）；503 时给客户端可见提示。 | open |
| m-3 | `server.js:176-189` | SSE 广播忽略 `res.write()` 背压、未注册 `res.on('error')`；慢客户端/半开连接可能积压内存，`try/catch` 抓不到异步 socket 错误。 | 检查 write 返回值 + `res.on('error')` + `res.writableLength` 阈值断线。 | open |
| m-4 | `sim.js:373-389, 405-407` | 完美格挡的 `perfect` FX 被 push 两次（格挡分支一次、`else if (perfect)` 再一次）。 | 删除重复 push。 | open |
| m-5 | `sim.js:291-299` | 动作前摇期间仍可用移动方向改写 `facing`，已经"出手"的攻击可以转向，客户端攻击弧也按当前 facing 画。 | 动作锁定朝向（只在 action 为空时更新 facing），或仅允许有限转向。 | open |
| m-6 | `sim.js:283-286` | 命中只在 startup 后**单帧**结算一次：无 active 窗口扫描、无多段、无受击硬直/浮空，目标在 active 帧内进入范围打不中；不对 z 做判定。原型可接受，但影响"打击感/判定"评估。 | 在 active 窗口内逐帧判定或至少记录判定帧；正式版移到 Unity/Fusion 的 hitbox 方案。 | open |
| m-7 | `game.js:646` | 找不到自己的玩家时 HUD 回退到 `s.players[0]`，会显示别人的名字/血量。 | 找不到显示 `DISCONNECTED` 占位。 | open |
| m-8 | `game.js:378-391, 519` | 近战距离下玩家名字/血条与木桩血条/文字重叠（截图可见），核心战斗画面可读性差。 | 名字/血条防重叠、木桩标签上移、或近战距离隐藏木桩文字。 | open |
| m-9 | `style.css:31-46` | canvas 用 `object-fit: contain` 自适应，但 HUD 用 `inset:0` 视口定位；非 16:9 窗口时 HUD 与画面区域错位。 | 用与 canvas 同尺寸的舞台容器定位 HUD，或 JS 计算 letterbox。 | open |
| m-10 | `test/*.test.js` | 覆盖缺口：10 个测试全绿但完全没覆盖 B-1/M-3/M-4/B-2 这类输入边界；`server.test.js` 没有"两个客户端互相可见"、没有验证输入真的改变权威状态；完美格挡只直接调 `applyDamage`，没测输入时序。 | 增加 §5 各 finding 的负例测试 + 双客户端可见性 + 输入→状态断言。 | open |
| m-11 | `server.js:67-76, 116-151` | `/input` 不校验 `Content-Type` 和 `Origin`（跨源简单 POST 可打，B-2 的一部分）；`GET /input` 落到静态 404 而非 405。 | 要求 `application/json`、校验 Origin/自定义 Header；非 POST 明确 405。 | open |
| m-12 | `server.js:207-208`、`mvp/README.md` | `HOST=0.0.0.0` 可把无鉴权服务暴露到局域网/公网，README 未警告。 | README 加粗警告"仅限 localhost，禁止暴露"；或默认拒绝非回环 HOST。 | open |
| m-13 | `server.js:214-219` | SIGINT 关服只 `server.close`+500ms 强退，不结束/通知 SSE 客户端；客户端表现为神秘重连。 | shutdown 里遍历 clients 发 `event: shutdown` 并 `res.end()`。 | open |
| m-14 | `sim.js:76`、`server.js:85` | 名字按 UTF-16 截断 `slice(0,18)` 可能劈开代理对（emoji），产生替换字符。 | 用 `Array.from(name).slice(0,18).join('')` 或码点截断。 | open |
| m-15 | `server.js:116-151` | 无输入限速：实测 50 条连续合法输入 2631 req/s 全 204，200 并发 199×204；动作/冷却由 sim 兜底，但带宽/CPU 可被刷。试点用可接受，生产必须限速。 | 每 token/IP 令牌桶（例如 ≤30–60 req/s）。 | open |
| m-16 | `sim.js:421-437`、`SPAWNS` | 重生固定出生点且无保护帧，可被蹲点。 | 重生 1–2s 无敌/位移保护（正式版再做）。 | open |
| m-17 | `server.js:176-189`、`sim.getState()` | 全量 JSON 状态广播：1 人时单帧 ~559B @21Hz，4 人+FX 时线性增长，无 delta/压缩；Web 原型可接受，不可扩展。 | 迁移到 Fusion 的增量快照；Web 原型若继续用，可做 delta/字段裁剪。 | open |
| m-18 | `sim.js:105, 14-15`、`game.js:682`、`server.js:99-102` 等 | 死代码/未接线：`lastSeen` 从不读、`JUMP_V`/`GRAVITY` 物理存在但无输入入口（与 M-2 同源）、客户端处理 `ev.type==='perfect'` toast 但服务器从不 push 该 event、`startsAt` 等。 | 接线或删除，避免误导后续维护。 | open |

---

## 6. 修复优先级与范围建议

### 6.1 叫它"可交给用户试玩"之前必须修（blocker）

1. **B-1**：入口 shape 校验 + request 级 try/catch（必做，否则任何异常输入/恶意网页都能毁掉试玩局）。
2. **B-2**：welcome 下发 session token、`/input` 校验 token + Origin/自定义 Header（必做；或者 Lead 明确签字接受仅本机可信环境，并在 README 写死限制、禁止 HOST=0.0.0.0）。建议直接修，成本很小。

### 6.2 作为"手感/时序验证"结论之前应该修（major）

3. **M-1**：真实 elapsed dt（否则所有手感数据无效，且和 REQ-TECH-002 30Hz 基线冲突）。这条比看起来重要：它决定这次 MVP 试玩有没有数据价值。
4. **M-2**：实现 jump 或删除跳跃宣传（不能一边写帮助一边 no-op）。
5. **M-3**：动作白名单 own-property 校验（1 行）。
6. **M-4**：seq 上界/有限整数校验（几行）。
7. **M-5**：明确 MVP 是否覆盖「装备=招式」；要么最小化实现 2 套招式表，要么改 README 与结论口径（这是范围/口径问题，不修代码也要修文档）。

### 6.3 原型阶段可以接受的

- UI/视觉：重叠、letterbox 错位、HUD 小字号 → 现有截图已能表达形态，等 M0 美术/UI。
- 无客户端预测/回滚、远程延迟、30Hz 全量快照 → README 已声明是形态验证，生产用 Fusion。
- 固定出生点无保护帧、无平衡/反作弊、刷新即新角色、无房间列表/账号/持久化 → README 已列为已知限制，符合 MVP 边界。
- 输入组合在客户端做 70ms 缓冲 → README 已声明生产移回服务器（注意 M-1 下该 70ms 实际是 ~78–94ms，文档要按实测写）。
- 几何占位美术、无音效、无设置菜单 → 阶段合理。

### 6.4 应该移到 Unity/Fusion 再做（不要在 Web MVP 里继续加码）

| 项 | 原因 |
|---|---|
| 网络模型 | HTTP 轮询 + SSE 只能验证"形态"：换成 Fusion 2 Server Mode 的可靠/非可靠通道、客户端预测、服务器校正、200ms 命中盒回放（REQ-TECH-002）。 |
| 输入管线 | 60Hz InputFrame + 时间戳 + **服务器端**组合解析（`docs/03`），替代客户端 70ms 缓冲；输入序列由服务器会话持有（同时天然修掉 B-2/M-4）。 |
| 判定/手感 | active 帧 hitbox、受击硬直、击飞、Z 轴、防御矩阵（cap 200ms、完美格挡 150ms/0.5 tick）——Web Canvas 原型不适合做最终判定调优。 |
| 相机/角色尺寸 | URP 正交相机 size8/pitch50/yaw45、1.8m≈78px、6/10m 可见性、14m 边缘指示——**必须走 M0 URP 验收，Web MVP 不能替代**。 |
| 性能/渲染 | 低多边形 + 像素贴图、像素密度、GPU 性能、阴影/描边等，Web Canvas 不作为依据。 |
| 输入设备 | 3 款键盘 QA（`validation/input/manual_test.html`）、键位重映射、经典/现代布局。 |
| 服务侧工程 | 账号/会话、房间/大厅/频道、速率限制、反作弊、持久化/计分、监控。 |
| 资产/数值 | 把 MVP 的 MOVES 表映射为 `docs/00`/`docs/02` 的数据驱动资产，并过平衡流程。 |

---

## 7. 明确的边界声明：**本 MVP 不是 M0 引擎验证的替代品**

本评审的所有"通过"只意味着 **Web 原型形态可用**，不包括以下任何一项，且**不得**用本 MVP 的截图/手感/性能数据去签署 M0 门：

- ❌ 不能验收 2.5D 正交相机的数字（size 8 / pitch 50 / yaw 45 / 1.8m≈78px / 6–10m 可见性 / 14m 边缘指示）——Web Canvas 是视觉近似；
- ❌ 不能验收 URP 渲染、像素贴图、低多边形资产、光照/描边/性能预算；
- ❌ 不能验收 Fusion 2 的网络手感（预测/校正/200ms 回放/丢包矩阵/150ms 格挡矩阵）——HTTP+SSE 的延迟结构与生产完全不同；
- ❌ 不能验收 60Hz InputFrame / 服务器组合解析 / 输入时间戳的延迟与正确性；
- ❌ 不能验收 3 款键盘 QA、键位重映射、UI 键盘导航（REQ-QA-001 的战斗以外部分）；
- ❌ 本报告的"能玩"只覆盖战斗循环 + 木桩 + 双人 PvP，不覆盖登录/大厅/匹配/结算/装备/聊天等 REQ-QA-001 要求的全流程。

这些仍按既定路线走 M0（URP 相机对账、Fusion 2 矩阵、键盘 QA），本 MVP 的价值是**提前暴露了交互形态、服务器权威结构、以及时序/输入边界问题**（其中 tick 率问题在 Web 与 Unity 都会踩到，值得带进 M0 清单）。

---

## 8. 复现与证据存档

### 8.1 复现命令（评审时实际执行）

```powershell
# 1) 作者测试（从 mvp/ 运行）
cd mvp
& "C:\Users\dai\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe" --test test/*.test.js
# → 10 tests, 10 pass, 0 fail（连续 5 次复跑一致）

# 2) 自起服务（评审者端口，避免干扰 Lead 的 3000）
$env:PORT='3100'
& "C:\Users\dai\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe" mvp\server.js
# 评审结束后已停止；复检 http://127.0.0.1:3100/health 已不可达

# 3) 独立探针（临时脚本，已删除）：33 项协议/容量/穿越/XSS 检查、PvP、资源门控、
#    无头 Chrome 键盘 E2E、崩溃复现、tick 率测量、移动速度测量均在此环境完成。
```

### 8.2 证据清理

- `mvp/review/` 下评审期间产生的临时脚本、日志、临时截图、Chrome profile 均已删除；**只保留本文件**。
- 未修改任何源文件（`mvp/sim.js`、`mvp/server.js`、`mvp/public/`、`mvp/test/`、`mvp/README.md`、`mvp/screenshots/`、`docs/` 均未被我写入）；Lead 的 3000 端口服务未被我停止或写入。
- 截图检查仅只读打开 `mvp/screenshots/mvp-demo.png`。

### 8.3 待核实项

- MVP 的数值表（HP 500 / MP 100 / GUARD 300 / ULT 100 / 木桩 5000 / 各招伤害与冷却）与 `docs/00`-`docs/02` 正式招式表的逐项映射关系：本次只核对了 README 与代码一致性，**未逐项对照设计基线（待核实）**。
- 作者截图 `mvp-demo.png` 的生成方式为 `mvp/scripts/screenshot.js`（CDP `?demo=1`）；本次未重跑作者脚本，而是用自建无头浏览器独立复现了等价画面。
- REQ-QA-001 的"菜单/匹配/聊天全键盘"部分不在 MVP 范围，未验证。
