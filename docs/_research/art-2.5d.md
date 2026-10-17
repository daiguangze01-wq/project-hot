# 2.5D 俯视 3D 低模 + 像素贴图：美术研究

> TASK-005 研究材料。最终以 `docs/04` 为准；预算为估算，±30%。

## 1. 总判断

与 Diablo III/Lost Ark 同为固定机位，关键差异是**正交**；像素感靠贴图光影、顶面剪影、限帧动画，不靠降分辨率。先定「角色多大、1m 多少像素」，再谈风格。

## 2. 参考取舍

- **Lost Ark**：固定斜俯视、只跟随/微缩放；借构图，不借写实比例。
- **RO**：2D billboard + 3D 地形；低帧可读但换装贵；不借 2D 资产（ADR-010）。
- **D3/D4**：固定机位、不旋转；环境降饱和、交互物提亮。
- **Hades**：3D 模型 + 手绘贴图做 2D 观感；借轮廓光。
- **Hytale**：角色 64px/单位、道具 32px/单位，无 PBR，阴影画进贴图；最接近参照。
- **MapleStory**：关键姿势 + 大色块 + 阶梯帧；借姿势。
- **GetAmped**：装备=招式、固定镜头；借复用，不借侧视。
- **Trove（反例）**：voxel + 高饱和 + 发光过载，30m 外糊成亮块（推断）。

## 3. 相机/构图

- 默认正交，pitch 50°（45–55° 内）、yaw 45°。
- 屏高比 ≈ 身高 × cos(俯角) / (2 × ortho size)：1.5m、size 8 约 6%；size 7/45° 约 7.6%。基线 8–12% 需把帽/武器算进有效身高（约 1.8m）或 size 降到 6。
- 建议测试：1.8m/size 7 或 1.5m/size 6；size 6 地面纵深≈15.7m、宽≈21.3m，交战半径≈8–10m；size 8 半径≈10–14m。
- 跟随用死区，角色置于屏高 55–60%，前方留 60% 视野；屏幕边缘做威胁/队友指示。
- 缩放 0.8–1.2 五档，point 采样、关 TAA。
- 遮挡用 dither 淡出（alpha clip），只淡出角色与相机间的屋顶/树冠。
- 高度：0.5m 台阶 + 投影 + 边缘高亮；Shadow Distance 30–40m，更远烘焙 AO。

## 4. 斜俯视剪影

- 俯视只见顶面，70% 辨识信息放顶面：帽顶/肩甲顶/武器顶各 2–3 色块，侧面只做暗部。
- 帽檐 ≥1.5× 头宽（45–60px）；单侧大肩甲指示朝向；头/肩/武器成不对称三角。
- 武器待机也外展 ≥30°；剑 ≥1.2m、枪 ≥2m；8 原型轮廓互斥（直线/弧/环/节）。
- 2.5–3 头身，头占 1/3–2/5；100px 高时头≈30–40px，五官 2–4px。
- 披风/尾 4–6 骨、摆幅 ≤0.3m，不遮预警。
- 3–8k tris、30–40 骨、贴图 64–128px、≤4 权重、1 材质；角色 64px/m（1.5m≈96px），32–64 色板，阵营 4 色替换，1px 暗描边 + 顶面亮边。
- 8–12fps 阶梯：每招 3–5 关键姿势，前摇/命中停留最久。

## 5. 环境

- 2m 网格；kit 2×2/2×4/4×4m，可拼 8×8/16×16m 房间；墙高 2/3/4m，台阶 0.5m，桥宽 4m，悬崖 2m 高差。
- 高度三档：0.5m 可走、1m 需跳、2m 不可逆；桥/崖边加 1px 亮边。
- 贴图 128–256px，地面 2m=64px（32px/m），墙面 trim sheet，地面禁高频噪声。
- 烘焙 lightmap + 顶点色 AO + 贴图内阴影；实时只留方向光 + 角色投影；屋顶/树冠打 occluder。
- 行走面中间调、墙压暗、交互物提亮；预警色不进环境。

## 6. VFX/UI

- VFX 64–256px sprite sheet、8–12fps、additive；地面预警用投影 quad/decal，正交下尺寸恒定。
- 预警圈 2–3 层：外圈红、内圈实心、扇形倒计时；红=即伤、黄=延迟、蓝=可反制。
- hitstop 40–80ms 只做客户端，不冻结服务器模拟；屏震 2–5px/80–120ms 不旋转；受击闪白 2 帧。
- UI 全键盘、无鼠标光标：Z/X/C/V 键帽 + 冷却扇形、焦点环 + 方向键、焦点顺序固定、无 hover、tooltip 随焦点、改键实时生效；伤害数字用像素字体。

## 7. 管线/预算

- Blockbench 起模 → Blender 绑定/烘焙 → Aseprite/Substance 调色 → Unity URP。
- 像素用 Aseprite 主画；Substance 只做烘焙/材质校验，不引入 PBR 噪声。
- 共享 30–40 骨骨架 + 武器 socket + 披风/尾链；共享移动/受击/死亡，8 套攻击按武器原型（每套 10–14 招），上半身 additive；动画按 8–12fps 烘焙后 stepped。
- 导入校验：tri 3–8k、骨 ≤40、贴图 64–128px（32 倍数）、色 ≤64、pivot 脚底、材质 ≤2（角色/武器各 1）；AssetPostprocessor + CI 阻断并写 manifest。
- 预算（估算 ±30%）：本研究报告约 EA 28–32 人月、1.0 60–65 人月；C6 详细估算约 EA 87、1.0 174 人月。差异来自是否含全套动画/外包返工/环境量/Boss 复杂度；最终以 `docs/04` 的 33–87/65–174 区间和 M0 实测为准。

## 8. 风格测试

- 1 角色 + 3 装备（剑/弓/法杖）+ 16×16m 环境 + 1 Boss + 1 套 VFX/UI；2 美术 + 1 技术美术，6–8 周。
- 正交下 10/20/30m 不改变角色像素大小，只决定是否在屏内与遮挡；size 6 时 20/30m 已在屏外，要测需 zoom out 到 size≈15/23。
- 建议：5–10m 测武器与攻击状态；20m（size 15）测武器原型 ≥80%；30m（size 23）测阵营 ≥70%；30m 只作战术视图。
- billboard 在正交下无透视失真，是强基线；3D 胜在换装/复用/多角度/高度；3D 差距 ≤10% 且换装更便宜即通过。
- 硬指标：GTX 1060 1080p 60fps、Art Lead/Human 签字。

## 9. 来源

- [Hytale 模型制作规范](https://hytale.com/news/2025/12/an-introduction-to-making-models-for-hytale)
- [Diablo III 45° 固定视角](https://www.ali213.net/news/html/2009/3484.html)
- [Lost Ark 镜头角度指南](https://cyberockk.com/2022/02/lost-ark-beginners-guide-classes-camera-angle-currencies/)
- [Ragnarok Online](https://en.wikipedia.org/wiki/Ragnarok_Online)
- [Hades 手绘角色 3D 化](https://www.gamedeveloper.com/art/learn-how-supergiant-brought-i-hades-i-hand-painted-characters-to-life)
- [Guilty Gear Xrd 3D 做 2D 感](https://www.polygon.com/2015/5/26/8663003/guilty-gear-xrd-cel-shading-making-of)
- [Trove 风格指南](https://trovesaurus.com/page=3976/)
- [Unity URP 阴影距离](https://docs.unity3d.com/Manual/shadow-distance.html)
- [Game feel：hitstop/屏震](https://gamedevacademy.org/game-feel-tutorial/)
