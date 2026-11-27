# -*- coding: utf-8 -*-
"""「잠이 오냐」 맞춤 메일 (2026-11-27 개편: 사용자가 고른 관심 시험·분야 기준, 하루/주 1통).
설정은 /me/ 「📬 잠이 오냐」 (user_prefs: exams=시험 계열 키, sdt=분야 키, xm=1 받기, xf=d 매일/w 월요일 1통). 계열·분야 정의는 interest.py.
한 통 구성: ① 곧 다가오는 접수·시험일(관심 시험) + 마감 임박(돈·주거·공모전) ② 오늘의 문제 1개 ③ 새 소식(시험 새 글·분야 새 항목). 소식이 하나도 없는 날은 안 보낸다.
사용: python digest.py            → 대장 계정에게만 (시험 모드)
      python digest.py --live     → xm=1 인 모든 회원에게
      python digest.py --dry      → D1 에서 읽어 보낼 건수만 출력(내용·주소 출력 없음, 발송·기록 없음)
      python digest.py --demo     → 가짜 회원 메일 내용을 텍스트로 출력(D1·SMTP 없이)
      --today YYYY-MM-DD          → 날짜 흉내
(옛 주제 메일 코드는 digest.py.bak_1127)"""
import os, re, sys, json, datetime, smtplib
from email.mime.text import MIMEText
from email.header import Header

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import interest as I
from alerts import q, smtp_pw, OWNER, SITE   # 같은 D1 조회·SMTP 금고 재사용
SENT = os.path.join(HERE, 'digest_sent.jsonl')
UTM = 'utm_source=digest&utm_medium=email&utm_campaign=jam_2611'
TODAY = datetime.date.fromisoformat(sys.argv[sys.argv.index('--today') + 1]) if '--today' in sys.argv else datetime.date.today()


def link(u):
    u = u if u.startswith('http') else SITE + u
    return (u + ('&' if '?' in u else '?') + UTM) if u.startswith(SITE) else u


def sections(exams, topics, weekly):
    """[(제목, [(글, 주소)])]"""
    win = 7 if weekly else 1
    secs = []
    soon = [(f'D-{n} {t}' if n else f'오늘 {t}', u) for n, t, u in I.exam_upcoming(set(exams), TODAY, 14 if weekly else 7)]
    dl = I.field_deadlines(topics, TODAY, (7, 3, 2, 1, 0) if weekly else (3, 1, 0))
    cnt = {}
    for e in dl:
        cnt[e['k']] = cnt.get(e['k'], 0) + 1
        if cnt[e['k']] <= 2:   # 분야마다 2건까지(한 종류가 메일을 덮지 않게)
            soon.append((f'{"오늘" if e["n"] == 0 else "D-" + str(e["n"])} {e["body"]} · {e["title"].split(".")[0]}', e['url']))
    if soon:
        secs.append(('⏰ 놓치면 니 손해다', soon[:10]))
    z = I.pick_quiz(exams, TODAY, 'mail')
    if z:
        mk = '①②③④⑤'
        secs.append(('🧠 오늘의 문제. 풀 수 있냐?', [(f'[{z["fam"]}] {I.short(z["q"].replace(chr(10), " "), 110)}  ' + ' '.join(f'{mk[i]} {I.short(c, 18)}' for i, c in enumerate(z['choices'][:5])), f'/exam/bank/{z["slug"]}/')]))
    news = []
    cut = (TODAY - datetime.timedelta(days=win)).isoformat()
    for a in I.rd(os.path.join(I.EXD, 'exam_articles.json')) or []:
        if I.family_of(a.get('exam_id') or '') in set(exams) and (a.get('date') or '') >= cut:
            news.append((I.short(a['title'], 56), a['url']))
    for t in topics:
        if t in I.SD_KIND:
            its = [i for i in I.sd_items(t) if (i.get('fetched_at') or '')[:10] >= cut]
            news += [(I.short(i['title'], 56), i['url']) for i in its[:2]]
        if t in I.APPLY_KIND:
            L = [a for a in I.rd('apply.json') or [] if a.get('kind') in I.APPLY_KIND[t] and cut <= (a.get('start') or '') <= TODAY.isoformat()]
            news += [(('새 지원금 ' if t == 'money' else '새 청약·임대 ') + I.short(a['title'], 50), f'/a/{a["id"]}/') for a in L[:2]]
        if t == 'issue':
            z2 = I.issue_today()
            if z2:
                news.append((f'오늘 이슈 {z2["n"]}건, 첫 번째: {I.short(z2["head"], 46)}. 뉴스도 안 보고 사냐', '/news/#brief'))
        if t == 'health':
            pk = (I.rd('assets/fridge/today.json') or {}).get('picks') or []
            if pk:
                news.append((f'오늘 뭐 먹냐: {", ".join(pk[:3])}. 또 대충 때우지 마라', '/fridge/'))
    if news:
        secs.append(('📰 모르고 있었지?', news[:10]))
    return secs


