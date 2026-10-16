// 루리 챗봇 — 브라우저 안에서만 동작 (검색 RAG + WebLLM 초경량 sLLM + 음성 STS)
// 기준 문서: _gongmo/chatbot_manual.md
const MODEL = 'Qwen2.5-0.5B-Instruct-q4f16_1-MLC';
const WEBLLM = 'https://cdn.jsdelivr.net/npm/@mlc-ai/web-llm@0.2.79/+esm';
const MANUAL = `너는 공모전 정보 사이트 「루리의 줍줍」의 안내 캐릭터 "루리"다.
규칙:
- 밝고 단정한 존댓말(~해요), 3~5문장으로 짧게.
- 반드시 아래 [찾은 공모전] 목록에 있는 것만 말한다. 목록에 없는 공모전·날짜·상금을 지어내지 않는다.
- 목록이 비었으면 "지금 목록에는 없어요"라고 하고 다른 검색어를 제안한다.
- 각 공모전은 이름, 마감일, 상금을 말하고, 자세한 요강은 공식 공고에서 확인하라고 안내한다.
- 원고 대리 작성, 당선 예측, 개인정보 요청, 공모전과 무관한 상담은 정중히 거절한다.`;
const FAQ = [
  [/세금|제세|원천징수/, '상금은 보통 제세공과금을 떼고 지급돼요. 자세한 건 응모 가이드의 「상금 수령」 글을 봐 주세요. <a href="/guide/prize/">가이드 보기</a>'],
  [/(AI|에이아이|인공지능).*(써도|사용|만들어도|괜찮)/, '공모전마다 달라요. 생성형 AI를 금지하거나 사용 표기를 요구하는 곳이 있으니 요강을 꼭 확인해 주세요.'],
  [/돈.*(보내|입금)|수수료.*(내라|요구)|당첨.*(입금|송금)/, '사기일 가능성이 높아요! 정상적인 공모전은 먼저 돈을 요구하지 않아요. 주최 기관 공식 연락처로 꼭 확인하세요.'],
  [/틀렸|오류|잘못된 정보|등록해|삭제해|제휴|광고|협찬/, '알려 주셔서 고마워요! 사이트 맨 아래 문의 메일로 공모전 이름과 함께 보내 주시면 확인할게요.'],
  [/^(안녕|하이|hi|hello)/i, '안녕하세요, 루리예요! "이번 주 마감 슬로건 공모전"처럼 물어보시면 찾아 드릴게요.'],
  [/(경품|이벤트|퀴즈|설문|댓글)/, null], // 아래에서 /event/ 안내 덧붙임
  [/(쓰는 법|작성법|요령|팁|처음 응모|어떻게 응모)/, '응모 요령은 가이드에 정리해 뒀어요. <a href="/guide/first/">처음 응모할 때 확인할 7가지</a>, <a href="/guide/proposal/">제안서 쓰는 법</a>, <a href="/guide/writing/">수기·문학 공모 요령</a>'],
];
const CAT = { '문학': /문학|시\b|소설|수필|수기|에세이|슬로건|네이밍|표어|글/, '아이디어·정책': /아이디어|정책|제안|기획|창업|마케팅/,
  '디자인': /디자인|캐릭터|포스터|일러스트|웹툰|그림|로고/, '영상': /영상|숏폼|쇼츠|UCC|사진|릴스|촬영/, '논문': /논문|리포트|학술/,
  'IT·과학': /IT|개발|해커톤|코딩|AI|데이터|과학|SW|소프트웨어/, '해외': /해외|국제|글로벌|일본|영어/ };
const STOP = /(공모전|공모|대회|경진대회|콘테스트|있어|있나|있나요|있는|없는|알려|줘|주세요|찾아|추천|좀|뭐|어떤|어떻게|요|이번|주|마감|임박|오늘|상금|큰|많은|만원|이상|혹시|지금|요즘|진행|중인|중에|관련|대한|관한|관해|대해|같은|하는|할만한|참여|응모|목록|리스트|보여|전부|모두|\d+)/g;
const GENERIC = /^(문학|글|글쓰기|아이디어|정책|디자인|영상|논문|IT|과학|해외|국제|글로벌|기타|분야)$/i;
const JOSA = /(으로|에서|에게|까지|부터|이랑|은|는|이|가|을|를|에|의|도|로|과|와|만)$/;

