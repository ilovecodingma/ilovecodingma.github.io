# -*- coding: utf-8 -*-
"""루리 줍줍 전자책 (2026-11-05 사용자 「우리도 책 출판하면 안 되나 · 섹션 만들어서 대충 만들어 보지 · E북 출판사 뭐 별건가」).
이미 있는 생활 가이드(kin_guides.json)를 주제·상황별로 묶어 책 한 권으로 낸다. 새 글을 지어내지 않고, 가이드 본문·확인일·출처를 그대로 싣는다.
  /book/                목록(색인 대상)
  /book/<slug>/         웹에서 읽기(가이드와 같은 본문이라 검색 제외 — 중복 문서를 색인시키지 않는다)
  /book/files/<slug>.epub · .pdf   내려받기(EPUB 은 빌드 때 바로, PDF 는 빌드 끝에 make_pdfs 가 바뀐 책만 다시 만든다)
  /book/cover/<slug>.png 표지
사용: build.py 의 kin_guides() 안에서 build(G, JR, page, root) → 주소 목록, 빌드 끝에서 make_pdfs(root)."""
import os, re, json, html, hashlib, zipfile, datetime

E = lambda t: html.escape(str(t), quote=True)
KEYF = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'books_keys.json')   # 파일을 다시 만들지 정하는 해시(공개 폴더에 두지 않는다)


def _keys():
    return json.load(open(KEYF, encoding='utf-8')) if os.path.exists(KEYF) else {}


def _setkey(k, v):
    d = _keys(); d[k] = v
    json.dump(d, open(KEYF, 'w', encoding='utf-8'), indent=1)
SITE = 'https://sungprofile.cloud'
PUB = '루리 줍줍'

BOOKS = [   # (slug, 제목, 부제, 소개, 고르는 방법, 표지색 2개)
    ('year-end-tax', '연말정산 한 권으로 끝내기', '공제 항목·준비 순서·환급까지', '연말정산 준비 순서, 소득공제·세액공제 항목, 간소화 자료와 환급 시기를 공식 출처 기준으로 묶었습니다.',
     {'rx': r'연말정산|세액공제|소득공제|경정청구|부양가족|기부금|환급', 'max': 16}, ('#4338ca', '#7c3aed')),
    ('resign', '퇴사할 때 챙길 것', '연차·퇴직금·건강보험·국민연금·실업급여', '퇴사 전후에 챙길 제도를 순서대로 묶었습니다. 단계마다 놓치기 쉬운 것과 공식 문의처를 함께 적었습니다.',
     {'journey': 'resign'}, ('#0f766e', '#0ea5a4')),
    ('housing', '전월세·이사 실전 가이드', '집 구하기부터 전입신고·보증금까지', '집을 구하고 계약하고 이사하는 순서대로, 전월세 계약에서 확인할 것과 보증금을 지키는 방법을 묶었습니다.',
     {'journey': 'housing'}, ('#b45309', '#ea580c')),
    ('parttime', '알바 권리 가이드', '근로계약서·주휴수당·4대보험·임금체불', '알바를 시작할 때부터 임금을 받을 때까지 알아야 할 권리와 절차를 묶었습니다.',
     {'journey': 'parttime'}, ('#be185d', '#e11d48')),
    ('money-trouble', '결제·빚 문제 해결 가이드', '환불·청약철회·채무조정', '결제 문제부터 큰 빚 문제까지, 어디에 무엇을 신청하는지 순서대로 묶었습니다.',
     {'journey': 'finance'}, ('#1d4ed8', '#0284c7')),
    ('winter-energy', '겨울 난방·에너지 가이드', '난방비·전기요금·에너지 지원 제도', '난방비와 전기요금 계산, 에너지 지원 제도, 겨울철 동파·한파 대비를 묶었습니다.',
     {'rx': r'난방|에너지|전기요금|가스요금|동파|보일러|한파', 'max': 14}, ('#9a3412', '#dc2626')),
]


def _checked(g):
    m = re.search(r'확인일\s*(\d{4}-\d{2}-\d{2})', g.get('basis') or '')
    return m.group(1) if m else ''


