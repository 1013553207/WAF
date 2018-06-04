import  re
import json
from typing import Dict, List
from datetime import datetime
#import mysql.connector
from datetime import  datetime, timedelta

from tornado import gen

import operator
import base64
try:
    import urlparse
except ImportError:
    from urllib.parse import urlparse, unquote

from src.waf.utils.otherObjects import featureRequest

@gen.coroutine
def getUrlQueryValues(path, begin, end, pool):
    sql = '''select args, rule_id from logs where path = '%s' and create_time between '%s' and '%s' '''  % (
        path,
        begin,
        end)
    #print(sql)
    cur = yield pool.execute(sql)
    values = {}
    result = cur.fetchall()
    result = sorted(result, key=lambda item: hash(item[0]))
    for item in  result:
        try:
            args = json.loads(item[0])
            kvs = args
            for k, v in kvs.items():
                res = values.get(k, [])
                # 0 标识异常的请求
                # 1 标识正常的请求
                res.append((v, 0 if int(item[1]) == -1 else 1))
                values[k] = res
        except Exception as e:
            pass
    return values

@gen.coroutine
def getPostQueryValues(url, key, begin, end, pool):
    sql = ''' select request_body from logs where path = %s and create_time between '%s' and '%s' '''
    cur = yield  pool.execute(sql)
    values = {}
    for item in  cur.fetchall():
        kvs =[(i.split('=')[0], i.split('=')[1]) for i in unquote(item[0]).split('&')]
        for k, v in kvs:
            res = values.get(k, [])
            res.append(v)
            values[k] = v
    return values

@gen.coroutine
def getRequestValues(path, begin, end, pool):
    sql = ''' select method, url, args, path, request_headers, request_body, rule_id from logs where path = '%s' and create_time between '%s' and '%s' limit 10000, 8000''' %(
        path,
        begin,
        end)
    #print(sql)
    cur = yield pool.execute(sql)
    values = []
    for item in cur.fetchall():
        ob = featureRequest(method=item[0],
                       url=item[3]) #base64.standard_b64decode(item[1]).decode('utf-8'))
        ob._headers = json.loads(item[4]) #base64.standard_b64decode(item[4]).decode('utf-8')
        try:
            #args = json.loads(item[2]) #base64.urlsafe_b64decode(item[2]).decode('utf-8')
            ob._query_params = json.loads(item[2]) #dict([(i.split('=')[0], i.split('=')[1]) for i in unquote(args).split('&')])
        except Exception as e:
            continue
        #ob.label_type = 'normal' if item[6] >= 0 else 'anomalous'
        ob.label_type = 'anormal' if int(item[6]) > 0 else 'normal'
        values.append(ob)
    return values


def getHeadValues(url, head, begin, end, pool):
    pass


def getCookieValues(url, key, begin, end, pool):
    pass

def read_and_group_requests(
        selected_endpoint_list: List[str], ds_url_list: List[str], normal_file_names: List[str],
        anomalous_file_names: List[str], read_func) -> Dict:
    d = {}

    # initialize dict with empty lists
    for key in selected_endpoint_list:
        d[key] = {
            'normal': [],
            'anomalous': [],
        }

    # read requests and group them by key
    for label, file_name_list in zip(
            ('normal', 'anomalous'),
            (normal_file_names, anomalous_file_names)
    ):
        for req in read_func(file_name_list):
            key = str(req)
            if key in selected_endpoint_list:
                d[key][label].append(req)

    # replace keys with ds_url
    new_d = {}
    for key, ds_url in zip(selected_endpoint_list, ds_url_list):
        new_d[ds_url] = d[key]

    return new_d


def group_requests(r_list: List[featureRequest], key_func) -> Dict:
    d = {}
    for r in r_list:
        k = key_func(r)
        d.setdefault(k, [])
        d[k].append(r)

    return d


