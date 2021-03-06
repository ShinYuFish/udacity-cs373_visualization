#!/usr/bin/env python

#------------------------------------To-Do--------------------------------------------#
#1. separate print path process and drawing process
#2. TBD
#-------------------------------------------------------------------------------------#
import rospy
import sys
import math
from std_msgs.msg import String
from visualization_msgs.msg import Marker
from visualization_msgs.msg import MarkerArray
import numpy as np
from grid import *

class print_path():
    def __init__(self):
        self.publisher = rospy.Publisher('visualize_marker_array', MarkerArray, queue_size=10)
        self.marker_array = MarkerArray()
        #--------------------------------Parameter Setup-------------------------------#
        #initialize map
        self.init = [0, 0]
        tmp_grid = grid(6, 10, 'num')
        tmp_grid.set_obstacle(1, 1, 3, 3)
        self.grid = tmp_grid.map
        self.goal = [len(self.grid)-1, len(self.grid[0])-1] 
        #initialize condition
        self.cost = 1
        self.is_get_goal = False
        self.no_path_to_go = False
        self.directions = [[-1, 0], # go up
            [ 0,-1], # go left
            [ 1, 0], # go down
            [ 0, 1]] # go right
        self.directions_name = ['^', '<', 'v', '>']
        #initialize openlist and walkthrough path
        self.openlist = []
        self.openlist.append([0, self.init[0], self.init[1]])
        self.closed = [[0 for row in range(len(self.grid[0]))] for col in range(len(self.grid))]
        self.walkthrough = [[' ' for row in range(len(self.grid[0]))] for col in range(len(self.grid))]
        self.expand = [[' ' for row in range(len(self.grid[0]))] for col in range(len(self.grid))]
        self.closed[self.init[0]][self.init[1]] = 1

        #--------------------------------Begin Plot-------------------------------# 
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                marker = Marker()
                marker.header.frame_id = "/world"
                marker.id = i * len(self.grid[0]) + j
                marker.ns = "tiles"
                marker.header.stamp = rospy.get_rostime()
                marker.type = marker.SPHERE
                marker.action = marker.ADD
                marker.scale.x = 0.5
                marker.scale.y = 0.5
                marker.scale.z = 0.5
                marker.pose.orientation.w = 1.0
                marker.pose.position.x = i
                marker.pose.position.y = j
                marker.color.a = 1.0 #1.0 -> complete not transparent 0.0-> complete transparent
                #set different color for available path and obstacle
                if self.grid[i][j] == 1:
                    marker.color.r = 0 / 255.0
                    marker.color.g = 0 / 255.0
                    marker.color.b = 0 / 255.0
                elif self.grid[i][j] == 0:
                    marker.color.r = 255 / 255.0
                    marker.color.g = 255 / 255.0
                    marker.color.b = 204 / 255.0
                self.marker_array.markers.append(marker)
        
        self.publisher.publish(self.marker_array)
        rospy.loginfo("Finished INITIALIZE process")
    #--------------------------------Path Finding Algorithm-------------------------------# 
    def iteration(self):
        if not self.openlist:
            self.no_path_to_go =True
            return
        else:
            self.openlist.sort()
            self.openlist.reverse()
            self.next = self.openlist.pop()

            x = self.next[1]
            y = self.next[2]
            self.value = self.next[0]
            print 'current postion:', x, ', ',y
            

            if x == self.goal[0] and y == self.goal[1]:
                self.is_get_goal = True
                self.expand[x][y] = '*'    
                rospy.loginfo("ARRIVE GOAL")
                return 
            else:
                for i in range(len(self.directions)):
                    x2 = x + self.directions[i][0]
                    y2 = y + self.directions[i][1]
                    if x2 >= 0 and x2 < len(self.grid) and y2 >=0 and y2 < len(self.grid[0]):
                        if self.closed[x2][y2] == 0 and self.grid[x2][y2] == 0:
                            g2 = self.value + self.cost
                            self.openlist.append([g2, x2, y2])
                            self.closed[x2][y2] = 1
                            self.walkthrough[x][y] = self.directions_name[i]
                            self.set_color(self.xy_to_id(x2,y2), 230, 172, 0 )
                            self.publisher.publish(self.marker_array)
                self.set_color(self.xy_to_id(x, y), 230, 115, 0)
                self.publisher.publish(self.marker_array)

    def backpropagation(self):
        '''
        iterate back to get directions
        '''
        x = 0
        y = 0
        count = 0
        while count < self.value:
            self.expand[x][y] = self.walkthrough[x][y]
            here = self.expand[x][y]
            if here in self.directions_name:
                direction = self.directions_name.index(here)
                x += self.directions[direction][0]
                y += self.directions[direction][1]
                self.set_color(self.xy_to_id(x, y), 64, 255, 0)            
            count += 1

        self.set_color(self.xy_to_id(self.init[0], self.init[1]), 64, 255, 0)
        self.publisher.publish(self.marker_array)
        return 
    #------------------------------Visualization Helper Function-------------------------------#
    def set_color(self, id, r, g, b):
        '''
        easier to set color for each marker
        '''
        self.marker_array.markers[id].color.r = r / 255.0
        self.marker_array.markers[id].color.g = g / 255.0
        self.marker_array.markers[id].color.b = b / 255.0

    def xy_to_id(self, x, y):
        '''
        turn one point's x,y coordinate into it's ID number
        '''
        return x * len(self.grid[0]) + y

    def draw(self):
        self.set_color(self.xy_to_id(self.init[0], self.init[1]), 255, 0, 0)
        self.set_color(self.xy_to_id(self.goal[0], self.goal[1]), 64, 255, 0)

        self.publisher.publish(self.marker_array)

def main(args):
    rospy.init_node('path_handler', anonymous=True)
    map = print_path()

    #d = rospy.Duration(0.5, 0)
    r = rospy.Rate(5) #Hz
    while (not rospy.is_shutdown()) and (not map.is_get_goal) and (not map.no_path_to_go):
        map.iteration()
        if map.is_get_goal:
            print "-----------------------ready to print path-----------------------------"
            map.backpropagation()
            rospy.loginfo("PRINT OUT THE PATH IN LOG")
            for i in range(len(map.expand)):
                print map.expand[i]
        elif map.no_path_to_go:
            rospy.logerr("UNABLE TO FIND A PATH")
        else:
            map.draw()
        #rospy.sleep(d)
        r.sleep()

#can be used as class by import
if __name__ == '__main__':
    try:
        main(sys.argv)
    #terminate program when using ctrl+c or close node
    except rospy.ROSInterruptException:
        pass
