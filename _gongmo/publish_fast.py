# -*- coding: utf-8 -*-
"""빠른 게시 (2026-11-02 마케터 요청 「올릴 때마다 빌드·배포 대신」): 이슈 JSON 하나를 검증 → _gongmo/issues/ 에 저장 → /issue/<slug>/ 와 /issue/ 허브만 렌더 →
사이트맵 갱신 → IndexNow → 해당 파일만 커밋·푸시. 전체 빌드(10분)와 잠금(20분)을 거치지 않아 라이브까지 GitHub Pages 배포 시간(2~3분)만 걸린다.
사용: python -X utf8 publish_fast.py <JSON 경로> [--no-push]   (이슈 / 계산기(inputs·steps) / 관심 묶음(communities) 을 필드로 자동 판별)
결과: 표준 출력에 JSON 한 줄 {"ok": true, "urls": [...]} 또는 {"ok": false, "errors": [...]} (실패하면 종료 코드 1)."""
import glob, os, re, sys, json, shutil, subprocess, datetime, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SITE = 'https://sungprofile.cloud'
KEY = '5d0b54e7778c4d46a6de43d65f168163'
sys.path.insert(0, HERE)


def out(d, code=0):
    print(json.dumps(d, ensure_ascii=False))
    sys.exit(code)


def validate(c):
    e = []
    if not isinstance(c, dict):
        return ['최상위가 JSON 객체여야 해요']
    for k in ('slug', 'title', 'desc', 'h1', 'date', 'summary'):
        if not isinstance(c.get(k), str) or not c[k].strip():
            e.append(f'{k}: 비어 있거나 문자열이 아니에요')
    if isinstance(c.get('slug'), str) and not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,60}', c['slug']):
        e.append('slug: 영문 소문자·숫자·하이픈 3~61자여야 해요')
    try:
        datetime.date.fromisoformat(c.get('date', ''))
    except Exception:
        e.append('date: YYYY-MM-DD 형식이어야 해요')
    kd = c.get('keep_days', 4)
    if not isinstance(kd, int) or not 1 <= kd <= 30:
        e.append('keep_days: 1~30 사이 정수여야 해요')
    for k, n in (('confirmed', 2), ('unconfirmed', 2), ('faq', 2), ('sources', 2), ('related', 2)):
        v = c.get(k, [])
        if not isinstance(v, list) or any(not isinstance(x, (list, tuple)) or len(x) != n or not all(isinstance(y, str) and y.strip() for y in x) for x in v):
            e.append(f'{k}: [[문자열, 문자열], ...] 형태여야 해요')
    for i, x in enumerate(c.get('sources', []) if isinstance(c.get('sources'), list) else []):
        if isinstance(x, (list, tuple)) and len(x) == 2 and isinstance(x[1], str) and not x[1].startswith(('http://', 'https://')):
            e.append(f'sources[{i}]: 주소는 http(s):// 로 시작해야 해요')
    secs = c.get('sections', [])
    if not isinstance(secs, list) or any(not isinstance(s, dict) or not isinstance(s.get('h'), str) or not s['h'].strip() for s in secs):
        e.append('sections: [{h, p, ul[]}] 형태여야 해요(h 필수)')
    if not c.get('confirmed') and not c.get('sections'):
        e.append('confirmed 또는 sections 중 하나는 있어야 해요')
    if not isinstance(c.get('lury_note', ''), str):
        e.append('lury_note: 문자열이어야 해요')
    return e


def kind_of(c):
    if isinstance(c, dict) and 'inputs' in c and 'steps' in c:
        return 'calc'
    if isinstance(c, dict) and 'communities' in c:
        return 'pick'
    return 'issue'


