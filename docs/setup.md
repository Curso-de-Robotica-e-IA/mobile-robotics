
# Guia de Setup e Execução Experimental
Este documento descreve as etapas necessárias para preparar a infraestrutura híbrida do projeto e estabelecer a comunicação correta entre o PC Host e o TurtleBot 4 para a coleta de dados de navegação e conectividade.

## 1. Pré-requisitos de Sistema
Para executar a arquitetura completa do experimento, você precisará de:
* **PC Host (Nav2 / ROS 2):** Ambiente Linux com Docker e NVIDIA Container Toolkit configurados.
* **PC Coletor (Sinal BLE):** Ambiente Windows com o Android Debug Bridge (ADB) configurado nas variáveis de ambiente (`PATH`) e Python 3.
* **Plataforma Robótica:** TurtleBot 4 (base iRobot Create 3 + Raspberry Pi) rodando ROS 2 Humble.

## 2. Configuração do Docker (Do Zero)
Caso seja a primeira vez rodando o projeto nesta máquina ou se o arquivo `Dockerfile` tiver sofrido alterações em suas dependências, siga os passos de construção:

1. **Compilação da Imagem:**
Construa a imagem base contendo o ROS 2 e os utilitários de simulação/nav.
```bash
./build_docker.sh
```

2. **Criação do Container:**
Execute o script principal para montar os volumes e injetar as permissões da GPU.
```bash
./run_docker.sh
```

> **⚠️ Nota de Configuração:** O script `run_docker.sh` injeta a variável `-e TZ=America/Recife`. Isso é estritamente necessário para sincronizar o tempo do container e evitar que os logs de navegação do PC fiquem horas à frente do relógio interno do hardware do robô, o que corromperia a árvore de TF.

## 3. Fluxo de Execução (Rodando o Experimento)
Com a infraestrutura construída, siga este fluxo todas as vezes que for realizar uma rodada (*run*) de coleta de dados no corredor:

### Passo 3.1: Iniciar o Ambiente ROS 2
Com o container Docker ligado, abra os terminais necessários:
```bash
./start_docker.sh
```

### Passo 3.2: Subir a Pilha de Navegação
Dentro de abas separadas no terminal do Docker, inicie os componentes na seguinte ordem:

1. **Servidor de Mapa:**
Execute o comando para encontrar o mapa no ambiente, ele retorna o caminho completo do arquivo `hall_cin_v4.yaml`:
```bash
find / -name "hall_cin_v4.yaml"
```

Em seguida, substitua `/caminho/para/hall_cin_v4.yaml` pelo caminho retornado no comando:
```bash
ros2 launch turtlebot4_navigation map_server.launch.py map:=/caminho/para/hall_cin_v4.yaml
```

2. **Nav2 (Cérebro da Navegação):**
```bash
ros2 launch turtlebot4_navigation nav2.launch.py
```

3. **Interface Visual (RViz):**
```bash
ros2 launch turtlebot4_viz view_robot.launch.py
```

### Passo 3.3: Localização Inicial (Pose Estimate)
Com o RViz aberto, o mapa estará visível, mas o robô não saberá onde está.
* Selecione a ferramenta **2D Pose Estimate** no menu superior do RViz.
* Clique e arraste no mapa para indicar a posição física e a direção exata para onde a frente do robô está apontando.
* Aguarde a leitura do Lidar coincidir com as paredes do mapa.

### Passo 3.4: Coleta de Dados Simultânea
Quando a árvore de TF estiver carregada e sem erros no terminal, inicie a rodada de testes paralelamente:

1. **No Linux (Docker):** Execute o script de navegação autônoma para despachar o robô na trajetória planejada.
```bash
python3 scripts/collection/nav_3points.py
```

2. **No Windows (PC Colector):** Simultaneamente, dispare o script ADB para iniciar a extração em tempo real das métricas BLE (RSSI, PHY) dos smartphones conectados.
```powershell
cd C:\SeuDiretorio\scripts
.\script_celular.ps1
```

### Passo 3.5: Finalização e Exportação
Acompanhe o monitoramento do terminal Windows. Assim que o evento de **desconexão total** do sinal Bluetooth for registrado:

1. Pressione `Ctrl+C` em ambos os terminais para abortar a navegação e encerrar a leitura ADB.
2. Os arquivos `.csv` gerados pela sessão serão automaticamente descarregados no diretório `data/raw/` para posterior sincronização de *timestamps*.
