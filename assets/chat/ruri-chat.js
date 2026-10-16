// 루리의 줍줍 — 시나리오형 추천 챗봇 (브라우저 안에서만 동작, 모델 없음): 시작 메뉴·후속 버튼·찜/마감 알림·캘린더·상세 페이지 맞춤
// 데이터: /data.json(진행 중 대회), /events.json(경품 이벤트). 기준 문서: _gongmo/chatbot_manual.md
const FAQ = [
  [/세금|제세|원천징수/, '상금은 보통 제세공과금을 떼고 지급돼요. 자세한 건 <a href="/guide/prize/">상금 수령 가이드</a>를 봐 주세요.'],
  [/(AI|에이아이|인공지능).*(써도|사용|만들어도|괜찮)/, '대회마다 달라요. 생성형 AI 를 금지하거나 표기를 요구하는 곳이 있으니 요강을 꼭 확인해 주세요.'],
  [/돈.*(보내|입금)|수수료.*(내라|요구)|당첨.*(입금|송금)/, '사기일 가능성이 높아요! 정상적인 대회·이벤트는 먼저 돈을 요구하지 않아요. 주최 기관 공식 연락처로 확인하세요.'],
  [/틀렸|오류|잘못된 정보|등록해|삭제해|제휴|광고|협찬/, '알려 주셔서 고마워요! 사이트 맨 아래 문의 메일로 보내 주시면 확인할게요.'],
  [/(쓰는 법|작성법|요령|팁|처음 응모|어떻게 응모)/, '응모 요령은 가이드에 있어요. <a href="/guide/first/">처음 응모할 때 확인할 7가지</a> · <a href="/guide/proposal/">제안서 쓰는 법</a> · <a href="/guide/writing/">글 공모 요령</a>'],
  [/청약|임대|공모주|지원금/, '청약·신청 일정은 <a href="/apply/">청약·신청</a> 페이지에 모아 두고 있어요.'],
  [/중복|여러\s*개|동시에|두\s*군데/, '한 작품을 여러 공모전에 같이 내는 건 대부분 금지예요(이중 응모·기수상작 제외 규정). 서로 다른 작품이면 여러 곳에 내도 괜찮아요. 요강의 「유의사항」을 꼭 보세요.'],
  [/저작권|권리|소유권|가져가/, '당선작 저작권이 주최 측으로 넘어가는지(양도), 이용만 허락하는지(이용허락) 대회마다 달라요. 요강의 「저작권」 항목을 응모 전에 확인하세요.'],
  [/당선.*(후|되면|다음)|발표.*(언제|어디)|시상/, '당선되면 보통 ① 개별 연락(문자·메일) ② 원본·서류 제출 ③ 제세공과금 공제 후 상금 지급 순서예요. 발표일과 방법은 공고에 적혀 있어요.'],
  [/사기|피싱|가짜|의심/, '정상 공모전은 참가비·보증금·수수료를 먼저 받지 않아요. 당첨 연락이 와도 주최 기관 공식 홈페이지·대표번호로 다시 확인하세요.'],
];
const FAQ_CHIPS = [['상금 세금', '상금 세금은?'], ['AI 써도 돼요?', 'AI로 만들어도 돼요?'], ['사기 구별', '사기 구별하는 법'], ['중복 응모', '중복 응모 돼요?'], ['저작권', '저작권은 누구 거예요?'], ['당선 후 절차', '당선되면 다음은?']];
// 신분 → 자격 문구
const WHO = { '누구나': null, '대학생': /대학|대학생|대학원|청년/, '청소년': /청소년|중학|고등|초등|학생/, '직장인·일반': /일반|성인|국민|누구나|제한\s*없/ };
const FAV = 'jupjup_fav_v1';
const fav = { get() { try { return JSON.parse(localStorage.getItem(FAV)) || []; } catch { return []; } }, set(v) { try { localStorage.setItem(FAV, JSON.stringify(v)); } catch {} },
  has(id) { return fav.get().some(x => x.id === id); }, toggle(i) { const l = fav.get(), k = l.findIndex(x => x.id === i.id); if (k >= 0) l.splice(k, 1); else l.push({ id: i.id, title: i.title, end: i.end }); fav.set(l); return k < 0; } };
