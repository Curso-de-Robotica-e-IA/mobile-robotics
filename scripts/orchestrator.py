#!/usr/bin/env python3
"""
Orquestrador - Cenário 1: Missões independentes em paralelo

TB1 e TB2 partem de P1 (próximos um do outro) e seguem em linha reta,
cada um na direção em que já está apontado, até percorrer uma distância
alvo (P2), se afastando progressivamente um do outro.

Este nó:
  - distribui uma missão independente para cada robô (namespace próprio);
  - monitora o estado de cada robô separadamente (odometria, distância
    percorrida, conclusão);
  - sincroniza o início (só começa quando TODOS os robôs têm odometria)
    e o fim (encerra quando TODOS concluem);
  - loga a distância entre os robôs ao longo do tempo, evidenciando que
    eles se afastam;
  - valida namespaces/tópicos avisando se algum robô não responde.
"""

import csv
import math
import os
from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


# ======================================================================
# CONFIGURAÇÃO DAS MISSÕES (N robôs)
# ======================================================================

ROBOT_CONFIGS = [
    {
        'name': 'tb1',
        'cmd_topic': '/tb1/cmd_vel',
        'odom_topic': '/tb1/odom',
        'target_distance': 1.0,   # metros
        'speed': 0.1,            # m/s
    },
    {
        'name': 'tb2',
        'cmd_topic': '/tb2/cmd_vel',
        'odom_topic': '/tb2/odom',
        'target_distance': 1.0,   # metros
        'speed': 0.1,            # m/s
    },
]

CONTROL_PERIOD = 0.05        # 20 Hz
ODOM_TIMEOUT_SEC = 10.0      # aviso se não chegar odometria nesse tempo
SEPARATION_LOG_PERIOD = 1.0  # loga afastamento entre robôs a cada 1s

# ----------------------------------------------------------------------
# LOG CSV
# ----------------------------------------------------------------------
CSV_LOG_ENABLED = True
CSV_LOG_DIR = os.path.expanduser('/logs')  
CSV_LOG_RATE_HZ = 10.0                  # taxa de gravação (<= 1/CONTROL_PERIOD)


class RobotMission:
    """Encapsula o estado e o controle de UM robô, de forma independente."""

    def __init__(self, node: Node, name: str, cmd_topic: str,
                 odom_topic: str, target_distance: float, speed: float):
        self.node = node
        self.name = name
        self.target_distance = target_distance
        self.speed = speed

        self.x0 = None
        self.y0 = None
        self.x = None
        self.y = None

        self.done = False
        self.start_time = None
        self.end_time = None
        self.last_cmd = 0.0  # último comando linear.x efetivamente enviado

        self.cmd_pub = node.create_publisher(Twist, cmd_topic, 10)
        self.odom_sub = node.create_subscription(
            Odometry, odom_topic, self._odom_callback,
            qos_profile_sensor_data
        )

    # -- odometria -----------------------------------------------------
    def _odom_callback(self, msg: Odometry):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y

        if self.x0 is None:
            self.x0 = self.x
            self.y0 = self.y
            self.node.get_logger().info(
                f'[{self.name}] posição inicial: '
                f'x={self.x0:.3f} m, y={self.y0:.3f} m'
            )

    @property
    def has_odom(self) -> bool:
        return self.x is not None and self.y is not None

    def distance_traveled(self) -> float:
        return math.hypot(self.x - self.x0, self.y - self.y0)

    # -- controle --------------------------------------------------------
    def step(self, now: float):
        """Executa um passo de controle independente para este robô."""

        if self.done:
            self._publish_stop()
            return

        if self.start_time is None:
            self.start_time = now

        dist = self.distance_traveled()

        if dist >= self.target_distance:
            self._publish_stop()
            self.done = True
            self.end_time = now
            elapsed = self.end_time - self.start_time
            self.node.get_logger().info(
                f'[{self.name}] MISSÃO CONCLUÍDA '
                f'(dist={dist:.3f} m, tempo={elapsed:.2f} s)'
            )
        else:
            self._publish_velocity(self.speed)

    def _publish_velocity(self, linear_x: float):
        msg = Twist()
        msg.linear.x = linear_x
        self.cmd_pub.publish(msg)
        self.last_cmd = linear_x

    def _publish_stop(self):
        self.cmd_pub.publish(Twist())
        self.last_cmd = 0.0


