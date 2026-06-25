#!/usr/bin/env python3

"""
Grava uma trajetória de referência a partir do AMCL.

Uso:

    python3 record_trajectory.py

Encerrar:

    Ctrl+C

Saída:

    trajectory_YYYY-MM-DD_HH-MM-SS.csv
"""

import csv
import math
import signal
from datetime import datetime

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseWithCovarianceStamped


LOG_RATE_HZ = 10.0

OUTPUT_FILE = (
    f"trajectory_"
    f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
)


class TrajectoryRecorder(Node):

    def __init__(self):

        super().__init__("trajectory_recorder")

        self.current_x = None
        self.current_y = None
        self.current_yaw = None

        self.subscription = self.create_subscription(
            PoseWithCovarianceStamped,
            "/amcl_pose",
            self.pose_callback,
            10
        )

        self.file = open(
            OUTPUT_FILE,
            "w",
            newline=""
        )

        self.writer = csv.writer(self.file)

        self.writer.writerow([
            "timestamp",
            "x",
            "y",
            "yaw"
        ])

        self.timer = self.create_timer(
            1.0 / LOG_RATE_HZ,
            self.log_pose
        )

        self.start_time = self.get_clock().now()

        self.get_logger().info(
            f"Gravando trajetória em: {OUTPUT_FILE}"
        )

    def quaternion_to_yaw(
        self,
        x,
        y,
        z,
        w
    ):
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)

        return math.atan2(
            siny_cosp,
            cosy_cosp
        )

    def pose_callback(self, msg):

        pose = msg.pose.pose

        self.current_x = pose.position.x
        self.current_y = pose.position.y

        self.current_yaw = self.quaternion_to_yaw(
            pose.orientation.x,
            pose.orientation.y,
            pose.orientation.z,
            pose.orientation.w
        )

    def log_pose(self):

        if self.current_x is None:
            return

        elapsed = (
            self.get_clock().now() -
            self.start_time
        ).nanoseconds / 1e9

        self.writer.writerow([
            round(elapsed, 3),
            self.current_x,
            self.current_y,
            self.current_yaw
        ])

    def close(self):

        self.file.close()

        self.get_logger().info(
            f"Arquivo salvo: {OUTPUT_FILE}"
        )


recorder = None


def signal_handler(sig, frame):

    global recorder

    if recorder is not None:
        recorder.close()

    rclpy.shutdown()


def main():

    global recorder

    signal.signal(
        signal.SIGINT,
        signal_handler
    )

    rclpy.init()

    recorder = TrajectoryRecorder()

    try:
        rclpy.spin(recorder)

    except KeyboardInterrupt:
        pass

    finally:

        recorder.close()

        recorder.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()