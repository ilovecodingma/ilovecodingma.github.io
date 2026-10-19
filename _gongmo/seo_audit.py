# -*- coding: utf-8 -*-
"""전체 페이지 기술 SEO 점검 (2026-10-19 SEO·홍보 지침 P0). 빌드 결과 HTML을 읽어
title/description 고유성·길이, canonical, OG/Twitter, JSON-LD 파싱, noindex 분리, 내부 링크, 이미지 alt 를 센다.
결과: _gongmo/seo_audit.md (비공개, .gitignore). 실행: python seo_audit.py [--live 20]  (--live N: 무작위 N개 주소 실제 HTTP 상태 확인)"""
import collections, json, os, random, re, sys, html
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SITE = 'https://sungprofile.cloud'
SKIP = ('admin', 'me', 'assets', 'w', 'community')


def pages():
    for f in ROOT.rglob('index.html'):
        rel = f.relative_to(ROOT).parts
        if rel[0] in SKIP or rel[0].startswith(('_', '.')):
            continue
        yield '/' + '/'.join(rel[:-1]) + ('/' if len(rel) > 1 else ''), f


def meta(doc, name, attr='name'):
    m = re.search(rf'<meta {attr}="{re.escape(name)}" content="([^"]*)"', doc)
    return html.unescape(m.group(1)) if m else None


def main():
    P, T, D = {}, collections.defaultdict(list), collections.defaultdict(list)
    prob = collections.defaultdict(list)
    links = collections.Counter()
    for u, f in pages():
        doc = f.read_text(encoding='utf-8', errors='ignore')
        head = doc[:12000]
        noidx = 'noindex' in head
        t = re.search(r'<title>([^<]*)</title>', head)
        t = html.unescape(t.group(1)).strip() if t else ''
        d = meta(head, 'description') or ''
        can = re.search(r'<link rel="canonical" href="([^"]+)"', head)
        P[u] = noidx
        if not noidx:
            T[t].append(u); D[d].append(u)
            if not t: prob['title 없음'].append(u)
            elif len(t) > 70: prob['title 70자 초과(검색 결과에서 잘림)'].append(u)
            if not d: prob['description 없음'].append(u)
            elif len(d) < 40: prob['description 40자 미만'].append(u)
            elif len(d) > 160: prob['description 160자 초과'].append(u)
            if not can: prob['canonical 없음'].append(u)
            elif can.group(1) != SITE + u: prob['canonical 이 자기 주소와 다름'].append(f'{u} → {can.group(1)}')
            for k in ('og:title', 'og:description', 'og:image', 'og:url'):
                if meta(head, k, 'property') is None: prob[f'{k} 없음'].append(u)
            if meta(head, 'twitter:card') is None: prob['twitter:card 없음'].append(u)
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', doc, re.S):
            try:
                json.loads(m.group(1))
            except Exception as e:
                prob['JSON-LD 파싱 실패'].append(f'{u} ({str(e)[:40]})')
        for m in re.finditer(r'<img\b[^>]*>', doc):
            if 'alt=' not in m.group(0): prob['img alt 속성 없음'].append(u); break
        for m in re.finditer(r'href="(/[^"#?]*)', doc):
            links[m.group(1)] += 1
    for k, v in T.items():
        if len(v) > 1: prob['title 중복'].append(f'「{k[:40]}」 {len(v)}곳: ' + ', '.join(v[:3]))
    for k, v in D.items():
        if k and len(v) > 1: prob['description 중복'].append(f'{len(v)}곳: ' + ', '.join(v[:3]))
    rb = (ROOT / 'robots.txt').read_text(encoding='utf-8')
    for px in ('/admin/', '/me/'):
        if f'Disallow: {px}' not in rb: prob['robots.txt 에 비공개 경로 차단 없음'].append(px)
    live = []
    if '--live' in sys.argv:
        import requests
        n = int(sys.argv[sys.argv.index('--live') + 1])
        for u in random.sample([u for u in P if not P[u]], min(n, len(P))) + ['/없는-주소-점검/']:
            try:
                live.append((u, requests.get(SITE + u, timeout=20, allow_redirects=False).status_code))
            except Exception as e:
                live.append((u, repr(e)[:40]))
    n_idx = sum(1 for v in P.values() if not v)
    out = [f'# SEO 점검 ({__import__("datetime").datetime.now():%Y-%m-%d %H:%M})', f'- 페이지 {len(P)}개 · 색인 대상 {n_idx}개 · 색인 제외 {len(P) - n_idx}개', '']
    for k, v in sorted(prob.items(), key=lambda kv: -len(kv[1])):
        out.append(f'## {k}: {len(v)}건'); out += [f'- {x}' for x in v[:8]]; out.append('')
    if live:
        out.append('## 실제 HTTP 상태 (무작위 표본)'); out += [f'- {u} → {s}' for u, s in live]
    (HERE / 'seo_audit.md').write_text('\n'.join(out), encoding='utf-8')
    print('\n'.join(out[:3]))
    for k, v in sorted(prob.items(), key=lambda kv: -len(kv[1])):
        print(f'{k}: {len(v)}')
    if live:
        print('HTTP', collections.Counter(s for _, s in live))
    return prob


if __name__ == '__main__':
    main()
