// TASK-062 manual_test.html 页面自检脚本（可选证据，不是硬件测试）。
//
// 用途：在无浏览器自动化工具时，用 headless Chrome/Edge 验证页面 JS 逻辑
// （DOM 渲染、组合判定、顺序输入判定、报告生成、重置），避免页面脚本报错。
//
// 用法（Windows，Chrome/Edge 路径按本机调整）：
//   1) 在 manual_test.html 的 </body> 前注入本文件内容，另存为 selftest.html；
//   2) chrome.exe --headless=new --disable-gpu --no-sandbox --allow-file-access-from-files
//        --user-data-dir=<临时目录> --dump-dom --virtual-time-budget=5000 file:///<selftest.html>
//   3) 在输出中查找 <pre id="selftest-json">SELFTEST_JSON:{"ok":true,...}。
//
// 注意：该自检使用合成 KeyboardEvent，只证明页面逻辑正确，不能作为键盘硬件证据；
// 硬件证据必须由真人在 manual_test.html 上物理按键产生。
(function () {
  'use strict';
  var failures = [];
  var checks = 0;
  function check(name, cond, detail) {
    checks++;
    if (!cond) failures.push(name + (detail ? ' :: ' + detail : ''));
  }
  function q(id) { return document.getElementById(id); }
  function text(id) { var el = q(id); return el ? el.textContent : ''; }
  function rows(tbodyId) { return document.querySelectorAll('#' + tbodyId + ' tr'); }
  function statusOf(tbodyId, idx) {
    var tr = rows(tbodyId)[idx];
    return tr ? tr.querySelector('td.status').textContent : '';
  }
  function observedOf(tbodyId, idx) {
    var tr = rows(tbodyId)[idx];
    return tr ? tr.cells[4].textContent : '';
  }
  function clickOp(tbodyId, idx) {
    var tr = rows(tbodyId)[idx];
    if (!tr) { failures.push('missing row ' + tbodyId + '[' + idx + ']'); return; }
    tr.cells[tr.cells.length - 1].querySelector('button').click();
  }
  function down(code, key) {
    document.dispatchEvent(new KeyboardEvent('keydown', { code: code, key: key, bubbles: true, cancelable: true }));
  }
  function up(code, key) {
    document.dispatchEvent(new KeyboardEvent('keyup', { code: code, key: key, bubbles: true, cancelable: true }));
  }
  function reset() { q('btnResetAll').click(); }

  function run() {
    reset();

    // 1. 基本渲染
    check('combo rows = 15', rows('comboTbody').length === 15, String(rows('comboTbody').length));
    check('seq rows = 3', rows('seqTbody').length === 3, String(rows('seqTbody').length));
    check('expected table', document.querySelectorAll('#expected table tbody tr').length >= 6);

    // 2. 单键 K01
    clickOp('comboTbody', 0);
    down('KeyZ', 'z');
    check('K01 pass', statusOf('comboTbody', 0) === '通过', statusOf('comboTbody', 0));
    check('K01 observed 1', observedOf('comboTbody', 0) === '1', observedOf('comboTbody', 0));
    up('KeyZ', 'z');

    // 3. 实时计数
    down('KeyZ', 'z'); down('KeyX', 'x'); down('KeyC', 'c');
    check('current count 3', text('currentCount') === '3', text('currentCount'));
    check('session max >= 3', Number(text('sessionMax')) >= 3, text('sessionMax'));
    up('KeyZ', 'z'); up('KeyX', 'x'); up('KeyC', 'c');

    // 4. C+X 防御显示
    reset();
    down('KeyC', 'c'); down('KeyX', 'x');
    check('last combo GUARD', text('lastCombo').indexOf('GUARD') >= 0, text('lastCombo'));
    up('KeyX', 'x'); up('KeyC', 'c');

    // 5. K10 三键组合
    reset();
    clickOp('comboTbody', 9);
    down('KeyZ', 'z'); down('KeyX', 'x'); down('KeyC', 'c');
    check('K10 pass', statusOf('comboTbody', 9) === '通过', statusOf('comboTbody', 9));
    check('K10 observed 3', observedOf('comboTbody', 9) === '3', observedOf('comboTbody', 9));
    up('KeyZ', 'z'); up('KeyX', 'x'); up('KeyC', 'c');

    // 6. K07 C+X 组合
    reset();
    clickOp('comboTbody', 6);
    down('KeyC', 'c'); down('KeyX', 'x');
    check('K07 pass', statusOf('comboTbody', 6) === '通过', statusOf('comboTbody', 6));
    check('K07 observed 2', observedOf('comboTbody', 6) === '2', observedOf('comboTbody', 6));
    up('KeyC', 'c'); up('KeyX', 'x');

    // 7. 方向组合 K12
    reset();
    clickOp('comboTbody', 11);
    down('ArrowUp', 'ArrowUp'); down('KeyZ', 'z'); down('KeyC', 'c');
    check('K12 pass', statusOf('comboTbody', 11) === '通过', statusOf('comboTbody', 11));
    check('K12 observed 3', observedOf('comboTbody', 11) === '3', observedOf('comboTbody', 11));
    up('ArrowUp', 'ArrowUp'); up('KeyZ', 'z'); up('KeyC', 'c');

    // 8. Shift 单键（非修饰键期望 0）
    reset();
    clickOp('comboTbody', 5);
    down('ShiftLeft', 'Shift');
    check('K06 pass', statusOf('comboTbody', 5) === '通过', statusOf('comboTbody', 5));
    check('K06 observed 0', observedOf('comboTbody', 5) === '0', observedOf('comboTbody', 5));
    check('shift not counted', text('currentCount') === '0', text('currentCount'));
    up('ShiftLeft', 'Shift');

    // 9. 不通过路径：K14 只按 3/4 键后结束
    reset();
    clickOp('comboTbody', 13);
    down('ArrowUp', 'ArrowUp'); down('KeyZ', 'z'); down('KeyX', 'x');
    clickOp('comboTbody', 13);
    check('K14 fail on stop', statusOf('comboTbody', 13) === '不通过', statusOf('comboTbody', 13));
    check('K14 observed 3', observedOf('comboTbody', 13) === '3', observedOf('comboTbody', 13));
    up('ArrowUp', 'ArrowUp'); up('KeyZ', 'z'); up('KeyX', 'x');

    // 10. 顺序输入 S1
    reset();
    clickOp('seqTbody', 0);
    down('KeyZ', 'z'); up('KeyZ', 'z');
    down('KeyX', 'x'); up('KeyX', 'x');
    down('KeyC', 'c');
    check('S1 pass', statusOf('seqTbody', 0) === '通过', statusOf('seqTbody', 0));
    check('S1 span recorded', rows('seqTbody')[0].cells[3].textContent !== '—', rows('seqTbody')[0].cells[3].textContent);
    up('KeyC', 'c');

    // 11. 顺序输入 S2
    reset();
    clickOp('seqTbody', 1);
    down('KeyZ', 'z'); up('KeyZ', 'z');
    down('ArrowUp', 'ArrowUp');
    down('KeyC', 'c');
    check('S2 pass', statusOf('seqTbody', 1) === '通过', statusOf('seqTbody', 1));
    up('ArrowUp', 'ArrowUp'); up('KeyC', 'c');

    // 12. 报告
    reset();
    clickOp('comboTbody', 0);
    down('KeyZ', 'z');
    up('KeyZ', 'z');
    q('btnBuildReport').click();
    var report = q('reportArea').value;
    check('report built', report.indexOf('TASK-062') >= 0 && report.indexOf('K01') >= 0, report.slice(0, 80));
    check('report has UA', report.indexOf('浏览器:') >= 0);

    // 13. 布局切换（现代）
    q('toggleLayout').click();
    down('KeyZ', 'z');
    check('modern Z = LIGHT', text('lastCombo').indexOf('LIGHT_ATTACK') >= 0, text('lastCombo'));
    up('KeyZ', 'z');
    q('toggleLayout').click();

    // 14. 重置全部
    reset();
    check('reset session max', text('sessionMax') === '0', text('sessionMax'));
    check('reset status', statusOf('comboTbody', 0) === '未测试', statusOf('comboTbody', 0));
    check('reset last combo', text('lastCombo') === '—', text('lastCombo'));
  }

  function finish() {
    var out = { ok: failures.length === 0, checks: checks, failures: failures };
    var pre = document.createElement('pre');
    pre.id = 'selftest-json';
    pre.textContent = 'SELFTEST_JSON:' + JSON.stringify(out);
    document.body.appendChild(pre);
    document.title = out.ok ? 'SELFTEST_OK' : 'SELFTEST_FAIL';
  }

  document.addEventListener('DOMContentLoaded', function () {
    try {
      run();
    } catch (err) {
      failures.push('EXCEPTION: ' + (err && err.stack ? err.stack : String(err)));
    }
    finish();
  });
})();


