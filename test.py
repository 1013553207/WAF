#!/usr/bin/env python3
"""Example for aiohttp.web basic server
with table definition for routes
"""
import string
import requests
import random
import time

payload = {'movie': '5', 'action': 'go'}

cookies = dict(PHPSESSID='kr3hodt7agfggsjmqaqhnpqri7', security_level='1')

for i in range(6000):
    nums = ''.join(random.choices(string.digits, k=random.randint(1, 20)))
    if len(nums)%4 == 0:
        continue 
    payload['movie'] = nums
    req = requests.get("http://127.0.0.1/sqli_2.php", params=payload, cookies=cookies)
    #time.sleep(0.2)\
    #print(nums)
    print(req.status_code, nums)





