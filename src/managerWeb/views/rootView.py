# -*- coding: utf-8 -*-
from tornado import web
from tornado import gen

from src.managerWeb.config.setting import *

class rootViewHandler(web.RequestHandler):
    @gen.coroutine
    def get(self):
        self.redirect('/homepage')
