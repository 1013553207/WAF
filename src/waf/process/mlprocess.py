
import re
import json
from datetime import datetime
from datetime import  datetime, timedelta

from tornado import gen
import tornadoredis
from src.waf.matchRule import funcs
from src.waf.transFunc import *
import src.waf.utils as utils
from src.waf.train_and_detect import HMMmodel, outlierDection, charRNN


from src.waf.utils.otherObjects import featureRequest

try:
    import urlparse
except ImportError:
    from urllib.parse import urlparse, unquote

import string
import numpy as np


from .base import BaseProcessPhase

limitNUM = 2000

class MlProcessPhase(BaseProcessPhase):
    def __init__(self, *args, **kargs):
        super(MlProcessPhase, self).__init__(*args, **kargs)

    @gen.coroutine
    def requestPhase(self, traditionPhase=None):  # -1 no model; 0 right; 1 find problem
        if self.request.isStatic:
            return False
        end = datetime.now()
        begin = end - timedelta(days=5)
        match_count = 0
        for phase in ['args', 'header', 'cookie', 'request']:
            if phase == 'args' and self.request.args:
                values = self.request.args #[(item.split('=')[0], item.split('=')[1]) for item in unquote(self.request.args).split('&')]
                datas = None
                hmodel_match = False
                rmodel_match = False

                for k, v in values.items():
                    key = '%s_%s_%s' % (self.request.path, phase, k)
                    hmmmodel_key = key + '_hmm'
                    rnnmodel_key = key + '_rnn'
                    hmmodel = yield HMMmodel.getModel(self.client, hmmmodel_key)
                    rnnmodel = yield charRNN.getModel(self.client,  rnnmodel_key)

                    if rnnmodel is None or hmmodel is None:
                        datas = yield utils.getUrlQueryValues(self.request.path, begin, end, self.pool)
                        # if not datas and
                        if datas and len(set(datas[k])) < int(0.1 * len(datas[k])):
                            continue

                    if rnnmodel is None:
                        if datas and len(datas[k]) >= limitNUM:
                            charRNN.trainModel(self.config, rnnmodel_key, datas[k])

                    if hmmodel is None:
                        if datas and len(datas[k]) >= limitNUM:
                            HMMmodel.trainModel(self.config, hmmmodel_key, datas[k])

                    if hmmodel and not hmodel_match:
                        print('hmm model process!')
                        if HMMmodel.estimate(hmmodel, v):
                            hmodel_match = True

                    if rnnmodel and not rmodel_match:
                        print('rnn model process!')
                        if charRNN.estimate(rnnmodel, v):
                            rmodel_match = True
                    if hmodel_match or rmodel_match:
                        match_count += 1
                        break
                    if hmmodel is None and rnnmodel is None:
                        res = yield traditionPhase.requestPhase(phase, v)
                        print(res)
                        if res:
                            match_count += 1
                            break
                        #continue
            if phase == 'request':
                outliermodels = yield outlierDection.getModel(self.client, self.request.path)
                datas = None
                if not outliermodels:
                    datas = yield utils.getRequestValues(self.request.path, begin, end, self.pool)
                    if len(datas) <= limitNUM:
                        continue
                    else:
                        outlierDection.trainModel(self.config, self.request.path, datas)
                else:
                    count = outlierDection.estimate(outliermodels, self.request, datas)
                    match_count += count

        if match_count > 0:
            print('found instruction')
            return True
        return False

    @gen.coroutine
    def reponsePhase(self):
        return True