function ics(i) {  // 마감일 캘린더 파일 (마감 하루 전 오전 9시 알림)
  const d = i.end.replace(/-/g, ''), url = location.origin + '/c/' + i.id + '/';
  const body = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//jupjup//ruri//KO', 'BEGIN:VEVENT', 'UID:' + i.id + '@sungprofile.cloud', 'DTSTAMP:' + new Date().toISOString().replace(/[-:]/g, '').slice(0, 15) + 'Z',
    'DTSTART;VALUE=DATE:' + d, 'SUMMARY:[마감] ' + i.title.replace(/[,;]/g, ' '), 'DESCRIPTION:' + url, 'URL:' + url,
    'BEGIN:VALARM', 'TRIGGER:-PT15H', 'ACTION:DISPLAY', 'DESCRIPTION:내일 마감 — ' + i.title.replace(/[,;]/g, ' '), 'END:VALARM', 'END:VEVENT', 'END:VCALENDAR'].join('\r\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([body], { type: 'text/calendar' })); a.download = i.id + '_마감.ics'; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 4000);
}
// 관심 분야 → 데이터 태그·키워드
const INTEREST = {
  '슬로건·글': { tags: ['문학'], re: /슬로건|네이밍|표어|문구|수기|시|수필|에세이|글/ },
  '아이디어': { tags: ['아이디어·정책'], re: /아이디어|정책|제안|기획/ },
  '디자인·그림': { tags: ['디자인'], re: /디자인|캐릭터|포스터|일러스트|웹툰|그림/ },
  '영상·사진': { tags: ['영상'], re: /영상|숏폼|사진|UCC|릴스/ },
  'IT·AI': { tags: ['IT·과학'], re: /AI|해커톤|개발|데이터|SW/ },
  '해외': { tags: ['해외'], re: /해외|국제|글로벌/ },
  '경품 이벤트': { ev: true },
};
const STYLE = { '쉬운 것': 'easy', '상금 큰 것': 'prize', '마감 임박': 'soon' };
const EASY_RE = /슬로건|네이밍|명칭|표어|문구|한\s*줄|삼행시|디카시|사진|아이디어/;
const EZ_RANK = { '댓글 1줄': 0, '폼 1분': 0, '응모만': 0, '설문 5분': 1, '퀴즈 풀기': 1, '댓글+폼': 1 };
const STOP = /(공모전|공모|대회|경진대회|콘테스트|있어|있나|있나요|있는|없는|알려|줘|주세요|찾아|추천|좀|뭐|어떤|어떻게|요|이번|주|마감|임박|오늘|상금|큰|많은|만원|이상|혹시|지금|요즘|진행|중인|중에|관련|대한|관한|관해|대해|같은|하는|할만한|참여|응모|목록|리스트|보여|전부|모두|\d+)/g;
const JOSA = /(으로|에서|에게|까지|부터|이랑|은|는|이|가|을|를|에|의|도|로|과|와|만)$/;
const PKEY = 'jupjup_pref_v1';

let items = null, events = null, speak = false, rec = null;
const $ = (s, r = document) => r.querySelector(s);
const el = (t, c, h) => { const e = document.createElement(t); if (c) e.className = c; if (h != null) e.innerHTML = h; return e; };
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const today = (() => { const n = new Date(); return Math.round(Date.UTC(n.getFullYear(), n.getMonth(), n.getDate()) / 864e5); })();
const dn = s => { const p = s.split('-'); return Math.round(Date.UTC(+p[0], p[1] - 1, +p[2]) / 864e5); };
const ga = (n, p) => { try { window.gtag && gtag('event', n, p || {}); } catch {} };  // GA4 맞춤 이벤트
const pref = { get() { try { return JSON.parse(localStorage.getItem(PKEY)) || null; } catch { return null; } },
               set(v) { try { localStorage.setItem(PKEY, JSON.stringify(v)); } catch {} } };

