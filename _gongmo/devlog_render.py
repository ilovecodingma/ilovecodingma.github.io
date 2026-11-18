# -*- coding: utf-8 -*-
"""업무일지 그림(PNG) 만들기. 사용: python -X utf8 devlog_render.py YYYY-MM-DD
입력 _gongmo/devlog/YYYY-MM-DD.json = {"date":..., "sessions":[{"name":..., "did":[...], "result":[...], "blocked":[...], "next":[...]}]}
출력 _gongmo/devlog/img/YYYY-MM-DD.png (세션마다 한 줄 카드: 한 일 → 결과, 막힌 것·내일). 개인정보는 입력 단계에서 가린다."""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W = 1600
COL = [(37, 99, 235), (22, 163, 74), (217, 119, 6), (147, 51, 234), (220, 38, 38), (8, 145, 178), (101, 163, 13), (219, 39, 119)]
F = lambda sz, b=False: ImageFont.truetype(r'C:\Windows\Fonts\malgunbd.ttf' if b else r'C:\Windows\Fonts\malgun.ttf', sz)


def wrap(d, text, font, width):
    out, cur = [], ''
    for ch in str(text):
        if d.textlength(cur + ch, font=font) > width:
            out.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def render(day):
    jp = os.path.join(HERE, 'devlog', day + '.json')
    data = json.load(open(jp, encoding='utf-8'))
    ses = data.get('sessions', [])
    probe = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    f_t, f_b, f_s = F(26, True), F(21), F(18)
    cards = []
    for i, s in enumerate(ses):
        lines = []
        for lab, key in (('한 일', 'did'), ('결과', 'result'), ('막힌 것', 'blocked'), ('내일', 'next')):
            v = s.get(key) or []
            if isinstance(v, str):
                v = [v]
            for t in v[:4]:
                for j, ln in enumerate(wrap(probe, t, f_b, W - 330)):
                    lines.append((lab if j == 0 else '', ln))
        cards.append((s.get('name', '?'), lines, COL[i % len(COL)]))
    H = 150 + sum(max(70, 36 + 30 * len(l)) + 14 for _, l, _ in cards) + 40
    im = Image.new('RGB', (W, H), (248, 250, 252)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 110), fill=(15, 23, 42))
    d.text((40, 24), f'{day} 업무일지', font=F(40, True), fill='white')
    d.text((40, 76), f'루리 줍줍 · 세션 {len(cards)}곳이 하루 동안 한 일', font=f_s, fill=(203, 213, 225))
    y = 130
    for name, lines, c in cards:
        h = max(70, 36 + 30 * len(lines))
        d.rounded_rectangle((30, y, W - 30, y + h), 14, fill='white', outline=(226, 232, 240), width=2)
        d.rounded_rectangle((30, y, 250, y + h), 14, fill=c)
        d.text((48, y + h // 2 - 16), name, font=f_t, fill='white')
        ty = y + 18
        for lab, ln in lines:
            if lab:
                d.text((270, ty), lab, font=f_s, fill=c)
            d.text((350, ty), ln, font=f_b, fill=(30, 41, 59))
            ty += 30
        y += h + 14
    os.makedirs(os.path.join(HERE, 'devlog', 'img'), exist_ok=True)
    out = os.path.join(HERE, 'devlog', 'img', day + '.png')
    im.save(out)
    print('저장', out, im.size)


if __name__ == '__main__':
    render(sys.argv[1])