def _pick(spec, G, JR):
    by = {g['slug']: g for g in G}
    if spec.get('journey'):
        j = next((x for x in JR if x['slug'] == spec['journey']), None)
        return [by[s['slug']] for s in (j['steps'] if j else []) if s['slug'] in by]
    rx = re.compile(spec['rx'])
    L = [g for g in G if rx.search(g['name'] + ' ' + g['h1'])]
    L.sort(key=lambda g: (-len(rx.findall(g['name'] + ' ' + g['h1'])), g['name']))
    return L[:spec.get('max', 16)]


def _sec_html(sc, lvl=3):
    _sh = (sc.get('h') or '').strip()   # 제목 없는 섹션(앞 섹션에 덧붙인 설명)은 제목 줄 없이 잇는다
    h = f'<h{lvl}>{E(_sh)}</h{lvl}>' if _sh else ''
    if sc.get('table'):
        head, rows = sc['table'][0], sc['table'][1:]
        h += ('<table class="bk-t"><thead><tr>' + ''.join(f'<th>{E(c)}</th>' for c in head) + '</tr></thead><tbody>'
              + ''.join('<tr>' + ''.join(f'<td>{E(str(c)[1:] if isinstance(c, str) and c.startswith("*") else c)}</td>' for c in r) + '</tr>' for r in rows) + '</tbody></table>')
    if sc.get('ul'):
        tag = 'ol' if re.search(r'절차|순서|단계', _sh) else 'ul'
        h += f'<{tag}>' + ''.join(f'<li>{x}</li>' for x in sc['ul']) + f'</{tag}>'
    if sc.get('p'):
        h += f'<p>{sc["p"]}</p>'
    if sc.get('html'):
        h += sc['html']
    return h


def _chapter(n, g):
    """한 장(章) = 가이드 한 편. 본문·질문·출처를 그대로 싣고 확인일과 문의처를 장 머리에 적는다."""
    faq = ''.join(f'<dt>{E(q)}</dt><dd>{E(a)}</dd>' for q, a in g.get('faq') or [])
    src = ''.join(f'<li><a href="{E(u)}">{E(nm)}</a></li>' for nm, u in g.get('sources') or [])
    return (f'<section class="bk-ch" id="ch{n}"><p class="bk-no">{n}장</p><h2>{E(g["h1"])}</h2>'
            f'<p class="bk-meta">확인일 {E(_checked(g) or "표기 없음")} · 공식 출처 {len(g.get("sources") or [])}곳 · 문의 {E(g.get("contact") or "")}</p>'
            f'<div class="bk-lead">{E(g["lead"])}</div>'
            + ''.join(_sec_html(sc) for sc in g['sections'])
            + (f'<h3>자주 묻는 질문</h3><dl class="bk-faq">{faq}</dl>' if faq else '')
            + (f'<h3>공식 출처</h3><ul class="bk-src">{src}</ul>' if src else '')
            + f'<p class="bk-web">웹에서 최신 내용 보기: <a href="{SITE}/money/guide/{g["slug"]}/">{SITE}/money/guide/{g["slug"]}/</a></p></section>')