let items = null, engine = null, loading = false, speak = false, rec = null, searchOnly = false;
let setReady = () => {};
const $ = (s, r = document) => r.querySelector(s);
const el = (t, c, h) => { const e = document.createElement(t); if (c) e.className = c; if (h != null) e.innerHTML = h; return e; };
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const today = (() => { const n = new Date(); return Math.round(Date.UTC(n.getFullYear(), n.getMonth(), n.getDate()) / 864e5); })();
const dn = s => { const p = s.split('-'); return Math.round(Date.UTC(+p[0], p[1] - 1, +p[2]) / 864e5); };

async function load() {
  if (items) return items;
  const d = await (await fetch('/data.json', { cache: 'no-cache' })).json();
  items = d.items.map(i => ({ ...i, left: dn(i.end) - today, hay: (i.title + ' ' + i.org + ' ' + i.field + ' ' + i.tags.join(' ')).toLowerCase() })).filter(i => i.left >= 0);
  return items;
}

// ---- 검색(RAG): 기간·분야·상금·키워드 ----
function search(q) {
  let r = items.slice(), why = [];
  if (/오늘/.test(q)) { r = r.filter(i => i.left === 0); why.push('오늘 마감'); }
  else if (/이번\s*주|임박|곧/.test(q)) { r = r.filter(i => i.left <= 7); why.push('7일 안 마감'); }
  else if (/이번\s*달|한\s*달/.test(q)) { r = r.filter(i => i.left <= 31); why.push('한 달 안 마감'); }
  const mon = q.match(/(\d{1,2})\s*월/); if (mon) { r = r.filter(i => +i.end.slice(5, 7) === +mon[1]); why.push(mon[1] + '월 마감'); }
  const cats = Object.keys(CAT).filter(c => CAT[c].test(q));
  if (cats.length) { r = r.filter(i => cats.some(c => i.tags.includes(c))); why.push(cats.join('·')); }
  const man = q.match(/(\d+)\s*만\s*원?\s*이상/); if (man) { r = r.filter(i => i.pv >= +man[1] * 1e4); why.push(man[1] + '만원 이상'); }
  const words = q.replace(STOP, ' ').split(/[\s,.?!]+/).map(w => w.replace(JOSA, '')).filter(w => w.length >= 2 && !GENERIC.test(w));
  if (words.length) {
    const sc = r.map(i => [i, words.every(w => i.hay.includes(w.toLowerCase())) ? words.reduce((s, w) => s + (i.title.includes(w) ? 3 : 1), 0) : 0]);
    const hit = sc.filter(x => x[1] > 0);
    r = hit.sort((a, b) => b[1] - a[1] || a[0].left - b[0].left).map(x => x[0]); why.push('「' + words.join(' ') + '」');  // 안 맞으면 0건
  }
  if (!why.length && !/상금|큰|많은|고액/.test(q)) return { list: [], total: 0, why, vague: true };
  if (/상금|큰|많은|고액/.test(q)) { r.sort((a, b) => b.pv - a.pv || a.left - b.left); why.push('상금 큰 순'); }
  else if (!words.length) r.sort((a, b) => a.left - b.left || b.pv - a.pv);
  return { list: r.slice(0, 5), total: r.length, why };
}

function cards(list) {
  return '<div class="rc-list">' + list.map(i =>
    `<a class="rc-card" href="/c/${i.id}/"><b>${esc(i.title)}</b><span>${i.left ? 'D-' + i.left : 'D-DAY'} · ${i.end.replace(/-/g, '.')} 마감${i.pv ? ' · ' + esc(i.prize) : ''}</span></a>`).join('') + '</div>';
}

