

import os
import sys
import pickle
import redis
from typing import List

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline, make_union

from sklearn.svm import OneClassSVM
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

from src.waf import featureExtraction
from src.waf.utils import pipeline
from multiprocessing import Pool, Process

from src.waf.utils.otherObjects import featureRequest

from tornado import gen
try:
    import urlparse
except ImportError:
    from urllib.parse import urlparse, unquote


TF_LIST = tuple(
    tf
    for tf in featureExtraction.NUMBERS_TF_LIST
    if issubclass(tf, featureExtraction.base.KeyTransformer))


RANDOM_STATE = 2
TRAIN_SIZE = 4800

NU = 0.01
GAMMA = 0.01

rng = np.random.RandomState(42)


#urls = [l.split(' ')[1] for l in csic.SELECTED_ENDPOINT_LIST]

def trainLocalModel(r, key, datas):

    r_list = datas
    requests = pipeline.group_requests(r_list, lambda r: '{} {}'.format(r.method, r.url))

    for i, (k, v_list) in enumerate(sorted(requests.items())):

        d2 = pipeline.group_requests(v_list, lambda r: r.label_type)

        normal_request = d2.get('normal', [])
        anormal_request = d2.get('anormal', [])

        anormal_size = int(0.01 * len(normal_request))

        train_list, _ = train_test_split(
            normal_request + anormal_request[-anormal_size: -1],
            random_state=RANDOM_STATE,
            train_size=TRAIN_SIZE)

        clf_svm = make_pipeline(
            make_union(*[class_() for class_ in TF_LIST]),
            OneClassSVM(kernel='sigmoid', nu=NU, gamma='auto'))

        clf_isolation = make_pipeline(
            make_union(*[class_() for class_ in TF_LIST]),
            IsolationForest(n_estimators=128, max_samples=400, max_features=0.7, random_state=rng))

        #clf_lof =  make_pipeline(
        #    make_union(*[class_() for class_ in TF_LIST]),
        #    LocalOutlierFactor(n_neighbors=20))

        models = [clf_svm.fit(train_list), clf_isolation.fit(train_list)] #, clf_lof.fit(train_list)]
        return models
        #r.set(key, pickle.dumps(models))


def _trainModel(config, key, datas):
    r = redis.Redis(host=config['host'],
                    port=config['port'],
                    #password=config['passwd'],
                    decode_responses=True)
    key_status = key + '_status'
    status = r.get(key_status)
    if status is None:
        r.set(key_status, 'training')
        model = trainLocalModel(r, key, datas)
        r.set(key, pickle.dumps(model))
        r.delete(key_status)


def trainModel(config, key, datas):
    #创建进程，然后训练模型，放到redis里
    p = Process(target=_trainModel, args=(config['redis'], key,  datas))
    p.daemon = True
    p.start()
    '''
    _trainModel(config['redis'], key, datas)
     '''

_outlier_localsmodel = {}

@gen.coroutine
def getModel(client, key):
    model = _outlier_localsmodel.get(key, None)
    if model:
        return model
    # model = yield Task(client.get, key)
    model = yield client.get(key)
    if model:
        model = pickle.loads(model)
        # 需要反序列化
        _outlier_localsmodel[key] = model #pickle.loads(model)
        return model


def estimate(models, request, hisRequests=None):
    ob = featureRequest(method=request.method,
                        url=request.path)
    ob._headers = request.headers
    ob._query_params = request.args #dict([(i.split('=')[0], i.split('=')[1]) for i in unquote(request.args).split('&')])
    count = 0
    for model in models:
        count += 1 if model.predict(ob) == -1 else 0
    return count

def estimate_LOF(model, request, hisRequests=None):
    ob = featureRequest(method=request.method,
                        url=request.path)
    ob._headers = request.headers
    ob._query_params = request.args
    hisRequests += [ob]
    if model.fit_predict(hisRequests)[-1] == -1:
        return True
    return False