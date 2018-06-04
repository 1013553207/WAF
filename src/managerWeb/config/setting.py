# -*- coding: utf-8 -*-
import os
from mako.lookup import TemplateLookup

settings = {
        'debug': True
}

BASEPATH = os.path.join(os.path.dirname(__file__), "..")

STATIC_HOME = os.path.join(BASEPATH, 'static')

TLOOPUP = TemplateLookup(
    directories=[os.path.join(BASEPATH, 'template')],
    output_encoding='utf-8',
    input_encoding='utf-8',
    default_filters=['decode.utf8'],
    encoding_errors='replace'
)

if __name__ == '__main__':
    print(STATIC_HOME)