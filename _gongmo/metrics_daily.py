# -*- coding: utf-8 -*-
"""성과 측정 일일 기록 (2026-10-23 Growth Engine 지시 5번).
새 API 호출 없이, 이미 매일 만들어지는 파일에서 숫자만 모아 metrics_log.jsonl 에 하루 한 줄(같은 날짜는 덮어씀)로 쌓는다.
  - 서치콘솔: gsc_daily.json (gsc.py)        → 노출·클릭·CTR·평균순위·검색어/페이지 수, 사이트맵 제출 수
  - 색인:     index_history.jsonl (index_watch.py) 의 마지막 줄 → 색인·발견됨·모름, gsc_pages.json 표본 색인율
  - 재방문:   retention.json (retention.py)
  - 사이트:   sitemap.xml 주소 수, 색인 제외(noindex) 수, 주제별 페이지 수
측정 불가는 null 로 남긴다(광고 수익: 애드센스 승인·API 없음 / 구독 전환: D1 읽기 한도 때문에 여기선 읽지 않음).
사용: python metrics_daily.py [--show]
"""
import json, os, re, sys, datetime, collections

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG = os.path.join(HERE, 'metrics_log.jsonl')
PROMO = os.path.expanduser(r'~\tools\promo_share')


def jl(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None


def last_line(p):
    try:
        L = [l for l in open(p, encoding='utf-8').read().splitlines() if l.strip()]
        return json.loads(L[-1]) if L else None
    except Exception:
        return None


def collect():
    today = datetime.date.today().isoformat()
    row = {'date': today}
    g = jl(os.path.join(HERE, 'gsc_daily.json')) or {}
    qs, ps = g.get('queries') or [], g.get('pages') or []
    imp = sum(q.get('impr', 0) for q in qs); clk = sum(q.get('clicks', 0) for q in qs)
    pimp = sum(p.get('impr', 0) for p in ps); pclk = sum(p.get('clicks', 0) for p in ps)
    row['search'] = {'range': g.get('range'), 'impressions': max(imp, pimp), 'clicks': max(clk, pclk),
                     'ctr_pct': round(100 * max(clk, pclk) / max(imp, pimp), 2) if max(imp, pimp) else 0,
                     'queries': len(qs), 'pages_with_impr': len(ps),
                     'avg_pos': round(sum(q['pos'] * q['impr'] for q in qs) / imp, 1) if imp else None}
    row['sitemaps_submitted'] = {os.path.basename(s['path']): int(s['contents'][0]['submitted']) for s in g.get('sitemaps', []) if s.get('contents')}
    ih = last_line(os.path.join(PROMO, 'index_history.jsonl')) or {}
    gp = jl(os.path.join(HERE, 'gsc_pages.json')) or {}
    row['index'] = {'inspected': ih.get('n'), 'indexed': ih.get('색인'), 'discovered_not_indexed': ih.get('발견됨·미색인'), 'unknown': ih.get('모름'),
                    'indexed_pct': round(100 * ih['색인'] / ih['n'], 1) if ih.get('n') else None, 'sample_file_pct': gp.get('indexed_pct'), 'at': ih.get('date')}
    r = jl(os.path.join(HERE, 'retention.json')) or {}
    row['retention'] = {'visitors': r.get('visitors'), 'returning_2plus_days': r.get('returning_2plus_days'), 'rate': r.get('rate'), 'days_observed': r.get('days_observed')}
    sm = os.path.join(ROOT, 'sitemap.xml')
    n_sm = len(re.findall(r'<loc>', open(sm, encoding='utf-8').read())) if os.path.exists(sm) else None
    by = collections.Counter()
    for r_, _d, fs in os.walk(ROOT):
        if 'index.html' in fs and '.git' not in r_ and os.sep + '_' not in r_.replace(ROOT, ''):
            rel = os.path.relpath(r_, ROOT).replace(os.sep, '/')
            by[rel.split('/')[0] if rel != '.' else '(home)'] += 1
    row['site'] = {'sitemap_urls': n_sm, 'pages_by_section': dict(by.most_common(14))}
    row['not_measured'] = {'ad_revenue': None, 'subscription_conversion': None, 'cost': None}
    return row


if __name__ == '__main__':
    row = collect()
    rows = []
    if os.path.exists(LOG):
        rows = [json.loads(l) for l in open(LOG, encoding='utf-8') if l.strip()]
    rows = [x for x in rows if x['date'] != row['date']] + [row]
    with open(LOG, 'w', encoding='utf-8', newline='\n') as f:
        for x in rows:
            f.write(json.dumps(x, ensure_ascii=False) + '\n')
    s, i = row['search'], row['index']
    print(f"{row['date']} 노출 {s['impressions']} · 클릭 {s['clicks']} · CTR {s['ctr_pct']}% · 평균순위 {s['avg_pos']} | "
          f"색인 {i['indexed']}/{i['inspected']} ({i['indexed_pct']}%) | 재방문 {row['retention']['rate']} | 사이트맵 {row['site']['sitemap_urls']}쪽 | 누적 {len(rows)}일")