def build_mail(nick, exams, topics, weekly):
    secs = sections(exams, topics, weekly)
    if not secs:
        return None, None
    parts = ''.join(f'<p style="font-size:15px;font-weight:800;color:#ff7a9d;margin:18px 0 4px">{t}</p><ul style="padding-left:18px;margin:0">'
                    + ''.join(f'<li style="margin:6px 0"><a href="{link(u)}" style="color:#e8eaf2;font-weight:700;text-decoration:none">{x}</a></li>' for x, u in L) + '</ul>' for t, L in secs)
    greet = '이번 주 니 꼴이다' if weekly else '오늘 니 꼴이다'
    body = (f'<div style="font-family:sans-serif;max-width:560px;margin:auto;padding:20px;border-radius:16px;background:#11131c;color:#e8eaf2"><p style="font-size:18px;font-weight:800;color:#ff4d7d;margin:0 0 4px">{nick}, 잠이 오냐?</p>'
            f'<p style="margin:0;font-size:13px;color:#9097ad">{TODAY.month}월 {TODAY.day}일 · {greet}</p>{parts}'
            f'<p style="margin:20px 0 0"><a href="{SITE}/app/?{UTM}" style="background:#ff4d7d;color:#fff;padding:10px 16px;border-radius:10px;text-decoration:none;font-weight:700">관심 시험·분야 바꾸기 · 끄기</a></p>'
            f'<p style="font-size:12px;color:#9097ad;margin-top:14px">가난한 박과장 · 고른 것만 보낸다. 귀찮으면 끄면 된다.</p></div>')
    return f'[잠이 오냐] {TODAY.month}/{TODAY.day} {I.short(secs[0][1][0][0], 26)}', body


def main():
    live, dry, demo = '--live' in sys.argv, '--dry' in sys.argv, '--demo' in sys.argv
    if demo:
        for ex, tp, w in (('toeic,civil,korhist', 'money,house,issue', False), ('gisa,itcert,realtor', 'dev,job,contest,health', True)):
            ex, tp = ex.split(','), tp.split(',')
            subj, body = build_mail('박과장', ex, tp, w)
            print('제목:', subj)
            for t, L in sections(ex, tp, w):
                print(' ', t)
                for x, u in L:
                    print('    -', x, '→', u)
        return
    users = q("SELECT u.id, u.email, u.nick, p.data FROM users u JOIN user_prefs p ON p.user_id = u.id WHERE p.data LIKE '%\"xm\":\"1\"%' AND u.banned = 0")
    sent = set()
    if os.path.exists(SENT):
        for l in open(SENT, encoding='utf-8'):
            try:
                sent.add(tuple(json.loads(l)['k']))
            except Exception:
                pass
    mails = []
    for u in users:
        em = u['email']
        if em.endswith('.login') or em.endswith('@example.com') or (not live and em != OWNER):
            continue
        pf = json.loads(u['data'] or '{}')
        weekly = pf.get('xf') == 'w'
        if weekly and TODAY.weekday() != 0:
            continue
        if (u['id'], TODAY.isoformat(), 'x') in sent:
            continue
        ex, tp = I.csv(pf.get('exams')), I.csv(pf.get('sdt'))
        if not ex and not tp:
            continue
        subj, body = build_mail(u['nick'], ex, tp, weekly)
        if subj:
            mails.append((u, subj, body))
    print('잠이 오냐 메일 대상', len(users), '보낼 메일', len(mails), '전체' if live else '시험 모드(대장 계정만)')
    if dry or not mails:
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
        msg['List-Unsubscribe'] = f'<{SITE}/app/>'
        s.sendmail(msg['From'], [u['email']], msg.as_string())
        with open(SENT, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'k': [u['id'], TODAY.isoformat(), 'x']}, ensure_ascii=False) + '\n')
        print('보냄', u['id'])
    s.quit()


if __name__ == '__main__':
    main()
