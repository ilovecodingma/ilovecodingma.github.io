# -*- coding: utf-8 -*-
"""개발 업무일지 섹션(/devlog/): _gongmo/devlog/YYYY-MM-DD.json(세션별 한 일)과 devlog/img/YYYY-MM-DD.png(업무 그림)를 날짜별 페이지로 공개한다.
2026-11-19 사장님 지시: 매일 밤 12시에 모든 세션에게 하루 한 일을 물어 그림으로 만들어 올린다. 누구나 볼 수 있게 공개(색인 허용). 개인정보는 입력 단계에서 가린다."""
import glob
import html
import json
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape
CSS = ('<style>.dl{max-width:900px;margin:0 auto}.dl img{max-width:100%;height:auto;border:1px solid #e2e8f0;border-radius:10px}.dl h2{margin:24px 0 8px}.dl ul{padding-left:18px}.dl li{margin:4px 0;line-height:1.7}.dl .sn{font-weight:700}</style>')
SEC = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+|sk-[A-Za-z0-9_\-]{12,}|\b01[016789]-?\d{3,4}-?\d{4}\b')


def _c(s):
    return SEC.sub('[가림]', str(s))


def pages(page, root):
    days = sorted(glob.glob(os.path.join(HERE, 'devlog', '20??-??-??.json')), reverse=True)
    if not days:
        return []
    imgdir = os.path.join(root, 'devlog', 'img'); os.makedirs(imgdir, exist_ok=True)
    urls, items = [], []
    for jp in days:
        day = os.path.basename(jp)[:-5]
        try:
            data = json.load(open(jp, encoding='utf-8'))
        except Exception:
            continue
        src = os.path.join(HERE, 'devlog', 'img', day + '.png')
        has = os.path.exists(src)
        if has:
            shutil.copyfile(src, os.path.join(imgdir, day + '.png'))
        ses = data.get('sessions', [])
        txt = ''
        for s in ses:
            blk = ''
            for lab, key in (('한 일', 'did'), ('결과', 'result'), ('막힌 것', 'blocked'), ('내일', 'next')):
                v = s.get(key) or []
                v = [v] if isinstance(v, str) else v
                if v:
                    blk += f'<li><b>{lab}</b>: ' + ' / '.join(E(_c(x)) for x in v) + '</li>'
            txt += f'<h2>{E(_c(s.get("name", "?")))}</h2><ul>{blk or "<li>회신 없음</li>"}</ul>'
        body = (f'<div class="dl"><p class="bc"><a href="/">홈</a> › <a href="/devlog/">개발 업무일지</a> › {day}</p><h1>{day} 업무일지</h1>'
                + (f'<p><img src="/devlog/img/{day}.png" alt="{day} 세션별 업무 그림" loading="lazy"></p>' if has else '') + txt
                + '<p><a href="/devlog/">← 업무일지 목록</a></p></div>' + CSS)
        page(f'/devlog/{day}/', f'{day} 업무일지 — 루리 줍줍 개발', f'{day} 하루 동안 각 세션이 한 일을 그림과 글로 정리한 업무일지입니다.', body,
             [('홈', '/'), ('개발 업무일지', '/devlog/'), (day, f'/devlog/{day}/')])
        urls.append(f'/devlog/{day}/')
        items.append((day, len(ses), has))
    li = ''.join(f'<li><a href="/devlog/{d}/"><b>{d}</b> 업무일지</a> <small>세션 {n}곳</small></li>' for d, n, _ in items)
    body = ('<div class="dl"><p class="bc"><a href="/">홈</a> › 개발 업무일지</p><h1>개발 업무일지</h1>'
            '<p>루리 줍줍을 만드는 AI 세션들이 하루 동안 한 일을 매일 밤 12시에 모아 그림으로 정리합니다. 누구나 볼 수 있게 공개합니다.</p>'
            f'<ul>{li}</ul></div>' + CSS)
    page('/devlog/', '개발 업무일지 — 매일 밤 12시, 세션별 하루 한 일', '루리 줍줍을 만드는 AI 세션들의 하루 업무를 그림으로 정리해 매일 공개하는 개발 업무일지입니다.', body, [('홈', '/'), ('개발 업무일지', '/devlog/')])
    urls.append('/devlog/')
    print('개발 업무일지', len(items), '일')
    return urls
