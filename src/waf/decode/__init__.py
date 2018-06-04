#!/usr/bin/env python
'''
解码模块，对各种编码进行解码
url解码
base64解码
html解码
unicode解码
整体形成一个数据流的pipeline
'''

import chardet
import base64
import html
import json

from urllib.parse import unquote, urlparse

def isBase64(str):
    return False
    if not str:
        return False
    if len(str) % 4 != 0:
        return False
    for c in str:
        if  'a'<=c<='z' or  'A'<=c<='Z' or '0'<=c<='9' or c in '+/=':
            continue
        else:
            return False
    return True

def urlUnescape(url):
    return unquote(url)

def htmlUnescape(content):
    return html.unescape(content)

def code2UTF8(bytes):
    res = chardet.detect(bytes)
    bytes.decode(res['encoding']).encode('utf-8').decode('utf-8')

def requestDecode(request):
    o = urlparse(request.url)
    request.args = None
    request.path = o.path
    if o.query:
        query = dict([(i.split('=')[0], i.split('=')[1]) for i in o.query.split('&')])
        for i in query:
            v = unquote(query[i])
            if isBase64(v):
                v = base64.standard_b64decode(bytes(v, 'utf-8')).decode('utf-8')
            query[i] = v
        request.args = query #json.dumps(query)
    request.headers = dict(request.headers) #json.dumps()
    request.url = base64.standard_b64encode(request.url.encode('utf-8'))
    request.cookie = base64.standard_b64encode(request.cookie.encode('utf-8'))
    request.user_agent = base64.standard_b64encode(request.user_agent.encode('utf-8'))
    if request.body and isinstance(request.body, str):
        request.body = base64.standard_b64encode(request.body.encode('utf-8'))
    return request

def responeDecode(respone):
    pass