// ---- 답변 ----
async function answer(q) {
  await load();
  for (const [re, txt] of FAQ) if (re.test(q) && txt) return { html: txt, say: txt.replace(/<[^>]+>/g, '') };
  const { list, total, why, vague } = search(q);
  const ev = /(경품|이벤트|퀴즈|설문|댓글)/.test(q) ? ' 경품 이벤트는 <a href="/event/">경품 이벤트 모음</a>에 따로 있어요.' : '';
  if (!list.length) {
    const t = (vague ? '어떤 공모전을 찾으시는지 조금만 더 알려 주세요.' : '지금 목록에는 맞는 공모전이 없어요.') + ' "이번 주 마감", "영상 공모전", "상금 큰 공모전"처럼 바꿔서 물어봐 주세요.' + ev;
    return { html: t, say: t.replace(/<[^>]+>/g, '') };
  }
  const head = `${why.length ? why.join(', ') + ' 조건으로 ' : ''}${total}건을 찾았어요. ${/상금|큰|많은|고액/.test(q) ? '상금이 큰' : '마감이 가까운'} 것부터 보여 드릴게요.`;
  if (!engine) return { html: esc(head) + ev + cards(list), say: head + ' ' + list.slice(0, 3).map(i => i.title).join(', ') };
  const ctx = list.map((i, n) => `${n + 1}. ${i.title} / 주최 ${i.org} / 마감 ${i.end} / 상금 ${i.prize} / 분야 ${i.tags.join(',')}`).join('\n');
  const box = el('p', 'rc-gen', '');
  return { stream: async (bubble) => {
    bubble.appendChild(box);
    let out = '';
    const chunks = await engine.chat.completions.create({ stream: true, temperature: 0.3, max_tokens: 220, messages: [
      { role: 'system', content: MANUAL }, { role: 'user', content: `[찾은 공모전]\n${ctx}\n\n[질문] ${q}` }] });
    for await (const c of chunks) { out += c.choices[0]?.delta?.content || ''; box.textContent = out; scroll(); }
    bubble.insertAdjacentHTML('beforeend', ev + cards(list));
    return out;
  } };
}

// ---- sLLM (WebLLM, WebGPU) ----
async function enableAI(btn, note) {
  if (engine || loading) return;
  if (!navigator.gpu) { note.textContent = '이 기기는 AI 를 돌릴 수 없어요 · 간단 검색 모드를 써 주세요'; setReady(false, 'nogpu'); return; }
  loading = true; btn.disabled = true;
  try {
    const webllm = await import(WEBLLM);
    engine = await webllm.CreateMLCEngine(MODEL, { initProgressCallback: p => { note.textContent = 'AI 준비 중 ' + Math.round((p.progress || 0) * 100) + '% (처음 한 번 약 300MB)'; } });
    note.textContent = 'AI 켜짐 · 브라우저 안에서만 실행돼요'; btn.textContent = 'AI 켜짐'; btn.classList.add('on'); setReady(true);
  } catch (e) { note.textContent = 'AI 를 켜지 못했어요'; btn.disabled = false; setReady(false, 'fail'); console.warn(e); }
  loading = false;
}

// ---- 음성(STS): 마이크(WebRTC) → 인식 → 답변 → 합성 ----
function talk(t) {
  if (!speak || !window.speechSynthesis) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(t.slice(0, 300)); u.lang = 'ko-KR'; u.rate = 1.05; u.pitch = 1.15;
  const v = speechSynthesis.getVoices().find(v => /ko/i.test(v.lang) && /female|SunHi|Heami|Yuna|여/i.test(v.name)) || speechSynthesis.getVoices().find(v => /ko/i.test(v.lang));
  if (v) u.voice = v; speechSynthesis.speak(u);
}
async function listen(btn, input, send) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { alertBot('이 브라우저는 음성 인식을 지원하지 않아요. 크롬이나 엣지에서 써 주세요.'); return; }
  if (rec) { rec.stop(); return; }
  try { const s = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } }); s.getTracks().forEach(t => t.stop()); }
  catch { alertBot('마이크 권한이 필요해요.'); return; }
  speak = true; $('#rc-spk').classList.add('on');
  rec = new SR(); rec.lang = 'ko-KR'; rec.interimResults = true;
  btn.classList.add('rec');
  rec.onresult = e => { input.value = [...e.results].map(r => r[0].transcript).join(''); if (e.results[e.results.length - 1].isFinal) send(); };
  rec.onend = () => { btn.classList.remove('rec'); rec = null; };
  rec.start();
}

