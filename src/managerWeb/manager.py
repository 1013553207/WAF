# -*- coding: utf-8 -*-
import tornado.web
import tornado.httpserver
import tornado.auth
import tornado.ioloop


from src.managerWeb.config import setting
from tornado.web import StaticFileHandler

from src.managerWeb.views import rootView, \
                                homeView


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', rootView.rootViewHandler),
            (r'/homepage', homeView.homeViewHandler),
            (r"/static/(.*)", StaticFileHandler, {"path": setting.STATIC_HOME})
        ]
        tornado.web.Application.__init__(self, handlers, **setting.settings)

if __name__ == '__main__':
    app = Application()
    server = tornado.httpserver.HTTPServer(app)
    server.listen(80)
    tornado.ioloop.IOLoop.instance().start()