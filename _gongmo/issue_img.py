# -*- coding: utf-8 -*-
"""이슈·가이드 글에 붙일 자유 이용 사진 찾기·내려받기 (2026-11-05 사용자 「사진들도 가져와서」).
출처는 위키미디어 공용(Wikimedia Commons)만 쓴다. 라이선스가 CC0·퍼블릭 도메인·CC BY·CC BY-SA·KOGL 1유형인 사진 파일(jpg/png)만 후보로 올리고,
글에는 「자료 사진」임과 작가·라이선스·출처 주소를 함께 적는다. 인물 의혹·사건 글에는 인물 사진을 붙이지 않는다(고르는 사람이 판단).
  python -X utf8 issue_img.py search queries.json out_dir     # {"slug": "검색어"} → 후보 목록(candidates.json)과 묶음 그림(sheet_*.png)
  python -X utf8 issue_img.py apply picks.json                 # {"slug": {"n": 후보 번호, "alt": "사진 설명"}} → assets/issue/img/slug.webp + 이슈 JSON 의 image 필드
"""
import io, json, os, re, sys, time, html
import requests
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
API = 'https://commons.wikimedia.org/w/api.php'
UA = {'User-Agent': 'RuriJupjupImageFetcher/1.0 (https://sungprofile.cloud/about/)'}
OK_LIC = re.compile(r'^(CC0|Public domain|PD|CC BY(-SA)? [0-9.]+|KOGL Type 1)', re.I)
IMG_DIR = os.path.join(ROOT, 'assets', 'issue', 'img')


def clean(t):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', t or ''))).strip()


def search(q, n=8):
    r = requests.get(API, headers=UA, timeout=30, params={
        'action': 'query', 'format': 'json', 'generator': 'search', 'gsrnamespace': 6, 'gsrsearch': q + ' filetype:bitmap', 'gsrlimit': n,
        'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata', 'iiurlwidth': 1200})
    out = []
    for p in sorted((r.json().get('query') or {}).get('pages', {}).values(), key=lambda x: x.get('index', 99)):
        ii = (p.get('imageinfo') or [{}])[0]; em = ii.get('extmetadata') or {}
        lic = clean((em.get('LicenseShortName') or {}).get('value'))
        if ii.get('mime') not in ('image/jpeg', 'image/png') or not OK_LIC.match(lic) or ii.get('width', 0) < 800 or ii.get('width', 0) < ii.get('height', 0) * 1.1:
            continue   # 가로 사진만(세로·정사각은 본문 머리 사진으로 어색함)
        out.append({'title': p['title'], 'page': ii.get('descriptionurl'), 'thumb': ii.get('thumburl'), 'w': ii.get('width'), 'h': ii.get('height'), 'lic': lic,
                    'author': clean((em.get('Artist') or {}).get('value'))[:60], 'desc': clean((em.get('ImageDescription') or {}).get('value'))[:140],
                    'date': clean((em.get('DateTimeOriginal') or {}).get('value'))[:20]})
    return out


