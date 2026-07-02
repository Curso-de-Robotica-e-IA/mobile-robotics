# Mobile Robotics Navigation Experiments (CBSoft Edition)

Repositório de experimentos de navegação autônoma com **TurtleBot 4 + ROS 2/Nav2**, com coleta simultânea de métricas de conectividade wireless (Bluetooth/BLE) em ambientes indoor controlados. Projeto desenvolvido no CRIAR - Centro de Informática (CIn/UFPE) como parte da linha de pesquisa em robótica móvel e sistemas cyber-físicos.

## Visão Geral

O escopo deste projeto apresenta uma infraestrutura baseada em robótica móvel para testar a qualidade do sinal Bluetooth Low Energy (BLE) sob condições controladas e reprodutíveis. Utilizamos o TurtleBot 4 como plataforma experimental em um corredor indoor mapeado (`hall_cin_v4`) para avaliar a degradação do sinal (RSSI) e os limites de desconexão em função da distância. A avaliação comparou dois tipos de conexão entre dois dispositivos: uma configuração **homogênea** (Motorola <-> Motorola) e outra **heterogênea** (Motorola <-> POCO). Para cada tipo, foram realizadas 3 rodadas, com um dispositivo fixo e outro móvel em cima do robô ao longo da mesma trajetória até a perda total da conexão.

### Hipótese de Pesquisa
- Essa abordagem mitiga a variabilidade e a atenuação causada pela interferência humana (*body shadowing*) inerente aos testes manuais?

## Plataforma

| Componente        | Especificação           |
|-------------------|-------------------------|
| Robô              | TurtleBot 4             |
| Sistema           | ROS 2 Humble            |
| Navegação         | Nav2                    |
| Mapa              | hall_cin_v4 (CIn/UFPE)  |
| Arquitetura       | PC Host + Raspberry Pi  |
| Coleta wireless   | nRF Connect + ADB       |

## Cenários Planejados

| # | Cenário                       | Foco                                         | Status     |
|---|-------------------------------|----------------------------------------------|------------|
| 1 | Degradação BLE (Homogênea)    | Distância de desconexão e RSSI               | Concluído  |
| 2 | Degradação BLE (Heterogênea)  | Distância de desconexão e RSSI               | Concluído  |
| 3 | Extensão para Wi-Fi           | Generalização para outras tecnologias        | Planejado  |
| 4 | Oclusão por Obstáculos        | Comportamento sob diferentes interferências  | Planejado  |
| 5 | Automação Completa do Setup   | Redução de intervenção manual                | Planejado  |

## Estrutura do Repositório

```text
mobile-robotics/
├── docs/               # Documentação
│   ├── setup.md        # Guia de instalação e configuração
│   ├── troubleshoot.md # Guia de resolução de problemas 
│   └── scenarios/      # Descrição formal de cada cenário
├── maps/               # Mapas do ambiente (.yaml + .pgm)
├── config/             # Configurações Nav2, AMCL
├── scripts/
│   ├── collection/     # Coleta de dados (BLE, NAV2 logs)
│   ├── analysis/       # Análise e geração de métricas/plots
│   └── utils/          # Utilitários reutilizáveis
├── data/               # .gitignore
│   ├── raw/            
│   └── processed/      
├── results/            # .gitignore
│   ├── plots/          # Gráficos gerados
│   └── reports/        # Relatórios de experimento
├── .gitignore
└── README.md
```

## Início Rápido
Para configurar o ambiente do zero, consulte o guia completo em [guia completo](docs/setup.md).

Para preparar e rodar um experimento físico, siga o fluxo de execução abaixo:

1. Execute o build da imagem Docker (necessário apenas na primeira execução ou caso altere dependências).
2. Ligue o Docker e estabeleça a conexão de rede com o TurtleBot 4.
3. Em terminais separados dentro do container, inicialize a infraestrutura do ROS 2 executando: o servidor de mapa, a pilha de navegação e a interface visual (RViz).
4. No RViz, utilize a ferramenta 2D Pose Estimate para definir a pose inicial exata do robô no mapa.
5. Aguarde o carregamento completo da árvore de TF e dos Costmaps.
6. Inicie simultaneamente o script de navegação (no terminal do Docker) e o script de coleta BLE. 
    - ⚠️ Atenção: O script de coleta de sinal utiliza comandos ADB e deve ser executado obrigatoriamente no ambiente Windows (Host).
7. Monitore a execução até a ocorrência da desconexão BLE. Neste momento, finalize manualmente ambos os scripts (Nav e ADB).
8. Os logs de saída serão gerados e salvos automaticamente no diretório data/raw.

## Equipe CRIAR - CIn/UFPE 
- Fernanda Neves
- Beatriz Oliveira
- Adrien Durand-Petiteville (orientador)
- Breno Miranda (orientador)
