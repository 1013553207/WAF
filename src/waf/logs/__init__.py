#!/usr/bin/env python
'''
日志模块，记录的东西比较少
'''
import json
from datetime import  datetime

def stage_data(request, respone):
    fields = ['rule_id', 'ip', 'method', 'url', 'user_agent', 'request_headers', 'request_body', 'response_headers',
              'response_body']
    sql = '''insert into `logs`(`create_time`,
          `rule_id`,
          `ip`,
          `method`,
          `url`,
          `args`,
          `path`,
          `cookie`,
          `user_agent`,
          `request_headers`,
          `request_body`,
          `response_headers`,
          `response_body`) value(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
    params = (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
              request.rule_id,
              request.remote_ip,
              request.method,
              request.url,
              json.dumps(request.args) if request.args else '{}',
              request.path,
              request.cookie,
              request.user_agent,
              json.dumps(request.headers),
              request.body if request.body else b'',
              json.dumps(respone.headers) if respone else '{}',
              respone.body if respone else b'')
    return sql, params