
import sys
import os
import re
import redis

import numpy as np
import string
import pickle

from multiprocessing import Pool, Process
from hmmlearn import hmm
from tornado.gen import Task
from tornado import gen

#iters = 1000
ITERS = 10
NUMS = 5000

def getHindSize():
    count = 3
    for i in string.printable:  # range(33, 127):
        if 'a' <= i <= 'z':
            continue
        elif 'A' <= i <= 'Z':
            continue
        elif '0' <= i <= '9':
            continue
        else:
            count += 1
    return count


def trainLocalModel(hidesize, iters, train, train_len):
    model = hmm.MultinomialHMM(n_components=hidesize, n_iter=iters)
    model.fit(train, lengths=train_len)
    return model


def etl(line):
    mapdict = {ch: index for index, ch in enumerate(string.printable)}
    vers = []
    for c in line:
        v = mapdict.get(c, None)
        if v is not None:
            vers.append([v])
    return vers  # np.array(vers)

def processtrainData(datas):
    x = []; x_lens = []
    vers = etl(string.printable)  # .strip())
    x += vers
    x_lens.append(len(vers))
    for v, label in datas:
        vers = etl(v)
        x += vers
        x_lens.append(len(vers))
    x = np.array(x)
    return (x, x_lens)

def _trainModel(config, key, datas):
    r = redis.Redis(host=config['host'],
                    port=config['port'],
                    #password=config['passwd'],
                    decode_responses=True)
    key_status = key + '_status'
    status = r.get(key_status)
    if status is None:
        r.set(key_status, 'training')
        datas = list(filter(lambda item: item[1] == 0, datas))[:NUMS]
        train, train_lens = processtrainData(datas)
        model = trainLocalModel(getHindSize(), ITERS, train, train_lens)
        r.set(key, pickle.dumps(model))
        r.delete(key_status)


def trainModel(config, key, datas):
    #创建进程，然后训练模型，放到redis里
    p = Process(target=_trainModel, args=(config['redis'], key,  datas))
    p.daemon = True
    p.start()

_hmm_localsmodel = {}

@gen.coroutine
def getModel(client, key):
    model = _hmm_localsmodel.get(key, None)
    if model:
        return model
    # model = yield Task(client.get, key)
    model = yield client.get(key)
    if model:
        model = pickle.loads(model)
        # 需要反序列化
        _hmm_localsmodel[key] = model #pickle.loads(model)
        return model

def estimate(model, sequence):
    v = np.array([[string.printable.index(iv)] for iv in sequence])
    if model.score(v) <= -1000:
        return True
    return False