async function load() {
  if (items) return;
  const [d, ev] = await Promise.all([fetch('/data.json', { cache: 'no-cache' }).then(r => r.json()), fetch('/events.json', { cache: 'no-cache' }).then(r => r.json()).catch(() => [])]);
  items = d.items.map(i => ({ ...i, left: dn(i.end) - today, hay: (i.title + ' ' + i.org + ' ' + i.field + ' ' + i.tags.join(' ')).toLowerCase() })).filter(i => i.left >= 0);
  events = ev.map(e => ({ ...e, left: dn(e.end) - today })).filter(e => e.left >= 0);
}

// ---- 추천: 관심 분야·스타일·지역으로 점수 ----
function recommend(p) {
  const ints = p.ints.map(k => INTEREST[k]).filter(Boolean);
  const wantEv = ints.some(x => x.ev), cats = ints.filter(x => !x.ev);
  const region = (p.region || '').trim();
  const out = [];
  if (cats.length || !wantEv) {
    for (const i of items) {
      if (cats.length && !cats.some(x => x.tags.some(t => i.tags.includes(t)) || x.re.test(i.title))) continue;
      const txt = i.title + i.org + (i.elig || '');
      let s = cats.length ? 3 : 0;
      if (p.style === 'easy' && EASY_RE.test(i.title + ' ' + i.field)) s += 3;
      if (p.style === 'prize') s += Math.min(4, i.pv ? Math.log10(i.pv) - 4 : 0);
      if (p.style === 'soon') s += i.left <= 3 ? 3 : i.left <= 7 ? 2 : i.left <= 14 ? 1 : 0;
      if (region && txt.includes(region)) s += 4;
      else if (/(시민|도민|거주|재학|재직|관내)/.test(i.elig || '')) s -= 2;  // 내 지역 아닌 지역 한정은 뒤로
      s += i.pv ? 0.5 : 0;
      s -= i.left > 60 ? 1 : 0;
      out.push({ k: 'c', i, s });
    }
  }
  if (wantEv) for (const e of events) {
    let s = 2 + (EZ_RANK[e.ez] != null ? 2 - EZ_RANK[e.ez] : 0) + (e.left <= 3 ? 1 : 0);
    if (region && (e.title + e.org).includes(region)) s += 2;
    out.push({ k: 'e', i: e, s });
  }
  out.sort((a, b) => b.s - a.s || a.i.left - b.i.left);
  if (wantEv && cats.length) {  // 경품도 골랐으면 대회 4 + 경품 2 로 섞기
    const c = out.filter(x => x.k === 'c').slice(0, 4), e = out.filter(x => x.k === 'e').slice(0, 2);
    return [...c, ...e];
  }
  return out.slice(0, 6);
}

// ---- 자유 질문 검색 ----
const CAT = { '문학': /문학|시\b|소설|수필|수기|에세이|글짓기/, '아이디어·정책': /아이디어|정책|제안|기획|창업|마케팅/,
  '디자인': /디자인|캐릭터|포스터|일러스트|웹툰|그림|로고/, '영상': /영상|숏폼|쇼츠|UCC|사진|릴스|촬영/, '논문': /논문|리포트|학술/,
  'IT·과학': /IT|개발|해커톤|코딩|AI|데이터|과학|SW|소프트웨어/, '해외': /해외|국제|글로벌|일본|영어/ };
