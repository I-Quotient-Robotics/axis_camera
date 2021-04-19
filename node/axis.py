#!/usr/bin/env python
# -*- coding: utf-8 -*-
  
import sys
import cv2
import time
import urllib
import urllib2

import rospy
from sensor_msgs.msg import CompressedImage, CameraInfo
#import camera_info_manager

class axis(object):
  def __init__(self, hostname, username, password, frame_id):
    self.hostname = hostname
    self.username = username
    self.password = password
    self.frame_id = frame_id
    self.timeout = 2.5

    self.url_axis = "http://%s" % hostname
    self.url_image = 'http://%s/mjpg/video.mjpg?' % hostname

    self.pub_image = rospy.Publisher("~image_raw/compressed", CompressedImage, queue_size=1)
    #self.pub_image_info = rospy.Publisher("~image_info",CameraInfo, queue_size=1)

    self.loginAuth()
    self.openCamera()

  def loginAuth(self):
    try:
      password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
      password_mgr.add_password(None, self.url_axis, self.username, self.password)
      handler = urllib2.HTTPDigestAuthHandler(password_mgr)
      opener = urllib2.build_opener(handler)
      urllib2.install_opener(opener)
      return True
    except:
      return False

  def openCamera(self):
    try:
      self.fp = urllib2.urlopen(self.url_image, timeout=self.timeout)
      rospy.loginfo("opening camera successful!!")
      return True
    except urllib2.URLError, e:
      rospy.logerr("Error opening URL %s\t" % (self.url_image))
      return False

  def getImage(self):
    boundary = self.fp.readline()
    if boundary == '--myboundary\r\n':
      return False
    header = {}
    while not rospy.is_shutdown():
      line = self.fp.readline()
      if line == "\r\n":
        break
      line = line.strip()
      parts = line.split(": ", 1)
      try:
        header[parts[0]] = parts[1]
      except:
        rospy.logwarn('Problem encountered with image header.  Setting '
                      'content_length to zero')
        header['Content-Length'] = 0
    content_length = int(header['Content-Length'])
    if content_length > 0:
      self.img = self.fp.read(content_length)
      self.fp.readline()
      return True  

  def pubImage(self):
    image = CompressedImage()
    image.header.stamp = rospy.Time.now()
    image.header.frame_id = self.frame_id
    image.format = "jpeg"
    image.data = self.img
    self.pub_image.publish(image)

  def pubImageInfo(self):
    msg = CameraInfo()
    msg.header.stamp = rospy.Time.now()
    msg.header.frame_id = self.frame_id
    msg.height = 1080
    msg.width  = 1920
    self.pub_image_info.publish(msg)
