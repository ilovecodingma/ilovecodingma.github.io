# -*- coding: utf-8 -*-
"""홈(/) 수험 중심 화면 (2026-11-25 사용자 「메인은 수험」「교육 집중으로 쭉 개편」).
섹션: 다가오는 시험 · 문제은행 · 시험 글 · 수험생 스펙(공모전) · 수험생 식단 · 위키(생활 정보)."""
import datetime
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
E = html.escape


def _exists(u):
    return os.path.exists(os.path.join(ROOT, u.strip('/'), 'index.html'))


def _upcoming(n=8):
    try:
        import exam
        ex = exam._load()
    except Exception:
        return []
    today = datetime.date.today()
    out = []
    for x in ex:
        d = x.get('exam_date') or ''
        try:
            dd = datetime.date.fromisoformat(d[:10])
        except ValueError:
            continue
        if dd >= today and _exists(f'/exam/{x["id"]}/'):
            out.append(((dd - today).days, x))
    out.sort(key=lambda t: (t[0], t[1]['name']))
    return out[:n]


def _banks(n=6):
    d = os.path.join(HERE, 'exam_data', 'bank')
    out = []
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if not f.endswith('.json'):
            continue
        try:
            b = json.load(open(os.path.join(d, f), encoding='utf-8'))
        except Exception:
            continue
        u = f'/exam/bank/{b.get("id")}/'
        if _exists(u):
            out.append((u, b.get('name', ''), len(b.get('questions', []))))
    return out[:n]


def _articles(n=6):
    try:
        import exam_articles
        items = exam_articles._items()
    except Exception:
        return []
    return [(x['url'], x['title']) for x in items[:n]]


def _sec(sid, title, more, body):
    return (f'<section class="h2-sec" aria-labelledby="{sid}"><div class="h2-hd"><h2 id="{sid}">{title}</h2>'
            f'<a href="{more[0]}">{more[1]} →</a></div>{body}</section>')


def sections(ctx, ic):
    out = ''
    up = _upcoming()
    if up:
        li = ''
        for dday, x in up:
            tag = '오늘' if dday == 0 else f'D-{dday}'
            li += (f'<li><p class="kk">{tag} · {E(x.get("exam_date") or "")}</p><h3><a href="/exam/{E(x["id"])}/">{E(x["name"])}</a></h3>'
                   f'<p class="sm">{E(x.get("category") or "시험")}</p></li>')
        out += _sec('s-ex', '다가오는 시험', ('/exam/', '시험 일정 전체'), f'<ul class="gd-l">{li}</ul>')
    bk = _banks()
    if bk:
        li = ''.join(f'<li><p class="kk">유사문제 {n}문항</p><h3><a href="{u}">{E(nm)}</a></h3></li>' for u, nm, n in bk)
        out += _sec('s-bk', '문제은행', ('/exam/bank/', '문제은행 전체'), f'<ul class="gd-l">{li}</ul>')
    ar = _articles()
    if ar:
        li = ''.join(f'<li><h3><a href="{E(u)}">{E(t)}</a></h3></li>' for u, t in ar)
        out += _sec('s-ar', '시험 글', ('/exam/articles/', '시험 글 모음'), f'<ul class="gd-l">{li}</ul>')
    n_c = ctx.get('n_contest')
    out += _sec('s-sp', '수험생 스펙', ('/contest/', '스펙 찾기'),
                '<ul class="gd-l"><li><p class="kk">대외활동·공모전</p><h3><a href="/contest/">학생·취준생이 낼 수 있는 공모전'
                + (f' {n_c}건' if n_c else '') + '</a></h3><p class="sm">생활기록부·자기소개서·이력서에 쓸 수 있는 활동을 마감순으로 모았어요.</p></li>'
                '<li><h3><a href="/prep/">내 응모 준비 — 마감 역산 일정</a></h3></li></ul>')
    out += _sec('s-di', '수험생 식단', ('/diet/', '식단 보기'),
                '<ul class="gd-l"><li><p class="kk">시험 기간 식단</p><h3><a href="/diet/meal/">집밥 식단표</a></h3><p class="sm">공부하는 동안 속이 편하고 든든한 한 끼를 모았어요.</p></li>'
                '<li><h3><a href="/fridge/">재료로 찾는 건강 레시피</a></h3></li></ul>')
    out += _sec('s-wk', '위키 — 생활 정보', ('/wiki/', '위키 열기'),
                '<ul class="gd-l"><li><p class="kk">세금·보험·지원금</p><h3><a href="/wiki/">생활 돈 가이드·응모 가이드·개발 지식</a></h3>'
                '<p class="sm">수험과 별개로 찾는 생활 정보는 위키에 모아 두었어요.</p></li></ul>')
    return out
