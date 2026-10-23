# -*- coding: utf-8 -*-
"""공모전 게시 전 품질 게이트 (2026-10-23 재심사 지침 7번). 순수 함수 — 어긋난 항목을 검수 대기로 돌리고 사유를 남긴다.
hold(목록·추천·색인에서 뺌): 분류 불일치 · 자격/지역 모순 · 링크 성격 모순.  recollect(게시는 하되 재수집 대상): 잘린 자격·잘린 공고 핵심.
누락값을 「없음」으로 바꾸지 않는다 — 여기서는 판정만 하고 값은 건드리지 않는다."""
import re

LIT_WORDS = re.compile(r'문학|시나리오|수필|소설|백일장|에세이|글쓰기|동화|수기|웹소설|네이밍|슬로건|시 공모')
TECH_WORDS = re.compile(r'창업|경진대회|해커톤|스타트업|사업화|소프트웨어')


def check(c, region_kind, np_broken=None):
    """→ (hold 사유 목록, recollect 사유 목록)"""
    hold, rec = [], []
    tags = c.get('tags') or []
    t = c.get('title') or ''
    if tags and tags[0] == '문학' and TECH_WORDS.search(t) and not LIT_WORDS.search(t):
        hold.append('분류 불일치: 대표 분야가 문학인데 제목은 기술·창업·AI 공모')
    el = (c.get('elig') or '').strip()
    rk = region_kind(el)
    if c.get('region') and rk == 'national' and not re.search(r'제한\s*(?:문구\s*)?없|전국|없음', str(c.get('region'))):
        hold.append('자격 문구는 전국(국내 거주)인데 지역 제한 값이 따로 있음')
    if c.get('verified_official') and re.search(r'all-con|thinkyou|wevity|contestkorea|linkareer|campuspick', c.get('link') or ''):
        hold.append('공식 대조 완료로 표시됐는데 접수 링크는 수집처')
    if c.get('elig_raw') and not el:
        rec.append('자격 문구가 잘려 비움(재수집)')
    for cid, lab, v in (np_broken or []):
        if cid == c['id']:
            rec.append(f'공고 핵심 「{lab}」 추출이 잘려 비게시(재수집): {v}')
    return hold, rec
