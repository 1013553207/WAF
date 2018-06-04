# -*- coding: utf-8 -*-
import re

search = lambda st, partten:  re.search(partten, st)
match = lambda  st, partten:  re.match(partten, st)

funcs = {
    'args': search,
    'cookie': search,
    'requestbody': search,
    'responsebody': search,
    'url': search,
    'user_agent': lambda st, partten:  partten in st
}