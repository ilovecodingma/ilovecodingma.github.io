"""집 PC 작업 스케줄러용: 최신 데이터 받기 → 수집 → 변경분 커밋·푸시. 로그는 _trend/local.log."""
import os, subprocess, sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, '_trend', 'local.log')
NOWIN = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def run(*cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', creationflags=NOWIN)
    return r.returncode, (r.stdout + r.stderr).strip()


def main():
    out = [f'== {datetime.now():%Y-%m-%d %H:%M:%S}']
    out.append(run('git', 'pull', '-q', '--rebase', '-X', 'theirs')[1])
    py = sys.executable.replace('pythonw.exe', 'python.exe')
    code, txt = run(py, os.path.join('_trend', 'collect.py'))
    out.append(txt)
    if code == 0:
        run('git', 'add', 'trend/data')
        if run('git', 'diff', '--cached', '--quiet')[0]:
            run('git', 'commit', '-q', '-m', f'트렌드 데이터 갱신 {datetime.now():%m-%d %H:%M} (PC)')
            for _ in range(3):
                c, t = run('git', 'push', '-q')
                if c == 0:
                    out.append('push ok')
                    break
                out.append(t)
                run('git', 'pull', '-q', '--rebase', '-X', 'theirs')
    lines = []
    if os.path.exists(LOG):
        with open(LOG, encoding='utf-8', errors='replace') as f:
            lines = f.read().splitlines()[-2000:]
    with open(LOG, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines + [x for x in out if x]) + '\n')


if __name__ == '__main__':
    main()
