import logging

from .sync_db import EchoWebSocket

import tornado.ioloop
from tornado.options import define,options
import threading

define('ws_port',default=9000,type=int)

_logger = logging.getLogger(__name__)

def main():
    application = tornado.web.Application([(r"/", EchoWebSocket), ])
    application.listen(options.ws_port)
    threading._start_new_thread(tornado.ioloop.IOLoop.instance().start, ())
    _logger.info('websocket service has started!! listening on Port %s' % options.ws_port)

main()
