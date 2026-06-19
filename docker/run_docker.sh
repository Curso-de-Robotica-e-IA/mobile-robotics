# Precisa desse comando todas as vezes que for rodar o docker
xhost si:localuser:root

docker run -it \
           --privileged \
           --name ttb4 \
           --net=host --privileged \
           --device=/dev/ttyUSB0 \
           -e ROS_DOMAIN_ID=0 \
           -v /dev:/dev \
           -v /tmp/.X11-unix:/tmp/.X11-unix \
           -v /etc/timezone:/etc/timezone:ro \
           -v /etc/localtime:/etc/localtime:ro \
           --volume="$HOME/.Xauthority:/root/.Xauthority:rw" \
           --volume="$HOME/dev/turtlebot4/ttb4_ws:/ttb4_ws:rw" \
           --env=QT_X11_NO_MITSHM=1 \
           --env="DISPLAY" \
	   --env="NVIDIA_DRIVER_CAPABILITIES=all"\
           --gpus all \
           --rm \
           t4 \
           bash
