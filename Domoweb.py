#!/usr/bin/env python

import sys
if sys.version_info < (2, 6):
    print "Sorry, requires Python 2.6 or 2.7."
    sys.exit(1)    

# MQ
import os
from zmq.eventloop import ioloop
ioloop.install()
import domoweb
from domoweb.handlers import MainHandler, PageHandler, ConfigurationHandler, WSHandler, NoCacheStaticFileHandler, MQHandler
from domoweb.loaders import packLoader, mqDataLoader

#import tornado.ioloop
import tornado.web
from tornado.options import options
import logging

logging.basicConfig(format='%(asctime)s %(name)s:%(levelname)s %(message)s',level=logging.INFO)

logger = logging.getLogger('domoweb')

domoweb.FULLPATH = os.path.normpath(os.path.abspath(__file__))
domoweb.PROJECTPATH = os.path.dirname(domoweb.FULLPATH)
domoweb.PACKSPATH = os.path.join(domoweb.PROJECTPATH, 'packs')

application = tornado.web.Application(
    handlers=[
        (r"/(\d*)", MainHandler),
        (r"/page", PageHandler),
        (r"/configuration", ConfigurationHandler),
        (r"/widget/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "packs", 'widgets')}),
        (r"/images/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "static", 'images')}),
        (r"/libraries/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "static", 'libraries')}),
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "static", 'css')}),
        (r"/js/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "static", 'js')}),
        (r"/components/(.*)", NoCacheStaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "components")}),
        (r'/ws/', WSHandler),
    ],
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    debug=True,
    autoreload=True,
)

if __name__ == '__main__':

#    domoweb.VERSION = "dev.%s" % commands.getoutput("cd %s ; hg id -n 2>/dev/null" % domoweb.PROJECTPATH)

    # Check log folder
    if not os.path.isdir("/var/log/domoweb"):
        sys.stderr.write("Error: /var/log/domoweb do not exist")
        sys.exit(1)
    
    # Check config file
    SERVER_CONFIG = '/etc/domoweb.cfg'
    if not os.path.isfile(SERVER_CONFIG):
        sys.stderr.write("Error: Can't find the file '%s'\n" % SERVER_CONFIG)
        sys.exit(1)

    options.define("sqlite_db", default="/var/lib/domoweb/db.sqlite", help="Database file path", type=str)
    options.define("port", default=40404, help="Launch on the given port", type=int)
    options.define("debut", default=False, help="Debug mode", type=bool)
    options.parse_config_file("/etc/domoweb.cfg")

    logger.info("Running from : %s" % domoweb.PROJECTPATH)

    packLoader.loadWidgets(domoweb.PACKSPATH)
    packLoader.loadIconsets(domoweb.PACKSPATH)
    packLoader.loadThemes(domoweb.PACKSPATH)
    mqDataLoader.loadDatatypes()
    mqDataLoader.loadDevices()

    logger.info("Starting tornado web server")
    application.listen(options.port)
    logger.info("Starting MQ Handler")
    MQHandler()
    ioloop.IOLoop.instance().start() 