class MultiRobotOrchestrator(Node):

    def __init__(self):
        super().__init__('multi_robot_orchestrator')

        self.missions = [
            RobotMission(
                self,
                cfg['name'],
                cfg['cmd_topic'],
                cfg['odom_topic'],
                cfg['target_distance'],
                cfg['speed'],
            )
            for cfg in ROBOT_CONFIGS
        ]

        self.mission_started = False
        self.mission_finished = False
        self._odom_wait_ticks = 0
        self._odom_timeout_warned = False
        self._separation_log_ticks = 0
        self._initial_separation = None

        # -- log CSV -----------------------------------------------------
        self.csv_writer = None
        self.csv_file = None
        self._csv_t0 = None
        self._csv_last_write = None
        self._csv_period = 1.0 / CSV_LOG_RATE_HZ

        if CSV_LOG_ENABLED:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.csv_path = os.path.join(
                CSV_LOG_DIR, f'multi_robot_log_{timestamp}.csv'
            )
            self.csv_file = open(self.csv_path, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            self.csv_writer.writerow([
                'time_s', 'robot', 'x', 'y', 'x0', 'y0',
                'distance_traveled', 'target_distance',
                'speed_cmd', 'cmd_linear_x', 'done',
                'separation_between_robots',
            ])
            self.get_logger().info(f'Gravando log CSV em: {self.csv_path}')

        self.timer = self.create_timer(CONTROL_PERIOD, self.control_loop)

        self.get_logger().info('=' * 50)
        self.get_logger().info(' Multi-Robot Orchestrator - Cenário 1')
        self.get_logger().info('=' * 50)
        self.get_logger().info(
            f'Aguardando odometria de: '
            f'{", ".join(m.name for m in self.missions)}...'
        )

    # ------------------------------------------------------------------
    def control_loop(self):
        now = self.get_clock().now().nanoseconds / 1e9

        # -- validação: esperar odometria de todos os robôs --------------
        missing = [m.name for m in self.missions if not m.has_odom]
        if missing:
            self._odom_wait_ticks += 1
            elapsed_wait = self._odom_wait_ticks * CONTROL_PERIOD
            if elapsed_wait > ODOM_TIMEOUT_SEC and not self._odom_timeout_warned:
                self._odom_timeout_warned = True
                self.get_logger().warn(
                    f'Sem odometria há {elapsed_wait:.1f}s para: '
                    f'{missing}. Verifique namespace/remap dos tópicos '
                    f'/odom desses robôs.'
                )
            return

        # -- iniciar missão (sincronizado: só quando todos estão prontos) -
        if not self.mission_started:
            self.mission_started = True
            self.get_logger().info('=' * 50)
            self.get_logger().info(' INICIANDO MISSÕES (paralelas)')
            self.get_logger().info('=' * 50)
            for m in self.missions:
                self.get_logger().info(
                    f'{m.name} -> {m.target_distance:.2f} m '
                    f'a {m.speed:.2f} m/s'
                )
            self._initial_separation = self._separation()
            self.get_logger().info(
                f'Separação inicial entre robôs: '
                f'{self._initial_separation:.3f} m'
            )
            self._csv_t0 = now

        # -- executar um passo independente de cada robô ------------------
        for m in self.missions:
            m.step(now)

        # -- gravar linha no CSV (uma linha por robô, taxa configurável) --
        self._log_csv(now)

        # -- log periódico do afastamento entre robôs ---------------------
        self._separation_log_ticks += 1
        ticks_per_log = max(1, int(SEPARATION_LOG_PERIOD / CONTROL_PERIOD))
        if self._separation_log_ticks % ticks_per_log == 0:
            self.get_logger().info(
                f'Separação atual entre robôs: {self._separation():.3f} m'
            )

        # -- verificar conclusão global (sincronização de fim) ------------
        if all(m.done for m in self.missions) and not self.mission_finished:
            self.mission_finished = True
            self.stop_all()

            final_sep = self._separation()
            self.get_logger().info('=' * 50)
            self.get_logger().info(' TODAS AS MISSÕES FORAM CONCLUÍDAS!')
            self.get_logger().info('=' * 50)
            for m in self.missions:
                elapsed = (m.end_time - m.start_time) if m.end_time else 0.0
                self.get_logger().info(
                    f'  {m.name}: {m.distance_traveled():.3f} m '
                    f'em {elapsed:.2f} s'
                )
            self.get_logger().info(
                f'Separação inicial -> final: '
                f'{self._initial_separation:.3f} m -> {final_sep:.3f} m'
            )
            self.get_logger().info(
                'Resultado: robôs concluíram missões independentes '
                'em paralelo, sem interferência entre namespaces.'
            )

            rclpy.shutdown()

    # ------------------------------------------------------------------
    def _log_csv(self, now: float):
        if self.csv_writer is None:
            return

        # limita a taxa de gravação (não precisa ser 20Hz para análise)
        if (self._csv_last_write is not None
                and (now - self._csv_last_write) < self._csv_period):
            return
        self._csv_last_write = now

        t = now - self._csv_t0 if self._csv_t0 is not None else 0.0
        sep = self._separation()

        for m in self.missions:
            self.csv_writer.writerow([
                f'{t:.3f}',
                m.name,
                f'{m.x:.4f}',
                f'{m.y:.4f}',
                f'{m.x0:.4f}',
                f'{m.y0:.4f}',
                f'{m.distance_traveled():.4f}',
                f'{m.target_distance:.4f}',
                f'{m.speed:.4f}',
                f'{m.last_cmd:.4f}',
                int(m.done),
                f'{sep:.4f}',
            ])
        self.csv_file.flush()

    # ------------------------------------------------------------------
    def _separation(self) -> float:
        """Distância atual entre o 1º e o 2º robô da lista (métrica de
        afastamento, útil para validar visualmente o experimento)."""
        if len(self.missions) < 2:
            return 0.0
        a, b = self.missions[0], self.missions[1]
        return math.hypot(a.x - b.x, a.y - b.y)

    def stop_all(self):
        for m in self.missions:
            m._publish_stop()
        self.get_logger().info(
            f'Comando STOP enviado para: '
            f'{", ".join(m.name for m in self.missions)}.'
        )

    def destroy_node(self):
        self.get_logger().info('Encerrando orquestrador...')
        self.stop_all()
        if self.csv_file is not None:
            self.csv_file.close()
            self.get_logger().info(f'Log CSV salvo em: {self.csv_path}')
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    node = MultiRobotOrchestrator()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('CTRL+C recebido.')
    finally:
        node.stop_all()
        if rclpy.ok():
            rclpy.shutdown()
        node.destroy_node()


if __name__ == '__main__':
    main()