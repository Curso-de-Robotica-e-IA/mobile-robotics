# Mobile Robotics Navigation Experiments (DWB x RPP)

Repositório de experimentos de navegação autônoma com **TurtleBot 4 + ROS 2/Nav2**, com coleta simultânea de métricas de conectividade wireless (Bluetooth/BLE) em ambientes indoor controlados. Projeto desenvolvido no CRIAR - Centro de Informática (CIn/UFPE) como parte da linha de pesquisa em robótica móvel e sistemas cyber-físicos.

## Visão Geral

O escopo deste projeto visa criar uma infraestrutura baseada em robótica móvel para testar a qualidade do sinal Bluetooth Low Energy (BLE) sob condições estritamente controladas e reprodutíveis, mitigando a variabilidade causada por interferência humana (body shadowing).

Para garantir a validade dos dados wireless coletados, executamos uma fase de Simulação (Calibração Cinemática), que consiste na avaliação e *parameter sweep* de controladores locais do Nav2 (DWB vs. RPP) no motor Ignition/Gazebo. O robô é submetido a um cenário de estresse (Labirinto em L) com um distúrbio posicional inicial (offset de 50 cm). O objetivo é minimizar o True Cross-Track Error (True CTE) e garantir que o robô seja capaz de executar curvas ortogonais perfeitas sem oscilações na trajetória.

## Plataforma

| Componente        | Especificação           |
|-------------------|-------------------------|
| Robô              | TurtleBot 4             |
| Sistema           | ROS 2 Humble            |
| Navegação         | Nav2 (DWB e RPP)        |
| Simulador         | Ignition Gazebo         |
| Mapa              | `maze.yaml`             |

## Cenários Planejados

| # | Cenário                       | Foco                                         | Status     |
|---|-------------------------------|----------------------------------------------|------------|
| 1 | Baseline de Controladores (Simulação) | Comparação DWB vs RPP via True CTE em curvas de 90° | Concluído  |
| 2 | Otimização Paramétrica (Sweep)        | Sintonia de `PathDist`, `PathAlign`, `lookahead_dist` e `use_regulated_linear_velocity_scaling`   | Concluído  |

## Estrutura do Repositório

```text
mobile-robotics/
├── docs/                               # Documentação
│   ├── setup.md                        # Guia de instalação e configuração
│   ├── troubleshoot.md                 # Guia de resolução de problemas 
│   └── scenarios/                      # Descrição formal de cada cenário
│       └── how_to_run_experiment.md    # Roteiro prático para reprodução dos testes
├── maps/                               # Mapas do ambiente (.yaml + .pgm)
├── config/                             # Configurações Nav2, AMCL
├── scripts/            
│   ├── collection/                     # Coleta de dados (BLE, NAV2 logs)
│   ├── analysis/                       # Análise e geração de métricas/plots
│   └── utils/                          # Utilitários reutilizáveis
├── data/                               # .gitignore
│   ├── raw/                        
│   └── processed/                  
├── results/                            # .gitignore
│   ├── plots/                          # Gráficos gerados
│   └── reports/                        # Relatórios de experimento
├── .gitignore
└── README.md
```

## Início Rápido
Para configurar o ambiente do zero, consulte o guia completo em [guia completo](docs/setup.md).

Para preparar e rodar um experimento, consulte o roteiro passo a passo em [como rodar experimentos](docs/scenarios/how_to_run_experiments.md).

## Equipe CRIAR - CIn/UFPE 
- Fernanda Neves
- Beatriz Oliveira
- Adrien Durand-Petiteville (orientador)
- Breno Miranda (orientador)
