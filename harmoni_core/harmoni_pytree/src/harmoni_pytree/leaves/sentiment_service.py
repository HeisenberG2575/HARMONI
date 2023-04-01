#!/usr/bin/env python3

# Common Imports
import rospy
import roslib

from harmoni_common_lib.constants import *
from actionlib_msgs.msg import GoalStatus
from harmoni_common_lib.service_server import HarmoniServiceServer
from harmoni_common_lib.service_manager import HarmoniServiceManager
from harmoni_common_lib.action_client import HarmoniActionClient
import harmoni_common_lib.helper_functions as hf
from harmoni_sentiment.sentiment_service import SentimentService
# Specific Imports
from harmoni_common_lib.constants import ActuatorNameSpace, ActionType, State, DialogueNameSpace
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
from collections import deque 
import soundfile as sf
import numpy as np
import boto3
import re
import json
import ast
import sys

#py_tree
import py_trees
import time

import py_trees.console

class SentimentServicePytree(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        self.name = name
        self.server_state = None
        self.service_client_sentiment = None
        self.client_result = None
        self.send_request = True

        # here there is the inizialization of the blackboards
        self.blackboards = []
        self.blackboard_sentiment = self.attach_blackboard_client(name=self.name, namespace=ActuatorNameSpace.sentiment.name)
        self.blackboard_sentiment.register_key("result", access=py_trees.common.Access.WRITE)
        self.blackboard_bot = self.attach_blackboard_client(name=self.name, namespace=DialogueNameSpace.bot.name +"/"+PyTreeNameSpace.trigger.name)
        self.blackboard_bot.register_key("result", access=py_trees.common.Access.READ)

        super(SentimentServicePytree, self).__init__(name)
        self.logger.debug("%s.__init__()" % (self.__class__.__name__))

    def setup(self,**additional_parameters):
        self.service_client_sentiment = HarmoniActionClient(self.name)
        self.server_name = "sentiment_default"
        self.service_client_sentiment.setup_client(self.server_name, 
                                            self._result_callback,
                                            self._feedback_callback)
        self.logger.debug("Behavior %s interface action clients have been set up!" % (self.server_name))
        
        self.blackboard_sentiment.result = "null"

        self.logger.debug("%s.setup()" % (self.__class__.__name__))

    def initialise(self):   
        self.logger.debug("%s.initialise()" % (self.__class__.__name__))

    def update(self):    
        if self.send_request:
            rospy.loginfo("-------------------THE MESSAGE RECEIVED IS ")
            rospy.loginfo(self.blackboard_bot.result["message"])
            self.send_request = False
            self.logger.debug(f"Sending goal to {self.server_name}")
            self.service_client_sentiment.send_goal(
                action_goal = ActionType["REQUEST"].value,
                optional_data = self.blackboard_bot.result["message"],
                wait=False,
            )
            self.logger.debug(f"Goal sent to {self.server_name}")
            new_status = py_trees.common.Status.RUNNING
        else:
            new_state = self.service_client_sentiment.get_state()
            print("update : ",new_state)
            if new_state == GoalStatus.ACTIVE:
                new_status = py_trees.common.Status.RUNNING
            elif new_state == GoalStatus.SUCCEEDED:
                if self.client_result is not None:
                    self.blackboard_sentiment.result = self.client_result
                    self.client_result = None
                    new_status = py_trees.common.Status.SUCCESS
                else:
                    self.logger.debug(f"Waiting fot the result ({self.server_name})")
                    new_status = py_trees.common.Status.RUNNING
            elif new_state == GoalStatus.PENDING:
                self.send_request = True
                self.logger.debug(f"Cancelling goal to {self.server_name}")
                self.service_client_sentiment.cancel_all_goals()
                self.client_result = None
                self.logger.debug(f"Goal cancelled to {self.server_name}")
                #self.service_client_sentiment.stop_tracking_goal()
                #self.logger.debug(f"Goal tracking stopped to {self.server_name}")
                new_status = py_trees.common.Status.RUNNING
            else:
                new_status = py_trees.common.Status.FAILURE
                raise

        self.logger.debug("%s.update()[%s]--->[%s]" % (self.__class__.__name__, self.status, new_status))
        return new_status

        
    def terminate(self, new_status):
        new_state = self.service_client_sentiment.get_state()
        print("terminate : ",new_state)
        if new_state == GoalStatus.SUCCEEDED or new_state == GoalStatus.ABORTED or new_state == GoalStatus.LOST:
            self.send_request = True
        if new_state == GoalStatus.PENDING:
            self.send_request = True
            self.logger.debug(f"Cancelling goal to {self.server_name}")
            self.service_client_sentiment.cancel_all_goals()
            self.client_result = None
            self.logger.debug(f"Goal cancelled to {self.server_name}")
            #self.service_client_sentiment.stop_tracking_goal()
            #self.logger.debug(f"Goal tracking stopped to {self.server_name}")
        self.logger.debug("%s.terminate()[%s->%s]" % (self.__class__.__name__, self.status, new_status))

    def _result_callback(self, result):
        """ Recieve and store result with timestamp """
        self.logger.debug("The result of the request has been received")
        self.logger.debug(
            f"The result callback message from {result['service']} was {len(result['message'])} long"
        )
        self.client_result = result["message"]
        return

    def _feedback_callback(self, feedback):
        """ Feedback is currently just logged """
        self.logger.debug("The feedback recieved is %s." % feedback)
        self.server_state = feedback["state"]
        return

def main():
    #command_line_argument_parser().parse_args()

    py_trees.logging.level = py_trees.logging.Level.DEBUG
    
    blackboardProva = py_trees.blackboard.Client(name="blackboardProva", namespace=DialogueNameSpace.bot.name +"/"+PyTreeNameSpace.trigger.name)
    blackboardProva.register_key("result", access=py_trees.common.Access.WRITE)
    blackboardProva.result = {
                                "message": "Ciao sono Kitty"
                            }
    blackboardProva2 = py_trees.blackboard.Client(name="blackboardProva2", namespace=ActuatorNameSpace.sentiment.name)
    blackboardProva2.register_key("result", access=py_trees.common.Access.READ)                        
    print(blackboardProva)
    print(blackboardProva2)

    rospy.init_node("sentiment_default", log_level=rospy.INFO)
    
    sentimentPyTree = SentimentServicePytree("SentimentServicePytree")
    sentimentPyTree.setup()
    try:
        for unused_i in range(0, 10):
            sentimentPyTree.tick_once()
            time.sleep(0.5)
            print(blackboardProva)
            print(blackboardProva2)
        print("\n")
    except KeyboardInterrupt:
        print("Exception occurred")
        pass

if __name__ == "__main__":
    main()