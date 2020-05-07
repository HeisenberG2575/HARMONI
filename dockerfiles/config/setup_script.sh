#!/bin/bash

echo 'Hello, rosmaster'

source /opt/ros/$ROS_DISTRO/setup.bash 
source /root/harmoni_catkin_ws/devel/setup.bash

alias rh="roscd; cd .."
alias rs="roscd; cd ../src"
alias cm="roscd; cd ..; catkin_make"
alias cb="roscd; cd ..; catkin build"
alias cbs="roscd; cd ..; catkin build; source devel/setup.bash"
alias rlspeech="roslaunch harmoni_stt stt_example.launch"
alias rlservices="roslaunch harmoni_decision services.launch use_harmoni_services:=false"
alias rlrouters="roslaunch harmoni_decision routers.launch"

# if [ "$ROS_HOSTNAME" = "ros_w2l" ]
# then 
#     roslaunch harmoni_stt stt_example.launch

# elif [ "$ROS_HOSTNAME" = "ros_pc" ]
# then 
#     roslaunch harmoni_decision services.launch use_harmoni_services:=false

# elif [ "$ROS_HOSTNAME" = "harmoni_core" ]
# then 
#     roscore
#     roslaunch harmoni_decision routers.launch

# fi