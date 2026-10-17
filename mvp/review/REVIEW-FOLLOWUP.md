---
id: REV-071-FU
type: review
task: TASK-071（修复后窄范围复评）
subject: Project Hot — Web MVP 修复后独立复评（REVIEW-FOLLOWUP）
version: 1.0
status: final
owner: mvp-reviewer
reviewers: [lead]
depends_on: [REV-071, TASK-070]
last_reviewed: 2026-10-18
scope: mvp/
verdict: pass-with-fixes（原 blocker 全部关闭；本机可玩）
blockers: 0
majors: 0
minors: 4
---

# REV-071-FU — Web MVP 修复后独立复评

> 窄范围复核 Lead 声明的修复，不修改任何源文件，只写 `mvp/review/`。
> 方法：重读 `mvp/sim.js`、`mvp/server.js`、`mvp/public/game.js`、`mvp/test/*.test.js`、`mvp/README.md` + 独立重跑测试 5 次 + 自起服务（PORT=3100）+ 独立 SSE 客户端/攻击性 HTTP 探针 + 隔离子进程崩溃 fuzz + 模拟层独立推导 + 无头 Chrome 键盘 E2E + 新旧截图核对。临时脚本/日志已删除。

---

## 0. 结论

| 问题 | 结论 |
|---|---|
| 原 blocker B-1（畸形输入杀进程） | ✅ **已关闭**。历史 3 条崩溃向量全部 400；隔离子进程连发 **31 条畸形请求 + 120 条确定性 fuzz**，进程始终存活，之后合法输入仍 204，无未捕获异常栈。 |
| 原 blocker B-2（`/input` 无身份绑定） | ✅ **已关闭**。welcome 下发 36 hex 随机 token；缺失/伪造 token → 401；A 的 token 驱动 B → 403 且 B 未被移动；token 不出现在广播 state；SSE 断开后旧 token → 401；非 JSON content-type → 400。 |
| 原 major M-1（30Hz 名不副实） | ✅ **已关闭**。实测 **29.97Hz / 3s（delta 90 tick）**、SSE 广播 30 帧/s、有效移速 **5.12 u/s**（声明 5.2；修复前 21.42Hz / 3.63 u/s）。 |
| 原 major M-2（V 跳跃 no-op） | ✅ **已关闭**。网络实测 z 峰值 0.70 且落地归 0；键盘 V 端到端同样 z=0.70；空中二段跳被拒。 |
| 原 major M-3（原型链动作） | ✅ **已关闭**。constructor/toString/`__proto__`/hasOwnProperty → 204 但不产生 action、玩家不卡死，之后 light 正常。 |
| 原 major M-4（seq 无上界） | ✅ **已关闭**。stale/huge(1e15)/string/float/负数/0/Infinity 全部 409；之后合法 seq 仍 204；窗口边界恰为 +3000（+3001 拒绝）。 |
| 原 major M-5（装备=招式缺失） | ✅ **按缩减范围关闭**。`blade`/`fist` 两套招式表在 sim 与线协议上都生效（拳师 skill1 **-15 MP** vs 剑豪 -20；拳师轻击 26 伤害 vs 剑豪 30），HUD 显示核心名；README 已明确"只有 2 核心招式表差异，防具/符文/外观不在 MVP，不能据此说装备=招式已完整验证"。 |
| 声明的 minors | 大部分确认修复：held 全量快照、完美格挡 FX 去重（count=1）、动作中朝向锁定、HUD 不再回退显示他人、木桩标签上移（截图与 live 截图均确认不再与角色名叠字）。**名字码点截断只修了 server 一层，sim/客户端仍按 UTF-16 截断**（见 F-2）。 |
| **本机可玩吗** | ✅ **可玩**。键盘 E2E 12/12：连接（token 流程）、W 移动、C 轻击（拳师 26 伤害）、Z+C（MP -15）、V 跳跃（z 0.7）、Space 防御、HUD 与服务器一致、正常游玩 0 JS 异常；XSS 仍被转义。 |
| 新 blocker | **无**。 |

**本轮问题计数：blocker 0 · major 0 · minor 4（均为新增/残留小问题，不阻塞本机试玩）。**

---

## 1. 独立证据

