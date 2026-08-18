"""
Script: go_to_start.py
Descrição: Navega o robô até o ponto inicial da rota experimental.
           Deve ser executado antes de cada run para garantir
           que o robô sempre parte do mesmo ponto.
Uso: python3 go_to_start.py
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
import math
import sys

# ── Ponto inicial da rota ────────────────────────────────────────────────────
START_X   = -2.0004353523254395
START_Y   =  5.971445560455322
START_YAW = -1.5708  # -90° → robô aponta para -Y (direção do goal)
# ────────────────────────────────────────────────────────────────────────────


def yaw_to_quaternion(yaw):
    return (math.sin(yaw / 2), math.cos(yaw / 2))  # (z, w)


class GoToStart(Node):
    def __init__(self):
        super().__init__('go_to_start')
        self._action_client = ActionClient(
            self, NavigateToPose, 'navigate_to_pose')
        self.done = False
        self.success = False

    def send_goal(self):
        self.get_logger().info('Aguardando action server Nav2...')
        self._action_client.wait_for_server()

        goal = NavigateToPose.Goal()
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = START_X
        pose.pose.position.y = START_Y
        pose.pose.position.z = 0.0

        z, w = yaw_to_quaternion(START_YAW)
        pose.pose.orientation.z = z
        pose.pose.orientation.w = w

        goal.pose = pose

        self.get_logger().info(
            f'Navegando para ponto inicial: x={START_X:.4f}, y={START_Y:.4f}')

        future = self._action_client.send_goal_async(
            goal,
            feedback_callback=self.feedback_callback)
        future.add_done_callback(self.goal_response_callback)

    def feedback_callback(self, feedback):
        dist = feedback.feedback.distance_remaining
        self.get_logger().info(
            f'Distância restante: {dist:.2f} m', throttle_duration_sec=2.0)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal rejeitado pelo Nav2!')
            self.done = True
            return
        self.get_logger().info('Goal aceito. Navegando para o ponto inicial...')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def result_callback(self, future):
        result = future.result().status
        if result == 4:  # STATUS_SUCCEEDED
            self.get_logger().info(
                '✓ Ponto inicial atingido. Robô pronto para iniciar a rota.')
            self.success = True
        else:
            self.get_logger().error(
                f'✗ Falha ao atingir o ponto inicial. Status: {result}')
        self.done = True


def main():
    rclpy.init()
    node = GoToStart()
    node.send_goal()

    while not node.done:
        rclpy.spin_once(node, timeout_sec=0.5)

    node.destroy_node()
    rclpy.shutdown()
    sys.exit(0 if node.success else 1)


if __name__ == '__main__':
    main()