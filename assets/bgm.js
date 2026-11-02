/* 배경음악: 파일 없이 웹오디오로 즉석 합성하는 잔잔한 앰비언트(저작권 문제 없음). 브라우저 규칙상 첫 터치·스크롤·키 입력 때 시작하고, 사용자가 끄면 기억한다. */
(function () {
  var KEY = 'ruri-bgm', st = 'on';
  try { st = localStorage.getItem(KEY) || 'on'; } catch (e) {}
  var AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
  var ctx = null, master = null, timer = null, playing = false, step = 0;
  var CH = [[57, 60, 64, 67, 71], [53, 57, 60, 64, 67], [48, 55, 60, 64, 67], [55, 59, 62, 66, 69]];   // Am9 · Fmaj7 · Cmaj7 · G6
  var btn = document.createElement('button'); btn.type = 'button'; btn.className = 'bgm-b';
  function label() { btn.setAttribute('aria-pressed', playing ? 'true' : 'false'); btn.innerHTML = playing ? '<i>♪</i> 음악 끄기' : '<i>♪</i> 음악 켜기'; btn.title = '저작권 걱정 없는 합성 배경음'; }
  function hz(m) { return 440 * Math.pow(2, (m - 69) / 12); }
  function build() {
    ctx = new AC(); master = ctx.createGain(); master.gain.value = 0;
    var lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 1400; lp.Q.value = .3;
    var d = ctx.createDelay(1.5); d.delayTime.value = .42; var fb = ctx.createGain(); fb.gain.value = .38; var wet = ctx.createGain(); wet.gain.value = .35;
    lp.connect(master); lp.connect(d); d.connect(fb); fb.connect(d); d.connect(wet); wet.connect(master); master.connect(ctx.destination);
    ctx._in = lp;
  }
  function chord() {
    var t = ctx.currentTime, notes = CH[step % CH.length]; step++;
    notes.forEach(function (m, i) {
      [0, 1].forEach(function (k) {
        var o = ctx.createOscillator(), g = ctx.createGain(); o.type = k ? 'triangle' : 'sine'; o.frequency.value = hz(m) * (k ? 1.004 : 1);
        var v = (k ? .05 : .08) / (1 + i * .25);
        g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + 2.2); g.gain.linearRampToValueAtTime(v * .6, t + 5.5); g.gain.linearRampToValueAtTime(0, t + 8.4);
        o.connect(g); g.connect(ctx._in); o.start(t); o.stop(t + 8.6);
      });
    });
    var mel = notes[(step * 2) % notes.length] + 12;   // 가끔 높은 음 하나
    var o2 = ctx.createOscillator(), g2 = ctx.createGain(); o2.type = 'sine'; o2.frequency.value = hz(mel);
    g2.gain.setValueAtTime(0, t + 3); g2.gain.linearRampToValueAtTime(.05, t + 3.2); g2.gain.exponentialRampToValueAtTime(.0008, t + 6.5);
    o2.connect(g2); g2.connect(ctx._in); o2.start(t + 3); o2.stop(t + 6.6);
  }
  function on() {
    if (!ctx) build(); if (ctx.state === 'suspended') ctx.resume();
    playing = true; master.gain.cancelScheduledValues(ctx.currentTime); master.gain.linearRampToValueAtTime(.55, ctx.currentTime + 2.5);
    chord(); timer = setInterval(chord, 7600); label();
  }
  function off() {
    playing = false; if (timer) clearInterval(timer);
    if (ctx) { master.gain.cancelScheduledValues(ctx.currentTime); master.gain.linearRampToValueAtTime(0, ctx.currentTime + 1.2); }
    label();
  }
  btn.addEventListener('click', function (e) { e.stopPropagation(); if (playing) { off(); try { localStorage.setItem(KEY, 'off'); } catch (x) {} } else { on(); try { localStorage.setItem(KEY, 'on'); } catch (x) {} } });
  function first() {
    ['pointerdown', 'keydown', 'scroll', 'touchstart'].forEach(function (n) { window.removeEventListener(n, gesture, true); });
    if (st !== 'off' && !playing) on();
  }
  function gesture(e) { if (e.target === btn || (btn.contains && btn.contains(e.target))) return; first(); }
  document.addEventListener('DOMContentLoaded', function () { document.body.appendChild(btn); label(); });
  if (document.readyState !== 'loading') { document.body.appendChild(btn); label(); }
  if (st !== 'off') ['pointerdown', 'keydown', 'scroll', 'touchstart'].forEach(function (n) { window.addEventListener(n, gesture, { capture: true, passive: true }); });
  document.addEventListener('visibilitychange', function () { if (!ctx) return; if (document.hidden) ctx.suspend(); else if (playing) ctx.resume(); });
})();
