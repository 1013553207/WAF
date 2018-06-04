
import  re
import json
from datetime import datetime
#import mysql.connector
from datetime import  datetime, timedelta

from tornado import gen
#import tornadoredis
from src.waf.matchRule import funcs
from src.waf.transFunc import *
import src.waf.utils as utils
from src.waf.train_and_detect import HMMmodel#, charRNN # fptree
from src.waf.utils.otherObjects import featureRequest

try:
    import urlparse
except ImportError:
    from urllib.parse import urlparse, unquote

import string
import numpy as np


from .base import BaseProcessPhase

class tradProcessPhase(BaseProcessPhase):
    def __init__(self, *args, **kargs):
        super(tradProcessPhase, self).__init__(*args, **kargs)

    @gen.coroutine
    def requestPhase(self, field, data):  # -1 no model; 0 right; 1 find problem
        '''
        fields = self.rules.keys()
        fields = filter(lambda i: i[1] == 1, fields)
        for field, phase in fields:
            func = funcs.get(field, None)
            data = getattr(self.request, field)
            if func is None or data is None:
                continue
            data = urlDecode(data) if data else None
        '''
        fields = self.rules.keys()
        key = list(filter(lambda i: i[0] == field, fields))[0]
        func = funcs.get(field, None)

        print('traditional process regex rule!')
        for rule in self.rules[key].values():
            try:
                if data and isinstance(data, str) and func(data, rule[2]) and rule[3] == 1:
                    #print('found instruction!')
                    #print(field, data, rule[2])
                    self.request.rule_id = rule[0]
                    self.log()
                    return True
            except Exception as e:
                print(e, data, rule[2])
                pass
        #print('not found instruction!')
        self.request.rule_id = -1
        self.log()
        return False

    def reponsePhase(self):
        return True