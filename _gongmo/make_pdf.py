# -*- coding: utf-8 -*-
"""정보성 글(가이드·개발 지식·편집 글)을 PDF 로 미리 만들어 /pdf/<이름>.pdf 에 둔다. 내용이 바뀐 글만 다시 만든다(해시 비교).
 사용: build.py 끝에서 make(ROOT, paths) 호출  |  python make_pdf.py  (전체 점검)"""
import os, sys, re, json, hashlib, threading, http.server, socketserver, functools, time

PDF_PREFIX = ('/guide/', '/dev/', '/review/', '/ssul/')
SKIP = ('/dev/qna/',)


def pdf_name(path):
    return re.sub(r'[^0-9A-Za-z가-힣]+', '-', path.strip('/')).strip('-') + '.pdf'


def is_pdf_path(path):
    return path.startswith(PDF_PREFIX) and path.count('/') == 3 and path not in SKIP


def make(root, paths):
    from playwright.sync_api import sync_playwright
    out = os.path.join(root, 'pdf'); os.makedirs(out, exist_ok=True)
    stf = os.path.join(out, '_hash.json'); st = json.load(open(stf, encoding='utf-8')) if os.path.exists(stf) else {}
    todo = []
    for p in paths:
        f = os.path.join(root, p.strip('/'), 'index.html')
        if not os.path.exists(f): continue
        h = hashlib.md5(open(f, 'rb').read() + open(os.path.join(root, 'assets', 'print.css'), 'rb').read()).hexdigest()
        if st.get(p) != h or not os.path.exists(os.path.join(out, pdf_name(p))): todo.append((p, h))
    keep = {pdf_name(p) for p in paths}
    for f in os.listdir(out):
        if f.endswith('.pdf') and f not in keep: os.remove(os.path.join(out, f))
    if not todo: return 0, len(paths)
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=root)); port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    n = 0
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(channel='msedge', headless=True); pg = b.new_context(viewport={'width': 900, 'height': 1200}, locale='ko-KR').new_page()
            for p, h in todo:
                try:
                    pg.goto(f'http://127.0.0.1:{port}{p}', wait_until='networkidle', timeout=40000); pg.wait_for_timeout(500)
                    pg.add_style_tag(content='*{box-shadow:none!important;text-shadow:none!important;backdrop-filter:none!important;background-image:none!important}.pc,#comments,.hd,.ft,.rc,.say img,.card img,ul.list,.mg-s:last-of-type,.hub-rel{display:none!important}')
                    pg.evaluate("() => { document.querySelectorAll('main h2').forEach(h => { if (/^(같이 보면 좋은 페이지|마감 임박 공모전)/.test(h.textContent.trim())) { let n = h; const rm = []; while (n) { rm.push(n); n = n.nextElementSibling; if (n && n.tagName === 'H2' && !/^(같이 보면|마감 임박)/.test(n.textContent.trim())) break; } rm.forEach(x => x.remove()); } }); }")
                    title = (pg.title() or '').split('|')[0].strip()
                    pg.pdf(path=os.path.join(out, pdf_name(p)), format='A4', print_background=False, prefer_css_page_size=True,
                           display_header_footer=True, header_template='<span></span>',
                           footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#888;font-family:sans-serif"><span class="title"></span> · <span class="pageNumber"></span>/<span class="totalPages"></span></div>',
                           margin={'top': '16mm', 'bottom': '18mm', 'left': '14mm', 'right': '14mm'})
                    st[p] = h; n += 1
                except Exception as e:
                    print('PDF 실패', p, repr(e)[:70])
            b.close()
    finally:
        srv.shutdown()
    json.dump(st, open(stf, 'w', encoding='utf-8'))
    return n, len(paths)


if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ps = []
    for pre in PDF_PREFIX:
        d = os.path.join(root, pre.strip('/'))
        if os.path.isdir(d):
            for s in sorted(os.listdir(d)):
                p = f'{pre}{s}/'
                if os.path.exists(os.path.join(d, s, 'index.html')) and is_pdf_path(p): ps.append(p)
    print(make(root, ps))