### 1.1 测试（作者测试，独立重跑 5 次）

```powershell
cd mvp
& "C:\Users\dai\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe" --test test/*.test.js
```

**5/5 次均为 15 tests / 15 pass / 0 fail**（Node v24.21.0，PowerShell，无 flake）。
新增测试确实覆盖了：`held:5`/`held:'up'` 拒绝、jump 起落、cores 差异、seq 上界、token 缺失/伪造/串玩家、两客户端互相可见。仍未覆盖：`?core` 原型链、星平面名字、dash 穿身（见 §2）。

### 1.2 B-1 回归：隔离子进程 + 历史崩溃向量 + fuzz

自起子进程（PORT=3141），保持 1 个 SSE 玩家，逐条发送：

| 请求 | 结果 |
|---|---|
| 历史向量：body=`null` | 400 `payload_must_be_object`（修复前 exit 1） |
| 历史向量：`held:5` | 400 `held_must_be_object`（修复前 exit 1） |
| 历史向量：`held:"up"` | 400 `held_must_be_object`（修复前 exit 1） |
| held `true/null/[]`、actions `'light'/{}`、payload `[]/5/"x"/true`、seq `null/{}/[]/true/1e999`、playerId 数字/对象、token 对象/数组、9KB body、错误 content-type、proto pollution 尝试 | 全部 400/401/403/409/413，进程存活 |
| actions `[{}]`、constructor/toString/`__proto__` actions | 204 但无状态副作用，进程存活 |
| 之后合法输入 | **204**（畸形与 fuzz 之后服务仍可正常接受输入） |
| 120 条确定性 fuzz（混合类型 payload） | 状态分布 {400:88, 401:20, 403:5, 409:7}，**0 次崩溃**，无未捕获异常栈；`/health` 全程 ok |

结论：**B-1 关闭**。崩溃栈不再出现（stderr 只有 `?core=__proto__` 场景被 try/catch 记录的一条 `input handler error`，见 §2-F1）。

### 1.3 B-2 回归：token 身份绑定（真实线协议）

| 检查 | 实测 |
|---|---|
| welcome 携带 token | p1/p2 各 36 hex 字符且互不相同 |
| token 泄漏 | 广播 state JSON 中**不含**任何 token |
| 缺 token | 401 `invalid_session` |
| 伪造 token | 401 |
| A 的 token + B 的 playerId | 403 `player_session_mismatch`；随后 B 的 x 未变化 |
| B 用自己 token 操作自己 | 204 |
| 非 `application/json` | 400 `content_type_must_be_json`（跨源简单 POST 被挡，配合 token 关掉 CSRF 面） |
| SSE 关闭后旧 token | 401（session 随连接清理） |
| 路径穿越 | 仍 404 |

结论：**B-2 关闭**。`/events` 仍是未鉴权 GET（可被跨源打开占名额），但无法读取 token 或操控他人，属可接受的原型残余。

### 1.4 M-1 回归：tick 率 / 广播率 / 有效移速

| 测量 | 修复前 | 本次实测 |
|---|---|---|
| `/health` tick 增量（3s 墙钟） | 21.42Hz | **29.97Hz**（delta 90 / wall 3.00s） |
| SSE state 帧率（1s） | ~21帧 | **30 帧/s** |
| 按住右 1s 位移 | 3.63 u/s（0.699×） | **5.12 u/s**（声明 5.2，含输入往返，容差内） |
| sim 直接步进 1s | — | 5.62 单位（测试起点与木桩重叠导致分离修正偏差，网络测量为准） |

结论：**M-1 关闭**（`hrtime` 固定步进 + 追帧生效；`README` 的 30Hz 描述现在与实测相符）。

### 1.5 M-2 / M-3 / M-4 / M-5 回归

