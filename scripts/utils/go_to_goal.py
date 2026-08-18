#!/usr/bin/env python3
import os
import csv
import time
import argparse
import math
from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import qos_profile_sensor_data

# Usamos NavigateThroughPoses para rotas multi-pontos suaves
from nav2_msgs.action import NavigateThroughPoses
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry

def euler_from_quaternion(q):
    """Converte quaternion para ângulo de Euler (yaw)."""
    siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)

class GoToGoalNode(Node):
    def __init__(self, controller_name, run_number, odom_topic):
        super().__init__('go_to_goal_node')
        self.controller_name = controller_name
        self.run_number = run_number
        self.start_time = None

        # Cliente de Ação para múltiplos pontos
        self.action_client = ActionClient(self, NavigateThroughPoses, 'navigate_through_poses')

        self.trajectory_data = []
        self.recording = False
        
        # Variáveis para armazenar a última velocidade lida do robô
        self.latest_v_linear = 0.0
        self.latest_v_angular = 0.0

        # 1. Inscrição no /odom APENAS para ler a velocidade real do controlador
        self.vel_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.vel_callback,
            qos_profile_sensor_data)

        # 2. Inscrição no Ground Truth para ler a posição perfeita
        self.odom_sub = self.create_subscription(
            Odometry,
            odom_topic,
            self.odom_callback,
            qos_profile_sensor_data)
        
        self.get_logger().info(f'Gravando posição de {odom_topic} e velocidades de /odom')

    def vel_callback(self, msg):
        """Atualiza a velocidade baseada no cálculo real das rodas do robô."""
        self.latest_v_linear = msg.twist.twist.linear.x
        self.latest_v_angular = msg.twist.twist.angular.z

    def odom_callback(self, msg):
        """Salva a posição do simulador mesclada com a velocidade do robô."""
        if not self.recording:
            return

        now = datetime.now().isoformat()
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        yaw = euler_from_quaternion(q)

        # Usa as velocidades salvas pelo vel_callback
        v_linear = self.latest_v_linear
        v_angular = self.latest_v_angular

        self.trajectory_data.append([now, x, y, yaw, v_linear, v_angular])

    def send_goal(self):
        self.get_logger().info('Aguardando o servidor de navegação Nav2 (NavigateThroughPoses)...')
        self.action_client.wait_for_server()

        goal_msg = NavigateThroughPoses.Goal()

        # ---------------------------------------------------------
        # Ponto 1: Intermediário (A curva)
        # ---------------------------------------------------------
        p1 = PoseStamped()
        p1.header.frame_id = 'map'
        p1.header.stamp = self.get_clock().now().to_msg()
        p1.pose.position.x = -2.034727096557617
        p1.pose.position.y = -0.045293934643268585
        p1.pose.position.z = 0.002471923828125
        # Apontando aproximadamente para o Leste (para ajudar o DWB na transição)
        p1.pose.orientation.z = -0.707
        p1.pose.orientation.w = 0.707

        # ---------------------------------------------------------
        # Ponto 2: Final (O Destino)
        # ---------------------------------------------------------
        p2 = PoseStamped()
        p2.header.frame_id = 'map'
        p2.header.stamp = self.get_clock().now().to_msg()
        p2.pose.position.x = 2.0069382190704346
        p2.pose.position.y = -0.0032528620213270187
        p2.pose.position.z = -0.001434326171875
        p2.pose.orientation.w = 1.0

        # Adiciona os pontos na ordem em que devem ser percorridos
        goal_msg.poses = [p1, p2]

        self.get_logger().info('Enviando rota para o robô...')
        
        self.recording = True
        self.start_time = time.time()
        
        self.send_goal_future = self.action_client.send_goal_async(goal_msg)
        self.send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Objetivo rejeitado pelo Nav2!')
            self.recording = False
            rclpy.shutdown()
            return

        self.get_logger().info('Objetivo aceito, iniciando navegação e gravação da trajetória...')
        self.get_result_future = goal_handle.get_result_async()
        self.get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        status = future.result().status
        duration = time.time() - self.start_time
        self.recording = False
        
        if status == 4: # SUCCEEDED
            self.get_logger().info('✓ Rota concluída com sucesso!')
            success = True
        else:
            self.get_logger().warn(f'✗ Navegação falhou ou foi cancelada. Status: {status}')
            success = False
            
        self.save_data(duration, success)
        rclpy.shutdown()

    def save_data(self, duration, success):
        out_dir = 'data/processed'
        os.makedirs(out_dir, exist_ok=True)
        
        # Arquivo de Trajetória
        csv_file = os.path.join(out_dir, f'{self.controller_name}-Baseline-R{self.run_number:02d}.csv')
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'x', 'y', 'yaw', 'linear_vel', 'angular_vel'])
            writer.writerows(self.trajectory_data)
        
        self.get_logger().info(f'[{len(self.trajectory_data)} amostras] Trajetória salva em: {csv_file}')

        # Arquivo de Metadados
        meta_file = os.path.join(out_dir, f'{self.controller_name}-Baseline-R{self.run_number:02d}_meta.csv')
        with open(meta_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['run_id', 'controller', 'timestamp', 'duration_s', 'poses_count', 'success'])
            writer.writerow([self.run_number, self.controller_name, datetime.now().isoformat(), round(duration, 2), len(self.trajectory_data), success])


def main(args=None):
    parser = argparse.ArgumentParser(description="Envia o robô por uma rota de múltiplos pontos gravando a trajetória.")
    parser.add_argument('--run', type=int, required=True, help="Número da rodada (ex: 1)")
    parser.add_argument('--controller', type=str, required=True, help="Nome do controlador (ex: DWB ou RPP)")
    parser.add_argument('--odom_topic', type=str, default='/sim_ground_truth_pose', 
                        help="Tópico de odometria para gravar.")
    
    parsed_args, unknown = parser.parse_known_args()

    rclpy.init(args=args)
    node = GoToGoalNode(parsed_args.controller, parsed_args.run, parsed_args.odom_topic)
    node.send_goal()
    rclpy.spin(node)

if __name__ == '__main__':
    main()