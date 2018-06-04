#!/usr/bin/env python

from urllib.parse import urlparse
staticFile = ['.css', '.png', '.jpg', '.ttf', '.gif', '.js', '.flv', '.ico', '.swf']

def upstream(request, CONFIG):
    host = request.headers.get('host', None)
    if host in (CONFIG['client']['ip'], CONFIG['client']['host'], None):
        host = '%s:%d' % (CONFIG['server']['ip'], CONFIG['server']['port'])
    url = 'http://%s/%s' % ('180.76.234.10', request.uri)
    return  url


def setRequestAttr(request):
    o = urlparse(request.url)
    request.args = o.query
    request.path = o.path
    isStatic =  any([o.path.endswith(i) for i in staticFile])
    request.cookie = request.headers.get('cookie')
    request.requestbody = request.body
    request.user_agent = request.user_agent if request.user_agent else request.headers['User-Agent']
    request.isStatic = isStatic
    return request

'''
request.cookie
request.user_agent
'''