| 项 | 证据 |
|---|---|
| **M-2 jump** | 网络：`actions:['jump']` → 16×50ms 采样 z 峰值 **0.70**，尾部 3 次 z=0（落地）；浏览器键盘 V 同结果；sim：airborne 时二次 jump=false。 |
| **M-3 白名单** | HTTP 204 但 state 无 action；之后 light 204 且 action.type=light；sim 直调 `tryAction('constructor'/'toString'/'__proto__'/'hasOwnProperty'/''/42)` 全 false，`action=null`。 |
| **M-4 seq** | stale/huge/string/float/negative/0/Infinity 全 409；合法 seq 10 → 204；窗口边界 +3000 接受、+3001 拒绝。 |
| **M-5 cores** | sim 招式表：拳师 light 26/heavy 85/skill1 60MP15CD3…；剑豪 light 30/skill1 70MP20CD4…；网络：`?core=fist` welcome `{core:'fist',coreName:'拳师'}`、`?core=blade` 对应剑豪、未知 core 回退到真实核心；拳师 skill1 实测 MP 100→85（-15）；浏览器键盘 Z+C 同样 -15 且 HUD 显示"BrowserFollow · 拳师"、技能槽 CD 2.7（拳师 3s 冷却生效）。 |

### 1.6 键盘 E2E（无头 Chrome，12/12）

| 检查 | 实测 |
|---|---|
| 页面连接（token 流程） | `connected · p1` |
| HUD 核心显示 | `BrowserFollow · 拳师` |
| 第二观察者 + 双核心状态 | 浏览器 fist / 观察者 blade，state 均带 core |
| W 移动 | y 4.8 → 0.845 |
| C 轻击（拳师） | 木桩 4974 → 4948 = **26 伤害** |
| Z+C（拳师技能1） | MP 100 → **85**（-15） |
| V 跳跃 | 服务器 z 峰值 0.70，落地归 0 |
| Space 防御 | guarding true → false |
| HUD 与服务器一致 | MP 85、木桩 4948 一致 |
| 正常游玩 JS 异常 | **0** |
| XSS（`<img onerror><svg onload>` 名字） | `window.__pwn=null`、`img/svg` 元素 0、名字以文本显示 → 仍安全 |

### 1.7 截图复核

| 截图 | 结论 |
|---|---|
| `mvp/screenshots/mvp-demo.png`（更新后） | HUD `PixelKnight · 剑豪`（核心名已显示）；木桩标签上移到 `g.y-118`，与角色名明显分离、不再叠字；技能槽冷却/ULT 百分比可见；场地/影子/选中环正常。**但发现演示数值异常**：MP 50（技能1+技能2 都放了）而木桩仅 4940（只掉了 60 = 2×轻击 30）、ULT 7，说明两个技能都没打到木桩——原因见 §2-F3（dash 穿身导致的 whiff），不是 HUD 造假。 |
| 我在键盘 E2E 中另拍的 live 截图（临时，已删除） | 双人同屏、拳师 HUD（HP500/MP85/GUARD300/ULT3）、木桩 4948、技能1 CD 2.7s、名字/木桩标签不再重叠；与服务器状态一致。 |

### 1.8 环境 / 清理

- Node v24.21.0；自起服务 `PORT=3100`，复评结束后已停止（`/health` 已不可达）；未触碰 Lead 的 3000 端口服务。
- 未修改任何源文件（`mvp/sim.js`、`mvp/server.js`、`mvp/public/`、`mvp/test/`、`mvp/README.md`、`mvp/screenshots/`、`docs/` 均未被我写入）；本轮临时脚本、fuzz 输出、live 截图、Chrome profile 已删除，`mvp/review/` 只新增本文件。

---

## 2. 新增/残留问题（blocker 0 · major 0 · minor 4）

```text
SEVERITY: minor
ID: F-1
LOCATION: mvp/server.js:92（`const core = u.searchParams.get('core')`）、mvp/sim.js:171（`(core && CORES[core])`）、mvp/sim.js:234（`const core = CORES[p.core] || CORES.blade`）
ISSUE: `?core=` 是未做 own-property 校验的原型链查找——与修复前的 M-3 同类，只是搬到了 core 参数。实测 `GET /events?core=__proto__`：welcome 返回 `{id:'p5', core:'__proto__'}`（无 coreName）；该玩家之后每次动作 POST → **500 `internal_error`**（`Cannot read properties of undefined (reading 'light')`，被 server.js 的 try/catch 捕获，进程存活、其他玩家不受影响）。`?core=constructor` 则得到怪异的 `coreName:'Object'`（core 表取到 Object 构造函数）。玩家只能自伤（cannot act），且需要手工构造 URL；不构成 blocker。
FIX: `if (typeof core !== 'string' || !Object.prototype.hasOwnProperty.call(CORES, core)) core = undefined;`（server 或 sim.addPlayer 入口均可），`sim.getMove` 里同样加 own-property 防护；补一条负例测试（core=__proto__ / constructor / hasOwnProperty）。
STATUS: open
```

