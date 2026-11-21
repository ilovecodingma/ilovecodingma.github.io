# -*- coding: utf-8 -*-
"""마케터 원자료를 저장소(_gongmo/exam_data)로 복사: exams_2027.json, cut_*.json → cuts/<exam_id>.json. 사용: python -X utf8 exam_sync.py"""
import glob
import json
import os
import shutil

SRC = r'C:\Users\k\tools\marketer\calendar'
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exam_data')
os.makedirs(os.path.join(DST, 'cuts'), exist_ok=True)
p = os.path.join(SRC, 'exams_2027.json')
if os.path.exists(p):
    json.load(open(p, encoding='utf-8'))
    shutil.copyfile(p, os.path.join(DST, 'exams_2027.json'))
    print('일정', p)
for nm in ('jeongsi_2027_universities.json', 'nonsul_2026_2027.json'):
    q = os.path.join(SRC, nm)
    if os.path.exists(q):
        json.load(open(q, encoding='utf-8'))
        shutil.copyfile(q, os.path.join(DST, nm))
        print('표', nm)
q = os.path.join(SRC, 'exam_articles.json')
if os.path.exists(q):
    json.load(open(q, encoding='utf-8'))
    shutil.copyfile(q, os.path.join(DST, 'exam_articles.json'))
    print('시험 글 목록')
for f in glob.glob(os.path.join(SRC, 'cut_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    eid = {'suneung-2027': 'csat-2027'}.get(d['exam_id'], d['exam_id'])   # 마케터 컷 파일의 exam_id 와 일정표 id 가 다를 때 맞춘다
    shutil.copyfile(f, os.path.join(DST, 'cuts', eid + '.json'))
    print('컷', eid)
