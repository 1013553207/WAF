# -*- coding: utf-8 -*-

import os
import json
import copy
import datetime

import atexit
import pickle

try:
    import urlparse
except ImportError:
    from urllib.parse import urlparse

from tornado import httpserver
from tornado import ioloop
from tornado import iostream
from tornado import gen
from tornado import web
from tornado import httpclient
from tornado.concurrent import Future

from tornado.log import access_log, app_log, gen_log
from tornado.options import define, options, parse_command_line

from tornado_mysql import pools
import tredis

from src.waf.parseRules import parseRules
from src.waf.preprocess import  preprocess
from src.waf.process import BaseProcessPhase, MlProcessPhase, tradProcessPhase



RULES = None
CONFIG = None

pools.DEBUG = True

POOL = None
REDIS = None

requestobj = []


def future_set_result_unless_cancelled(future, value):
    """Set the given ``value`` as the `Future`'s result, if not cancelled.

    Avoids asyncio.InvalidStateError when calling set_result() on
    a cancelled `asyncio.Future`.

    .. versionadded:: 5.0
    """
    if not future.cancelled():
        future.set_result(value)



#@web.stream_request_body
class GenAsyncHandler(web.RequestHandler):
    def __init__(self, *args, **kargs):
        super(GenAsyncHandler, self).__init__(*args, **kargs)
        self.http_client = httpclient.AsyncHTTPClient(max_clients=32)

    @gen.coroutine
    def _execute(self, transforms, *args, **kwargs):
        """Executes this request with the given output transforms."""
        self._transforms = transforms
        try:
            if self.request.method not in self.SUPPORTED_METHODS:
                raise web.HTTPError(405)
            self.path_args = [self.decode_argument(arg) for arg in args]
            self.path_kwargs = dict((k, self.decode_argument(v, name=k))
                                    for (k, v) in kwargs.items())
            # If XSRF cookies are turned on, reject form submissions without
            # the proper cookie
            if self.request.method not in ("GET", "HEAD", "OPTIONS") and \
                    self.application.settings.get("xsrf_cookies"):
                self.check_xsrf_cookie()

            result = self.prepare()
            if result is not None:
                result = yield result
            if self._prepared_future is not None:
                # Tell the Application we've finished with prepare()
                # and are ready for the body to arrive.
                future_set_result_unless_cancelled(self._prepared_future, None)
            if self._finished:
                return

            if web._has_stream_request_body(self.__class__):
                # In streaming mode request.body is a Future that signals
                # the body has been completely received.  The Future has no
                # result; the data has been passed to self.data_received
                # instead.
                try:
                    yield self.request.body
                except iostream.StreamClosedError:
                    return

            #method = getattr(self, self.request.method.lower())
            result = self.method(*self.path_args, **self.path_kwargs)
            if result is not None:
                result = yield result
            if self._auto_finish and not self._finished:
                self.finish()
        except Exception as e:
            try:
                self._handle_request_exception(e)
            except Exception:
                app_log.error("Exception in exception handler", exc_info=True)
            if (self._prepared_future is not None and
                    not self._prepared_future.done()):
                # In case we failed before setting _prepared_future, do it
                # now (to unblock the HTTP server).  Note that this is not
                # in a finally block to avoid GC issues prior to Python 3.4.
                self._prepared_future.set_result(None)

    @gen.coroutine
    def method(self, *args, **kargs):
        global CONFIG
        url = preprocess.upstream(self.request, CONFIG)
        req = httpclient.HTTPRequest(url=url,
                                       method=self.request.method,
                                       headers=self.request.headers,
                                       body= None if self.request.method.lower() in ('option', 'get', 'head') else self.request.body,
                                       follow_redirects=False)

        req.remote_ip = self.request.remote_ip
        flag = yield self.process(copy.deepcopy(req))
        if flag:
            self.set_status(403)
            self.write('Forbidden!!!')
        else:
            try:
                response = yield self.http_client.fetch(req)
            except httpclient.HTTPError as e:
                if e.response is not None:
                    response = e.response
            self.set_status(response.code)
            data = response.body
            for key, value in response.headers.items():
                #if key == 'Transfer-Encoding':
                if key == 'Content-Length':
                    value = len(data)
                self.set_header(key, value)
            self.write(response.body)
        self.flush()

    @gen.coroutine
    def process(self, req):
        global CONFIG, RULES, POOL, REDIS
        rulePhase = None
        if CONFIG['bypass']:
            processPhase = BaseProcessPhase(RULES, POOL, REDIS, CONFIG, req)
        else:
            rulePhase = tradProcessPhase(RULES, POOL, REDIS, CONFIG, req)
            processPhase = MlProcessPhase(RULES, POOL, REDIS, CONFIG, req)
        flag = yield processPhase.requestPhase(rulePhase)
        print('main process', flag)
        if flag:
            return True
        return False

@gen.engine
def redisConnect():
    global REDIS
    client = tredis.Client([{"host": CONFIG['redis']['host'], "port": CONFIG['redis']['port'], "db": 0}],
                           auto_connect=False)
    flag = yield client.connect()
    if flag:
        REDIS = client

if __name__ == "__main__":
    app = web.Application([
        (r"/.*", GenAsyncHandler),
    ])
    basepath = os.path.dirname(__file__)
    RULES = parseRules(os.path.join(basepath, 'waf/config/new_rules.xml'))
    CONFIG = json.load(open(os.path.join(basepath, 'waf/config/sites.json'), 'r'))
    POOL = pools.Pool(
            CONFIG['connection'],
            max_idle_connections=2,
            max_recycle_sec=3,
            max_open_connections=5,)
    http_server = httpserver.HTTPServer(app)
    http_server.listen(CONFIG['client']['port'], CONFIG['client']['ip'])
    install = ioloop.IOLoop.instance()
    install.add_callback(redisConnect)
    install.start()