// ---- UI ----
let log, alertBot, scroll;
function ui() {
  const root = el('div', 'rc');
  root.innerHTML = `<button class="rc-fab" aria-label="루리에게 물어보기"><img src="/assets/ruri/avatar.webp" alt=""><span>루리에게 물어보기</span></button>
<section class="rc-panel" hidden aria-label="루리 챗봇"><header><img src="/assets/ruri/avatar.webp" alt=""><div><b>루리</b><small id="rc-note">진행 중 공모전에서 찾아 드려요</small></div>
<button class="rc-ai" title="브라우저 안에서 초경량 AI(약 300MB)를 켭니다">AI 켜기</button><button id="rc-spk" class="rc-ic" title="답변 읽어 주기">🔈</button><button class="rc-x rc-ic" aria-label="닫기">✕</button></header>
<div class="rc-log" role="log" aria-live="polite"></div>
<div class="rc-chips"><button>이번 주 마감</button><button>상금 큰 공모전</button><button>영상 숏폼 공모전</button><button>슬로건 공모전</button><button>해외 공모전</button></div>
<form class="rc-in"><button type="button" class="rc-mic rc-ic" title="말로 물어보기">🎤</button><input placeholder="예) 이번 주 마감 슬로건 공모전" aria-label="질문"><button class="rc-go">보내기</button></form></section>`;
  document.body.appendChild(root);
  const panel = $('.rc-panel', root), input = $('input', root), note = $('#rc-note', root);
  log = $('.rc-log', root); scroll = () => { log.scrollTop = log.scrollHeight; };
  const add = (who, html) => { const b = el('div', 'rc-m ' + who, html); log.appendChild(b); scroll(); return b; };
  alertBot = t => add('bot', esc(t));
  const ctrls = () => [input, $('.rc-go', root), $('.rc-mic', root), ...root.querySelectorAll('.rc-chips button')];
  let gate = null;
  setReady = (on, why) => {
    const ok = on || searchOnly;
    ctrls().forEach(c => c.disabled = !ok);
    input.placeholder = ok ? '예) 이번 주 마감 슬로건 공모전' : '먼저 위의 「AI 켜기」를 눌러 주세요';
    if (gate) { gate.remove(); gate = null; }
    if (ok) { if (!log.querySelector('.rc-hello')) add('bot rc-hello', searchOnly && !engine ? '간단 검색 모드예요. "이번 주 마감", "영상 공모전"처럼 물어봐 주세요.' : '준비됐어요! 어떤 공모전을 찾으세요? 말로 물어보려면 🎤 를 눌러 주세요.'); input.focus(); return; }
    gate = add('bot rc-gate', '안녕하세요, 루리예요!<br>AI 를 켜면 대화할 수 있어요. 브라우저 안에서만 돌아가고, 처음 한 번 약 300MB 를 받아요.'
      + '<div class="rc-gbtn"><button class="rc-on">AI 켜기</button>' + (why ? '<button class="rc-lite">간단 검색 모드로 쓰기</button>' : '') + '</div>'
      + (why === 'nogpu' ? '<small>이 기기는 AI 를 지원하지 않아요(PC 크롬·엣지 권장). 간단 검색 모드는 바로 쓸 수 있어요.</small>' : why === 'fail' ? '<small>AI 를 켜지 못했어요. 다시 시도하거나 간단 검색 모드를 써 주세요.</small>' : ''));
    gate.querySelector('.rc-on').onclick = () => enableAI($('.rc-ai', root), note);
    const lite = gate.querySelector('.rc-lite'); if (lite) lite.onclick = () => { searchOnly = true; note.textContent = '간단 검색 모드'; setReady(false); };
  };
  const send = async () => {
    const q = input.value.trim(); if (!q || (!engine && !searchOnly)) return; input.value = '';
    add('me', esc(q)); const b = add('bot', '<i class="rc-dot">찾는 중…</i>');
    try {
      const a = await answer(q); b.innerHTML = '';
      if (a.stream) { const t = await a.stream(b); talk(t); } else { b.innerHTML = a.html; talk(a.say); }
    } catch (e) { b.textContent = '앗, 잠시 문제가 생겼어요. 다시 물어봐 주세요.'; console.warn(e); }
    scroll();
  };
  $('.rc-fab', root).onclick = () => { panel.hidden = !panel.hidden; if (!panel.hidden) { if (!log.children.length) setReady(!!engine, navigator.gpu ? '' : 'nogpu'); load(); } };
  $('.rc-x', root).onclick = () => { panel.hidden = true; if (window.speechSynthesis) speechSynthesis.cancel(); };
  $('form', root).onsubmit = e => { e.preventDefault(); send(); };
  root.querySelectorAll('.rc-chips button').forEach(c => c.onclick = () => { input.value = c.textContent; send(); });
  $('.rc-ai', root).onclick = e => enableAI(e.currentTarget, note);
  $('#rc-spk', root).onclick = e => { speak = !speak; e.currentTarget.classList.toggle('on', speak); if (!speak && window.speechSynthesis) speechSynthesis.cancel(); };
  $('.rc-mic', root).onclick = e => listen(e.currentTarget, input, send);
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ui); else ui();