```text
SEVERITY: minor
ID: F-2
LOCATION: mvp/sim.js:103（`createPlayer` 里 `String(name).slice(0, 18)`）；mvp/public/game.js:22（`playerName = (qs.get('name') || …).slice(0, 18)`）
ISSUE: 名字"码点截断"只修了 server.js:91 一层，另外两层仍是 UTF-16 截断，导致修复不完整：
  a) 服务器：`?name=a😀…`（18 码点 / 35 UTF-16 单元）经 server 码点截断后为 18 码点，再进 sim.createPlayer 被 `.slice(0,18)` 按 UTF-16 截成 **10 码点、末尾是孤立高代理 `\ud83d`**（实测 storedCodePoints=10, endsWithLoneSurrogate=true）。
  b) 客户端：同一 `.slice(0,18)` 后 `encodeURIComponent(playerName)` 对孤立代理抛 **URIError: URI malformed**（实测 headless Chrome：`game.js:223`，页面停在初始 "SSE · 30Hz server"/"Player"，不连接）。
  仅影响手工构造的星平面（emoji）名字，不影响普通 URL/玩家名；不是 blocker。
FIX: 三处统一用 `Array.from(String(name)).slice(0,18).join('')`（server 已有，sim + client 补上）；可在 client 用 `String.fromCodePoint`/码点迭代或 try/catch 包裹 encodeURIComponent。
STATUS: open
```

```text
SEVERITY: minor
ID: F-3
LOCATION: mvp/sim.js:238-280（tryAction 中 `if (m.dash)` 直接位移，不做目标/碰撞检查）、sim.js:340-344（命中只在 startup 后一帧按当前 facing 结算）、mvp/scripts/screenshot.js 演示脚本（?demo=1）
ISSUE: 剑豪技能1 的 2.0 突进会**穿过目标**且命中仍按原朝向结算，导致贴脸释放时 dash 把玩家送到目标另一侧、单帧命中判定落空（whiff）。sim 独立复现：起点 y=+1.4 面向木桩放 skill1 → 结束 y≈-0.81、木桩 5000→5000（whiff）；对照从 y=+3.0 释放 → y≈+1.01、木桩 5000→4930（命中 70）。这也解释了更新后 `mvp-demo.png` 的数值：MP 50 说明技能1/技能2 都放了，但木桩只掉 60（两次轻击，30+30；第二下因 0.75s 连段窗口在 30Hz 真实时间下刚好错过）、ULT 7（60×0.12），两个技能都因穿身/背向而落空。原型可接受，但（a）dash 无碰撞/无目标检查值得进 M0 判定清单；（b）官方演示截图目前展示不出技能伤害，建议演示脚本从更远处出手或先停步再放技能，避免评审误读。
FIX: MVP 内可选：dash 前记录朝向、命中判定使用激活时朝向/位置快照，或 dash 遇目标/边界停止；或至少调整 demo 脚本站位（不改 sim 也可，改 `mvp/scripts/screenshot.js` 的演示输入）。M0 侧把"突进穿身/位移技能与 hitbox 关系"列入 Fusion 判定验收。
STATUS: open
```

```text
SEVERITY: minor
ID: F-4（残留观察，非功能缺陷）
LOCATION: mvp/sim.js:388-414（resolveHit 不读 z）、mvp/sim.js:340-344（单帧命中）；mvp/server.js:230-237（广播写失败时只删 clients/sim，未删 sessions）
ISSUE:
  a) 跳跃现在能起落，但命中判定完全忽略 z（跳起不能躲任何攻击），2.5D 的 Z 轴在 MVP 里仍只是表现位移；这不阻塞试玩，但属于 M0 必须明确的设计点。
  b) 广播写异常分支（server.js:234-236）删除 client/player 时未同步删除 `sessions` 里的 token（仅在 SSE cleanup 里删），属潜在内存/悬空 session 小泄漏（正常关闭路径已覆盖，实测 token 失效正确）。两条都建议记入 M0/后续清理。
FIX: (a) 在 docs/03 命中判定节明确 z/跳跃是否参与（MVP 不参与则写入限制）；(b) 抽出统一 `dropClient(id)` 同时清 clients/sessions/sim。
STATUS: open
```

