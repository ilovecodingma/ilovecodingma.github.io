# -*- coding: utf-8 -*-
"""글에 붙이는 자료 사진 (2026-11-05 사용자 「사진들도 가져와서」「앞으로 자동으로 붙이고 출처 다 넣어」).
사진 은행(photo_bank.json)은 위키미디어 공용에서 가져와 사람이 눈으로 확인한 자유 이용 사진만 담는다(issue_img.py bank 로 추가).
빌드는 글 제목이 은행의 키워드(rx)에 맞으면 그 사진을 자동으로 붙이고, 작가·라이선스·출처 주소를 사진 아래에 적는다.
- 원고 JSON 의 "image": false → 사진 없음. "image": {…}(issue_img.py apply 가 써 넣은 값) → 그 사진. "image": "은행 key" → 그 은행 사진.
- 연예 분류와 의혹·사망·범죄 피해 글에는 자동으로 붙이지 않는다(사진이 사실처럼 읽히거나 당사자에게 누가 될 수 있어서).
- 자동 검색 결과를 그대로 쓰지 않는 이유: 검색 첫 결과가 엉뚱한 사진인 경우가 많았다(「서울고등법원」→ 옛 사진·드라마 로고)."""
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
_BANK = None
SENSITIVE = re.compile(r'의혹|폭로|학폭|별세|사망|부고|성범죄|성폭|협박|스토킹|흉기|살인|자살|극단|피해 고백|임신|이혼|열애|유출')
E = lambda t: html.escape(str(t), quote=True)


def bank():
    global _BANK
    if _BANK is None:
        f = os.path.join(HERE, 'photo_bank.json')
        _BANK = json.load(open(f, encoding='utf-8')) if os.path.exists(f) else []
        for b in _BANK:
            b['_rx'] = re.compile(b['rx'])
    return _BANK


def pick(c):
    """이슈 원고 c 에 붙일 사진 정보(dict) 또는 None."""
    im = c.get('image')
    if im is False:
        return None
    if isinstance(im, dict) and im.get('file'):
        return im
    if isinstance(im, str):
        return next((b for b in bank() if b['key'] == im), None)
    t = (c.get('h1') or '') + ' ' + (c.get('title') or '')
    if (c.get('category') or '') == '연예' or SENSITIVE.search(t):
        return None
    return next((b for b in bank() if b['_rx'].search(t)), None)


def url(p, small=False):
    f = p['file']
    return '/assets/issue/img/' + (f[:-5] + '_s.webp' if small else f)


def figure(p, eager=False):
    """본문용 사진 + 출처(자료 사진임을 밝히고 작가·라이선스·출처 주소를 적는다)."""
    cap = f'자료 사진: {E(p["alt"])} · {E(p.get("author") or "작가 미상")} · {E(p["license"])} · <a href="{E(p["source"])}" target="_blank" rel="noopener nofollow">Wikimedia Commons</a>'
    return (f'<figure class="ph"><img src="{url(p)}" width="{p.get("w", 1200)}" height="{p.get("h", 675)}" alt="{E(p["alt"])}"'
            + ('' if eager else ' loading="lazy"') + f' decoding="async"><figcaption>{cap}</figcaption></figure>')


def thumb(p):
    return f'<img class="ph-t" src="{url(p, True)}" width="160" height="90" alt="" loading="lazy" decoding="async">'


CSS = ('<style>.ph{margin:16px 0}.ph img{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;border-radius:12px;background:#e2e8f0}'
       '.ph figcaption{margin-top:6px;font-size:12.5px;line-height:1.5;color:#64748b}.ph figcaption a{color:inherit;text-decoration:underline}'
       '.ph-t{flex:0 0 auto;width:104px;height:auto;aspect-ratio:16/9;object-fit:cover;border-radius:8px;background:#e2e8f0}</style>')