def validate_calc(c, B):
    e = []
    for k in ('slug', 'name', 'title', 'desc', 'h1', 'lead'):
        if not isinstance(c.get(k), str) or not c[k].strip():
            e.append(f'{k}: 비어 있거나 문자열이 아니에요')
    if isinstance(c.get('slug'), str) and not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,60}', c['slug']):
        e.append('slug: 영문 소문자·숫자·하이픈 3~61자여야 해요')
    for k in ('inputs', 'steps', 'outputs', 'verify'):
        if not isinstance(c.get(k), list) or not c[k]:
            e.append(f'{k}: 비어 있지 않은 목록이어야 해요')
    if e:
        return e
    seen = [i.get('id') for i in c['inputs']]
    for st in c['steps']:
        if not B._calc_expr_ok(st.get('expr', ''), seen):
            e.append(f'steps.{st.get("id")}: 수식에 허용되지 않은 글자나 모르는 이름이 있어요')
        seen.append(st.get('id'))
    for o in c['outputs']:
        if not B._calc_expr_ok(o.get('expr', ''), seen):
            e.append(f'outputs.{o.get("label")}: 수식에 허용되지 않은 글자나 모르는 이름이 있어요')
    if not e:
        e += B._calc_verify(c)
    return e


def validate_pick(c):
    e = []
    for k in ('slug', 'title', 'desc', 'intro'):
        if not isinstance(c.get(k), str) or not c[k].strip():
            e.append(f'{k}: 비어 있거나 문자열이 아니에요')
    if isinstance(c.get('slug'), str) and not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,60}', c['slug']):
        e.append('slug: 영문 소문자·숫자·하이픈 3~61자여야 해요')
    for k in ('communities', 'guides', 'issues'):
        v = c.get(k, [])
        if not isinstance(v, list) or any(not isinstance(x, str) for x in v):
            e.append(f'{k}: 문자열 목록이어야 해요')
    return e


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', cwd=ROOT, **kw)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    push = '--no-push' not in sys.argv
    if not args or not os.path.exists(args[0]):
        out({'ok': False, 'errors': ['사용법: publish_fast.py <이슈 JSON 경로>']}, 1)
    try:
        c = json.load(open(args[0], encoding='utf-8'))
    except Exception as ex:
        out({'ok': False, 'errors': ['JSON 읽기 실패: ' + repr(ex)[:120]]}, 1)
    kind = kind_of(c)
    building = os.path.exists(os.path.join(HERE, '.lock'))   # 전체 빌드가 사이트맵을 쓰는 중이면 사이트맵은 건드리지 않는다(다음 빌드가 포함)
    import build as B
    errs = validate(c) if kind == 'issue' else validate_calc(c, B) if kind == 'calc' else validate_pick(c)
    if errs:
        out({'ok': False, 'kind': kind, 'errors': errs}, 1)
    warn = [f'title 에 「{w}」 표현이 있어요(방침상 피하기)' for w in ('논란', '의혹', '사망설') if w in c['title']]
    # 제목 검수(경고 수준, 2026-11-03 네이버·구글 제목 기준): 고유 제목 · 같은 키워드 2회 이상 반복 금지 · 홍보 문구 금지
    import re as _re
    _tt = c['title']
    for _w in sorted({w for w in _re.findall(r'[가-힣A-Za-z0-9]{2,}', _tt) if len(_re.findall(_re.escape(w), _tt)) >= 2 and w not in ('2026', '2027')}):
        warn.append(f'title 에 「{_w}」가 2번 이상 들어 있어요(같은 키워드 반복 금지)')
    for _w in ('최고', '대박', '무료 증정', '지금 바로', '클릭', '꼭 보세요', '필독', '충격', '난리'):
        if _w in _tt:
            warn.append(f'title 에 홍보·자극 문구 「{_w}」가 있어요')
    _dup = [os.path.basename(p)[:-5] for d_ in ('issues', 'calcs', 'picks') for p in glob.glob(os.path.join(HERE, d_, '*.json'))
            if os.path.basename(p)[:-5] != c['slug'] and json.load(open(p, encoding='utf-8')).get('title') == _tt]
    if _dup:
        warn.append('같은 title 의 글이 이미 있어요: ' + ', '.join(_dup[:3]) + ' (고유 제목 필요)')
    sl = c['slug']
    sub = {'issue': 'issues', 'calc': 'calcs', 'pick': 'picks'}[kind]
    dst = os.path.join(HERE, sub, sl + '.json')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.abspath(args[0]) != os.path.abspath(dst):
        shutil.copyfile(args[0], dst)
    if kind == 'issue':
        urls = B.issue_json_pages(); p_ = f'/issue/{sl}/'; hub = '/issue/'; gitdirs = ['issue']
    elif kind == 'calc':
        urls = B.calc_pages(); p_ = f'/money/tools/{sl}/'; hub = '/money/tools/'; gitdirs = ['money/tools']
    else:
        urls = B.pick_pages(); p_ = f'/pick/{sl}/'; hub = '/pick/'; gitdirs = ['pick']
    if p_ not in urls:
        out({'ok': False, 'kind': kind, 'errors': ['페이지가 만들어지지 않았어요(보관 기간 경과 또는 빌드 검사 실패)']}, 1)
    new = [SITE + p_, SITE + hub]
    smap = 'sitemap-money.xml' if p_.startswith('/money/') else 'sitemap-etc.xml'
    if not building:
        today = datetime.date.today().isoformat()
        for fn in (smap, 'sitemap.xml'):
            f = os.path.join(ROOT, fn)
            if not os.path.exists(f):
                continue
            t = open(f, encoding='utf-8').read()
            add = ''.join(f'<url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n' for u in new if f'<loc>{u}</loc>' not in t)
            if add and '</urlset>' in t:
                open(f, 'w', encoding='utf-8', newline='\n').write(t.replace('</urlset>', add + '</urlset>'))
    sent = None
    try:   # IndexNow (새 주소만)
        body = json.dumps({'host': 'sungprofile.cloud', 'key': KEY, 'keyLocation': f'{SITE}/{KEY}.txt', 'urlList': new}).encode()
        ok = False
        for ep in ('https://api.indexnow.org/indexnow', 'https://searchadvisor.naver.com/indexnow'):
            try:
                urllib.request.urlopen(urllib.request.Request(ep, data=body, headers={'Content-Type': 'application/json; charset=utf-8'}), timeout=30); ok = True
            except Exception:
                pass
        sent = ok
        if ok:
            F = os.path.join(HERE, 'indexnow_sent.json')
            old = set(json.load(open(F, encoding='utf-8'))) if os.path.exists(F) else set()
            json.dump(sorted(old | set(new)), open(F, 'w', encoding='utf-8', newline=''), ensure_ascii=False, indent=1)
    except Exception:
        sent = False
    pushed = None
    if push:
        paths = gitdirs + [f'_gongmo/{sub}/{sl}.json'] + ([] if building else [smap, 'sitemap.xml'])
        r = run(['git', 'add', '--'] + paths)
        if run(['git', 'diff', '--cached', '--quiet', '--'] + paths).returncode:
            run(['git', 'commit', '-q', '-m', f'빠른 게시({kind}): {c.get("h1", sl)[:40]} ({sl})\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>', '--'] + paths)
        pr = run(['git', 'push', 'origin', 'HEAD:main'])
        pushed = pr.returncode == 0
        if not pushed:
            out({'ok': False, 'errors': ['푸시 실패(페이지는 만들었고 커밋됨, 잠시 뒤 다시 실행): ' + (pr.stderr or '')[-160:]]}, 1)
    out({'ok': True, 'kind': kind, 'urls': [SITE + p_, SITE + hub], 'indexnow': sent, 'pushed': pushed, 'sitemap_updated': not building,
         'warnings': warn, 'live_in': '푸시 후 약 2~3분(GitHub Pages 배포)'})


if __name__ == '__main__':
    main()