CSS = ('<style>.bk-cv{margin:8px 0 24px;padding:36px 28px;border-radius:12px;color:#fff}.bk-cv small{display:block;font-size:13px;font-weight:700;opacity:.85;letter-spacing:.04em}.bk-cv h1{margin:10px 0 8px;font-size:clamp(28px,6vw,40px);line-height:1.25;color:#fff;border:0}'
       '.bk-cv p{margin:0;font-size:16px;opacity:.92}.bk-cv .ed{margin-top:22px;font-size:13px;opacity:.85}'
       '.bk-dl{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}main .bk-dl a{display:inline-flex;align-items:center;min-height:44px;padding:0 16px;border:1px solid var(--bd,#e2e8f0);border-radius:8px;background:var(--card,#fff);color:var(--tx,#0f172a);font-weight:700;font-size:14.5px;text-decoration:none}main .bk-dl a.p{background:var(--brand,#6d28d9);border-color:var(--brand,#6d28d9);color:#fff}'
       '.bk-pre{padding:14px 16px;border:1px solid var(--bd,#e2e8f0);border-radius:8px;background:var(--card,#fff);font-size:14.5px;line-height:1.7;color:var(--mu,#475569)}'
       '.bk-toc{list-style:none;margin:8px 0 28px;padding:0;border-top:1px solid #cbd5e1;counter-reset:c}.bk-toc li{border-bottom:1px solid var(--bd,#e2e8f0)}main .bk-toc a{display:flex;gap:12px;padding:12px 2px;color:var(--tx,#0f172a);text-decoration:none;font-size:15.5px;line-height:1.5}.bk-toc a b{flex:0 0 auto;width:34px;color:var(--mu,#64748b);font-weight:700}.bk-toc a:hover span{text-decoration:underline}'
       '.bk-ch{margin:40px 0 0;padding-top:28px;border-top:2px solid var(--tx,#0f172a)}.bk-no{margin:0;font-size:13px;font-weight:800;color:var(--brand,#6d28d9);letter-spacing:.04em}.bk-ch h2{margin:6px 0 8px;font-size:24px;line-height:1.35;border:0;padding:0}.bk-ch h3{margin:26px 0 8px;font-size:18px}'
       '.bk-meta{margin:0 0 12px;font-size:13.5px;color:var(--mu,#64748b)}.bk-lead{margin:0 0 8px;padding:14px 16px;border-left:3px solid var(--brand,#6d28d9);background:#faf8ff;line-height:1.75}'
       '.bk-t{border-collapse:collapse;width:100%;font-size:14.5px;margin:8px 0}.bk-t th,.bk-t td{border:1px solid var(--bd,#e2e8f0);padding:8px 10px;text-align:left;vertical-align:top;line-height:1.6}.bk-t th{background:#f8fafc;font-size:13.5px}'
       '.bk-faq dt{margin:12px 0 2px;font-weight:700}.bk-faq dd{margin:0;line-height:1.7;color:var(--mu,#475569)}.bk-src{font-size:14px}.bk-web{margin-top:14px;font-size:13px;color:var(--mu,#64748b)}'
       '.bk-col{margin:40px 0 0;padding:18px;border:1px solid var(--bd,#e2e8f0);border-radius:8px;font-size:14px;line-height:1.75;color:var(--mu,#475569)}.bk-col b{color:var(--tx,#0f172a)}'
       '.bk-g{list-style:none;margin:16px 0 0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.bk-g li{display:grid;grid-template-columns:120px minmax(0,1fr);gap:16px;padding:16px;border:1px solid var(--bd,#e2e8f0);border-radius:12px;background:var(--card,#fff)}'
       '.bk-g img{width:120px;height:auto;border-radius:6px;box-shadow:0 2px 8px rgba(15,23,42,.18)}.bk-g h2{margin:0 0 4px;font-size:18px;line-height:1.35;border:0;padding:0}main .bk-g h2 a{color:inherit;text-decoration:none}.bk-g h2 a:hover{text-decoration:underline}.bk-g p{margin:0 0 6px;font-size:14px;line-height:1.6;color:var(--mu,#475569)}.bk-g small{display:block;font-size:12.5px;color:#64748b;margin-bottom:8px}.bk-g .bk-dl{margin:0}.bk-g .bk-dl a{min-height:40px;padding:0 12px;font-size:13.5px}'
       '@media(max-width:700px){.bk-g{grid-template-columns:1fr}.bk-g li{grid-template-columns:88px minmax(0,1fr);gap:12px;padding:14px}.bk-g img{width:88px}.bk-cv{padding:28px 20px}}'
       '@media print{.bk-dl,.bc{display:none!important}.bk-cv{break-after:page;min-height:230mm;display:flex;flex-direction:column;justify-content:center;-webkit-print-color-adjust:exact;print-color-adjust:exact}.bk-toc{break-after:page}.bk-ch{break-before:page;border:0;margin:0;padding:0}.bk-t{font-size:9.5pt}.bk-col{break-before:page}main a[href^="http"]:after{content:""!important}}</style>')


