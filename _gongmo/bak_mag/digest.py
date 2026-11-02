# -*- coding: utf-8 -*-
"""맞춤 소식 메일 (2026-10-20 사용자 「그 사람이 듣고 싶은 정보를 회원가입하면 보내 주는 서비스」).
회원이 /me/ 의 「📬 받고 싶은 소식」(user_prefs topics, dg=1)에서 고른 주제만, 소식이 있는 날에 하루 한 통. 발송은 alerts.py 와 같은 네이버 SMTP.
주제: recipe(오늘의 메뉴) · apply(새 지원금·마감 임박) · contest(마감 임박 공모전) · issue(루리 뉴스 브리핑) · game(Epic 무료·스팀 할인) · money(전문가 발언 요약) · event(오늘 마감 경품)
사용: python digest.py            → 대장 계정(sung2011103@naver.com)에게만 (시험 모드)
      python digest.py --live     → dg=1 인 모든 회원에게
      python digest.py --dry      → 보낼 내용만 출력(발송·기록 없음)"""
import os, re, sys, json, datetime, smtplib
from email.mime.text import MIMEText
from email.header import Header

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from alerts import q, smtp_pw, OWNER, SITE   # 같은 D1 조회·SMTP 금고 재사용
SENT = os.path.join(HERE, 'digest_sent.jsonl')
UTM = '?utm_source=digest&utm_medium=email&utm_campaign=digest_2610'
TODAY = datetime.date.today()
LABEL = {'recipe': '🍳 오늘의 메뉴', 'apply': '💰 지원금·청약', 'contest': '🏆 마감 임박 공모전', 'issue': '📺 루리 뉴스', 'game': '🎮 게임', 'money': '📊 전문가 말 vs 시세', 'event': '🎁 오늘 마감 경품'}


def rd(p):
    f = os.path.join(ROOT, p)
    return json.load(open(f, encoding='utf-8')) if os.path.exists(f) else None


def fr_slug(n):
    return re.sub(r'[^0-9A-Za-z가-힣]+', '-', n).strip('-')


def days(d):
    try:
        return (datetime.date.fromisoformat(d) - TODAY).days
    except Exception:
        return 999


def unesc(s):
    import html
    return html.unescape(html.unescape(s or ''))


def sec_recipe():
    pk = (rd('assets/fridge/today.json') or {}).get('picks') or []
    if not pk:
        return []
    return [(f'{n}', f'{SITE}/fridge/r/{fr_slug(n)}/') for n in pk[:3]] + [('재료로 찾기 · 분류별 레시피', SITE + '/fridge/')]


def sec_apply():
    A = rd('apply.json') or []
    soon = sorted([a for a in A if a.get('end') and not (a.get('always') or a['end'].startswith('2099')) and 0 <= days(a['end']) <= 3], key=lambda a: a['end'])[:4]
    new = [a for a in A if a.get('start') and (TODAY - datetime.date.fromisoformat(a['start'])).days <= 1 and a not in soon][:3] if A else []
    return [(f'D-{days(a["end"])} {a["title"][:40]}' if days(a['end']) else f'오늘 마감 {a["title"][:40]}', f'{SITE}/a/{a["id"]}/') for a in soon] + [(f'🆕 {a["title"][:40]}', f'{SITE}/a/{a["id"]}/') for a in new]


def sec_contest():
    C = (rd('data.json') or {}).get('items') or []
    soon = sorted([c for c in C if c.get('end') and 0 <= days(c['end']) <= 3], key=lambda c: (-(c.get('pv') or 0), c['end']))[:4]
    return [(f'{"오늘 마감" if days(c["end"]) == 0 else "D-" + str(days(c["end"]))} {c["title"][:40]}' + (f' · {c["prize"]}' if c.get('pv') else ''), f'{SITE}/c/{c["id"]}/') for c in soon]


def sec_issue():
    it = (rd('news/brief.json') or {}).get('items') or []
    return [(f'{unesc(x["headline"])[:46]} ({x["outlets"]}곳 보도)', SITE + '/news/#brief') for x in it[:3]]


def sec_game():
    g = rd('_gongmo/game_cache.json') or {}
    fr = (g.get('epic') or {}).get('free') or []
    sp = [x for x in ((g.get('steam') or {}).get('specials') or []) if x.get('off', 0) >= 50][:2]
    return [(f'🎁 Epic 무료: {x["name"]} (~{x["end"]})', SITE + '/game/') for x in fr[:2]] + [(f'🔥 스팀 {x["off"]}% 할인: {x["name"]}', SITE + '/game/') for x in sp]


