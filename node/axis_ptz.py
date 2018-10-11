#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import time
import math
import urllib
import urllib2
import threading

import rospy
import tf
import tf.broadcaster
from sensor_msgs.msg import JointState
from axis_camera.msg import axis_ptz_cmd
from axis_camera.msg import axis_ptz_msg


class axis_ptz(object):
    def __init__(self, hostname, username, password, joint_pub_flage, pan_joint_name="pan_tilt", tilt_joint_name="tilt_joint"):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = 5
        self.joint_pub_flage = joint_pub_flage
        self.pan_joint_name = pan_joint_name
        self.tilt_joint_name = tilt_joint_name
        
        self.url_axis = "http://%s" % hostname
        self.url_ptz = "http://%s/axis-cgi/com/ptz.cgi?" % self.hostname
        self.url_ptz_pos = "http://%s/axis-cgi/com/ptz.cgi?query=position" % self.hostname

        if self.joint_pub_flage:
            self.pub_joint = rospy.Publisher("joint_states", JointState, queue_size=1)
        self.pub_state = rospy.Publisher("axis_ptz_msg", axis_ptz_msg, queue_size=1)
        self.sub = rospy.Subscriber("axis_ptz_cmd", axis_ptz_cmd, self.callback, queue_size=1)

        self.loginAuth()


    def loginAuth(self):
        rospy.loginfo("login auth")
        try:
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, self.url_axis, self.username, self.password)
            handler = urllib2.HTTPDigestAuthHandler(password_mgr)
            opener = urllib2.build_opener(handler)
            urllib2.install_opener(opener)
            return True
        except:
            rospy.logerr("auth fail!!")
            return False

    def callback(self, msg):
        if self.set_ptz(msg.pan, msg.tilt, msg.zoom, msg.speed):
            rospy.loginfo("set pos successful!!")
        else:
            rospy.logerr("set pos error!!! ")

    def set_ptz(self, pan, tilt, zoom, speed):
        ptz_params = urllib.urlencode({'camera': 1, 'pan': pan, 'tilt': tilt, 'zoom': zoom, 'speed': speed})
        url_ptz_  = self.url_ptz + ptz_params
        try:
            fp = urllib2.urlopen(url_ptz_, timeout=self.timeout)
            return True
        except urllib2.URLError, e:
            rospy.logerr("Error opening URL %s\t" % (url_ptz_) + "Possible timeout.")
            return False

    def pub_ptz_msg(self):
        pos = self.read_pos()
        self.pub_state.publish(pos)
        if self.joint_pub_flage:
            msg = JointState()
            msg.header.stamp = rospy.Time.now()
            msg.name.append(self.pan_joint_name)
            msg.name.append(self.tilt_joint_name)

            msg.position.append(-pos.pan / 180.0 * math.pi)
            msg.position.append(-pos.tilt / 180.0 * math.pi)

            self.pub_joint.publish(msg)

    def read_pos(self):
        try:
            fp = urllib2.urlopen(self.url_ptz_pos, timeout=self.timeout)
        except urllib2.URLError, e:
            rospy.logerr("Error opening URL %s\t" % (self.url_ptz_pos) + "Possible timeout.")
            return 0
        time.sleep(0.01)
        str_s = fp.read()
        if str_s:
            list_s = str_s.split('\r\n')
            data = {}
            for _ in range(0,(len(list_s)-1)):
                s = list_s[_].split('=')
                if s[0]== 'autofocus' or s[0]== 'autoiris':
                    if s[1] == 'on':
                        data[s[0]] = 1
                    else:
                        data[s[0]] = 0
                else:
                    data[s[0]] = float(s[1])

            msg = axis_ptz_msg()
            msg.pan = data['pan']
            msg.tilt = data['tilt']
            msg.zoom = data['zoom']
            msg.focus = data['focus']
            msg.brightness = data['brightness']
            msg.autofocus = bool(data['autofocus'])
            msg.autoiris = bool(data['autoiris'])
            return msg