def _cover(root, slug, title, sub, colors):
    """표지 그림(600×840). 제목이 바뀔 때만 다시 그린다."""
    out = os.path.join(root, 'book', 'cover'); os.makedirs(out, exist_ok=True)
    key = hashlib.md5(json.dumps([title, sub, colors], ensure_ascii=False).encode()).hexdigest()[:8]
    f = os.path.join(out, f'{slug}-{key}.png'); rel = f'/book/cover/{slug}-{key}.png'
    if os.path.exists(f):
        return rel
    for old in os.listdir(out):
        if old.startswith(slug + '-'):
            os.remove(os.path.join(out, old))
    from PIL import Image, ImageDraw
    import widget as W
    w, h = 600, 840
    c1, c2 = (tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in colors)
    im = Image.new('RGB', (w, h)); px = im.load()
    for y in range(h):
        t = y / (h - 1); col = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))
        for x in range(w):
            px[x, y] = col
    d = ImageDraw.Draw(im)
    d.text((48, 56), '루리 줍줍 가이드북', font=W._font(24, True), fill=(255, 255, 255))
    d.line((48, 100, 120, 100), fill=(255, 255, 255), width=3)
    y = 250
    words, line = title.split(' '), ''
    for wd in words + ['']:
        test = (line + ' ' + wd).strip()
        if wd and d.textlength(test, font=W._font(54, True)) <= w - 96:
            line = test; continue
        if line:
            d.text((48, y), line, font=W._font(54, True), fill=(255, 255, 255)); y += 72
        line = wd
    y += 14
    line = ''
    for ch_ in sub + '\n':
        if ch_ != '\n' and d.textlength(line + ch_, font=W._font(24)) <= w - 96:
            line += ch_; continue
        d.text((48, y), line, font=W._font(24), fill=(255, 255, 255)); y += 36; line = '' if ch_ == '\n' else ch_
    d.text((48, h - 96), '공식 출처와 확인일을 적어 정리한 무료 전자책', font=W._font(20), fill=(255, 255, 255))
    d.text((48, h - 62), 'sungprofile.cloud', font=W._font(20, True), fill=(255, 255, 255))
    im.save(f, 'PNG', optimize=True)
    return rel


def _xhtml(frag):
    """EPUB 용: HTML 조각을 형식이 맞는 XHTML 로 바꾸고, 전자책 뷰어가 못 다루는 요소(스크립트·SVG·입력 칸)는 뺀다."""
    import lxml.html
    from lxml import etree
    el = lxml.html.fragment_fromstring(frag, create_parent='div')
    for bad in el.xpath('.//script|.//style|.//svg|.//canvas|.//iframe|.//button|.//input|.//select|.//form|.//noscript'):
        p = bad.getparent()
        if p is not None:
            p.remove(bad)
    for a in el.xpath('.//a[@href]'):
        if a.get('href', '').startswith('/'):
            a.set('href', SITE + a.get('href'))
        for k in ('target', 'rel', 'onclick'):
            if k in a.attrib:
                del a.attrib[k]
    for x in el.iter():
        for k in list(x.attrib):
            if k.startswith('on') or k in ('loading', 'decoding', 'data-l', 'style'):
                del x.attrib[k]
    s = etree.tostring(el, method='xml', encoding='unicode')
    return re.sub(r'^<div>|</div>$', '', s)


