# inbox — AI 生成收件

按下面结构放文件：

```text
inbox/hot_blade_01/
  character_ref.png
  sheets/hot_blade_01_S_idle.png
  sheets/hot_blade_01_S_walk.png
  sheets/hot_blade_01_S_run.png
  sheets/hot_blade_01_S_light_attack.png
  sheets/hot_blade_01_S_heavy_attack.png
  sheets/hot_blade_01_S_run_light_attack.png
  sheets/hot_blade_01_S_run_heavy_attack.png
  sheets/hot_blade_01_S_jump.png
  sheets/hot_blade_01_S_jump_attack.png
  sheets/hot_blade_01_S_guard.png
  manifest.json
```

- 可以先交 `character_ref` + `idle` + `walk`，不要一次全做。
- PNG、透明背景、无抗锯齿；命名/帧数见 [request-hot-blade-01.md](../../generation/request-hot-blade-01.md)。
- `manifest.json` 记录工具/模型/prompt/seed/许可/人工修改。
- 放好后告诉 Lead“inbox 有文件”，Lead 做切帧/调色/Unity 导入。