def sec_money():
    n = ((rd('analyst/data.json') or {}).get('exp_meta') or {}).get('n24')
    return [(f'최근 24시간 전문가 발언 {n}건을 시세 차트와 함께 정리했어요', SITE + '/money/experts/')] if n else []


def sec_event():
    E = rd('events.json') or []
    soon = [e for e in E if e.get('end') and 0 <= days(e['end']) <= 1][:5]
    return [(f'{"오늘" if days(e["end"]) == 0 else "내일"} 마감 {unesc(e["title"])[:40]}', e['link']) for e in soon]


SEC = {'recipe': sec_recipe, 'apply': sec_apply, 'contest': sec_contest, 'issue': sec_issue, 'game': sec_game, 'money': sec_money, 'event': sec_event}


def build_mail(u, topics, cache):
    parts, first = '', ''
    for t in topics:
        if t not in SEC:
            continue
        if t not in cache:
            try:
                cache[t] = SEC[t]()
            except Exception as e:
                print('섹션 실패', t, repr(e)[:80]); cache[t] = []
        L = cache[t]
        if not L:
            continue
        first = first or L[0][0]
        lis = ''.join(f'<li style="margin:6px 0"><a href="{url}{UTM if url.startswith(SITE) else ""}" style="color:#1e1b4b;font-weight:700;text-decoration:none">{txt}</a></li>' for txt, url in L)
        parts += f'<p style="font-size:15px;font-weight:800;color:#5b21b6;margin:18px 0 4px">{LABEL[t]}</p><ul style="padding-left:18px;margin:0">{lis}</ul>'
    if not parts:
        return None, None
    body = (f'<div style="font-family:sans-serif;max-width:560px;margin:auto;padding:20px;border-radius:16px;background:#faf5ff"><p style="font-size:18px;font-weight:800;color:#5b21b6;margin:0 0 4px">{u["nick"]}님, 오늘의 소식이에요</p>'
            f'<p style="margin:0;font-size:13px;color:#6b7280">{TODAY.month}월 {TODAY.day}일 · 고르신 주제만 모았어요</p>{parts}'
            f'<p style="margin:20px 0 0"><a href="{SITE}/me/#topics" style="background:#7c3aed;color:#fff;padding:10px 16px;border-radius:10px;text-decoration:none;font-weight:700">받는 주제 바꾸기·끄기</a></p>'
            f'<p style="font-size:12px;color:#6b7280;margin-top:14px">회원가입 때 고르신 주제만 보내 드려요. 소식이 없는 날은 보내지 않아요. 정보는 공식 공고·언론 보도·공개 자료 기준이니 신청 전 원문을 확인하세요. · 루리의 줍줍</p></div>')
    return f'[루리의 줍줍] {TODAY.month}/{TODAY.day} 오늘의 소식 — {first[:30]}', body


def main():
    live, dry = '--live' in sys.argv, '--dry' in sys.argv
    users = q("SELECT u.id, u.email, u.nick, p.data FROM users u JOIN user_prefs p ON p.user_id = u.id WHERE p.data LIKE '%\"dg\":\"1\"%' AND u.banned = 0")
    sent = set()
    if os.path.exists(SENT):
        for l in open(SENT, encoding='utf-8'):
            try:
                sent.add(tuple(json.loads(l)['k']))
            except Exception:
                pass
    cache, mails = {}, []
    for u in users:
        em = u['email']
        if em.endswith('.login') or em.endswith('@example.com') or (not live and em != OWNER):
            continue
        if (u['id'], TODAY.isoformat()) in sent:
            continue
        topics = [x for x in (json.loads(u['data'] or '{}').get('topics') or '').split(',') if x]
        if not topics:
            continue
        subj, body = build_mail(u, topics, cache)
        if subj:
            mails.append((u, subj, body))
    print('소식 메일 대상', len(users), '보낼 메일', len(mails), '전체' if live else '시험 모드(대장 계정만)')
    if dry or not mails:
        for u, subj, body in mails:
            print(u['nick'], subj)
        return
    user, pw = smtp_pw()
    s = smtplib.SMTP('smtp.naver.com', 587, timeout=30)
    s.starttls()
    s.login(user, pw)
    for u, subj, body in mails:
        msg = MIMEText(body, 'html', 'utf-8')
        msg['Subject'] = Header(subj, 'utf-8')
        msg['From'] = user if '@' in user else f'{user}@naver.com'
        msg['To'] = u['email']
        msg['List-Unsubscribe'] = f'<{SITE}/me/#topics>'
        s.sendmail(msg['From'], [u['email']], msg.as_string())
        with open(SENT, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'k': [u['id'], TODAY.isoformat()]}, ensure_ascii=False) + '\n')
        print('보냄', u['nick'])
    s.quit()


if __name__ == '__main__':
    main()
