# Mycroft Skill that starts a http-server on port 8085 &
# takes & displays pictures from the raspi-camera every few seconds
# By Nold 2017 - GPLv3 licensed

# pip install picamera
import picamera

import SimpleHTTPServer
import SocketServer

import threading

from time import sleep
from os.path import dirname, join, abspath

from os import rename, mkdir, chdir
from shutil import copyfile

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger
from mycroft.util import play_wav

__author__ = 'nold'

logger = getLogger(__name__)


class LiveCamera(MycroftSkill):
    http_port = 8085
    http_root_path = '/tmp/mycroft-livecamera'
    update_interval = 2
    resolution = (1024, 768)

    do_shutdown = False

    def __init__(self):
        super(LiveCamera, self).__init__(name="LiveCamera")

    def initialize(self):
        if self.config:
            self.update_interval = self.config.get('update_interval', 2)
            self.http_port = self.config.get('http_port', 8085)
            self.resolution = self.config.get('resolution', '720p')

        try:
            self.camera = picamera.PiCamera(resolution=self.resolution)
        except:
            logger.error("Couldn't open PiCamera Interface, is it enabled?")
        else:
            logger.debug("Creating temp-dir & moving files")
            try:
                mkdir(self.http_root_path)
            except:
                pass
            logger.debug("http_root_path: " + str(self.http_root_path))

            copyfile(str(dirname(abspath(__file__)) + "/static/index.html"),\
                     str(self.http_root_path + "/index.html" ))
            chdir(self.http_root_path)

            logger.debug("Starting PictureThread...")
            self.picture_thread = threading.Thread(target=self.take_pictures)
            self.picture_thread.daemon = True
            self.picture_thread.start()

            logger.debug("Starting HTTPServerThread...")
            self.http_thread = threading.Thread(target=self.http_server)
            self.http_thread.daemon = True
            self.http_thread.start()

    def http_server(self):
        #TODO: We should catch this, but without the Server
        #      we don't need to continue anyway..
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        SocketServer.TCPServer.allow_reuse_address = True
        self.httpd = SocketServer.TCPServer(("", self.http_port), Handler)
        logger.info("Serving at port " + str(self.http_port))
        self.httpd.serve_forever()

    def take_pictures(self):
        logger.debug("PictureThread loaded!")
        while not self.do_shutdown:
            try:
                self.camera.capture(str(self.http_root_path) + '/tmp-image.jpg')
            except:
                logger.error("Couldn't capture picture; dying!")
                self.do_shutdown = True

            try:
                rename(str(self.http_root_path) + '/tmp-image.jpg',\
                        str(self.http_root_path) + '/image.jpg')
            except:
                logger.error("Couldn't move image for serving... Trying to continue")
            sleep(self.update_interval)

    def stop(self):
        self.do_shutdown = True
        sleep(self.update_interval)

        try:
            self.httpd.shutdown()
        except:
            pass
        finally:
            self.httpd.server_close()

        try:
            self.camera.close()
        except:
            pass

def create_skill():
    return LiveCamera()
