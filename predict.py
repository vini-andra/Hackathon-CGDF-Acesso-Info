#!/usr/bin/env python3
"""
Script de Predição para Submissão
Sistema de Identificação de Dados Sensíveis - Hackathon Participa DF

Este script é usado pela banca para avaliar o modelo.
Recebe um arquivo de entrada e gera um arquivo CSV com as predições.

Uso:
    python predict.py <arquivo_entrada> <arquivo_saida>

Exemplo:
    python predict.py dados_teste.xlsx predicoes.csv

O arquivo de saída terá o formato:
    ID,Predicao
    1,0
    2,1
    3,0
    ...

Onde:
    1 = Contém dados pessoais (deve ser classificado como NÃO público)
    0 = Não contém dados pessoais (pode permanecer como público)
"""

import sys
import os
import csv
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.detectores import SistemaDeteccaoIntegrado
from src.carregador import CarregadorDados


def fazer_predicoes(arquivo_entrada: str, arquivo_saida: str, 
                    coluna_texto: str = None, verbose: bool = True):
    """
    Executa predições e salva resultados.
    
    Args:
        arquivo_entrada: Caminho do arquivo de entrada.
        arquivo_saida: Caminho do arquivo de saída (CSV).
        coluna_texto: Nome da coluna com o texto (auto-detecta se None).
        verbose: Se True, mostra progresso.
    """
    # Configuração otimizada para alta precisão
    config = {
        'cpf_sensibilidade': 0.80,
        'rg_sensibilidade': 0.75,
        'telefone_sensibilidade': 0.75,
        'email_sensibilidade': 0.85,
        'nome_sensibilidade': 0.70,
        'endereco_sensibilidade': 0.80,
    }
    
    # Inicializa sistema (LLM auto-detecta API key)
    sistema = SistemaDeteccaoIntegrado(config, usar_gliner=True)
    carregador = CarregadorDados(coluna_texto=coluna_texto)
    
    # Carrega dados
    if verbose:
        print(f"Carregando dados de: {arquivo_entrada}")
    
    registros = list(carregador.carregar_arquivo(arquivo_entrada))
    
    if verbose:
        print(f"Total de registros: {len(registros)}")
        print("Processando...")
    
    # Faz predições
    predicoes = []
    
    for i, registro in enumerate(registros):
        # Analisa texto
        contem_dados = sistema.contem_dados_pessoais(registro.texto)
        
        predicoes.append({
            'ID': registro.id,
            'Predicao': 1 if contem_dados else 0
        })
        
        # Progresso
        if verbose and (i + 1) % 50 == 0:
            print(f"  Processados: {i + 1}/{len(registros)}")
    
    # Salva resultados
    with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['ID', 'Predicao'])
        writer.writeheader()
        writer.writerows(predicoes)
    
    if verbose:
        # Estatísticas
        total_positivos = sum(1 for p in predicoes if p['Predicao'] == 1)
        total_negativos = len(predicoes) - total_positivos
        
        print(f"\nResultados salvos em: {arquivo_saida}")
        print(f"  - Total de registros: {len(predicoes)}")
        print(f"  - Classificados como contendo dados pessoais: {total_positivos}")
        print(f"  - Classificados como NÃO contendo dados pessoais: {total_negativos}")
    
    return predicoes


def main():
    """Função principal."""
    if len(sys.argv) < 3:
        print("Uso: python predict.py <arquivo_entrada> <arquivo_saida> [coluna_texto]")
        print()
        print("Exemplo:")
        print("  python predict.py dados_teste.xlsx predicoes.csv")
        print("  python predict.py dados.csv saida.csv 'Texto Mascarado'")
        sys.exit(1)
    
    arquivo_entrada = sys.argv[1]
    arquivo_saida = sys.argv[2]
    coluna_texto = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Verifica arquivo de entrada
    if not os.path.exists(arquivo_entrada):
        print(f"Erro: Arquivo não encontrado: {arquivo_entrada}")
        sys.exit(1)
    
    # Executa predições
    fazer_predicoes(arquivo_entrada, arquivo_saida, coluna_texto)


if __name__ == "__main__":
    main()
