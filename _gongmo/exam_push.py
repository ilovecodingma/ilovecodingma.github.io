# -*- coding: utf-8 -*-
"""「잠이 오냐」 관심 기준 웹푸시 발송 (2026-11-27). push.py 의 q·send·log·KEY 를 그대로 쓴다(개인키는 PC 에만).
구독은 /app/ → 워커 /api/push/sub → D1 push_subs(exams·topics·sch·qz·nw·qh). 시험 id ↔ 문제은행 매핑표와 분야 목록은 interest.py 맨 위(FAMILIES·FIELDS).
사용: python exam_push.py sched   → 관심 시험 접수 시작·마감·시험일 D-7/3/1/0 + 관심 분야(돈·주거·공모전) 마감 D-3/1/0 (하루 1통, 아침 09:10)
      python exam_push.py quiz    → 오늘의 문제 1개. 구독자가 고른 시각(qh)에 맞춰 매시 정각 실행
      python exam_push.py news    → 관심 시험 새 글 + 관심 분야 새 소식(자기개발·돈·주거·노동·공모전·이슈·식단), 저녁 19:10
      --dry                       → 보낼 내용만 출력(발송·기록 없음)
      --demo                      → D1 을 건드리지 않고 가짜 구독 몇 개로 출력 확인(--dry 와 함께)
      --today YYYY-MM-DD / --hour N → dry 에서 날짜·시각 흉내
처음 news 를 돈 날은 지금 올라온 항목을 '이미 본 것'으로만 기록한다."""
import os, sys, json, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import interest as I
STATE = os.path.join(HERE, 'exam_push_state.json')
DEMO = [   # --demo 용 가짜 구독(개인정보 아님)
    {'endpoint': 'demo-1', 'exams': 'toeic,civil,korhist', 'topics': 'money,house,issue', 'sch': 1, 'qz': 1, 'nw': 1, 'qh': 8},
    {'endpoint': 'demo-2', 'exams': 'gisa,itcert,csat', 'topics': 'dev,job,contest,health', 'sch': 1, 'qz': 1, 'nw': 1, 'qh': 8},
    {'endpoint': 'demo-3', 'exams': 'realtor,socialw,carework', 'topics': 'money', 'sch': 1, 'qz': 1, 'nw': 1, 'qh': 21}]


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'sched'
    dry, demo = '--dry' in sys.argv, '--demo' in sys.argv
    today = datetime.date.fromisoformat(arg('--today')) if arg('--today') else datetime.date.today()
    hour = int(arg('--hour')) if arg('--hour') else datetime.datetime.now().hour
    if demo and not dry:
        sys.exit('--demo 는 --dry 와 같이만 쓴다')
    P = None
    if not demo:
        import push as P   # pywebpush·D1 토큰은 실제 구독을 읽을 때만 필요
        subs = [s for s in P.q('SELECT endpoint, p256dh, auth, exams, topics, sch, qz, nw, qh FROM push_subs WHERE exams IS NOT NULL OR topics IS NOT NULL')]
    else:
        subs = DEMO
    st = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {}
    seen = st.setdefault('seen', {})

    def out(sub, msg):
        if dry:
            print(f'  [{mode}] {msg["title"]}\n       {msg["body"].replace(chr(10), " / ")}  → {msg["url"]}')
            return 1
        return int(P.send(sub, msg, False))

    ok = 0
    print(f'== {mode} 구독 {len(subs)} / {today}{" (dry)" if dry else ""}')
    if mode == 'sched':
        for s in subs:
            if s['sch'] == 0:
                continue
            evs = I.exam_events(I.csv(s['exams']), today) + I.field_deadlines(I.csv(s['topics']), today)
            evs.sort(key=lambda e: e['n'])
            if evs:
                ok += out(s, I.sched_msg(evs))
    elif mode == 'quiz':
        for s in subs:
            if s['qz'] == 0 or int(s['qh'] if s['qh'] is not None else 8) != hour:
                continue
            z = I.pick_quiz(I.csv(s['exams']), today, s['endpoint'])
            if z:
                ok += out(s, I.quiz_msg(z, today, s['endpoint']))
    elif mode == 'quest':   # 가입 회원의 목표(상태창)에 맞는 오늘의 퀘스트 — 구독자가 고른 시각(qh)에 매시 정각
        for s in quest_subs(P, demo):
            if int(s['qh'] if s['qh'] is not None else 8) != hour:
                continue
            m = quest_msg(s.get('prefs') or {}, today)
            if m:
                ok += out(s, m)
    elif mode == 'news':
        # 본 목록 갱신: 분야별 현재 항목을 한 번만 계산
        cur = {}
        for t in I.FIELDS:
            if t in ('health', 'issue'):
                continue
            cur[t] = I.field_news_all(t, today)
        cur['art'] = I.article_new(set(I.FAMILIES))
        if demo:   # 시험 출력용: 각 분야 앞쪽 2건을 '새 것'으로 흉내
            seen = {k: [x[0] for x in v[2:]] for k, v in cur.items()}; st['issue'] = ''
        first = not seen
        new = {k: [x for x in v if x[0] not in set(seen.get(k, []))] for k, v in cur.items()}
        print('새 항목', {k: len(v) for k, v in new.items()}, '(첫 실행: 기록만)' if first else '')
        iz = I.issue_today(); iss_new = bool(iz) and iz['date'] != st.get('issue')
        if not first:
            for s in subs:
                if s['nw'] == 0:
                    continue
                fams, tops = set(I.csv(s['exams'])), I.csv(s['topics'])
                arts = [x for x in new['art'] if x[3] in fams]
                if arts:
                    ok += out(s, I.article_msg(arts))
                for t in tops:
                    if t in new and new[t]:
                        ok += out(s, I.news_msg(t, new[t]))
                    elif t == 'issue' and iss_new:
                        ok += out(s, I.issue_msg(iz))
                    elif t == 'health':
                        pk = health_pick(P, today, st)
                        if pk:
                            ok += out(s, pk)
        if not dry:
            for k, v in cur.items():
                seen[k] = sorted(set(seen.get(k, [])) | {x[0] for x in v})[-3000:]
            if iz:
                st['issue'] = iz['date']
    if not dry:
        st['last_' + mode] = datetime.datetime.now().isoformat(timespec='minutes')
        json.dump(st, open(STATE, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'보냄 {ok}')


ROOT = os.path.dirname(HERE)
QDEMO = [{'endpoint': 'demo-q1', 'qh': 8, 'prefs': {'job': 'corp', 'goal': 'exam:korcham', 'gdate': '2027-01-11', 'gstart': '2026-11-20'}},
         {'endpoint': 'demo-q2', 'qh': 8, 'prefs': {'job': 'seeker', 'goal': 'exam:toeic', 'gdate': '2026-12-20', 'gstart': '2026-11-01'}}]


def quest_subs(P, demo):
    """푸시 구독 중 목표(user_prefs)가 있는 회원. 개인정보는 읽지 않고 job·goal·gdate·gstart 만 쓴다."""
    if demo:
        return QDEMO
    out = []
    for r in P.q('SELECT ps.endpoint, ps.p256dh, ps.auth, ps.qh, up.data FROM push_subs ps JOIN user_prefs up ON up.user_id = ps.uid WHERE ps.uid IS NOT NULL'):
        try:
            d = json.loads(r['data'] or '{}')
        except Exception:
            continue
        if d.get('goal') and d.get('gdate'):
            r['prefs'] = {k: d.get(k, '') for k in ('job', 'goal', 'gdate', 'gstart')}
            out.append(r)
    return out


def _goal(gid):
    """상태창(assets/jam/stat.js)과 같은 규칙: 'exam:<계열>' 은 시험 데이터로 즉석 플랜, 나머지는 goals.json"""
    if gid.startswith('exam:'):
        X = json.load(open(os.path.join(ROOT, 'assets', 'jam', 'exams.json'), encoding='utf-8'))
        f = next((x for x in X['fams'] if 'exam:' + x['k'] == gid), None)
        if not f:
            return None
        u = f'/exam/bank/{f["banks"][0]}/' if f['banks'] else '/exam/bank/'
        return {'name': f['name'] + ' 시험', 'phases': [
            {'name': '개념 잡기', 'share': .35, 'tasks': [{'t': '문제 5개 풀고 풀이를 읽어라', 'url': u}, {'t': '시험 일정부터 확인해라', 'url': '/exam/'}]},
            {'name': '문제 풀이', 'share': .4, 'tasks': [{'t': '문제 15개 풀어라. 틀린 건 다시', 'url': u}]},
            {'name': '실전 감각', 'share': .25, 'tasks': [{'t': '시간제로 문제 25개 풀어라', 'url': u}]}]}
    G = json.load(open(os.path.join(ROOT, 'assets', 'jam', 'goals.json'), encoding='utf-8'))
    return next((g for g in G['goals'] if g['id'] == gid), None)


def quest_msg(p, today):
    try:
        g = _goal(p['goal'])
        end = datetime.date.fromisoformat(p['gdate'])
        st = datetime.date.fromisoformat(p['gstart']) if p.get('gstart') else today
    except Exception:
        return None
    left = (end - today).days
    if not g or left < 0:
        return None
    f = max(0, min(.9999, (today - st).days / max(1, (end - st).days)))
    acc = 0
    ph = g['phases'][-1]
    for x in g['phases']:
        acc += x['share']
        if f < acc:
            ph = x
            break
    tasks = ph['tasks'][:3]
    body = '\n'.join('□ ' + t['t'] for t in tasks) + f'\n안 하면 생존 확률이 깎인다.'
    return {'title': f'퀘스트 도착 · {g["name"]} D-{left}', 'body': body, 'url': (tasks[0].get('url') or '/me/') + '?src=push_quest', 'tag': 'jam-quest'}


def health_pick(P, today, st):
    """식단·건강: 점심·저녁 메뉴 잔소리(push.pick_menu). dry/demo 에선 push 가 없어도 건너뛴다."""
    try:
        if P is None:
            import push as P
        slot = '점심' if datetime.datetime.now().hour < 15 else '저녁'
        pk = P.pick_menu(slot, st.get('meal_hist', [])[-7:])
        if not pk:
            return None
        _, n, e, m, why, sl = pk
        return {'title': f'오늘 {slot} 또 대충 때울래? 뭐 먹을지도 모르냐', 'body': f'{e} {n} · {m}분. 먹고 5분은 움직여라.', 'url': f'/fridge/r/{sl}/?src=push_nw', 'tag': 'jam-nw-health'}
    except Exception as ex:
        print('식단 건너뜀', repr(ex)[:80])
        return None


if __name__ == '__main__':
    main()
