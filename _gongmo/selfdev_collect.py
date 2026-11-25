# -*- coding: utf-8 -*-
"""가난한 박과장 자기개발 정보 수집기. 공개 출처에서 제목·링크만 모아 items.json 에 병합 저장.
실행: python selfdev_collect.py   (로그인/API 키 불필요, 호스트당 1초 이상 간격)"""
import hashlib, json, os, re, sys, time
from datetime import datetime
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "selfdev_data", "items.json")
KEEP = 500
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_last = {}

def get(url):
    host = urlparse(url).netloc
    wait = 1.2 - (time.time() - _last.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "ko"}, timeout=20)
    _last[host] = time.time()
    r.raise_for_status()
    return r

def soup(url):
    return BeautifulSoup(get(url).content, "html.parser")

def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()

NOISE = re.compile(r"채용|용역|입찰|경력경쟁|공무원 .*공고|연예|열애|화보|결혼설|이혼|광고|협찬|구매 ?대행|낙찰")

# ---- 출처별 수집기: (title, url) 목록 반환 ----
def links(url, sel, pat, strip_after=None, title_sel=None, base=None):
    s = soup(url)
    out = []
    for a in s.select(sel):
        h = a.get("href", "")
        if not re.search(pat, h):
            continue
        el = a.select_one(title_sel) if title_sel else None
        t = clean((el or a).get_text(" "))
        if strip_after:
            t = t.split(strip_after)[0].strip()
        t = re.sub(r"^\[[^\]]{1,6}\]\s*", "", t) if t.startswith("[공고]") or t.startswith("[기타]") else t
        if len(t) < 6 or t in ("자세히 보기", "더보기", "바로가기"):
            continue
        out.append((t, urljoin(base or url, h)))
    return out

def rss(url, cap=15):
    s = BeautifulSoup(get(url).content, "xml")
    out = []
    for it in s.find_all("item")[:cap]:
        t = clean(it.title.get_text()) if it.title else ""
        l = clean(it.link.get_text()) if it.link else ""
        if t and l:
            out.append((t, l))
    return out

SOURCES = [
    # name, default kind, fetch function
    ("정책브리핑 정책뉴스", "공지", lambda: links("https://www.korea.kr/news/policyNewsList.do", "a", r"policyNewsView\.do\?newsId=", title_sel="strong")),
    ("고용노동부 보도자료", "노동", lambda: links("https://www.moel.go.kr/news/enews/report/enewsList.do", "a", r"enewsView\.do\?news_seq=")),
    ("고용노동부 공지", "공지", lambda: links("https://www.moel.go.kr/news/notice/noticeList.do", "a", r"noticeView\.do\?bbs_seq=")),
    ("과기정통부 보도자료", "IT", lambda: links("https://www.msit.go.kr/bbs/list.do?sCode=user&mId=307&mPid=208", "a", r"/bbs/view\.do\?.*nttSeqNo=", strip_after=" 부서 담당자")),
    ("금융감독원 보도자료", "재테크", lambda: links("https://www.fss.or.kr/fss/bbs/B0000188/list.do?menuNo=200218", "table a", r"view\.do\?nttId=")),
    ("한국장학재단 공지", "지원제도", lambda: links("https://www.kosaf.go.kr/ko/notice.do", "a", r"mode=view.*seqNo=", base="https://www.kosaf.go.kr/ko/notice.do")),
    ("KOSA(AI·SW협회) 소식", "IT", lambda: links("https://www.sw.or.kr/site/sw/main.do", "a", r"/ex/board/View\.do\?cbIdx=")),
    ("KISA 공지", "IT", lambda: links("https://www.kisa.or.kr/401", "a", r"/401/form\?postSeq=")),
    ("연합뉴스 RSS", "시사", lambda: rss("https://www.yna.co.kr/rss/news.xml")),
    ("한겨레 RSS", "시사", lambda: rss("https://www.hani.co.kr/rss/")),
    ("경향신문 RSS", "시사", lambda: rss("https://www.khan.co.kr/rss/rssdata/total_news.xml")),
    ("매일경제 RSS", "재테크", lambda: rss("https://www.mk.co.kr/rss/30100041/")),
]

