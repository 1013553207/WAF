# -*- coding: utf-8 -*-

import base64
from urllib.parse import unquote

def trim(data):
    return data.strip()

def urlEncode(data):
    pass

def urlDecode(data):
    if isinstance(data, str):
        return unquote(data)
    else:
        return data

def removeComments(data):
    pass

def length(data):
    return str(len(data))


