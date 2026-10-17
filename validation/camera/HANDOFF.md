TASK: TASK-060
STATUS: done

CHANGED:
- validation/camera/run.py（新增；确定性模型 + 合成渲染，seed 20261017）
- validation/camera/metrics.csv（新增；15 行 × 35 列：shipped size 7/8/9 × pitch 45/50/55 + zoom size 15/23 × 3 pitch）
- validation/camera/render_size7.png、render_size8.png、render_size9.png（新增；1920×1080 合成图，标注 "SYNTHETIC MODEL RENDER - NOT UNITY"）
- validation/camera/REPORT.md（新增；结论先行、公式/结果/文档对照/建议/限制）
- validation/camera/HANDOFF.md（本文件）
- 未修改 docs/、AGENTS.md、docs/tasks.json、validation/README.md、validation/REPORT.md；未写其他 stream 目录。

DECISIONS:
- 屏高口径采用 H_eff = 1.8m（含帽/武器有效剪影），与 docs/02 §3.1、docs/04 §4 对齐；同时输出 H_body = 1.5m 列以暴露 docs/00 §3.1「1.5m 基准」与 70–90px 口径的冲突（见 REPORT §4）。
- 「在视口内」定义 3 种方向口径并全部入 CSV：inside_forward（相机正前方脚点，主口径）、inside_world_axis（世界 +X 轴，yaw=45° 时为屏幕对角）、inside_any_direction（半对角上界）。
- 固定验证参数：pitch 45/50/55° × size 7/8/9，yaw = 45°（TASK-060 brief 公式给出；docs 未定义 yaw，已作为待补参数上报），1920×1080，默认 zoom 1.0×，相机居中无前移。
- zoom-out 行按 docs/02 §3.1 的 size 15/23 × pitch 45/50/55 独立成行核对（不复用 shipped 行）。
- 合成图把 6/10/14m 角色按真实投影位置绘制（因此 size 7/8 下 10/14m 被裁或出屏是结论本身）；另加 1:1 角色剪出条与俯视示意 inset，分别用于「美术剪影可辨性参考」与「视口矩形 vs 距离环」。
- 不改基线：所有参数建议仅写入 REPORT §5（默认 size 8/pitch 50°/yaw 45°；相机前移 anchor 0.67–0.77 等），实际变更需 ADR-002 复访 + Human 门（AGENTS §9）。

EVIDENCE:
- 复现命令（PowerShell）：
  `C:\Users\dai\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe validation\camera\run.py`
- 输出：metrics.csv（15 行）、render_size7/8/9.png、stdout 自检 + REPORT FACTS + sha256。
- 确定性：seed 20261017；两个不同输出目录各跑一次，metrics.csv 与 render_size8.png 的 SHA256 逐字节一致（本机已验证）。
- 脚本自带 assert 全过：角色屏高公式；屏幕四角投射 z=0 多边形；half_width/half_depth 与闭式解误差 <1e-9；正前方 10m 投影一致；CSV 行数 15。Python 3.12.14 / numpy 2.3.5 / Pillow 12.3.0，只依赖 stdlib+numpy+Pillow。
- 最终 SHA256：
  - metrics.csv `156a168d9547f0b46fe6f9d7d771965723a3d3a3214e0f1c730239b296f5f992`
  - render_size7.png `ba172c2c70dafebea317256efae064aa7e835d7b4175f42ea7ec11ff51dc69f3`
  - render_size8.png `b2d88c285a805d54e203ad8eac3e19366a6ad5527535a260faf516cdb4101d08`
  - render_size9.png `920f834b5c5ecaecb602c0afffb092707b0871affd242d11c8d677f4dd21671d`
- 关键数字（H_eff 1.8m，1080p）：char px size 7/8/9 @p50 = 89.3 / 78.1 / 69.4（70–90px 严格 5/9 组合通过）；可见地面半宽 12.44/14.22/16.00m，半深 @p50 9.14/10.44/11.75m；6m 正前 9/9 在屏内、10m 正前 5/9、14m 正前 0/9；20/30m 必须 zoom-out；size 15/23 仅在 pitch≤50° 脚点口径勉强成立。

RISKS:
- 模型级验证，不含 Unity/URP 实际渲染、遮挡/后处理/AA/地形高差；真实可读性可能不同。需 M0 引擎实测（REPORT §5.5 清单）后才能作为最终决策证据。
- 无 playtest：docs/02 的 6/10/14m 识别率阈值 90/85/80% 未验证，合成图不能替代。
- 假设 H_eff = 1.8m（含帽/武器）；实际美术包围盒需在 Unity 量测回填，否则 70–90px 结论可能偏移。
- 假设 yaw = 45°（docs 未定义）；若最终 yaw 不同，世界轴 14m 可见性/构图需重跑。
- 假设相机居中（无前移/跟随偏移）；若采用 camera lead，需按 REPORT §5.2 的 anchor 数值重跑。
- 70–90px 只在默认缩放 1.0× 成立；0.8×/1.2× 分别为 62.5/93.7px，若验收要求跨缩放保持 70–90px 则不可行，需先改口径。
- docs/00 §3.1「1.5m 基准」「M0 可校准 6–8」与 70–90px 存在口径冲突（size 6 = 104.1px）；已提修正建议但未改 docs（超出写域，需 Lead/Human 走 baseline 变更）。

NEXT:
- validation-reviewer（TASK-063）：重跑 `run.py`，核对公式/CSV/三张图/结论；重点复核「inside_forward / world_axis / any_direction」口径与 14m 结论；按 AGENTS §7 出 REVIEW（blocker/major/minor）。
- Lead/Orchestrator（TASK-064）：把 REPORT §4/§5.4 的 docs 修正建议（1.5m vs 1.8m、size 6–8、yaw 缺失、14m 验收前提、20/30m zoom size 公式）纳入 `validation/REPORT.md` 与 baseline 决策请求；如需改默认相机参数，按 docs/04 §4 与 AGENTS §9 走 ADR-002 复访 + Human 门。
- M0 引擎实现方：按 REPORT §5.5 在 URP 实测角色包围盒 78px、orthographicSize 语义、相机 anchor/边缘指示器、6/10/14m 真实识别率，再决定是否维持 size 8 / pitch 50° / yaw 45°。
