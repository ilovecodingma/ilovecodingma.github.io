# -*- coding: utf-8 -*-
"""루리의 줍줍 마감 알림 메일 (매일 아침 8시, 작업 스케줄러 JupJup_Alerts)
알림을 켠 회원(user_prefs alert=1)의 찜 중 마감이 3일 남은 날·당일인 것을 모아 한 통씩 보냄.
발송: 네이버 SMTP(DPAPI 금고 ~/.bsp_mail.xml). 같은 회원·같은 항목·같은 날은 한 번만(alerts_sent.jsonl).
사용: python alerts.py            → 대장 계정(sung2011103@naver.com)에게만 (시험 모드, 2026-10-17 시작)
      python alerts.py --live     → 알림 켠 모든 회원에게
      python alerts.py --dry      → 보낼 목록만 출력"""
import os, sys, json, datetime, subprocess, smtplib, urllib.request
from email.mime.text import MIMEText
from email.header import Header
sys.path.insert(0, os.path.expanduser('~/remote_login')); import cf_token
HERE = os.path.dirname(os.path.abspath(__file__))
DB = 'bad84d2c-a24e-4ba9-8de9-dad02f30e30e'; OWNER = 'sung2011103@naver.com'; SITE = 'https://sungprofile.cloud'
SENT = os.path.join(HERE, 'alerts_sent.jsonl')

def q(sql, params=None):
    a, t = cf_token.get()
    r = urllib.request.Request(f'https://api.cloudflare.com/client/v4/accounts/{a}/d1/database/{DB}/query', method='POST',
        data=json.dumps({'sql': sql, **({'params': params} if params else {})}).encode(), headers={'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json', 'User-Agent': 'wrangler/4.40.0'})
    return json.load(urllib.request.urlopen(r, timeout=60))['result'][0]['results']

def smtp_pw():
    ps = '$c = Import-Clixml "$env:USERPROFILE\\.bsp_mail.xml"; Write-Output $c.UserName; Write-Output $c.GetNetworkCredential().Password'
    o = subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True).stdout.split()
    return o[0], o[1]

def main():
    live, dry = '--live' in sys.argv, '--dry' in sys.argv
    today = datetime.date.today()
    users = q("SELECT u.id, u.email, u.nick FROM users u JOIN user_prefs p ON p.user_id = u.id WHERE p.data LIKE '%\"alert\":\"1\"%' AND u.banned = 0")
    sent = set()
    if os.path.exists(SENT):
        for l in open(SENT, encoding='utf-8'):
            try: sent.add(tuple(json.loads(l)['k']))
            except Exception: pass
    mails = []
    for u in users:
        em = u['email']
        if em.endswith('.login') or em.endswith('@example.com'): continue
        if not live and em != OWNER: continue
        items = q("SELECT item_id, title, end_date FROM user_items WHERE user_id = ? AND fav = 1 AND state = '' AND end_date != ''", [u['id']])
        due = []
        for it in items:
            d = (datetime.date.fromisoformat(it['end_date']) - today).days
            k = (u['id'], it['item_id'], today.isoformat())
            if d in (0, 3) and k not in sent: due.append((d, it, k))
        if due: mails.append((u, sorted(due, key=lambda x: x[0])))
    print('대상 회원', len(users), '보낼 메일', len(mails), '시험모드' if not live else '전체')
    if dry or not mails:
        for u, due in mails: print(u['nick'], [(d, it['title']) for d, it, _ in due])
        return
    user, pw = smtp_pw()
    s = smtplib.SMTP('smtp.naver.com', 587, timeout=30); s.starttls(); s.login(user, pw)
    for u, due in mails:
        link = lambda id: f"{SITE}/c/{id[2:]}/" if id.startswith('c:') else f"{SITE}/a/{id[2:]}/" if id.startswith('a:') else SITE
        rows = ''.join(f'<li style="margin:8px 0"><b style="color:{"#e11d48" if d == 0 else "#7c3aed"}">{"오늘 마감" if d == 0 else "D-3"}</b> '
                       f'<a href="{link(it["item_id"])}" style="color:#1e1b4b;font-weight:700">{it["title"] or it["item_id"]}</a></li>' for d, it, _ in due)
        html = f'''<div style="font-family:sans-serif;max-width:560px;margin:auto;padding:20px;border-radius:16px;background:#faf5ff">
<p style="font-size:18px;font-weight:800;color:#5b21b6;margin:0 0 6px">루리가 챙겨 왔어요! ⏰</p><p style="margin:0 0 10px">{u["nick"]}님이 찜한 것 중 마감이 다가온 게 있어요.</p><ul style="padding-left:18px">{rows}</ul>
<p style="margin:14px 0 0"><a href="{SITE}/me/" style="background:#7c3aed;color:#fff;padding:10px 16px;border-radius:10px;text-decoration:none;font-weight:700">내 공간에서 보기</a></p>
<p style="font-size:12px;color:#6b7280;margin-top:16px">알림은 <a href="{SITE}/me/">내 공간</a>에서 언제든 끌 수 있어요. · 루리의 줍줍</p></div>'''
        msg = MIMEText(html, 'html', 'utf-8'); msg['Subject'] = Header(f'⏰ 마감 임박 {len(due)}건 — 루리의 줍줍', 'utf-8'); msg['From'] = f'{Header("루리의 줍줍", "utf-8").encode()} <{user}@naver.com>' if '@' not in user else user; msg['To'] = u['email']
        s.sendmail(msg['From'] if '@' in msg['From'] else user, [u['email']], msg.as_string())
        with open(SENT, 'a', encoding='utf-8') as f:
            for _, it, k in due: f.write(json.dumps({'k': list(k)}, ensure_ascii=False) + '\n')
        print('보냄', u['nick'], len(due))
    s.quit()

if __name__ == '__main__':
    main()
