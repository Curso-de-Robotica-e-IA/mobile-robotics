#!/usr/bin/env python3

"""
Replay de trajetória gravada.

Lê um CSV gerado pelo record_trajectory.py e envia
a sequência de poses para o Nav2 usando NavigateThroughPoses.

Uso:

python3 replay_trajectory.py \
    --csv trajetoria_referencia.csv

"""

import csv
import argparse

import rclpy

from rclpy.node import Node

from geometry_msgs.msg import PoseStamped

from nav2_simple_commander.robot_navigator import (
    BasicNavigator,
    TaskResult,
)


# ==========================================
# CONFIGURAÇÕES
# ==========================================

WAYPOINT_SPACING = 1.0
# metros entre waypoints consecutivos


# ==========================================
# UTILIDADES
# ==========================================

def distance(p1, p2):
    dx = p1["x"] - p2["x"]
    dy = p1["y"] - p2["y"]
    return (dx**2 + dy**2) ** 0.5


def load_csv(csv_file):
    """
    Carrega trajetória gravada.
    """

    points = []

    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            points.append(
                {
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                    "yaw": float(row["yaw"]),
                }
            )

    return points


def reduce_waypoints(points):
    """
    Reduz a densidade do CSV.

    Ex:
    trajetória gravada com centenas de pontos.

    Mantemos apenas pontos separados
    por pelo menos WAYPOINT_SPACING metros.
    """

    if not points:
        return []

    result = [points[0]]

    last = points[0]

    for p in points[1:]:

        if distance(p, last) >= WAYPOINT_SPACING:
            result.append(p)
            last = p

    if result[-1] != points[-1]:
        result.append(points[-1])

    return result


def yaw_to_quaternion(yaw):
    """
    Converte yaw para quaternion.
    """

    import math

    qz = math.sin(yaw / 2.0)
    qw = math.cos(yaw / 2.0)

    return qz, qw


# ==========================================
# NODE
# ==========================================

class TrajectoryReplay(Node):

    def __init__(self):
        super().__init__("trajectory_replay")


# ==========================================
# MAIN
# ==========================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--csv",
        required=True,
        help="CSV da trajetória de referência"
    )

    args = parser.parse_args()

    rclpy.init()

    node = TrajectoryReplay()

    navigator = BasicNavigator()

    node.get_logger().info("Waiting Nav2...")

    navigator.waitUntilNav2Active()

    points = load_csv(args.csv)

    node.get_logger().info(
        f"Loaded {len(points)} trajectory samples"
    )

    waypoints = reduce_waypoints(points)

    node.get_logger().info(
        f"Generated {len(waypoints)} replay waypoints"
    )

    poses = []

    for p in waypoints:

        pose = PoseStamped()

        pose.header.frame_id = "map"
        pose.header.stamp = (
            navigator.get_clock()
            .now()
            .to_msg()
        )

        pose.pose.position.x = p["x"]
        pose.pose.position.y = p["y"]

        qz, qw = yaw_to_quaternion(
            p["yaw"]
        )

        pose.pose.orientation.z = qz
        pose.pose.orientation.w = qw

        poses.append(pose)

    node.get_logger().info(
        "Starting NavigateThroughPoses..."
    )

    navigator.goThroughPoses(poses)

    while not navigator.isTaskComplete():

        feedback = navigator.getFeedback()

        if feedback:
            try:
                node.get_logger().info(
                    f"Remaining distance: "
                    f"{feedback.distance_remaining:.2f} m"
                )
            except:
                pass

        rclpy.spin_once(node, timeout_sec=0.5)

    result = navigator.getResult()

    if result == TaskResult.SUCCEEDED:
        node.get_logger().info(
            "Trajectory replay completed."
        )

    elif result == TaskResult.FAILED:
        node.get_logger().error(
            "Trajectory replay failed."
        )

    elif result == TaskResult.CANCELED:
        node.get_logger().warning(
            "Trajectory replay canceled."
        )

    navigator.lifecycleShutdown()

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()