def _epub(root, slug, title, sub, desc, chapters, cover_rel, edition):
    out = os.path.join(root, 'book', 'files'); os.makedirs(out, exist_ok=True)
    f = os.path.join(out, slug + '.epub')
    uid = 'urn:uuid:' + hashlib.md5(('jupjup-book-' + slug).encode()).hexdigest()
    uid = uid[:17] + '-' + uid[17:21] + '-' + uid[21:25] + '-' + uid[25:29] + '-' + uid[29:41]
    css = ('body{font-family:sans-serif;line-height:1.7;margin:1em}h1{font-size:1.6em}h2{font-size:1.35em;margin-top:1.2em}h3{font-size:1.12em;margin-top:1.2em}'
           'table{border-collapse:collapse;width:100%;font-size:.9em}th,td{border:1px solid #999;padding:.35em .5em;text-align:left;vertical-align:top}th{background:#eee}'
           '.bk-no{font-weight:bold;color:#6d28d9}.bk-meta,.bk-web{font-size:.85em;color:#555}.bk-lead{border-left:3px solid #6d28d9;padding:.5em .8em;background:#f6f3ff}dt{font-weight:bold;margin-top:.8em}dd{margin:0}')
    wrap = lambda t, body: ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="ko" xml:lang="ko"><head><meta charset="utf-8"/>'
                            f'<title>{E(t)}</title><link rel="stylesheet" href="style.css"/></head><body>{body}</body></html>')
    files = [('cover.xhtml', wrap(title, f'<div style="text-align:center"><img src="cover.png" alt="{E(title)} 표지" style="max-width:100%"/></div>')),
             ('intro.xhtml', wrap('이 책에 대하여', f'<h1>{E(title)}</h1><p>{E(sub)}</p><p>{E(desc)}</p><h2>이 책에 대하여</h2><p>이 책은 {PUB}의 생활 가이드 {len(chapters)}편을 묶은 것입니다. '
                                              f'AI가 각 장 끝에 적은 공식 출처를 바탕으로 정리했고, 운영자가 한 건씩 직접 검토한 것은 아닙니다. 제도와 금액은 바뀔 수 있으니 신청 전에 공식 출처를 확인해 주세요. 법률·세무 상담이 아닙니다.</p>'
                                              f'<p>{E(edition)}</p>'))]
    for n, g in enumerate(chapters, 1):
        files.append((f'ch{n:03d}.xhtml', wrap(g['h1'], _xhtml(_chapter(n, g)))))
    files.append(('colophon.xhtml', wrap('판권', f'<h2>판권</h2><p><b>{E(title)}</b><br/>{E(edition)}<br/>펴낸 곳: {PUB} ({SITE})<br/>무료 배포 · 출처를 밝히면 자유롭게 공유할 수 있습니다.</p>')))
    nav = wrap('차례', '<nav epub:type="toc" id="toc"><h1>차례</h1><ol><li><a href="intro.xhtml">이 책에 대하여</a></li>'
               + ''.join(f'<li><a href="ch{n:03d}.xhtml">{n}장 {E(g["h1"])}</a></li>' for n, g in enumerate(chapters, 1)) + '<li><a href="colophon.xhtml">판권</a></li></ol></nav>')
    now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    man = ''.join(f'<item id="{nm.split(".")[0]}" href="{nm}" media-type="application/xhtml+xml"/>' for nm, _b in files)
    spine = ''.join(f'<itemref idref="{nm.split(".")[0]}"/>' for nm, _b in files)
    opf = ('<?xml version="1.0" encoding="utf-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bid" xml:lang="ko"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
           f'<dc:identifier id="bid">{uid}</dc:identifier><dc:title>{E(title)}</dc:title><dc:language>ko</dc:language><dc:creator>{PUB}</dc:creator><dc:publisher>{PUB}</dc:publisher>'
           f'<dc:description>{E(desc)}</dc:description><dc:date>{now[:10]}</dc:date><meta property="dcterms:modified">{now}</meta><meta name="cover" content="cover-img"/></metadata>'
           f'<manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="css" href="style.css" media-type="text/css"/>'
           f'<item id="cover-img" href="cover.png" media-type="image/png" properties="cover-image"/>{man}</manifest><spine>{spine}</spine></package>')
    body_key = hashlib.md5((opf.replace(now, '').replace(now[:10], '') + ''.join(b for _n, b in files) + nav).encode()).hexdigest()
    if os.path.exists(f) and _keys().get('epub:' + slug) == body_key:
        return '/book/files/' + slug + '.epub'   # 내용이 같으면 다시 쓰지 않는다(매 빌드마다 파일이 바뀌어 커밋이 커지지 않게)
    with zipfile.ZipFile(f, 'w') as z:
        z.writestr(zipfile.ZipInfo('mimetype'), 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml', '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>', zipfile.ZIP_DEFLATED)
        z.writestr('OEBPS/content.opf', opf, zipfile.ZIP_DEFLATED); z.writestr('OEBPS/nav.xhtml', nav, zipfile.ZIP_DEFLATED); z.writestr('OEBPS/style.css', css, zipfile.ZIP_DEFLATED)
        z.write(os.path.join(root, cover_rel.strip('/').replace('/', os.sep)), 'OEBPS/cover.png', zipfile.ZIP_DEFLATED)
        for nm, b in files:
            z.writestr('OEBPS/' + nm, b, zipfile.ZIP_DEFLATED)
    _setkey('epub:' + slug, body_key)
    return '/book/files/' + slug + '.epub'


def build(G, JR, page, root):
    """전자책 목록·읽기 화면·EPUB 을 만든다. 돌려주는 값: 사이트맵에 넣을 주소(목록 화면만)."""
    today = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date()
    made = []
    for slug, title, sub, desc, spec, colors in BOOKS:
        ch = _pick(spec, G, JR)
        if len(ch) < 3:
            continue
        cover = _cover(root, slug, title, sub, colors)
        last = max((_checked(g) for g in ch), default='') or today.isoformat()
        nsrc = sum(len(g.get('sources') or []) for g in ch)
        edition = f'{today.year}년 {today.month}월 판 · 내용 확인일 {last}까지 · {len(ch)}편 · 공식 출처 {nsrc}곳'
        try:
            epub = _epub(root, slug, title, sub, desc, ch, cover, edition)
        except Exception as e:
            print('전자책 EPUB 실패', slug, repr(e)[:100]); epub = ''
        p = f'/book/{slug}/'
        dl = ('<div class="bk-dl">' + (f'<a class="p" href="/book/files/{slug}.pdf" download>PDF 내려받기</a>' if os.path.exists(os.path.join(root, 'book', 'files', slug + '.pdf')) else '')
              + (f'<a href="{epub}" download>EPUB 내려받기</a>' if epub else '') + '<a href="/book/">다른 전자책</a></div>')
        toc = '<ol class="bk-toc">' + ''.join(f'<li><a href="#ch{n}"><b>{n}장</b><span>{E(g["h1"])}</span></a></li>' for n, g in enumerate(ch, 1)) + '</ol>'
        body = (f'<p class="bc"><a href="/">홈</a> › <a href="/book/">전자책</a> › {E(title)}</p>'
                f'<div class="bk-cv" style="background:linear-gradient(160deg,{colors[0]},{colors[1]})"><small>루리 줍줍 가이드북</small><h1>{E(title)}</h1><p>{E(sub)}</p><p class="ed">{E(edition)}</p></div>' + dl
                + f'<div class="bk-pre"><b>이 책에 대하여</b><br>{E(desc)} {PUB}의 생활 가이드 {len(ch)}편을 묶었고, AI가 각 장 끝의 공식 출처를 바탕으로 정리했습니다. 운영자가 한 건씩 직접 검토한 것은 아니며, 제도와 금액은 바뀔 수 있으니 신청 전에 공식 출처를 확인해 주세요. 법률·세무 상담이 아닙니다.</div>'
                + '<h2>차례</h2>' + toc + ''.join(_chapter(n, g) for n, g in enumerate(ch, 1))
                + f'<div class="bk-col"><b>판권</b><br>{E(title)} — {E(sub)}<br>{E(edition)}<br>펴낸 곳: {PUB} · {SITE}<br>무료 배포 · 출처를 밝히면 자유롭게 공유할 수 있습니다. 고칠 곳은 <a href="/contact/">문의</a>로 알려 주세요.</div>' + CSS)
        page(p, f'{title} — {sub} (무료 전자책)', desc, body, [('루리 줍줍', '/'), ('전자책', '/book/'), (title, p)], noindex=True)
        made.append(dict(slug=slug, title=title, sub=sub, desc=desc, n=len(ch), last=last, cover=cover, epub=epub, edition=edition))
    if not made:
        return []
    cards = ''.join(
        f'<li><a href="/book/{b["slug"]}/" tabindex="-1" aria-hidden="true"><img src="{b["cover"]}" width="120" height="168" alt="{E(b["title"])} 표지" loading="lazy"></a><div><h2><a href="/book/{b["slug"]}/">{E(b["title"])}</a></h2><p>{E(b["desc"])}</p>'
        f'<small>{b["n"]}편 · 내용 확인일 {b["last"]}까지</small><div class="bk-dl"><a class="p" href="/book/{b["slug"]}/">웹에서 읽기</a>'
        + (f'<a href="/book/files/{b["slug"]}.pdf" download>PDF</a>' if os.path.exists(os.path.join(root, 'book', 'files', b['slug'] + '.pdf')) else '')
        + (f'<a href="{b["epub"]}" download>EPUB</a>' if b['epub'] else '') + '</div></div></li>' for b in made)
    body = ('<p class="bc"><a href="/">홈</a> › 전자책</p><h1>루리 줍줍 전자책</h1>'
            f'<p class="cat-st">생활 가이드를 주제·상황별로 묶은 무료 전자책 {len(made)}권입니다. 장마다 확인일과 공식 출처를 적었고, 웹에서 읽거나 PDF·EPUB 으로 내려받을 수 있습니다.</p>'
            f'<ul class="bk-g">{cards}</ul>'
            '<h2>이 전자책은 이렇게 만듭니다</h2><ul class="gm-l"><li>새로 지어낸 글이 아니라, 사이트의 생활 가이드 본문을 그대로 묶습니다. 가이드가 고쳐지면 책도 다음 판에 반영됩니다.</li>'
            '<li>AI가 공식 출처를 바탕으로 정리했고, 운영자가 한 건씩 직접 검토한 것은 아닙니다. 장마다 확인일과 출처 주소를 적었습니다.</li>'
            '<li>무료이며, 출처를 밝히면 자유롭게 공유할 수 있습니다. 고칠 곳은 <a href="/contact/">문의</a>로 알려 주세요.</li></ul>' + CSS)
    page('/book/', '루리 줍줍 전자책 — 연말정산·퇴사·전월세 가이드북 무료 PDF·EPUB', f'연말정산, 퇴사, 전월세·이사, 알바 권리 등 생활 가이드를 묶은 무료 전자책 {len(made)}권. 장마다 확인일과 공식 출처를 적었습니다.',
         body, [('루리 줍줍', '/'), ('전자책', '/book/')])
    json.dump(made, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'books_built.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('전자책', len(made), '권', [(b['slug'], b['n']) for b in made])
    return ['/book/']


def make_pdfs(root):
    """읽기 화면(/book/<slug>/)을 PDF 로 저장한다. 화면 내용이 바뀐 책만 다시 만든다. 처음 만든 빌드에서는 PDF 단추가 다음 빌드부터 보인다."""
    import threading, http.server, socketserver, functools
    here = os.path.dirname(os.path.abspath(__file__))
    bf = os.path.join(here, 'books_built.json')
    if not os.path.exists(bf):
        return 0
    B = json.load(open(bf, encoding='utf-8'))
    out = os.path.join(root, 'book', 'files'); os.makedirs(out, exist_ok=True)
    todo = []
    for b in B:
        f = os.path.join(root, 'book', b['slug'], 'index.html')
        if not os.path.exists(f):
            continue
        doc = open(f, encoding='utf-8').read()
        m = re.search(r'<main[^>]*>(.*)</main>', doc, re.S)
        h = hashlib.md5(re.sub(r'<div class="bk-dl">.*?</div>', '', m.group(1) if m else doc, flags=re.S).encode()).hexdigest()
        h = hashlib.md5((h + open(os.path.join(root, 'assets', 'pro.css'), 'rb').read().hex()[:0] + str(os.path.getsize(os.path.join(root, 'assets', 'pro.css')))).encode()).hexdigest()   # 인쇄 모양(pro.css)이 바뀌어도 다시 만든다
        if not (os.path.exists(os.path.join(out, b['slug'] + '.pdf')) and _keys().get('pdf:' + b['slug']) == h):
            todo.append((b, h, None))
    if not todo:
        return 0
    from playwright.sync_api import sync_playwright

    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=root)); port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    n = 0
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel='msedge', headless=True); pg = br.new_context(viewport={'width': 900, 'height': 1200}, locale='ko-KR').new_page()
            for b, h, kf in todo:
                try:
                    pg.goto(f'http://127.0.0.1:{port}/book/{b["slug"]}/', wait_until='networkidle', timeout=60000); pg.wait_for_timeout(400)
                    pg.add_style_tag(content='.pc,#comments,.hd,.ft,.rc,.dd-note,.join-cta{display:none!important}*{box-shadow:none!important}')
                    pg.pdf(path=os.path.join(out, b['slug'] + '.pdf'), format='A4', print_background=True, display_header_footer=True, header_template='<span></span>',
                           footer_template=f'<div style="font-size:8px;width:100%;text-align:center;color:#888;font-family:sans-serif">{E(b["title"])} · {PUB} · <span class="pageNumber"></span>/<span class="totalPages"></span></div>',
                           margin={'top': '16mm', 'bottom': '18mm', 'left': '15mm', 'right': '15mm'})
                    _setkey('pdf:' + b['slug'], h); n += 1
                except Exception as e:
                    print('전자책 PDF 실패', b['slug'], repr(e)[:80])
            br.close()
    finally:
        srv.shutdown()
    return n
