"""퍼가기 위젯 (2026-10-18 연구 세션 요청 "3 ㄱ"): 다른 블로그·카페에 붙이는 공모전·지원금·핫이슈·D-day 위젯.
- /w/data.json        위젯 데이터 (매 빌드)
- /w/<종류>/          iframe 용 가벼운 페이지 (광고·GTAG 없음, 검색 제외)
- /w/img/*.png        매시간 다시 그리는 이미지 카드 (네이버 블로그·카페·디시용: 이미지 + 링크)
- /widget/            배포 페이지 (미리보기·옵션·코드 복사·붙이는 법)
모든 링크 ?src=w_<종류>, nofollow 없음. 노출은 /api/wv, 클릭은 /api/hit 의 src:w_* 로 집계."""
import os, re, json, datetime, html

SITE = 'https://sungprofile.cloud'
E = lambda s: html.escape(str(s or ''), quote=True)
# 분야 선택 (위젯용 이름 → 고르는 조건)
WCATS = [('all', '전체'), ('video', '영상'), ('design', '디자인'), ('write', '글쓰기'), ('photo', '사진'), ('food', '요리'), ('idea', '아이디어'), ('univ', '대학생')]


def _pick(c, k):
    t, f, el, ef = c.get('tags') or [], c.get('field') or '', c.get('elig') or '', c.get('effort') or ''
    return {'all': True, 'video': '영상' in t or ef == '영상', 'design': '디자인' in t or ef == '디자인', 'write': '문학' in t or ef == '원고',
            'photo': '사진' in f or ef == '사진', 'food': '요리·레시피' in t, 'idea': '아이디어·정책' in t or ef == '아이디어 제안서', 'univ': '대학생' in el}[k]


def _dd(end, today):
    n = (datetime.date.fromisoformat(end) - today).days
    return n, ('D-DAY' if n == 0 else f'D-{n}')


def data(live, aps, hot, today):
    out = {'updated': datetime.datetime.now().strftime('%m/%d %H:%M'), 'contest': {}, 'apply': [], 'hot': []}
    for k, _ in WCATS:
        L = sorted([c for c in live if _pick(c, k) and _dd(c['end'], today)[0] >= 0], key=lambda c: (c['end'], -(c.get('pv') or 0)))
        out['contest'][k] = [{'id': c['id'], 't': c['title'][:60], 'o': (c.get('org') or '')[:24], 'e': c['end'], 'p': c.get('prize') if c.get('pv') else ''} for c in L[:10]]
    A = sorted([a for a in aps if not a.get('always') and a.get('end') and _dd(a['end'], today)[0] >= 0], key=lambda a: a['end'])
    out['apply'] = [{'id': a['id'], 't': a['title'][:60], 'o': (a.get('org') or '')[:24], 'e': a['end'], 'k': a.get('kind', '')} for a in A[:10]]
    seen = []
    for v in hot:  # 같은 사건 다른 제목은 하나만 (단어 절반 넘게 겹치면 같은 것으로 봄)
        w = set(re.findall(r'[가-힣A-Za-z0-9]{2,}', v['title']))
        if any(len(w & x) * 2 > min(len(w), len(x)) for x in seen):
            continue
        seen.append(w)
        out['hot'].append({'s': v['slug'], 't': v['title'][:60], 'n': len(v.get('outs') or [])})
        if len(out['hot']) >= 6:
            break
    return out


