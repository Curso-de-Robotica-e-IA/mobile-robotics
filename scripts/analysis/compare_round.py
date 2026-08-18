#!/usr/bin/env python3
import sys
import re
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Importa as funções matemáticas e a rota ideal do script de baseline
from check_baseline import (
    load_run, build_reference, evaluate_metrics, MIN_EXPECTED_RUNS, IDEAL_PATH
)

DATA_DIR = Path("data/processed/RoundA")
BASELINE_DIR = Path("data/processed/baseline+nav2")
PLOT_DIR = Path("results/plots/RoundA")
PLOT_DIR.mkdir(parents=True, exist_ok=True)

# Parâmetros avaliados na Rodada A -> Tupla: (Prefixo_RodadaA, Nome_Controller_Baseline)
EXPERIMENTS = {
    "DWB_PathDist": ("DWB-PathDist", "DWB"),
    "DWB_PathAlign": ("DWB-PathAlign", "DWB"),
    "RPP_Lookahead": ("RPP-Lookahead", "RPP"),
    "RPP_RegVel": ("RPP-RegVel", "RPP")
}

def get_dynamic_versions(exp_dir, prefix):
    """
    Varre o diretório e extrai automaticamente os valores testados
    a partir dos nomes dos arquivos.
    """
    versions = set()
    for f in exp_dir.glob(f"{prefix}-*-R*.csv"):
        if "_meta" in f.name:
            continue
        
        match = re.match(rf"^{prefix}-(.+)-R\d{{2}}$", f.stem)
        if match:
            versions.add(match.group(1))
            
    def sort_key(x):
        try:
            return float(x)
        except ValueError:
            return x
            
    return sorted(list(versions), key=sort_key)

def plot_trajectories(reference_dict, exp_name):
    """
    Gera um gráfico sobrepondo as trajetórias reais (coordenadas absolutas
    do Ground Truth) com a trajetória de referência ideal.
    """
    fig, ax = plt.subplots(figsize=(8, 10))

    # Separa as cores: Baseline fica fixo em preto tracejado, os demais recebem paleta
    versions_only = [v for v in reference_dict.keys() if v != "Baseline"]
    colors = sns.color_palette("tab10", n_colors=len(versions_only))
    color_map = dict(zip(versions_only, colors))
    color_map["Baseline"] = "black"

    # Plota cada versão
    for version, ref_df in reference_dict.items():
        color = color_map[version]
        linestyle = "--" if version == "Baseline" else "-"
        linewidth = 2.5 if version == "Baseline" else 2
        alpha = 1.0 if version == "Baseline" else 0.8

        label_name = "Baseline" if version == "Baseline" else f"Valor: {version}"

        # Plota os dados ABSOLUTOS (Sem alinhamento translacional)
        # Isso garante que o desvio visual reflete perfeitamente o True CTE da tabela
        ax.plot(ref_df["x"], ref_df["y"], label=label_name,
                color=color, linestyle=linestyle, linewidth=linewidth, alpha=alpha)

    # Trajetória de referência ideal (linha reta início -> curva -> destino)
    ideal_x = [p[0] for p in IDEAL_PATH]
    ideal_y = [p[1] for p in IDEAL_PATH]
    ax.plot(ideal_x, ideal_y, label="Referência (rota ideal)",
            color="red", linestyle=":", linewidth=2,
            marker="o", markersize=6, zorder=5)

    ax.set_title(f"Comparação de Trajetórias (True CTE) - {exp_name}")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.6)

    # Proporção real: 1 m em X ocupa o mesmo tamanho visual que 1 m em Y.
    ax.set_aspect('equal', adjustable='datalim')

    plt.tight_layout()
    plt.savefig(PLOT_DIR / f"{exp_name}.png", dpi=300)
    plt.close()

def evaluate_experiment(folder_name, prefix, controller):
    print(f"\n{'='*70}\nAVALIAÇÃO: {folder_name}\n{'='*70}")
    
    exp_dir = DATA_DIR / folder_name
    base_dir = BASELINE_DIR / controller
    
    results = []
    references = {}

    # 1. Carregar e avaliar dados da Rodada A
    if exp_dir.exists():
        versions = get_dynamic_versions(exp_dir, prefix)
        for version in versions:
            runs = []
            all_files = sorted(exp_dir.glob(f"{prefix}-{version}-R*.csv"))
            data_files = [f for f in all_files if "_meta" not in f.name]
            
            for f in data_files[:MIN_EXPECTED_RUNS]:
                runs.append(load_run(f))
                    
            if len(runs) < MIN_EXPECTED_RUNS:
                print(f"[{version}] Arquivos insuficientes. Pulando...")
                continue
                
            reference, interpolated = build_reference(runs)
            references[version] = reference
            metrics = evaluate_metrics(reference, interpolated, runs)
            
            results.append({
                "Valor do Parâmetro": version,
                "CTE Médio (m)": metrics["cte"]["mean"],
                "Variância (m)": metrics["variance"]["mean"],
                "Yaw Rate Retas (rad/s)": metrics["yaw_rate"]["straight_mean"],
                "Picos Correção": metrics["corrections"]["count"],
                "Vel. Linear Média (m/s)": metrics["linear_vel"]["mean"]
            })
    else:
        print(f"Aviso: Diretório {exp_dir} não encontrado.")

    # 2. Carregar e avaliar dados do Baseline
    if base_dir.exists():
        runs = []
        all_files = sorted(base_dir.glob(f"{controller}-Baseline-R*.csv"))
        data_files = [f for f in all_files if "_meta" not in f.name]
        
        for f in data_files[:MIN_EXPECTED_RUNS]:
            runs.append(load_run(f))
            
        if len(runs) >= MIN_EXPECTED_RUNS:
            reference, interpolated = build_reference(runs)
            references["Baseline"] = reference
            metrics = evaluate_metrics(reference, interpolated, runs)
            
            results.append({
                "Valor do Parâmetro": "Baseline",
                "CTE Médio (m)": metrics["cte"]["mean"],
                "Variância (m)": metrics["variance"]["mean"],
                "Yaw Rate Retas (rad/s)": metrics["yaw_rate"]["straight_mean"],
                "Picos Correção": metrics["corrections"]["count"],
                "Vel. Linear Média (m/s)": metrics["linear_vel"]["mean"]
            })
        else:
            print(f"[Baseline] Arquivos insuficientes ({len(runs)} encontrados).")
    else:
        print(f"Aviso: Diretório de Baseline não encontrado: {base_dir}")

    # 3. Exibir resultados consolidados
    if results:
        df_results = pd.DataFrame(results)
        print(df_results.to_markdown(index=False, floatfmt=".4f"))
        plot_trajectories(references, folder_name)
    else:
        print("Nenhum dado válido para comparar após a leitura.")

def main():
    for folder, (prefix, controller) in EXPERIMENTS.items():
        evaluate_experiment(folder, prefix, controller)

if __name__ == "__main__":
    main()