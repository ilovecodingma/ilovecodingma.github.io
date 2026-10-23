# -*- coding: utf-8 -*-
"""카드용 짧은 표현 (2026-10-23 UI 2차 1번): 글자 수로 자르지 않는다.
원문이 한도 안이고 완결돼 있으면 그대로, 길면 쉼표·가운뎃점·슬래시 같은 항목 경계에서만 줄이고, 그래도 완결되지 않으면 None 을 돌려준다(호출 쪽이 「확인 필요」 표시)."""
import re

_OPEN, _CLOSE = '([{「『<', ')]}」』>'
_SPLIT = re.compile(r'\s*(?:,|，|·|ㆍ|/|;|\n|또는|및)\s*')
_BAD_END = re.compile(r'(?:[,/·(\[~\-:]|(?<=[가-힣])(?:이란|란|이며|이고|이나|으로|에서|에게|하여|하고|을|를|은|는|의|와|과)$|\b(?:및|또는|등의))$')
_BAD_START = re.compile(r'^(?:인\s|명\s|원\s|[,/·)\]:.\-])')


def complete(t):
    """열린 괄호, 문장 중간 종료, 의미 없는 영어 조각이 없는지."""
    t = (t or '').strip()
    if not t:
        return False
    if sum(t.count(c) for c in _OPEN) != sum(t.count(c) for c in _CLOSE):
        return False
    if _BAD_END.search(t) or _BAD_START.search(t):
        return False
    if re.fullmatch(r'[A-Za-z0-9 .\-_]+', t) and len(t) < 14 and not re.fullmatch(r'[A-Za-z]{2,}\d*', t):
        return False   # 「Official B」 같은 영어 조각
    ps = [x for x in re.split(r'\s*[,，·ㆍ/;]\s*', t) if x]
    if len(ps) >= 2 and len(ps[-1]) < 2:
        return False   # 「초, 중, 고, 학」 처럼 잘린 나열
    return True


def clip(text, n):
    """text 를 n자 이내의 완결된 표현으로. 불가능하면 None."""
    t = re.sub(r'\s+', ' ', (text or '')).strip()
    if not t:
        return None
    if len(t) <= n:
        return t if complete(t) else _drop_tail(t, n)
    return _drop_tail(t, n)


def _drop_tail(t, n):
    parts = [p for p in _SPLIT.split(t) if p]
    out, used = '', 0
    for p in parts:
        cand = (out + ' · ' + p) if out else p
        if len(cand) > n:
            break
        out, used = cand, used + 1
    if out and complete(out) and len(parts) > 1:
        return out + (' 외' if used < len(parts) else '')
    return None


_UI = re.compile(r'(?:첨부\s*파일|다운로드|바로\s*가기|목록으로|이전\s*글|다음\s*글|공유하기|스크랩|인쇄하기|더\s*보기|전체\s*보기)')


def strip_ui(t):
    """메뉴·버튼 문구(첨부파일 다운로드 등)를 지우고 공백을 정리한다."""
    return re.sub(r'\s+', ' ', _UI.sub(' ', t or '')).strip(' ,·/')


def repair(t):
    """잘린 문구 복구: 끝의 …·말줄임, 닫히지 않은 괄호 이후, 끊긴 쉼표 항목을 버린다. 끝이 자연스럽지 않으면 마지막 항목 경계에서 줄이고, 그래도 안 되면 빈 문자열."""
    t = re.sub(r'\s+', ' ', t or '').strip()
    t = re.sub(r'[…\.]{1,3}$', '', t).strip()
    depth, cut = 0, None
    for i, ch in enumerate(t):
        if ch in _OPEN:
            if depth == 0:
                cut = i
            depth += 1
        elif ch in _CLOSE and depth:
            depth -= 1
    if depth:
        t = t[:cut].strip(' ,·/')
    if complete(t) and len(t) >= 4:
        return t
    parts = [p for p in re.split(r'\s*[,·/]\s*', t) if p]
    while len(parts) > 1:
        parts.pop()
        cand = ', '.join(parts)
        if complete(cand) and len(cand) >= 4:
            return cand
    return ''
