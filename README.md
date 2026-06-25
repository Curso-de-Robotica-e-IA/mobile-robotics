# Mobile Robotics Navigation Experiments

Repositório de experimentos de navegação autônoma com TurtleBot 4 + ROS 2/Nav2, com coleta simultânea de métricas de conectividade wireless (BLE, Wi-Fi) em ambientes indoor controlados. Projeto desenvolvido no Centro de Informática (CIn/UFPE) como parte da linha de pesquisa em robótica móvel e sistemas cyber-físicos.

---

## Visão Geral

O projeto investiga a reprodutibilidade de trajetórias em navegação autônoma e seu impacto na qualidade de coleta de dados wireless. Utilizamos o TurtleBot 4 como plataforma experimental em um corredor indoor mapeado (hall_cin_v4), avaliando diferentes controladores locais do Nav2 (DWB e RPP) sob métricas de consistência de trajetória e estabilidade de sinal BLE.

---

## Plataforma

| Componente        | Especificação                        |
|-------------------|--------------------------------------|
| Robô              | TurtleBot 4 (differential drive)     |
| Sistema           | ROS 2 Humble                         |
| Navegação         | Nav2 (AMCL + DWB / RPP)             |
| Mapa              | hall_cin_v4 (CIn/UFPE)              |
| Arquitetura       | PC Host + Raspberry Pi               |
| Coleta wireless   | BLE via bleak (Python)               |

---

## Cenários Planejados

| # | Cenário                     | Foco                        | Status          |
|---|-----------------------------|-----------------------------|-----------------|
| 1 | Path Following              | Reprodutibilidade           | Em andamento    |
| 2 | Waypoint Density Study      | Planejamento de rota        | Planejado       |
| 3 | DWB vs RPP                  | Comparação de controllers   | Planejado       |
| 4 | Velocity Profile Study      | Perfil de movimento         | Planejado       |
| 5 | Dynamic Obstacles           | Robustez                    | Planejado       |
| 6 | RSSI-Driven Coverage Mapping| Mapeamento BLE autônomo     | Planejado       |

---

## Estrutura do Repositório

```text
mobile-robotics/

├── docs/               # Documentação
│   ├── setup.md        # Guia de instalação e configuração
│   └── scenarios/      # Descrição formal de cada cenário
├── maps/               # Mapas do ambiente (.yaml + .pgm)
├── config/             # Configurações Nav2, AMCL, controllers
├── scripts/
│   ├── collection/     # Coleta de dados (BLE, NAV2 logs)
│   ├── analysis/       # Análise e geração de métricas/plots
│   └── utils/          # Utilitários reutilizáveis
├── data/               # .gitignore
│   ├── raw/            
│   └── processed/      
├── results/
│   ├── plots/          # Gráficos gerados
│   └── reports/        # Relatórios de experimento
├── .gitignore
└── README.md
```

---

## Início Rápido

Para configurar o ambiente do zero, siga o guia completo em [docs/setup.md](docs/setup.md).

Para rodar um experimento:

```bash
# 1. Defina a pose inicial do robô
python3 scripts/utils/set_initial_pose.py

# 2. Grave a trajetória de referência
python3 scripts/collection/record_trajectory.py \
    --output data/processed/reference_path.csv

# 3. Execute o replay nas rodadas seguintes
python3 scripts/collection/replay_trajectory.py \
    --path data/processed/reference_path.csv --run 2
```

---

## Equipe

- Fernanda Neves
- Beatriz de Oliveira
- Breno Miranda (orientador)
- Adrien Durand-Petiteville (orientador)

CIn/UFPE — Grupo CRIAR