const GENERIC = /^(문학|글|글쓰기|아이디어|정책|디자인|영상|논문|IT|과학|해외|국제|글로벌|기타|분야)$/i;
function search(q) {
  let r = items.slice();
  const why = [];
  if (/오늘/.test(q)) { r = r.filter(i => i.left === 0); why.push('오늘 마감'); }
  else if (/이번\s*주|임박|곧/.test(q)) { r = r.filter(i => i.left <= 7); why.push('7일 안 마감'); }
  else if (/이번\s*달|한\s*달/.test(q)) { r = r.filter(i => i.left <= 31); why.push('한 달 안 마감'); }
  const mon = q.match(/(\d{1,2})\s*월/); if (mon) { r = r.filter(i => +i.end.slice(5, 7) === +mon[1]); why.push(mon[1] + '월 마감'); }
  const cats = Object.keys(CAT).filter(c => CAT[c].test(q));
  if (cats.length) { r = r.filter(i => cats.some(c => i.tags.includes(c))); why.push(cats.join('·')); }
  const man = q.match(/(\d+)\s*만\s*원?\s*이상/); if (man) { r = r.filter(i => i.pv >= +man[1] * 1e4); why.push(man[1] + '만원 이상'); }
  const words = q.replace(STOP, ' ').split(/[\s,.?!]+/).map(w => w.replace(JOSA, '')).filter(w => w.length >= 2 && !GENERIC.test(w));
  if (words.length) { r = r.filter(i => words.every(w => i.hay.includes(w.toLowerCase()))); why.push('「' + words.join(' ') + '」'); }
  const big = /상금|큰|많은|고액/.test(q);
  if (!why.length && !big) return { list: [], total: 0, vague: true };
  if (big) { r.sort((a, b) => b.pv - a.pv || a.left - b.left); why.push('상금 큰 순'); }
  else r.sort((a, b) => a.left - b.left || b.pv - a.pv);
  return { list: r.slice(0, 5), total: r.length, why, big };
}

const dd = l => l ? 'D-' + l : 'D-DAY';
function cardHTML(x) {
  if (x.k === 'e') return `<a class="rc-card" href="${esc(x.i.link)}" target="_blank" rel="noopener nofollow"><b>🎁 ${esc(x.i.title)}</b><span>${dd(x.i.left)} · ${esc(x.i.ez)}</span></a>`;
  const i = x.i || x;
  return `<div class="rc-cw"><a class="rc-card" href="/c/${i.id}/"><b>${esc(i.title)}</b><span>${dd(i.left)} · ${i.end.replace(/-/g, '.')} 마감${i.pv ? ' · ' + esc(i.prize) : ''}${i.effort ? ' · ' + esc(i.effort) : ''}</span></a><button type="button" class="rc-fav${fav.has(i.id) ? ' on' : ''}" data-fav="${i.id}" title="찜">${fav.has(i.id) ? '★' : '☆'}</button><button type="button" class="rc-cal" data-cal="${i.id}" title="캘린더에 마감일 넣기">📅</button></div>`;
}
const cards = list => '<div class="rc-list">' + list.map(cardHTML).join('') + '</div>';

function answer(q) {
  for (const [re, txt] of FAQ) if (re.test(q)) return { html: txt, say: txt.replace(/<[^>]+>/g, '') };
  const res = search(q);
  if (/(추천|뭐\s*할까|골라|맞는|어울리)/.test(q) && res.vague) return { pick: true };
  if (!res.list.length) {
    const t = (res.vague ? '어떤 걸 찾으시는지 조금만 더 알려 주세요.' : '지금 목록에는 맞는 게 없어요.') + ' "슬로건 공모전", "이번 주 마감", "상금 큰 영상"처럼 물어보시거나 위의 <b>취향 고르기</b>로 추천받아 보세요.';
    return { html: t, say: t.replace(/<[^>]+>/g, '') };
  }
  const head = `${res.why.join(', ')} 조건으로 ${res.total}건 찾았어요. ${res.big ? '상금이 큰' : '마감이 가까운'} 것부터 보여 드릴게요.`;
  return { html: esc(head) + cards(res.list), say: head + ' ' + res.list.slice(0, 3).map(i => i.title).join(', ') };
}

// ---- 음성: 마이크(WebRTC getUserMedia) → 인식 → 답변 → 합성 ----
function talk(t) {
  if (!speak || !window.speechSynthesis || !t) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(t.slice(0, 300)); u.lang = 'ko-KR'; u.rate = 1.05; u.pitch = 1.15;
  const vs = speechSynthesis.getVoices();
  const v = vs.find(v => /ko/i.test(v.lang) && /SunHi|Heami|Yuna|여/i.test(v.name)) || vs.find(v => /ko/i.test(v.lang));
  if (v) u.voice = v;
  speechSynthesis.speak(u);
}