def cmd_search(qf, out):
    os.makedirs(out, exist_ok=True)
    Q = json.load(open(qf, encoding='utf-8')); C = {}
    try: font = ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf', 15)
    except Exception: font = None
    sheets, row = [], []
    for slug, q in Q.items():
        try: c = search(q)[:4]
        except Exception as e: print('검색 실패', slug, repr(e)[:80]); c = []
        C[slug] = {'q': q, 'c': c}
        W, H = 300, 200
        S = Image.new('RGB', (4 * (W + 6) + 6, H + 46), '#fff'); d = ImageDraw.Draw(S)
        d.text((6, 4), f'{slug}  ·  {q}', fill='#111', font=font)
        for i, x in enumerate(c):
            try:
                im = Image.open(io.BytesIO(requests.get(x['thumb'].replace('/1200px-', '/330px-'), headers=UA, timeout=30).content)).convert('RGB')
                im.thumbnail((W, H)); S.paste(im, (6 + i * (W + 6), 26))
                d.text((10 + i * (W + 6), 28), str(i), fill='#fff', font=font, stroke_width=3, stroke_fill='#000')
            except Exception as e:
                d.text((10 + i * (W + 6), 60), 'x', fill='#c00', font=font)
            time.sleep(0.3)
        row.append(S)
        print(slug, len(c), [x['title'][5:40] for x in c])
        time.sleep(0.5)
    for k in range(0, len(row), 6):
        part = row[k:k + 6]
        T = Image.new('RGB', (part[0].width, sum(p.height for p in part)), '#fff'); y = 0
        for p in part: T.paste(p, (0, y)); y += p.height
        T.save(os.path.join(out, f'sheet_{k // 6}.png'))
    json.dump(C, open(os.path.join(out, 'candidates.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def cmd_apply(pf, cand):
    os.makedirs(IMG_DIR, exist_ok=True)
    P = json.load(open(pf, encoding='utf-8')); C = json.load(open(cand, encoding='utf-8'))
    for slug, pk in P.items():
        x = C[slug]['c'][pk['n']]
        f = os.path.join(HERE, 'issues', slug + '.json')
        if not os.path.exists(f): print('원고 없음', slug); continue
        im = Image.open(io.BytesIO(requests.get(x['thumb'], headers=UA, timeout=60).content)).convert('RGB')
        w, h = im.size; th = int(w * 9 / 16)   # 16:9 로 가운데 자름(세로가 남을 때만)
        if h > th: top = (h - th) // 2; im = im.crop((0, top, w, top + th))
        im.thumbnail((1200, 675))
        out = os.path.join(IMG_DIR, slug + '.webp'); q = 78
        im.save(out, 'WEBP', quality=q)
        while os.path.getsize(out) > 140_000 and q > 50: q -= 8; im.save(out, 'WEBP', quality=q)
        tn = im.copy(); tn.thumbnail((320, 180)); tn.save(os.path.join(IMG_DIR, slug + '_s.webp'), 'WEBP', quality=72)
        raw = open(f, encoding='utf-8').read(); d = json.loads(raw)
        d['image'] = {'file': slug + '.webp', 'w': im.size[0], 'h': im.size[1], 'alt': pk['alt'], 'author': x['author'] or '작가 미상', 'license': x['lic'], 'source': x['page']}
        json.dump(d, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=(1 if raw.startswith('{\n "') else 2))
        print(slug, im.size, os.path.getsize(out) // 1000, 'KB', x['lic'], '|', x['author'][:30])
        time.sleep(0.5)


def cmd_bank(spec):
    """사진 은행에 추가: [{"key","dir","slug","n","alt","rx"}] — dir/candidates.json 의 slug 후보 n번을 내려받아 assets/issue/img/b-key.webp 로 두고 photo_bank.json 에 적는다(같은 key 는 덮어씀)."""
    os.makedirs(IMG_DIR, exist_ok=True)
    BF = os.path.join(HERE, 'photo_bank.json')
    B = json.load(open(BF, encoding='utf-8')) if os.path.exists(BF) else []
    cache = {}
    for it in json.load(open(spec, encoding='utf-8')):
        cf = os.path.join(it['dir'], 'candidates.json')
        C = cache.setdefault(cf, json.load(open(cf, encoding='utf-8')))
        x = C[it['slug']]['c'][it['n']]
        re.compile(it['rx'])
        im = Image.open(io.BytesIO(requests.get(x['thumb'], headers=UA, timeout=60).content)).convert('RGB')
        w, h = im.size; th = int(w * 9 / 16)
        if h > th: top = (h - th) // 2; im = im.crop((0, top, w, top + th))
        elif h < th: tw = int(h * 16 / 9); left = (w - tw) // 2; im = im.crop((left, 0, left + tw, h))
        im.thumbnail((1200, 675))
        fn = 'b-' + it['key'] + '.webp'; out = os.path.join(IMG_DIR, fn); q = 78
        im.save(out, 'WEBP', quality=q)
        while os.path.getsize(out) > 140_000 and q > 50: q -= 8; im.save(out, 'WEBP', quality=q)
        tn = im.copy(); tn.thumbnail((320, 180)); tn.save(os.path.join(IMG_DIR, fn[:-5] + '_s.webp'), 'WEBP', quality=72)
        ent = {'key': it['key'], 'rx': it['rx'], 'file': fn, 'w': im.size[0], 'h': im.size[1], 'alt': it['alt'], 'author': re.sub(r'\s*(This photo was tak.*|, fro.*|The original uploader was.*)$', '', x['author']).strip() or '작가 미상',
               'license': x['lic'], 'source': x['page'], 'commons_title': x['title']}
        B = [b for b in B if b['key'] != it['key']] + [ent]
        print(it['key'], im.size, os.path.getsize(out) // 1000, 'KB', x['lic'], '|', ent['author'])
        time.sleep(0.5)
    order = [it['key'] for it in json.load(open(spec, encoding='utf-8'))]
    B.sort(key=lambda b: order.index(b['key']) if b['key'] in order else 999)
    json.dump(B, open(BF, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    if sys.argv[1] == 'search': cmd_search(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'apply': cmd_apply(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'bank': cmd_bank(sys.argv[2])
