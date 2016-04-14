#!/usr/bin/env python2

import rospy
import tf
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import Point
from nav_msgs.msg import OccupancyGrid

import numpy as np
import png
import random
import io

map_frame = "/map"
link_frame = "/base_link"


def pubGoal(x, y, th):
    ps = PoseStamped()
    ps.header.seq = 1
    ps.header.stamp = rospy.Time.now()
    ps.header.frame_id = "map"
    ps.pose.position.x = x
    ps.pose.position.y = y
    ps.pose.position.z = 0.0
    ps.pose.orientation = tf.transformations.quaternion_from_euler(0, 0, th)

    pubGoalPose.publish(ps)


def callbackGoal(data):
    rospy.loginfo(
        "RELAY (" +
        str(data.x) +
        "; " +
        str(data.y) +
        "; " +
        str(data.z) +
        ")"
    )
    pubGoal(data.x, data.y, data.z)


def callbackMap(data):
    rospy.loginfo("RELAY recieved map")
    na = np.array(data.data)
    p = np.reshape(na, (data.info.height, data.info.width), 'C')
    print p

    # rand = str(random.randrange(0, 999999))
    # path = '/tmp/' + rand + '.png'
    # f = open(path, 'wb')
    f = io.BytesIO()
    w = png.Writer(data.info.width, data.info.height, greyscale=True)
    w.write(f, (p / 100 + 1) * 100)

    # rospy.loginfo("RELAY map saved to " + path)

    pnghex = ''.join(["%02X" % ord(x) for x in f.getvalue()]).strip()

    f.close()

    rospy.loginfo("hex length: " + str(len(pnghex)))
    # rospy.loginfo(pnghex)


if __name__ == '__main__':
    rospy.init_node('relay', anonymous=True)
    rospy.loginfo("RELAY init")

    rospy.Subscriber("logistics_goal", Point, callbackGoal)
    rospy.Subscriber("map", OccupancyGrid, callbackMap)
    pubGoalPose = rospy.Publisher(
        'move_base_simple/goal', PoseStamped, queue_size=10)
    pubCurrentPose = rospy.Publisher(
        'logistics_pose', Point, queue_size=10)

    rate = rospy.Rate(1)
    listener = tf.TransformListener()

    while not rospy.is_shutdown():
        rospy.loginfo("RELAY pose lookup")

        while(
            (not listener.frameExists(map_frame)) or
            (not listener.frameExists(link_frame)) and
            (not rospy.is_shutdown())
        ):
            # rospy.loginfo("RELAY waiting for position")
            rate.sleep()

        t = listener.getLatestCommonTime(link_frame, map_frame)
        position, quaternion = listener.lookupTransform(
            link_frame, map_frame, t)

        rospy.loginfo("RELAY pose " + str((position, quaternion)))

        p = Point()

        pubCurrentPose.publish(p)

        rate.sleep()
