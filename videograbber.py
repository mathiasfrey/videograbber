#!/usr/bin/env python

# Author: mathias.frey[at]wu.ac.at
# Date: 2012-01-12
#
# Keywords: Python PyQt4 v4l video capture grab photobooth
#
# This code is more or less stolen from
# - http://stackoverflow.com/questions/2398958/python-qt-gstreamer
# - http://gstreamer-devel.966125.n4.nabble.com/Segfault-when-using-callbacks-in-gst-python-for-buffer-retrieval-td968801.html
#
# My modification: plug and play; no brainpower needed;-)
# just run this script, have a webcam connected
# and look for a test.png in /tmp/


import sys
import gobject 
gobject.threads_init() 

import gst

from PyQt4.Qt import *
from PyQt4 import QtWebKit


def fcapture(self):
    pm = QPixmap.grabWindow(wId)
    pm.save('/tmp/test.png')
    print 'captured!'

class ControlWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Quit button')

        quit = QPushButton('Close', self)
        quit.setGeometry(10, 10, 60, 35)
        
        # old style signal connection
        self.connect(quit, SIGNAL('clicked()'),
            qApp, SLOT('quit()'))
        
        
        # capture
        capture = QPushButton('Capture', self)
        capture.setGeometry(60, 60, 60, 35)
        
        # new style connection (more pythonic)
        capture.clicked.connect(fcapture)
        
#self.screenshot =
#ImageItem(QtGui.QImage.fromData(self._menu_manager.getImage(self.name)),
#550, imgHeight, self.scene(), self)
#self.screenshot.setPos(150, self.description.pos().y() +
#self.description.boundingRect().height() + 10)        

class VideoGrabber(QWidget):
    
    def __init__(self, parent=None):
        
        QWidget.__init__(self, parent)
        #self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('VideoGrabber')
        
        
        #
        #self.cameraWindow = QWidget(self)
        self.setGeometry(QRect(530, 20, 720, 1280))
        self.setObjectName("cameraWindow")
        #self.setAttribute(0, 1); # AA_ImmediateWidgetCreation == 0
        #self.setAttribute(3, 1); # AA_NativeWindow == 3    
        global wId
        wId = self.winId()


class Vid(object):
    
    def __init__(self, windowId):
        
        self.player = gst.Pipeline("player")
        #self.player = gst.element_factory_make("playbin2", "player")
        
        
        self.source = gst.element_factory_make("v4l2src", "vsource")
        self.sink = gst.element_factory_make("autovideosink", "outsink")
        self.source.set_property("device", "/dev/video0")
        
        #colorspace = gst.element_factory_make("ffmpegcolorspace", "colorspace")
        
        #import pdb; pdb.set_trace()
        
        # rotate video into correct viewing pos
        videoflip1 = gst.element_factory_make("videoflip")
        videoflip1.set_property('method', 'counterclockwise')
        
        # flip horizontally to achieve mirror effect
        videoflip2 = gst.element_factory_make("videoflip")
        videoflip2.set_property('method', 4)
        
        #colorspace.set_property('method', 'counterclockwise')
        #colorspace.set_property('method', 5)
        #
        
        #self.scaler = gst.element_factory_make("videoscale", "vscale")
        self.fvidscale = gst.element_factory_make("videoscale", "fvidscale")
        
        
        #videoflip = gst.element_factory_make("capsfilter", "videoflip")
        #videoflip.set_property('rotate','clockwise')
        

        self.fvidscale_cap = gst.element_factory_make("capsfilter", "fvidscale_cap")
        self.fvidscale_cap.set_property('caps', gst.caps_from_string('video/x-raw-yuv, width=720, height=1280'))
        
        self.window_id = None
        self.windowId = windowId
        #print windowId
    
        self.player.add(self.source, self.fvidscale, self.fvidscale_cap, self.sink, videoflip1, videoflip2)
        gst.element_link_many(self.source,self.fvidscale, self.fvidscale_cap, videoflip1, videoflip2, self.sink)
    
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)        
    
    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.player.set_state(gst.STATE_NULL)        

    def on_sync_message(self, bus, message):
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            win_id = self.windowId
            assert win_id
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_xwindow_id(win_id)

    def startPrev(self):
        self.player.set_state(gst.STATE_PLAYING)
    
    def pausePrev(self):
        self.player.set_state(gst.STATE_NULL)
        



        
        
if __name__ == '__main__':
    
    app = QApplication([])

    #m = QMainWindow()
    #m.show()    

    #web = QtWebKit.QWebView()
    #web.load(QUrl('http://bach.wu.ac.at/start/vz/'))
    #web.show()

    
    
    vg = VideoGrabber()
    vg.show()
    
    
    camera = Vid(wId)
    #import pdb; pdb.set_trace()
    #print wId
    camera.startPrev()
    
    cw = ControlWidget()
    cw.show()

    #cb = CaptureButton()
    #cb.show()

    app.exec_()