KINDS = [
    ("자격", r"자격|검정|시험|면허|기능사|기사"),
    ("강좌", r"강좌|교육|훈련|연수|아카데미|과정|부트캠프|MOOC|강의|양성"),
    ("지원제도", r"지원금|지원사업|장학|대출|보조|바우처|수당|급여|복지|청년|내일배움|모집|신청"),
    ("노동", r"근로|노동|임금|최저임금|산재|고용|실업|해고|퇴직|근로감독|노조|일자리"),
    ("재테크", r"세금|세무|세액|연말정산|금리|대출|예금|투자|주식|연금|보험|펀드|환율|부동산|금융|소비자"),
    ("IT", r"AI|인공지능|코딩|소프트웨어|SW|개발자|보안|사이버|데이터|클라우드|반도체|디지털"),
    ("요리", r"요리|레시피|식단|급식|식품|식약|영양|조리"),
]

KEYWORDS = ["근로감독", "최저임금", "임금", "산재", "고용", "일자리", "청년", "장학금", "대출", "금리", "세금", "연말정산",
            "연금", "보험", "투자", "금융", "AI", "인공지능", "코딩", "보안", "사이버", "교육", "훈련", "자격", "시험",
            "지원금", "복지", "신청", "모집", "부동산", "물가", "식품", "소비자", "반도체", "데이터"]

def classify(title, default):
    for k, p in KINDS:
        if re.search(p, title):
            # 시사 출처는 주제가 뚜렷할 때만 분류 변경
            return k if default != "시사" or k in ("노동", "재테크", "IT", "자격") else default
    return default

def summarize(title, source, kind):
    kws = [k for k in KEYWORDS if k in title][:3]
    base = f"{source.split()[0]} {kind} 소식"
    s = base + (" · " + "·".join(kws) if kws else "")
    return s[:40]

DATE = re.compile(r"(20\d{2})[.\-/ ]\s*(\d{1,2})[.\-/ ]\s*(\d{1,2})")
def dates(title):
    """제목에 4자리 연도가 붙은 날짜가 명시된 경우만 추출. 아니면 (None, None)."""
    ds = ["%04d-%02d-%02d" % tuple(map(int, m)) for m in DATE.findall(title)]
    if not ds or not re.search(r"신청|접수|모집|기간", title):
        return None, None
    return ds[0], (ds[1] if len(ds) > 1 else None)

def cost(title):
    if re.search(r"무료|무상|전액 ?지원", title):
        return "무료"
    if re.search(r"유료|수강료|참가비|수수료", title):
        return "유료"
    return "미확인"

def norm_url(u):
    return re.sub(r";jsessionid=[^?&]*", "", u)

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    old = []
    if os.path.exists(OUT):
        try:
            old = json.load(open(OUT, encoding="utf-8"))
        except Exception:
            old = []
    by_id = {x["id"]: x for x in old if x.get("title") not in ("자세히 보기", "더보기")}
    stat = {}
    for name, default, fn in SOURCES:
        try:
            rows = fn()
        except Exception as e:
            stat[name] = "실패:" + str(e)[:50]
            continue
        new = 0
        seen = set()
        for t, u in rows:
            u = norm_url(u)
            if NOISE.search(t) or u in seen:
                continue
            seen.add(u)
            iid = hashlib.sha1((name + u).encode()).hexdigest()[:16]
            if iid in by_id:
                continue
            kind = classify(t, default)
            a, b = dates(t)
            by_id[iid] = {"id": iid, "title": t, "source": name, "url": u, "kind": kind,
                          "apply_start": a, "apply_end": b, "cost": cost(t),
                          "summary": summarize(t, name, kind), "fetched_at": now}
            new += 1
        stat[name] = f"{len(seen)}건(신규 {new})"
    items = sorted(by_id.values(), key=lambda x: x["fetched_at"], reverse=True)[:KEEP]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    json.dump(items, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)
    for k, v in stat.items():
        print(f"{k}: {v}")
    print(f"총 {len(items)}건 저장 -> {OUT}")

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