// ---- UI ----
function ui() {
  const root = el('div', 'rc');
  root.innerHTML = `<button class="rc-fab" aria-label="루리에게 추천받기"><img src="/assets/ruri/avatar.webp" alt=""><span>루리에게 물어보기</span></button>
<section class="rc-panel" hidden aria-label="루리 추천 챗봇"><header><img src="/assets/ruri/avatar.webp" alt=""><div><b>루리</b><small>마감·상금·찜·캘린더까지 챙겨 드려요</small></div>
<button class="rc-ai rc-redo" title="취향 다시 고르기">취향 고르기</button><button id="rc-spk" class="rc-ic" title="답변 읽어 주기">🔈</button><button class="rc-x rc-ic" aria-label="닫기">✕</button></header>
<div class="rc-log" role="log" aria-live="polite"></div>
<form class="rc-in"><button type="button" class="rc-mic rc-ic" title="말로 물어보기">🎤</button><input placeholder="예) 슬로건 공모전, 이번 주 마감" aria-label="질문"><button class="rc-go">보내기</button></form></section>`;
  document.body.appendChild(root);
  const panel = $('.rc-panel', root), input = $('input', root), log = $('.rc-log', root);
  const scroll = () => { log.scrollTop = log.scrollHeight; };
  const add = (who, html) => { const b = el('div', 'rc-m ' + who, html); log.appendChild(b); scroll(); return b; };
  const byId = id => items.find(i => i.id === id);
  // 답 아래 빠른 버튼: chips([[라벨, 함수], ...])
  const chips = (b, list) => { const w = el('div', 'rc-chips'); list.forEach(([t, f]) => { const x = el('button', '', t); x.type = 'button'; x.onclick = () => { ga('chat_menu', { label: t.replace(/[^\p{L}\p{N} ]/gu, '').trim().slice(0, 30) }); w.remove(); f(); }; w.appendChild(x); }); b.appendChild(w); scroll(); return w; };
  const say = (html, next, list) => { const b = add('bot', html + (list && list.length ? cards(list) : '')); talk(html.replace(/<[^>]+>/g, '') + (list ? ' ' + list.slice(0, 3).map(x => (x.i || x).title).join(', ') : '')); if (next) chips(b, next); return b; };
  const me = t => add('me', esc(t));
  const C = list => list.map(i => ({ k: 'c', i }));
  const more = (list, title, n = 5) => {  // 5개씩 끊어 보여 주기
    let k = 0; const step = () => { const part = list.slice(k, k + n); k += n;
      say(k <= n ? title : '이어서 보여 드릴게요.', [...(k < list.length ? [['더 보기 ▾', step]] : []), ...back()], C(part)); };
    if (!list.length) return say('지금 조건에 맞는 공모전이 없어요. 조건을 바꿔 볼까요?', back()); step();
  };
  const back = () => [['🏠 처음 메뉴', menu]];
  const narrow = (base, label) => [['🎨 분야로 좁히기', () => { me('분야로 좁히기'); say('어떤 분야요?', Object.keys(CAT).map(c => [c, () => { me(c); more(base.filter(i => i.tags.includes(c)), `${label} · ${c} 공모전이에요.`); }])); }],
                                  ['⚡ 쉬운 것만', () => { me('쉬운 것만'); more(base.filter(i => EASY_RE.test(i.title + ' ' + i.field + ' ' + (i.effort || ''))), `${label} 중 금방 낼 수 있는 것만 골랐어요.`); }]];
  function menu() {
    say('무엇을 도와드릴까요?', [
      ['🔥 이번 주 마감', soon], ['⚡ 10분 안에 내는 것', quick], ['💰 상금 큰 것', big], ['🎯 나한테 맞는 것', who],
      ['📍 우리 동네 대회', local], [`⭐ 찜한 공모전${fav.get().length ? ' ' + fav.get().length : ''}`, favs], ['🤝 같이 할 팀 찾기', () => { location.href = '/community/'; }], ['❓ 자주 묻는 질문', faq]]);
  }
  function soon() { me('이번 주 마감'); const l = items.filter(i => i.left <= 7).sort((a, b) => a.left - b.left || b.pv - a.pv);
    const b = say(`7일 안에 마감하는 공모전이 ${l.length}건이에요. 급한 것부터 보여 드릴게요.`, null, C(l.slice(0, 5))); chips(b, [...narrow(l, '이번 주 마감'), ...(l.length > 5 ? [['더 보기 ▾', () => more(l.slice(5), '이어서 보여 드릴게요.')]] : []), ...back()]); }
  function quick() { me('10분 안에 내는 것');
    const l = items.filter(i => EASY_RE.test(i.title + ' ' + i.field + ' ' + (i.effort || ''))).sort((a, b) => a.left - b.left);
    const ev = events.filter(e => EZ_RANK[e.ez] === 0).sort((a, b) => a.left - b.left).slice(0, 3).map(i => ({ k: 'e', i }));
    say(`슬로건·네이밍·삼행시·사진처럼 짧게 내는 공모전 ${l.length}건, 댓글·폼 1분 경품도 같이 골랐어요.`, [['더 보기 ▾', () => more(l.slice(4), '이어서 짧게 내는 공모전이에요.')], ['🎁 경품만 더', () => { me('경품만 더'); say('1분이면 끝나는 경품 이벤트예요.', back(), events.filter(e => EZ_RANK[e.ez] != null).sort((a, b) => (EZ_RANK[a.ez] - EZ_RANK[b.ez]) || a.left - b.left).slice(0, 6).map(i => ({ k: 'e', i }))); }], ...back()], [...C(l.slice(0, 4)), ...ev]); }
  function big() { me('상금 큰 것'); say('상금 기준을 골라 주세요.', [100, 500, 1000].map(m => [`${m}만원 이상`, () => { me(`${m}만원 이상`); more(items.filter(i => i.pv >= m * 1e4).sort((a, b) => b.pv - a.pv), `상금 ${m}만원 이상, 큰 순이에요.`); }]).concat(back())); }
  function who() { me('나한테 맞는 것'); say('지금 어떤 신분이세요? 자격 조건에 맞춰 걸러 드릴게요.', Object.keys(WHO).map(w => [w, () => { me(w);
    const p = pref.get() || { ints: [], style: 'easy', region: '' }; p.who = w; pref.set(p);
    say('관심 있는 분야도 골라 주세요.', [...Object.keys(INTEREST).filter(k => k !== '경품 이벤트').map(k => [k, () => { me(k); p.ints = [k]; pref.set(p);
      const re = WHO[w], l = recommend(p).filter(x => x.k === 'c' && (!re || re.test(x.i.elig || '') || /제한\s*없|누구나/.test(x.i.elig || ''))).map(x => x.i);
      more(l, `${w} · ${k} 기준으로 골라 봤어요. 자격은 공고에서 한 번 더 확인해 주세요.`); }]), ['🧩 자세히 고르기', picker]]); }])); }
  function local() { me('우리 동네 대회'); const b = say('사는 시·군·구를 적어 주세요. (예: 부산, 수원, 강남)');
    const f = el('form', 'rc-inline', '<input placeholder="지역 이름" maxlength="10"><button>찾기</button>'); b.appendChild(f); scroll();
    f.onsubmit = e => { e.preventDefault(); const r = f.querySelector('input').value.trim(); if (!r) return; f.remove(); me(r);
      const p = pref.get() || { ints: [], style: 'easy' }; p.region = r; pref.set(p);
      more(items.filter(i => (i.title + i.org + (i.elig || '') + (i.region || '')).includes(r)).sort((a, b) => a.left - b.left), `「${r}」 관련·주민 대상 공모전이에요.`); }; }
  function favs() { me('찜한 공모전'); const l = fav.get().map(x => byId(x.id)).filter(Boolean).sort((a, b) => a.left - b.left);
    if (!l.length) return say('아직 찜한 공모전이 없어요. 카드 옆 ☆을 누르면 찜돼요. 마감이 다가오면 제가 먼저 알려 드릴게요!', back());
    say(`찜한 공모전 ${l.length}건이에요. 📅을 누르면 캘린더에 마감일이 들어가요.`, back(), C(l)); }
  function faq() { me('자주 묻는 질문'); say('궁금한 걸 골라 주세요.', FAQ_CHIPS.map(([t, q]) => [t, () => { me(t); const a = answer(q); say(a.html, [['❓ 다른 질문', faq], ...back()]); }]).concat(back())); }
  function detail(i) {  // 공모전 상세 페이지에서 열면 그 공모전 기준으로
    const chk = [`⏰ 마감 <b>${dd(i.left)}</b> (${i.end.replace(/-/g, '.')})`, i.elig ? `👤 자격: ${esc(i.elig)}` : '', i.effort ? `📝 형식: ${esc(i.effort)}` : '', i.pv ? `💰 상금: ${esc(i.prize)}` : '', '📌 분량·제출 방법·저작권은 공식 공고에서 확인'].filter(Boolean);
    say(`<b>${esc(i.title)}</b> 응모 준비 체크예요.<ul class="rc-chk">${chk.map(c => `<li>${c}</li>`).join('')}</ul>`, [
      [fav.has(i.id) ? '★ 찜 해제' : '☆ 찜하기', () => { const on = fav.toggle(i); say(on ? '찜했어요! 마감 3일 전부터 챗봇을 열면 알려 드릴게요.' : '찜을 뺐어요.', [['📅 캘린더에 넣기', () => ics(i)], ...back()]); }],
      ['📅 캘린더에 넣기', () => { ics(i); say('캘린더 파일을 받았어요. 열면 마감 전날 알림이 들어가요.', back()); }],
      ['🤝 같이 할 팀 찾기', () => { const t = document.getElementById('cm-teams'); if (t) { panel.hidden = true; t.scrollIntoView({ behavior: 'smooth' }); } else location.href = '/community/'; }],
      ['🔎 비슷한 공모전', () => { me('비슷한 공모전'); more(items.filter(x => x.id !== i.id && x.tags.some(t => i.tags.includes(t))).sort((a, b) => a.left - b.left), '같은 분야 진행 중 공모전이에요.'); }], ...back()]);
  }
  // 카드의 찜·캘린더 버튼 (이벤트 위임)
  log.addEventListener('click', e => {
    const f = e.target.closest('[data-fav]'), c = e.target.closest('[data-cal]');
    if (f) { const i = byId(f.dataset.fav); if (!i) return; const on = fav.toggle(i); if (on) ga('fav_add', { contest_id: i.id }); log.querySelectorAll(`[data-fav="${i.id}"]`).forEach(x => { x.classList.toggle('on', on); x.textContent = on ? '★' : '☆'; }); badge(); }
    if (c) { const i = byId(c.dataset.cal); if (i) { ics(i); ga('calendar_add', { contest_id: i.id }); } }
  });
  const urgent = () => fav.get().map(x => ({ ...x, left: dn(x.end) - today })).filter(x => x.left >= 0 && x.left <= 3).sort((a, b) => a.left - b.left);
  const badge = () => { $('.rc-fab', root).classList.toggle('alert', !!urgent().length); };
  badge();

  const showRec = p => {
    const r = recommend(p);
    const lab = [p.ints.join('·') || '전체', Object.keys(STYLE).find(k => STYLE[k] === p.style), p.region].filter(Boolean).join(' / ');
    const t = r.length ? `「${lab}」 취향으로 골라 봤어요!` : '조건에 맞는 게 지금은 없어요. 취향을 조금 넓혀 볼까요?';
    const b = add('bot', esc(t) + (r.length ? cards(r) : '') + '<div class="rc-act"><button class="rc-more">다른 취향으로</button></div>');
    b.querySelector('.rc-more').onclick = picker; chips(b, back());
    talk(t + ' ' + r.slice(0, 3).map(x => x.i.title).join(', '));
  };
  function picker() {
    const p = pref.get() || { ints: [], style: 'easy', region: '' };
    const b = add('bot rc-pick', `<b>어떤 걸 좋아하세요?</b> <small>여러 개 골라도 돼요</small>
<div class="rc-opts" data-g="ints">${Object.keys(INTEREST).map(k => `<button type="button" class="${p.ints.includes(k) ? 'on' : ''}">${k}</button>`).join('')}</div>
<b>무엇이 중요해요?</b><div class="rc-opts" data-g="style" data-one="1">${Object.keys(STYLE).map(k => `<button type="button" class="${p.style === STYLE[k] ? 'on' : ''}">${k}</button>`).join('')}</div>
<b>사는 지역</b> <small>선택 · 지역 대회를 먼저 보여 드려요</small><input class="rc-region" placeholder="예) 부산, 수원" value="${esc(p.region || '')}">
<button type="button" class="rc-on rc-get">추천받기</button>`);
    b.querySelectorAll('.rc-opts').forEach(g => g.querySelectorAll('button').forEach(x => x.onclick = () => {
      if (g.dataset.one) g.querySelectorAll('button').forEach(y => y.classList.remove('on'));
      x.classList.toggle('on');
    }));
    b.querySelector('.rc-get').onclick = () => {
      const np = { ints: [...b.querySelectorAll('[data-g=ints] .on')].map(x => x.textContent),
                   style: STYLE[(b.querySelector('[data-g=style] .on') || {}).textContent] || 'easy',
                   region: b.querySelector('.rc-region').value.trim().slice(0, 10) };
      pref.set(np); showRec(np);
    };
  }
  const send = async () => {
    const q = input.value.trim(); if (!q) return; input.value = '';
    add('me', esc(q)); ga('chat_ask', { q: q.slice(0, 40) }); await load();
    const a = answer(q);
    if (a.html) { const b = add('bot', a.html); talk(a.say); chips(b, [['🎯 취향으로 추천', picker], ['❓ 자주 묻는 질문', faq], ...back()]); }
    if (a.pick) picker();
  };
  const open = async () => {
    ga('chat_open', { page: location.pathname });
    await load();
    const u = urgent();
    if (u.length) say(`앗, 찜한 공모전 마감이 다가와요! ${u.map(x => `<b>${esc(x.title)}</b> ${dd(x.left)}`).join(', ')}`);
    const here = (location.pathname.match(/^\/c\/([^/]+)\//) || [])[1], i = here && byId(here);
    if (i) { say('이 공모전 같이 볼까요?'); detail(i); return; }
    add('bot', pref.get() ? '다시 오셨네요! 오늘은 뭘 찾아 드릴까요?' : '안녕하세요, 루리예요! 진행 중인 공모전에서 딱 맞는 걸 골라 드려요. 아래 버튼을 누르거나 그냥 물어보셔도 돼요.');
    menu();
  };
  $('.rc-fab', root).onclick = () => { panel.hidden = !panel.hidden; if (!panel.hidden && !log.children.length) open(); };
  $('.rc-x', root).onclick = () => { panel.hidden = true; if (window.speechSynthesis) speechSynthesis.cancel(); };
  $('.rc-redo', root).onclick = () => { load().then(picker); };
  $('form', root).onsubmit = e => { e.preventDefault(); send(); };
  $('#rc-spk', root).onclick = e => { speak = !speak; e.currentTarget.classList.toggle('on', speak); if (!speak && window.speechSynthesis) speechSynthesis.cancel(); };
  $('.rc-mic', root).onclick = async e => {
    const btn = e.currentTarget, SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { add('bot', '이 브라우저는 음성 인식을 지원하지 않아요. 크롬이나 엣지에서 써 주세요.'); return; }
    if (rec) { rec.stop(); return; }
    try { const s = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } }); s.getTracks().forEach(t => t.stop()); }
    catch { add('bot', '마이크 권한이 필요해요.'); return; }
    speak = true; $('#rc-spk', root).classList.add('on');
    rec = new SR(); rec.lang = 'ko-KR'; rec.interimResults = true; btn.classList.add('rec');
    rec.onresult = ev => { input.value = [...ev.results].map(r => r[0].transcript).join(''); if (ev.results[ev.results.length - 1].isFinal) send(); };
    rec.onend = () => { btn.classList.remove('rec'); rec = null; };
    rec.start();
  };
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ui); else ui();
