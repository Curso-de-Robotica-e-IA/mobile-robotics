#!/usr/bin/env python3

"""
Publica uma pose inicial fixa no tópico /initialpose.

Uso:
    python3 set_initial_pose.py

Pré-requisitos:
    - Nav2 ativo
    - AMCL ativo
    - Mapa carregado

Mapa:
    hall_cin_v4.yaml

Posição inicial:
    x = 1.0216323137283325
    y = 16.61626625061035
    z = 0.0
    w = 1.0
"""

import time

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseWithCovarianceStamped


# ==================================
# POSE INICIAL DO EXPERIMENTO
# ==================================

START_X = 1.0216323137283325
START_Y = 16.61626625061035

ORIENTATION_Z = 0.0
ORIENTATION_W = 1.0


class InitialPosePublisher(Node):

    def __init__(self):
        super().__init__("set_initial_pose")

        self.publisher = self.create_publisher(
            PoseWithCovarianceStamped,
            "/initialpose",
            10,
        )

    def publish_initial_pose(self):

        msg = PoseWithCovarianceStamped()

        msg.header.frame_id = "map"
        msg.header.stamp = self.get_clock().now().to_msg()

        msg.pose.pose.position.x = START_X
        msg.pose.pose.position.y = START_Y
        msg.pose.pose.position.z = 0.0

        msg.pose.pose.orientation.x = 0.0
        msg.pose.pose.orientation.y = 0.0
        msg.pose.pose.orientation.z = ORIENTATION_Z
        msg.pose.pose.orientation.w = ORIENTATION_W

        # Covariância pequena
        msg.pose.covariance[0] = 0.25
        msg.pose.covariance[7] = 0.25
        msg.pose.covariance[35] = 0.068

        self.publisher.publish(msg)

        self.get_logger().info(
            f"Pose inicial publicada: "
            f"x={START_X:.2f}, "
            f"y={START_Y:.2f}"
        )


def main():

    rclpy.init()

    node = InitialPosePublisher()

    try:

        # Espera publisher conectar
        time.sleep(2.0)

        # Publica algumas vezes
        for _ in range(5):

            node.publish_initial_pose()

            rclpy.spin_once(
                node,
                timeout_sec=0.1
            )

            time.sleep(0.5)

        node.get_logger().info(
            "Pose inicial enviada com sucesso."
        )

    finally:

        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()