### 确认已修复的 minor（复核通过）

| 原项 | 复核结果 |
|---|---|
| held 局部更新粘键 | ✅ 全量快照：`held:{}` 后 right/guard 归 false（sim 实测 + client 总发全量） |
| 完美格挡 FX 重复 | ✅ 一次完美格挡仅 1 个 perfect FX |
| 动作前摇可转向 | ✅ 动作中 facing 锁定（sim 实测 0 → 0） |
| HUD 回退到 players[0] | ✅ 代码改为找不到自己显示 `DISCONNECTED/reconnecting…`（game.js:650-655） |
| 木桩标签与名字重叠 | ✅ `drawDummy` 标签上移至 `g.y-118`；新旧截图都不再叠字 |
| 名字码点截断 | ⚠️ 仅 server 层修复；sim/client 仍 UTF-16（见 F-2） |

---

## 3. 结论与建议

### 3.1 复评判定

- **原 2 个 blocker：全部关闭**（有独立复现证据）。
- **原 5 个 major：全部关闭/按缩减范围关闭**（M-5 的"装备=招式"以"2 核心招式表差异 + README 明确范围"方式关闭）。
- **本机可玩：是**。键盘 E2E 12/12、无 JS 异常；双人 PvP/房间容量/资源门控/清理/穿越/XSS 这些原评审通过项没有回归（本轮抽测均通过）。
- **对外试玩：仍建议只在本机 localhost**；README 已写明不要 `HOST=0.0.0.0`、无账号/限速/反作弊。真实曝光前仍缺账号/限速/Origin/反作弊（原评审 §7 不变）。

**Verdict：pass-with-fixes（0 blocker / 0 major / 4 minor）；作为"本机可玩 MVP"可以放行，4 个 minor 建议在下一轮顺手修（F-1/F-2 各约几行；F-3 至少改演示脚本；F-4 记入 M0 清单）。**

### 3.2 仍不能宣称的事（与 REV-071 一致）

- 本 MVP 仍**不是 M0 引擎验证的替代品**：不能验收 URP 相机/角色占屏、渲染与资产、Fusion 2 的预测/校正/200ms 回放、60Hz InputFrame/服务器组合解析、3 款键盘 QA 与全流程键盘导航。
- 「装备=招式」仅验证"2 核心招式表差异"的最小形态；防具/符文/外观/数据驱动资产不在 MVP，README 已如实标注。
- PvP 平衡/反作弊/限速/账号不在 MVP 范围；`/events` 仍是可被跨源打开占位的未鉴权 GET（无法读 token、无法操控他人）。

### 3.3 建议的下一步（给 Lead/作者）

1. 顺手修 F-1/F-2（各几行 + 2 条负例测试）；F-3 至少改 `scripts/screenshot.js` 演示站位并重出截图，避免"技能放了没伤害"的误导性证据；F-4 记入 M0 判定/清理清单。
2. 若要正式对外试玩：补 `/events` 的占用防护（如短时连接超时/同源限制）、全局限速，并明确"仅 localhost"发布形态。
3. 保持"每轮修复 → 独立复跑 + 攻击性探针"的流程；本轮证明该流程能抓住 tick 率这类"测试全绿但体验失真"的问题。

---

## 4. 复评命令摘要

```powershell
# from mvp/
& "C:\Users\dai\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe" --test test/*.test.js   # 15/15，5 次
$env:PORT='3100'; & "…\node.exe" mvp\server.js   # 复评后已停止
# 独立探针（临时脚本，已删除）：token/畸形/seq/action/cores/tick/速度/jump 网络探针；
# 隔离子进程 31 畸形 + 120 fuzz；sim 层 dash/名字/seq 边界推导；无头 Chrome 键盘 E2E + XSS + 截图。
```

**证据清理**：本轮所有临时脚本/截图/Chrome profile 已删除；`mvp/review/` 现只有 `REVIEW.md` 与本文件。
