# 사진 없는 레시피의 대표 이미지 (2026-10-19 서치 콘솔 「레시피 구조화 데이터 문제」: Recipe.image 필수)
# 1200x900(4:3) JPG — 메뉴 이름·조리 시간·필수 재료 사진 타일. 재료·이름이 같으면 다시 만들지 않음.
import hashlib, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'assets', 'fridge', 'rc')
FB = r'C:\Windows\Fonts\malgunbd.ttf'
FR = r'C:\Windows\Fonts\malgun.ttf'
W, H = 1200, 900


def _font(p, n):
    return ImageFont.truetype(p, n)


def _wrap(d, text, f, maxw):
    lines, cur = [], ''
    for w in text.split(' '):
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def card(r, PI):
    """r: 레시피(n, m, lv, need, opt) · PI: 재료 사진 {이름: {'f': '/assets/...'}}. 사이트 경로를 돌려줌."""
    key = hashlib.md5(('v1|' + r['n'] + '|' + ','.join(r['need'])).encode('utf-8')).hexdigest()[:12]
    fn = f'{key}.jpg'
    fp = os.path.join(OUT, fn)
    if os.path.exists(fp):
        return f'/assets/fridge/rc/{fn}'
    os.makedirs(OUT, exist_ok=True)
    im = Image.new('RGB', (W, H), '#fff7ed')
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 14], fill='#0e7490')
    d.text((60, 50), '루리의 줍줍 · 냉장고 파먹기', font=_font(FB, 34), fill='#0e7490')
    n = r['n']
    size = 104
    while size > 60:
        ft = _font(FB, size)
        L = _wrap(d, n, ft, W - 120)
        if len(L) <= 2:
            break
        size -= 8
    y = 130
    for ln in L[:2]:
        d.text((60, y), ln, font=ft, fill='#1f2937')
        y += int(size * 1.25)
    d.text((60, y + 6), f'조리 약 {r["m"]}분 · {r["lv"]} · 1~2인분', font=_font(FR, 40), fill='#7c2d12')
    # 재료 타일
    ings = (r['need'] + r['opt'])[:5]
    tw, gap = 200, 22
    x0 = 60
    ty = H - 330
    d.text((60, ty - 62), '필수 재료 ' + ', '.join(r['need'])[:40], font=_font(FR, 32), fill='#374151')
    for i, g in enumerate(ings):
        x = x0 + i * (tw + gap)
        d.rounded_rectangle([x, ty, x + tw, ty + tw], radius=24, fill='#ffffff', outline='#fed7aa', width=3)
        p = PI.get(g, {}).get('f')
        src = os.path.join(ROOT, p.lstrip('/').replace('/', os.sep)) if p else ''
        if src and os.path.exists(src):
            try:
                ph = Image.open(src).convert('RGB')
                ph.thumbnail((tw - 24, tw - 24))
                im.paste(ph, (x + (tw - ph.width) // 2, ty + (tw - ph.height) // 2))
            except Exception:
                src = ''
        if not (src and os.path.exists(src)):
            f2 = _font(FB, 40 if len(g) <= 3 else 30)
            tl = d.textlength(g[:6], font=f2)
            d.text((x + (tw - tl) / 2, ty + tw / 2 - 26), g[:6], font=f2, fill='#9a3412')
        f3 = _font(FR, 28)
        tl = d.textlength(g[:8], font=f3)
        d.text((x + (tw - tl) / 2, ty + tw + 12), g[:8], font=f3, fill='#374151')
    d.text((W - 380, H - 56), 'sungprofile.cloud/fridge', font=_font(FR, 28), fill='#9ca3af')
    im.save(fp, 'JPEG', quality=78, optimize=True, progressive=True)
    return f'/assets/fridge/rc/{fn}'
