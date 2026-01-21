#!/usr/bin/env python3
"""
Script para otimização de sensibilidades por grid search.

Sistema de Identificação de Dados Sensíveis - Hackathon Participa DF

Este script encontra as melhores configurações de sensibilidade
para maximizar o F1-Score do modelo.

Uso:
    python atualizar_sensibilidade.py dados.xlsx labels.csv
"""

import itertools
import sys

from src import SistemaIdentificacaoDadosSensiveis


def otimizar_sensibilidades(arquivo_dados: str, arquivo_labels: str):
    """
    Encontra as melhores sensibilidades por grid search.

    Args:
        arquivo_dados: Caminho do arquivo de dados.
        arquivo_labels: Caminho do arquivo de labels.

    Returns:
        Tupla (melhor_config, melhor_f1).
    """
    # Importa função de carregar labels do main
    from main import carregar_labels
    labels = carregar_labels(arquivo_labels)

    melhor_f1 = 0
    melhor_config = {}

    # Grid de sensibilidades para testar
    valores = [0.6, 0.7, 0.8, 0.9]

    for cpf_s, nome_s, email_s in itertools.product(valores, valores, valores):
        config = {
            'cpf_sensibilidade': cpf_s,
            'nome_sensibilidade': nome_s,
            'email_sensibilidade': email_s,
        }

        sistema = SistemaIdentificacaoDadosSensiveis(config)
        sistema.processar_arquivo(arquivo_dados, labels=labels, verbose=False)
        metricas = sistema.calcular_metricas()

        if metricas.f1_score > melhor_f1:
            melhor_f1 = metricas.f1_score
            melhor_config = config.copy()
            print(f"Novo melhor F1: {melhor_f1:.4f} com config: {config}")

    return melhor_config, melhor_f1


def main():
    """Função principal."""
    if len(sys.argv) < 3:
        print("Uso: python atualizar_sensibilidade.py <dados.xlsx> <labels.csv>")
        print()
        print("Exemplo:")
        print("  python atualizar_sensibilidade.py dados.xlsx labels.csv")
        sys.exit(1)

    arquivo_dados = sys.argv[1]
    arquivo_labels = sys.argv[2]

    print(f"Otimizando sensibilidades...")
    print(f"Arquivo de dados: {arquivo_dados}")
    print(f"Arquivo de labels: {arquivo_labels}")
    print()

    config_otima, f1 = otimizar_sensibilidades(arquivo_dados, arquivo_labels)

    print()
    print(f"Configuração ótima encontrada:")
    for chave, valor in config_otima.items():
        print(f"  {chave}: {valor}")
    print(f"F1-Score: {f1:.4f}")


if __name__ == "__main__":
    main()