IFR = r'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>루리의 줍줍 위젯</title><style>
:root{--bg:#fff;--fg:#1e1b2e;--mu:#6b7280;--ln:#ece9f5;--ac:#6d28d9;--hi:#f5f3ff}
.dark{--bg:#17151f;--fg:#f3f1fa;--mu:#a4a0b5;--ln:#2c2939;--ac:#a78bfa;--hi:#221e30}
*{box-sizing:border-box}html,body{margin:0;height:100%}body{font:14px/1.45 -apple-system,"Malgun Gothic","Apple SD Gothic Neo",sans-serif;background:var(--bg);color:var(--fg);display:flex;flex-direction:column;border:1px solid var(--ln);border-radius:12px;overflow:hidden}
header{display:flex;align-items:center;gap:8px;padding:10px 12px;background:var(--hi);font-weight:800}header img{width:28px;height:28px;border-radius:50%}
ul{list-style:none;margin:0;padding:0;flex:1;overflow:auto}li a{display:flex;gap:10px;align-items:flex-start;padding:9px 12px;border-bottom:1px solid var(--ln);color:inherit;text-decoration:none}li a:hover{background:var(--hi)}
b.d{flex:none;min-width:52px;text-align:center;font-size:12px;padding:2px 6px;border-radius:99px;background:var(--ac);color:#fff}b.d.u{background:#dc2626}
span.t{display:block;font-weight:600;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}small{color:var(--mu)}
footer{padding:7px 12px;font-size:12px;color:var(--mu);border-top:1px solid var(--ln)}footer a{color:var(--ac);font-weight:700;text-decoration:none}
.big{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:14px;text-decoration:none;color:inherit}.big b{font-size:44px;color:var(--ac);line-height:1.1}.big span{font-weight:700;margin-top:6px}
</style></head><body><header><img src="/assets/ruri/avatar.webp" alt=""><span id="hd"></span></header><div id="bx" style="flex:1;display:flex;flex-direction:column;overflow:hidden"></div>
<footer><a id="ft" href="__SITE__/?src=w___K__" target="_blank" rel="noopener">루리의 줍줍</a>에서 매일 갱신 · <span id="up"></span></footer>
<script>(function(){var K='__K__',S='__SITE__',Q=new URLSearchParams(location.search),n=Math.min(10,Math.max(1,+Q.get('n')||5)),cat=Q.get('cat')||'all',src='?src=w_'+K;
if(Q.get('t')==='dark')document.body.className='dark';
var esc=function(s){return String(s||'').replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})};
var dd=function(e){var t=new Date(Date.now()+9*36e5).toISOString().slice(0,10),n=Math.round((new Date(e)-new Date(t))/864e5);return[n,n===0?'D-DAY':n<0?'마감':'D-'+n]};
var CN=__CN__;
fetch('/w/data.json',{cache:'no-cache'}).then(function(r){return r.json()}).then(function(D){var h=document.getElementById('hd'),b=document.getElementById('bx'),L=[];
document.getElementById('up').textContent=D.updated+' 기준';
if(K==='contest'){h.textContent='이번 주 마감 공모전'+(cat!=='all'?' · '+(CN[cat]||''):'');L=(D.contest[cat]||[]).slice(0,n).map(function(c){var d=dd(c.e);return'<li><a href="'+S+'/c/'+c.id+'/'+src+'" target="_blank" rel="noopener"><b class="d'+(d[0]<=3?' u':'')+'">'+d[1]+'</b><span><span class="t">'+esc(c.t)+'</span><small>'+esc(c.o)+(c.p?' · '+esc(c.p):'')+'</small></span></a></li>'})}
else if(K==='apply'){h.textContent='이번 주 지원금·청약 마감';L=D.apply.slice(0,n).map(function(a){var d=dd(a.e);return'<li><a href="'+S+'/a/'+encodeURIComponent(a.id)+'/'+src+'" target="_blank" rel="noopener"><b class="d'+(d[0]<=3?' u':'')+'">'+d[1]+'</b><span><span class="t">'+esc(a.t)+'</span><small>'+esc(a.k)+' · '+esc(a.o)+'</small></span></a></li>'})}
else if(K==='hot'){h.textContent='오늘의 핫이슈';L=D.hot.slice(0,Math.min(n,3)).map(function(x,i){return'<li><a href="'+S+'/hot/'+encodeURIComponent(x.s)+'/'+src+'" target="_blank" rel="noopener"><b class="d">'+(i+1)+'</b><span><span class="t">'+esc(x.t)+'</span><small>언론사 '+x.n+'곳 보도 · 나한테 달라지는 점 보기</small></span></a></li>'})}
else if(K==='dday'){var id=Q.get('id')||'';h.textContent='공모전 마감 카운터';return fetch('/data.json').then(function(r){return r.json()}).then(function(A){var c=(A.items||[]).filter(function(x){return x.id===id})[0];
if(!c){b.innerHTML='<a class="big" href="'+S+'/contest/'+src+'" target="_blank" rel="noopener"><span>공모전을 찾지 못했어요.<br>진행 중 공모전 보기 →</span></a>';return}var d=dd(c.end);
b.innerHTML='<a class="big" href="'+S+'/c/'+c.id+'/'+src+'" target="_blank" rel="noopener"><b>'+d[1]+'</b><span>'+esc(c.title)+'</span><small>'+c.end.replace(/-/g,'.')+' 마감'+(c.pv?' · '+esc(c.prize):'')+'</small></a>'})}
b.innerHTML='<ul>'+(L.join('')||'<li><a href="'+S+'/'+src+'" target="_blank" rel="noopener"><span class="t">지금 정리 중이에요. 사이트에서 보기 →</span></a></li>')+'</ul>'}).catch(function(){});
try{if(location.hostname==='sungprofile.cloud'&&!/sungprofile/.test(document.referrer))fetch('__API__/api/wv',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json'},body:JSON.stringify({k:K,r:document.referrer})})}catch(e){}})();</script></body></html>'''


def iframes(root, api):
    cn = json.dumps(dict(WCATS), ensure_ascii=False)
    for k in ('contest', 'apply', 'hot', 'dday'):
        d = os.path.join(root, 'w', k)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n').write(
            IFR.replace('__SITE__', SITE).replace('__K__', k).replace('__CN__', cn).replace('__API__', api or ''))


def _font(sz, bold=False):
    from PIL import ImageFont
    for f in (r'C:\Windows\Fonts\malgunbd.ttf' if bold else r'C:\Windows\Fonts\malgun.ttf', r'C:\Windows\Fonts\malgun.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def _fit(dr, t, f, w):
    if dr.textlength(t, font=f) <= w:
        return t
    while t and dr.textlength(t + '…', font=f) > w:
        t = t[:-1]
    return t + '…'


def card_png(path, title, rows, updated, root, accent=(109, 40, 217)):
    """rows: [(배지, 제목, 아랫줄, 빨강?)] → 720px 폭 PNG"""
    from PIL import Image, ImageDraw
    W, RH, HH, FH = 720, 74, 76, 46
    H = HH + RH * max(1, len(rows)) + FH
    im = Image.new('RGB', (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    dr.rectangle([0, 0, W, HH], fill=(245, 243, 255))
    try:
        av = Image.open(os.path.join(root, 'assets', 'ruri', 'avatar.webp')).convert('RGBA').resize((52, 52))
        m = Image.new('L', (52, 52), 0); ImageDraw.Draw(m).ellipse([0, 0, 51, 51], fill=255)
        im.paste(av, (16, 12), m)
    except Exception:
        pass
    dr.text((80, 18), title, font=_font(26, True), fill=(30, 27, 46))
    dr.text((W - 16, 30), updated + ' 갱신', font=_font(15), fill=(107, 114, 128), anchor='ra')
    fb, fs, fd = _font(21, True), _font(16), _font(17, True)
    y = HH
    for badge, t, sub, red in rows or [('', '지금 정리 중이에요', 'sungprofile.cloud 에서 확인하세요', False)]:
        if badge:
            bw = max(70, dr.textlength(badge, font=fd) + 24)
            dr.rounded_rectangle([16, y + 18, 16 + bw, y + 50], 16, fill=(220, 38, 38) if red else accent)
            dr.text((16 + bw / 2, y + 34), badge, font=fd, fill=(255, 255, 255), anchor='mm')
            x = 16 + bw + 14
        else:
            x = 16
        dr.text((x, y + 12), _fit(dr, t, fb, W - x - 16), font=fb, fill=(30, 27, 46))
        dr.text((x, y + 42), _fit(dr, sub, fs, W - x - 16), font=fs, fill=(107, 114, 128))
        y += RH
        dr.line([16, y - 1, W - 16, y - 1], fill=(236, 233, 245))
    dr.rectangle([0, H - FH, W, H], fill=accent)
    dr.text((W / 2, H - FH / 2), '루리의 줍줍에서 매일 갱신 · sungprofile.cloud', font=_font(17, True), fill=(255, 255, 255), anchor='mm')
    im.save(path, optimize=True)


def images(root, D, today):
    d = os.path.join(root, 'w', 'img')
    os.makedirs(d, exist_ok=True)
    cn = dict(WCATS)
    for k, _ in WCATS:
        rows = [(_dd(c['e'], today)[1], c['t'], f'{c["o"]}' + (f' · 상금 {c["p"]}' if c['p'] else '') + f' · {c["e"][5:].replace("-", "/")} 마감', _dd(c['e'], today)[0] <= 3) for c in D['contest'][k][:5]]
        card_png(os.path.join(d, 'contest-week.png' if k == 'all' else f'contest-week-{k}.png'), '이번 주 마감 공모전 TOP5' + ('' if k == 'all' else f' · {cn[k]}'), rows, D['updated'], root)
    rows = [(_dd(a['e'], today)[1], a['t'], f'{a["k"]} · {a["o"]} · {a["e"][5:].replace("-", "/")} 마감', _dd(a['e'], today)[0] <= 3) for a in D['apply'][:5]]
    card_png(os.path.join(d, 'apply-week.png'), '이번 주 지원금·청약 마감', rows, D['updated'], root, (14, 116, 144))
    rows = [(f'{i + 1}위', x['t'], f'언론사 {x["n"]}곳 보도 · 나한테 달라지는 점 정리', False) for i, x in enumerate(D['hot'][:3])]
    card_png(os.path.join(d, 'hot-today.png'), '오늘의 핫이슈 3', rows, D['updated'], root, (180, 83, 9))


def widget_page(page, say, D):
    opts = ''.join(f'<option value="{k}">{n}</option>' for k, n in WCATS)
    ids = ''.join(f'<option value="{E(c["id"])}">{E(c["t"][:40])} ({c["e"][5:]})</option>' for c in D['contest']['all'][:10])
    body = f'''<p class="bc"><a href="/">홈</a> › <a href="/contest/">공모전</a> › 위젯</p><h1>🧩 공모전 위젯 무료 — 블로그에 이번 주 마감 공모전 자동 표시</h1>
{say('o_present', '블로그·카페에 붙이면 <b>이번 주 마감 공모전</b>이 매시간 알아서 바뀌어요. 회원가입도, 비용도 없어요!')}
<p>루리의 줍줍이 매시간 정리하는 마감 공모전·지원금·핫이슈 목록을 내 블로그나 카페, 홈페이지에 그대로 띄울 수 있는 무료 위젯이에요. 공모전·대외활동 정보를 올리는 블로그라면 글마다 목록을 새로 쓰지 않아도 돼요. 위젯 안에는 광고가 없고, 항목을 누르면 루리의 줍줍 상세 페이지(마감·상금·자격·준비 일정)로 이동해요.</p>
<section class="wg"><h2>1. 위젯 고르기</h2><div class="wg-f">
<label>종류<select id="wk"><option value="contest">이번 주 마감 공모전 TOP5</option><option value="apply">이번 주 지원금·청약 마감</option><option value="hot">오늘의 핫이슈 3</option><option value="dday">D-day 카운터 (공모전 1개)</option></select></label>
<label id="wcl">분야<select id="wc">{opts}</select></label><label id="wil" hidden>공모전<select id="wi">{ids}</select></label>
<label>개수<select id="wn"><option>3</option><option selected>5</option><option>7</option><option>10</option></select></label>
<label>크기<select id="ws"><option value="300x380">작게 300×380</option><option value="360x480" selected>보통 360×480</option><option value="600x420">넓게 600×420</option></select></label>
<label>테마<select id="wt"><option value="light">밝음</option><option value="dark">어두움</option></select></label></div>
<h2>2. 미리보기</h2><div class="wg-pv"><iframe id="wf" title="위젯 미리보기" loading="lazy"></iframe><img id="wimg" alt="이미지 위젯 미리보기" width="360"></div>
<h2>3. 붙이는 코드</h2>
<div class="wg-c"><h3>🖼️ 이미지 + 링크 (네이버 블로그·카페·디시)</h3><textarea id="c1" readonly rows="3"></textarea><p><button data-c="c1">코드 복사</button><button id="cimg">이미지 주소 복사</button></p></div>
<div class="wg-c"><h3>🪟 iframe (티스토리·워드프레스·홈페이지)</h3><textarea id="c2" readonly rows="3"></textarea><p><button data-c="c2">코드 복사</button></p></div>
<div class="wg-c"><h3>📝 텍스트 목록 (어디든 붙여넣기)</h3><textarea id="c3" readonly rows="5"></textarea><p><button data-c="c3">코드 복사</button></p><p class="note">텍스트 목록은 복사한 그 시점의 목록이라 자동으로 바뀌지 않아요.</p></div></section>
<h2>블로그에 붙이는 법</h2><ul class="chk">
<li><b>네이버 블로그</b>: 글쓰기 → 사진 대신 「이미지 주소 복사」로 받은 주소를 이미지로 넣고, 이미지를 눌러 링크에 https://sungprofile.cloud/contest/?src=w_img 를 걸어요. 네이버 에디터는 붙인 이미지를 네이버 서버에 복사해 두기 때문에 자동 갱신은 안 될 수 있어요. 목록이 바뀌면 다시 붙이거나, 프로필·위젯 영역에 링크로 걸어 두세요.</li>
<li><b>티스토리</b>: 글쓰기 → 기본모드 오른쪽 위 「HTML」로 바꾸고 iframe 코드를 붙여요. 사이드바에 넣으려면 꾸미기 → 사이드바 → HTML 배너 출력에 붙여요.</li>
<li><b>워드프레스</b>: 블록 추가 → 「사용자 정의 HTML」 블록에 iframe 코드를 붙여요. 위젯 영역(외모 → 위젯)에도 같은 블록을 쓸 수 있어요.</li>
<li><b>네이버 카페·디시</b>: iframe 이 막혀 있어서 이미지 + 링크 방식이 좋아요. 이미지 주소로 그림을 넣고 아래에 사이트 링크를 한 줄 적어 주세요.</li></ul>
<p class="note">위젯 목록은 매시간 갱신돼요. 공모전 정보는 각 주최 기관 공고를 정리한 것이라, 응모 전 공식 공고를 꼭 확인하세요. 위젯을 붙인 뒤 문제가 있으면 <a href="/contact/">문의</a>로 알려 주세요.</p>
<link rel="stylesheet" href="/assets/widget/widget.css?v=1"><script defer src="/assets/widget/widget.js?v=1"></script>'''
    page('/widget/', '공모전 위젯 무료 — 블로그에 이번 주 마감 공모전 자동 표시', '블로그·카페·홈페이지에 이번 주 마감 공모전 TOP5, 지원금·청약 마감, 오늘의 핫이슈, D-day 카운터를 무료로 붙이세요. 이미지·iframe·텍스트 3가지 방식, 매시간 자동 갱신.',
         body, [('루리의 줍줍', '/'), ('공모전', '/contest/'), ('위젯', '/widget/')])


def build(root, live, aps, hot, page, say, api, today):
    D = data(live, aps, hot, today)
    os.makedirs(os.path.join(root, 'w'), exist_ok=True)
    json.dump(D, open(os.path.join(root, 'w', 'data.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    iframes(root, api)
    try:
        images(root, D, today)
    except Exception as e:
        print('widget images fail', e)
    widget_page(page, say, D)
    return ['/widget/']
