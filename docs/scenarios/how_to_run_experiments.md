# How to Run Simulation Experiments

Guia completo para executar os experimentos de calibração de controllers (DWB e RPP) no ambiente simulado, desde a inicialização até a coleta das 3 rodadas.

---

## Pré-requisitos

- Docker rodando (`sh run_docker.sh`)
- Repositório montado em `/ros2_ws`
- ROS 2 Humble + Nav2 + TurtleBot4 Simulator instalados na imagem

---

## Estrutura de terminais necessários

Você vai precisar de 4 terminais dentro do container.

```bash
# Para cada novo terminal:
sh start_docker.sh
```

---

## Passo 1 — Subir a simulação

**Terminal 1:**

```bash
ros2 launch turtlebot4_ignition_bringup turtlebot4_ignition.launch.py \
  world:=maze \
  use_sim_time:=true \
  x:=-2.775496 \
  y:=5.991405 \
  z:=0.002471 \
  yaw:=0.0
```

> Quando o mundo carregar, você deve clicar com o botão direito do mouse na base de carregamento do robô e selecionar "Remove" para que o robô não fique preso na base durante a rota.
> **Critério para avançar:** sem erros de `[ERROR]` no terminal.

---

## Passo 2 — Carregar o mapa (localização)

**Terminal 2:**

```bash
ros2 launch turtlebot4_navigation localization.launch.py \
  map:=/opt/ros/humble/share/turtlebot4_navigation/maps/maze.yaml \
  use_sim_time:=true
```

> **Critério para avançar:** AMCL ativo sem erros.

---

## Passo 3 — Subir o Nav2

**Terminal 3:**

Escolha o controller da sessão:

```bash
# `params_file` deve ser o caminho completo para o arquivo de parâmetros do controller escolhido.
ros2 launch turtlebot4_navigation nav2.launch.py \
  params_file:=/ros2_ws/config/controllers/dwb_params_baseline.yaml \
  use_sim_time:=true
```

> **Critério para avançar:** `Managed nodes are active`

---

## Passo 4 — [Opcional] Abrir RViz para monitorar

Se quiser visualizar. Pode pular se estiver rodando experimentos automatizados.

**Terminal 4 (opcional):**

```bash
ros2 launch turtlebot4_viz view_robot.launch.py
```

--- 

## Passo 5 — Publicar a pose inicial

**Terminal 4:**

```bash
cd /ros2_ws

python3 scripts/utils/set_initial_pose.py
```

> **Critério para avançar:** aguardar ~4s para o AMCL convergir.

---

## Passo 6 — Rodar as 3 rodadas de baseline

### Rota experimental (Labirinto em L)

```text
Start (Ponto de Partida):  x = -2.0004,  y =  5.9714
Vértice (Curva de 90°):    x = -2.0347,  y = -0.0453
Goal (Destino Final):      x =  2.0069,  y = -0.0033

Topologia: Rota Ortogonal em "L"
Trecho 1 (Descida no Eixo Y): ~6 metros 
Trecho 2 (Avanço no Eixo X):  ~4 metros
Distância Total Planejada:    ~10 metros
```

### Uma run por vez

Permite monitorar o comportamento antes de automatizar.

```bash
# Run 1
python3 scripts/utils/go_to_start.py
python3 scripts/utils/go_to_goal.py --run 1 --controller DWB --odom_topic /sim_ground_truth_pose

# Run 2
python3 scripts/utils/go_to_start.py
python3 scripts/utils/go_to_goal.py --run 2 --controller DWB --odom_topic /sim_ground_truth_pose

# Run 3
python3 scripts/utils/go_to_start.py
python3 scripts/utils/go_to_goal.py --run 3 --controller DWB --odom_topic /sim_ground_truth_pose
```

### Loop automático

```bash
for i in 1 2 3; do
    echo "=== Run $i — DWB ==="
    python3 scripts/utils/go_to_start.py
    python3 scripts/utils/go_to_goal.py \
        --run ${i#0} --controller DWB --odom_topic /sim_ground_truth_pose
    echo "Run $i concluída. Aguardando 3s..."
    sleep 3
done
```

> **Critério para avançar:** todas as 3 runs concluídas com sucesso.

---

## Passo 7 — Trocar para RPP e repetir

1. Encerrar Nav2 no Terminal 3 (`Ctrl+C`)
2. Subir com RPP:

```bash
ros2 launch turtlebot4_navigation nav2.launch.py \
  params_file:=/ros2_ws/config/controllers/rpp_params_baseline.yaml
```

3. Repetir Passos 5 e 6 com `--controller RPP`

---

## Arquivos gerados por run

```
data/processed/DWB-Baseline-R01.csv       ← trajetória
data/processed/DWB-Baseline-R01_meta.csv  ← metadados
```

### Formato do CSV de trajetória

```
timestamp, x, y, yaw, linear_vel, angular_vel
```

- `x`, `y` — posição em metros (frame `odom`)
- `yaw` — orientação em radianos
- `linear_vel` — velocidade linear em m/s
- `angular_vel` — velocidade angular em rad/s

---

## Referência rápida

> Todos os comandos devem ser executados dentro do container Docker.
> E devem conter o argumento `use_sim_time:=true` para sincronizar com o tempo simulado.

```
Terminal 1:  turtlebot4_ignition.launch.py  world:=maze use_sim_time:=true
Terminal 2:  localization.launch.py  map:=maze.yaml use_sim_time:=true
Terminal 3:  nav2.launch.py  params_file:=dwb_params_baseline.yaml use_sim_time:=true
Terminal 4:  set_initial_pose.py → go_to_start.py → go_to_goal.py
```