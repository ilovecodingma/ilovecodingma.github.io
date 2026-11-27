# -*- coding: utf-8 -*-
"""상태창 목표 선택용 시험 목록 → assets/jam/exams.json (빌드 때마다 새로). 계열별로 가까운 회차 3개 + 문제은행 id."""
import os, sys, json, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import interest
ROOT = os.path.dirname(HERE)
TODAY = datetime.date.today().isoformat()


def main():
    bankdir = os.path.join(HERE, 'exam_data', 'bank'); live = {}
    for f in os.listdir(bankdir):
        if f.endswith('.json'):
            try:
                b = json.load(open(os.path.join(bankdir, f), encoding='utf-8'))
                if not b.get('hold') and len(b.get('questions', [])) >= 15:
                    live[f[:-5]] = b.get('name', f[:-5])
            except Exception:
                pass
    fams = []
    for k, (name, pre, banks) in interest.FAMILIES.items():
        ex = sorted([e for e in interest.exams() if interest.family_of(e['id']) == k and (e.get('exam_date') or '') >= TODAY], key=lambda e: e['exam_date'])[:3]
        bk = [b for b in banks if b in live]
        if not ex and not bk:
            continue
        fams.append({'k': k, 'name': name, 'banks': bk, 'exams': [{'id': e['id'], 'name': e['name'], 'date': e['exam_date'], 'reg_end': e.get('reg_end') or ''} for e in ex]})
    out = os.path.join(ROOT, 'assets', 'jam', 'exams.json')
    json.dump({'built': TODAY, 'fams': fams}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('jam_exams', len(fams), '계열', sum(len(f['exams']) for f in fams), '회차')


if __name__ == '__main__':
    main()
