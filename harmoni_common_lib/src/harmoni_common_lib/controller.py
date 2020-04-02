#!/usr/bin/env python

# Importing the libraries
import rospy
import roslib
from action_server import HarmoniActionServer
from action_client import HarmoniActionClient
from collections import defaultdict

TIMEOUT_FOR_RESULT = 10
TIMEOUT_FOR_SERVER = 10

class HarmoniController(HarmoniActionServer):
    """
    A control provider receives some request from the manager and send the corresponding 
    request action to the child.
    This class provides basic controller functionality which the subclasses of controller can exploit
    """

    def __init__(self, controller_name, child_names, last_event):
        """ Initialization of the variables """
        self.timeout_for_result = TIMEOUT_FOR_RESULT
        self.timeout_for_server = TIMEOUT_FOR_SERVER
        self.last_event = last_event
        self.children_clients = defaultdict(HarmoniActionClient())
        for child in child_names:
            self.children_clients[child] = HarmoniActionClient()
        self.controller_name = controller_name

    def setup_actions(self, execute_goal_result_callback, execute_goal_feedback_callback):
        """ Setup clients of each subclass and the server of the controller"""
        for child, client in self.children_clients:
            client.setup_client(child, execute_goal_result_callback, execute_goal_feedback_callback)

        self.setup_server(self.controller_name, self.execute_goal_received_callback)
        return

    def setup_conditional_startup(self, condition_event, checked_event):
        """ Set condition for starting the action """
        while condition_event != checked_event:
            rospy.loginfo("Waiting for event to finish")
            rospy.Rate(1)
        rospy.loginfo("Conditional event ended successfully")
        return

    def execute_goal_received_callback(self, goal):
        """ 
        Receiving the request (server role)
        Check if setting up a conditional startup or not
        Sending the goal request to the server (client role)
        """
        rospy.loginfo("The request data are:" + str(goal))
        if goal.condition != "uncondition":  # check if the action is conditioned by another event or not
            self.setup_conditional_startup(goal.condition, self.last_event)

        rospy.loginfo("Start a goal request to the child")
        self.children_clients[goal.child].send_goal(action_goal=goal.child, optional_data=goal.optional_data, condition="", timeout=self.timeout)
        return
