FROM ros:humble

# nvidia-container-runtime
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=graphics,utility,compute

# Set environment variable to avoid dialog prompts
ENV DEBIAN_FRONTEND=noninteractive

# Source environments
# Set ROS_DOMAIN_ID to avoid conflicts with other ROS2 nodes running on the same network
# ID 0 is a common default, you can change it if you want to use a different one
ENV ROS_DOMAIN_ID=0

RUN apt-get update && apt-get install -y git gedit

RUN apt update && apt install -y python3-pip \
                                 python3-rosdep \
                                 python3-rosinstall \
                                 python3-rosinstall-generator \
                                 python3-wstool \
                                 build-essential 

# Turtlebot4 install
RUN apt update && apt install -y ros-humble-turtlebot4-desktop

# Turtlebot4 commons
RUN apt update && apt install -y ros-humble-turtlebot4-description \
                                 ros-humble-turtlebot4-msgs \
                                 ros-humble-turtlebot4-navigation \
                                 ros-humble-turtlebot4-node \
                                 ros-humble-teleop-twist-keyboard \
                                 ros-dev-tools
                                 
           
# Ignition Gazebo
RUN apt-get update && apt-get install -y wget && sh -c 'echo "deb http://packages.osrfoundation.org/gazebo/ubuntu-stable `lsb_release -cs` main" > /etc/apt/sources.list.d/gazebo-stable.list' && \
                                                 wget http://packages.osrfoundation.org/gazebo.key -O - | sudo apt-key add - && \
                                                 apt-get update && apt-get install -y ignition-fortress

# Simulation from source
RUN apt update && apt install -y ros-humble-turtlebot4-simulator terminator nano

# Use robot laser - Render engine
RUN sed -i 's/[[:space:]]*<render_engine>ogre<\/render_engine>/        <render_engine>ogre2<\/render_engine>/g' /opt/ros/humble/share/irobot_create_description/urdf/create3.urdf.xacro

# Bashrc
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "export ROS_DOMAIN_ID=0" >> /root/.bashrc

# Entrypoint
ADD entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
