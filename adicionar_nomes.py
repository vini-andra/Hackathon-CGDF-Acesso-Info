"""
Script para adicionar nomes de forma permanente ao sistema de detecção.

Este script:
1. Carrega nomes de um arquivo CSV
2. Extrai primeiros nomes e sobrenomes
3. Salva em arquivos JSON para uso permanente pelo detector
"""

import pandas as pd
import json
import os

# Diretório onde os arquivos JSON serão salvos
DIRETORIO_DADOS = os.path.join(os.path.dirname(__file__), 'dados')
ARQUIVO_NOMES = os.path.join(DIRETORIO_DADOS, 'nomes_proprios.json')
ARQUIVO_SOBRENOMES = os.path.join(DIRETORIO_DADOS, 'sobrenomes.json')


def carregar_nomes_existentes():
    """Carrega nomes já salvos nos arquivos JSON."""
    nomes_existentes = set()
    sobrenomes_existentes = set()
    
    if os.path.exists(ARQUIVO_NOMES):
        with open(ARQUIVO_NOMES, 'r', encoding='utf-8') as f:
            nomes_existentes = set(json.load(f))
    
    if os.path.exists(ARQUIVO_SOBRENOMES):
        with open(ARQUIVO_SOBRENOMES, 'r', encoding='utf-8') as f:
            sobrenomes_existentes = set(json.load(f))
    
    return nomes_existentes, sobrenomes_existentes


def carregar_nomes_do_csv(caminho_csv: str):
    """Carrega nomes do CSV e extrai primeiros nomes e sobrenomes únicos."""
    
    # Lê o arquivo (uma coluna com nomes completos)
    df = pd.read_csv(caminho_csv, header=None, names=['nome_completo'])
    
    # Conectivos para ignorar
    conectivos = {'de', 'da', 'do', 'das', 'dos', 'e', 'di', 'del'}
    
    primeiros_nomes = set()
    sobrenomes = set()
    
    for nome_completo in df['nome_completo'].dropna().unique():
        partes = nome_completo.strip().split()
        
        if len(partes) >= 2:
            # Primeiro nome
            primeiros_nomes.add(partes[0].lower())
            
            # Sobrenomes (ignora conectivos)
            for parte in partes[1:]:
                if parte.lower() not in conectivos:
                    sobrenomes.add(parte.lower())
    
    return primeiros_nomes, sobrenomes


def salvar_nomes_permanentemente(novos_nomes: set, novos_sobrenomes: set):
    """Salva os nomes de forma permanente em arquivos JSON."""
    
    # Cria o diretório se não existir
    os.makedirs(DIRETORIO_DADOS, exist_ok=True)
    
    # Carrega nomes existentes
    nomes_existentes, sobrenomes_existentes = carregar_nomes_existentes()
    
    # Combina com os novos
    todos_nomes = nomes_existentes.union(novos_nomes)
    todos_sobrenomes = sobrenomes_existentes.union(novos_sobrenomes)
    
    # Salva em arquivos JSON
    with open(ARQUIVO_NOMES, 'w', encoding='utf-8') as f:
        json.dump(sorted(list(todos_nomes)), f, ensure_ascii=False, indent=2)
    
    with open(ARQUIVO_SOBRENOMES, 'w', encoding='utf-8') as f:
        json.dump(sorted(list(todos_sobrenomes)), f, ensure_ascii=False, indent=2)
    
    nomes_adicionados = len(todos_nomes) - len(nomes_existentes)
    sobrenomes_adicionados = len(todos_sobrenomes) - len(sobrenomes_existentes)
    
    return len(todos_nomes), len(todos_sobrenomes), nomes_adicionados, sobrenomes_adicionados


def main(caminho_csv: str):
    """Função principal para adicionar nomes do CSV."""
    print(f"Carregando nomes de: {caminho_csv}")
    
    # Carrega do CSV
    novos_nomes, novos_sobrenomes = carregar_nomes_do_csv(caminho_csv)
    print(f"Encontrados no CSV: {len(novos_nomes)} primeiros nomes, {len(novos_sobrenomes)} sobrenomes")
    
    # Salva permanentemente
    total_nomes, total_sobrenomes, add_nomes, add_sobrenomes = salvar_nomes_permanentemente(
        novos_nomes, novos_sobrenomes
    )
    
    print(f"\n✅ Nomes salvos permanentemente!")
    print(f"   - Primeiros nomes: {total_nomes} total ({add_nomes} novos)")
    print(f"   - Sobrenomes: {total_sobrenomes} total ({add_sobrenomes} novos)")
    print(f"\nArquivos salvos em:")
    print(f"   - {ARQUIVO_NOMES}")
    print(f"   - {ARQUIVO_SOBRENOMES}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        caminho = sys.argv[1]
    else:
        # Caminho padrão
        caminho = '/home/vinicius/teste/ArquivosTeste/nomes.csv'
    
    main(caminho)