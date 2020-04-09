#!/usr/bin/env python

# Importing the libraries
import rospy
import roslib
from action_server import HarmoniActionServer


class HardwareControlServer(HarmoniActionServer, object):
    """
    A hardware control provider receives some data which it will formulate
    into an action for the hardware
    """

    def __init__(self, name, service_manager):
        """
        Initialize hardware control, logical defaults, and publishers/subscribers
        Can optionally test connctivity and availability of the hardware
        @name: the name of the hardware element, will be the name of the server
        @service_manager: service managers should have the following fuctionality:
            service_manager.test() # sends default or example action
            service_manager.do(data) # processes data and does action
            service_manager.reset_init() # Resets hardware variables to initial state

            service_manager.action_completed# True if action completed
            service_manager.cont = Bool # Used IF logic can dictate control flow
            service_manager.result_msg = String # 
        """

        self.name = name
        self.service_manager = service_manager

        success = self.service_manager.test()
        if success:
            rospy.loginfo("{name} has been successfully set up")
        else:
            rospy.logwarn("{name} has not been started")
        self.setup_server(name, self.execute_goal_received_callback)

    def execute_goal_received_callback(self, goal):
        """
        Handle function execute in the goal reiceved callback
        """
        self.service_manager.do(goal.optional_data)  # status is in response_received, result in return_msg
        self.send_feedback("Doing action")

        while not self.service_manager.action_completed:
            if self.preemption_status():
                success = False
                rospy.Rate(10)

        if success:
            self.send_result(
                do_continue=self.service_manager.cont,
                message=self.service_manager.return_msg)
        return


class WebServiceServer(HarmoniActionServer, object):
    """
    An external service provider receives some data which it will formulate
    into an API request of some cloud provider
    """

    def __init__(self, name, service_manager):
        """
        Initialize web client, logical defaults, and publishers/subscribers
        Can optionally test connctivity with web services
        @name: the name of the external service, will be the name of the server
        @service_manager: service managers should have the following fuctionality:
            service_manager.test() # sends default message to server
            service_manager.request(data) # processes data and sends through API
            service_manager.reset_init() # Resets server to initial state

            service_manager.response_received = Bool # True if API returned a response
            service_manager.cont = Bool # Used if logic can dictate control flow
            service_manager.result_msg = String # 
        """
        self.name = name
        self.service_manager = service_manager

        success = self.service_manager.test()
        if success:
            rospy.loginfo("{name} has been successfully set up")
        else:
            rospy.logwarn("{name} has not been started")

        self.setup_server(name, self.execute_goal_received_callback)

    def execute_goal_received_callback(self, goal):
        """
        Currently not supporting sending data to external service except through optional_data
        """
        self.service_manager.request(goal.optional_data)  # status is in response_recieved, result in return_msg
        self.send_feedback("Processing")

        while not self.service_manager.response_received:
            if self.preemption_status():
                success = False
                rospy.Rate(10)

        if success:
            self.send_result(
                do_continue=self.service_manager.cont,
                message=self.service_manager.return_msg)
            self.service_manager.reset_init()
        return


class InternalServiceServer(HarmoniActionServer, object):
    """
    An Internal Service controls the behavior of a class that processes some
    data from a topic(s) and publishes it to a topic
    """

    def __init__(self, name, service_manager):
        """
        Initialize, control flow of information through processing class
        @name: the name of the external service, will be the name of the server
        @service_manager: service managers should have the following fuctionality:
            service_manager.test() # sends default message to server
            service_manager.reset_init() # Resets server to initial state
            service_manager.start(rate) # Rate is communicated in optional data
            service_manager.stop()

            service_manager.status = Int # TODO Set up status class
        """
        self.name = name
        self.service_manager = service_manager

        success = self.service_manager.test()
        if success:
            rospy.loginfo("{name} has been successfully set up")
        else:
            rospy.logwarn("{name} has not been started")
        self.setup_server(name, self.execute_goal_received_callback)
        while not rospy.is_shutdown():
            self.send_feedback(self.service_manager.status)
            rospy.loginfo("The microphone service status is %i" %self.service_manager.status)
            rospy.Rate(.2)



    def execute_goal_received_callback(self, goal):
        """Control flow through internal processing class"""
        # TODO better case management
        if goal.action == "start_{self.name}":
            if goal.optional_data != "":
                self.service_manager.start(int(goal.optional_data))
            else:
                self.service_manager.start()
        elif goal.action == "pause_{self.name}":
            self.service_manager.stop()
        elif goal.action == "stop_{self.name}":
            self.service_manager.stop()
            self.service_manager.reset_init
        return


class HarwareReadingServer(HarmoniActionServer, object):
    """
    An hardware reading class controls the behavior of a class that processes some
    data from a sensor and publishes it to a topic
    """

    def __init__(self, name, service_manager):
        """
        Initialize, control flow of information through sensor class
        @name: the name of the external service, will be the name of the server
        @service_manager: service managers should have the following fuctionality:
            service_manager.test() # sends default message to server
            service_manager.reset_init() # Resets server to initial state
            service_manager.start(rate) # Rate is communicated in optional data
            service_manager.stop()

            service_manager.status = Int # TODO Set up status class
        """
        self.name = name
        rospy.loginfo("The service name is %s" % self.name)
        self.service_manager = service_manager

        success = self.service_manager.test()
        if success:
            rospy.loginfo("%s has been successfully set up" % self.name)
        else:
            rospy.logwarn("%s has not been started" % self.name)
        self.setup_server(name, self.execute_goal_received_callback)
 
    def update_feedback(self):
        """Update the feedback message """
        rospy.loginfo("Start updating the feedback")
        while not rospy.is_shutdown():
            if self.service_manager.status != 3:
                if self.service_manager.status != 0:
                    self.send_feedback(self.service_manager.status)
                rospy.Rate(.2)
            else:
                break
        return

    def execute_goal_received_callback(self, goal):
        """Control flow through internal processing class"""
        # TODO better case management here
        if goal.action == "start_%s" % self.name:
            if goal.optional_data != "":
                self.service_manager.start(int(goal.optional_data))
            else:
                self.service_manager.start()
        elif goal.action == "pause_%s" % self.name:
            self.service_manager.pause()
        elif goal.action == "stop_%s" % self.name:
            self.service_manager.stop()
            self.service_manager.reset_init
        return
