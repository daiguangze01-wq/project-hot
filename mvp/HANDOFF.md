# TASK-070 Handoff — Web 2.5D 键盘竞技场 MVP

```text
TASK: TASK-070
STATUS: done (REV-071 follow-up: 0 blocker / 0 major / 4 minor)

CHANGED:
  mvp/sim.js                      # authoritative 30Hz sim, 2 cores, jump, guard/perfect, respawn
  mvp/server.js                   # HTTP + SSE, session token, shape validation, fixed-step tick
  mvp/public/index.html           # HUD/canvas shell
  mvp/public/style.css            # pixel-ish HUD
  mvp/public/game.js              # isometric renderer, keyboard composer, SSE client
  mvp/test/sim.test.js            # 9 sim tests
  mvp/test/server.test.js         # 6 server/protocol tests
  mvp/scripts/screenshot.js       # CDP screenshot helper
  mvp/screenshots/mvp-demo.png    # 1280x720 demo screenshot
  mvp/README.md                   # run/controls/limits
  mvp/review/REVIEW.md            # independent REV-071 (pre-fix)
  mvp/review/REVIEW-FOLLOWUP.md   # independent re-check: 0B/0M/4 minors

DECISIONS:
  - MVP transport is HTTP POST /input + SSE /events (zero deps), not Fusion; production stays Fusion 2.
  - Each SSE session gets a random token; /input is bound to that token/player (B-2 fix).
  - Combat is authoritative in mvp/sim.js: clients send held+actions only.
  - Two battle cores (剑豪/拳师) demonstrate minimal equipment=moveset; armor/runes/cosmetics out of MVP.
  - V jump implemented; C+X/Space guard; Z+X+C ultimate; 70ms client combo buffer.
  - 30Hz fixed-step accumulator from process.hrtime (M-1 fix); measured 30.33Hz over 3s.
  - Default bind 127.0.0.1; no auth/rate-limit/anti-cheat -> not for exposure.

EVIDENCE:
  - node --test test/*.test.js: 15/15 pass (sim + server; includes malformed input, token, jump, own-property, seq, two clients, cores).
  - /health tick delta 91/3s = 30.33Hz after restart; independent follow-up measured 29.97Hz and 5.12 u/s.
  - Screenshot: mvp/screenshots/mvp-demo.png (demo mode; dummy 4802 = 198 damage, MP 50, ULT 24, HUD self-consistent).
  - Independent REV-071: playable on localhost, real 2-player PvP verified; blockers/majors then fixed.
  - Independent follow-up: B-1/B-2 + M-1–M-5 all closed; 15/15×5 no flake; 31 malformed + 120 fuzz no crash; token spoof 403; V jump z peak 0.70; constructor actions no-op.
  - Follow-up minors F-1 core prototype key, F-2 emoji truncation, F-3 demo skill1 whiff, F-4 jump/z observation: F-1/F-2/F-3 fixed; F-4 documented in README.

RISKS:
  - Not M0 engine validation; Web Canvas is visual/transport approximation.
  - No prediction/rollback; 33ms input + 30Hz snapshots; remote latency not representative.
  - Equipment=moveset only 2 cores; no armor/runes/cosmetics/data-driven assets.
  - No account/rooms/matchmaking/persistence/anti-cheat/rate limit; localhost only.
  - Single active-frame hit, no hitstun/knockup/Z hitboxes; prototype-level combat.
  - Reviewer follow-up must confirm fixes; if new blocker appears, reopen TASK-070.

NEXT:
  - TASK-071 follow-up: verify B-1/B-2/M-1–M-5 fixes; if pass, mark TASK-070/071 done.
  - User playtest: open two tabs, test read/guard/ultimate feel; collect notes.
  - M0 Unity/Fusion: URP camera, Fusion guard matrix, 3-keyboard QA, data-driven moveset.
```
