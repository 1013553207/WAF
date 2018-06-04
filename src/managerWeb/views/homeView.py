# -*- coding: utf-8 -*-
from tornado import web
from tornado import gen

from src.managerWeb.config.setting import *

class homeViewHandler(web.RequestHandler):
    @gen.coroutine
    def get(self):
        print(TLOOPUP.directories)
        homepage = TLOOPUP.get_template('homePage.html')
        data = homepage.render()
        self.write(data)
        self.flush()
        # self.finish()
