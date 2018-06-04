# -*- coding: utf-8 -*-

import re
import json
from datetime import datetime
import numpy as np
from datetime import  datetime, timedelta

import base64
import datetime
import pickle
import json
from tornado import gen
from src.waf.logs import stage_data
from src.waf.utils.otherObjects import featureRequest
from src.waf.decode import requestDecode, responeDecode

from src.waf.preprocess.preprocess import setRequestAttr
try:
    import urlparse
except ImportError:
    from urllib.parse import urlparse, unquote

import string



class BaseProcessPhase(object):
    def __init__(self, rules, pool, redis, config, request, respone=None):
        self.rules = rules
        self.pool = pool
        self.config = config
        self.client = redis
        waf_has_process = getattr(request, '_waf_has_process', False)
        if not waf_has_process:
            self.request = requestDecode(self.transfrom(request))
        else:
            self.request = request
        self.respone = respone

    def transfrom(self, request):
        #request.url = unquote(request.url, encoding='utf-8')
        request = setRequestAttr(request)
        request._waf_has_process = True
        return request

    @gen.coroutine
    def log(self):
        #print(sql)
        sql, params = stage_data(self.request, self.respone)
        yield self.pool.execute(sql, params)

    #@gen.coroutine
    def topick(self):
        pass

    @gen.coroutine
    def requestPhase(self, traditionPhase=None):
        #self.request.rule_id = -1
        #yield self.log()
        if 'sqli_1.php' in self.request.path and  self.request.args:
            with open('C:\\Users\\DIY\\Desktop\\multiWAF\\datasets\\anormal\\otherAnormal.txt', 'a+') as fd:
                fd.write(self.request.args['title']+'\n')
        return False

    @gen.coroutine
    def reponsePhase(self):
        pass
