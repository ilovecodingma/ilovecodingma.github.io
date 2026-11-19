# -*- coding: utf-8 -*-
"""빌드 없이 「급상승 한 줄」(plinks.HOT)만 홈·이슈·수능 글에 바로 끼운다. 사용: python -X utf8 hot_now.py  (끼운 뒤 git add/commit/push 는 빌드나 publish_fast 가 한다)"""
import plinks
print('끼운 곳', plinks.hot([]))
