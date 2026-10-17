# TASK-066 Handoff — 3 款键盘人工 QA（B6）

```text
TASK: TASK-066
STATUS: blocked-human
CHANGED:
  validation/input/hardware-qa/README.md          # protocol
  validation/input/hardware-qa/REPORT-TEMPLATE.md # fill-in report
  validation/input/hardware-qa/check-kit.ps1      # completeness check
  validation/input/hardware-qa/HANDOFF.md         # this file
DECISIONS:
  - B6 remains human-only; AI cannot physically press keys.
  - Use validation/input/manual_test.html (28/28 page-logic self-check already independently verified).
  - 3 categories: NKRO, 6KRO, membrane/2KRO; K01–K15 + S1–S3 ×100 each.
  - NKRO/6KRO supported-combo target ≥99%; 2KRO failures must map to Space/sequential/remap.
EVIDENCE:
  - validation/input/manual_test.html exists; reviewer independently reran 28/28 page logic.
  - No physical keyboard data yet; no report-*.txt files.
RISKS:
  - 2KRO/6KRO behaviour is hardware/firmware-specific; counting model is only a lower bound.
  - OS/IME/remote desktop/VM can swallow keys; protocol closes these.
NEXT:
  1. Human runs 3 keyboards per README, exports 3 .txt reports.
  2. Fill REPORT-TEMPLATE.md, run check-kit.ps1.
  3. Add conclusion to docs/07 TASK-066; close B6.
```
