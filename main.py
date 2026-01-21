#!/usr/bin/env python3
"""
Sistema de Identificação de Dados Sensíveis
1º Hackathon em Controle Social - Desafio Participa DF

Script principal para execução do sistema de detecção de dados pessoais
em pedidos de acesso à informação.

Uso:
    python main.py <arquivo_entrada> [opções]

Exemplos:
    python main.py dados.xlsx
    python main.py dados.csv --coluna-texto "Texto Mascarado"
    python main.py dados.xlsx --output resultados.csv --formato csv
    python main.py dados.xlsx --labels rotulos.csv --avaliar
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
import pandas as pd

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.detectores import SistemaDeteccaoIntegrado, DeteccaoEncontrada
from src.carregador import CarregadorDados, RegistroTexto, carregar_dados_rapido
from src.metricas import (
    Avaliador, ResultadoClassificacao, MetricasDesempenho,
    GeradorRelatorio
)


class SistemaIdentificacaoDadosSensiveis:
    """
    Sistema principal de identificação de dados sensíveis.
    
    Coordena carregamento de dados, detecção e geração de relatórios.
    """
    
    def __init__(self, config: Dict = None):
        """
        Inicializa o sistema.
        
        Args:
            config: Configurações do sistema.
        """
        self.config = config or {}
        self.detector = SistemaDeteccaoIntegrado(self.config)
        self.avaliador = Avaliador()
        self.resultados: List[ResultadoClassificacao] = []
    
    def processar_arquivo(self, 
                          caminho_entrada: str,
                          coluna_texto: str = None,
                          labels: Dict[any, bool] = None,
                          verbose: bool = True) -> List[ResultadoClassificacao]:
        """
        Processa um arquivo e retorna resultados.
        
        Args:
            caminho_entrada: Caminho do arquivo de entrada.
            coluna_texto: Nome da coluna com o texto.
            labels: Dicionário {id: True/False} com classificações reais.
            verbose: Se True, mostra progresso.
        
        Returns:
            Lista de ResultadoClassificacao.
        """
        self.resultados = []
        self.avaliador.limpar()
        
        # Carrega dados
        carregador = CarregadorDados(coluna_texto=coluna_texto)
        registros = list(carregador.carregar_arquivo(caminho_entrada))
        
        if verbose:
            print(f"\nProcessando {len(registros)} registros de '{caminho_entrada}'...")
            print("-" * 60)
        
        for i, registro in enumerate(registros):
            # Analisa o texto
            resumo = self.detector.obter_resumo(registro.texto)
            
            # Determina classificação predita
            classificacao_predita = resumo['contem_dados_pessoais']
            
            # Determina classificação real (se disponível)
            if labels is not None:
                classificacao_real = labels.get(registro.id, False)
            else:
                # Se não há labels, assume True se detectou (para modo demonstração)
                classificacao_real = classificacao_predita
            
            # Cria resultado
            resultado = ResultadoClassificacao(
                id=registro.id,
                texto=registro.texto,
                classificacao_real=classificacao_real,
                classificacao_predita=classificacao_predita,
                deteccoes=resumo['deteccoes'],
                confianca_media=resumo['confianca_media']
            )
            
            self.resultados.append(resultado)
            self.avaliador.adicionar_resultado(resultado)
            
            # Progresso
            if verbose and (i + 1) % 10 == 0:
                print(f"  Processados: {i + 1}/{len(registros)}")
        
        if verbose:
            print(f"\nProcessamento concluído: {len(self.resultados)} registros analisados")
        
        return self.resultados
    
    def calcular_metricas(self) -> MetricasDesempenho:
        """Calcula métricas de desempenho."""
        return self.avaliador.calcular_metricas()
    
    def gerar_relatorio(self, detalhado: bool = True) -> str:
        """Gera relatório de texto."""
        metricas = self.calcular_metricas()
        return GeradorRelatorio.gerar_relatorio_texto(
            metricas, self.resultados if detalhado else None, detalhado
        )
    
    def exportar_resultados(self, caminho: str, formato: str = 'csv'):
        """
        Exporta resultados para arquivo.
        
        Args:
            caminho: Caminho do arquivo de saída.
            formato: 'csv', 'json' ou 'txt'.
        """
        if formato == 'csv':
            GeradorRelatorio.gerar_csv_resultados(self.resultados, caminho)
        elif formato == 'json':
            metricas = self.calcular_metricas()
            dados = {
                'metricas': metricas.to_dict(),
                'resultados': [
                    {
                        'id': r.id,
                        'classificacao_real': r.classificacao_real,
                        'classificacao_predita': r.classificacao_predita,
                        'tipo_resultado': r.tipo_resultado,
                        'deteccoes': [
                            {
                                'tipo': d.tipo,
                                'valor': d.valor,
                                'posicao': (d.posicao_inicio, d.posicao_fim),
                                'confianca': d.confianca
                            }
                            for d in r.deteccoes
                        ]
                    }
                    for r in self.resultados
                ]
            }
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
        else:  # txt
            relatorio = self.gerar_relatorio()
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(relatorio)
    
    def obter_predicoes(self) -> List[Tuple[any, bool]]:
        """
        Retorna lista de (id, predicao) para submissão.
        
        Returns:
            Lista de tuplas (id_registro, contem_dados_pessoais).
        """
        return [(r.id, r.classificacao_predita) for r in self.resultados]


def carregar_labels(caminho: str) -> Dict[any, bool]:
    """
    Carrega arquivo de labels para avaliação.
    
    O arquivo deve ter formato CSV com colunas: ID,Label
    Onde Label é 1 (contém dados pessoais) ou 0 (não contém).
    """
    df = pd.read_csv(caminho)
    
    # Detecta colunas
    col_id = None
    col_label = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'id' in col_lower:
            col_id = col
        if 'label' in col_lower or 'class' in col_lower or 'target' in col_lower:
            col_label = col
    
    if col_id is None:
        col_id = df.columns[0]
    if col_label is None:
        col_label = df.columns[-1]
    
    return {row[col_id]: bool(row[col_label]) for _, row in df.iterrows()}


def main():
    """Função principal do sistema."""
    
    parser = argparse.ArgumentParser(
        description="Sistema de Identificação de Dados Sensíveis - Hackathon Participa DF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py dados.xlsx
  python main.py dados.csv --coluna-texto "Texto Mascarado"
  python main.py dados.xlsx --labels rotulos.csv --output resultados.json --formato json
  python main.py dados.xlsx --sensibilidade-cpf 0.9 --sensibilidade-nome 0.6
        """
    )
    
    parser.add_argument('entrada', help='Arquivo de entrada (xlsx, csv, json, txt)')
    
    parser.add_argument('--coluna-texto', '-c', 
                        help='Nome da coluna que contém o texto')
    
    parser.add_argument('--labels', '-l',
                        help='Arquivo CSV com labels reais para avaliação')
    
    parser.add_argument('--output', '-o',
                        help='Arquivo de saída para resultados')
    
    parser.add_argument('--formato', '-f', choices=['csv', 'json', 'txt'],
                        default='txt', help='Formato de saída (default: txt)')
    
    parser.add_argument('--detalhado', '-d', action='store_true',
                        help='Incluir detalhes de cada registro no relatório')
    
    parser.add_argument('--silencioso', '-s', action='store_true',
                        help='Modo silencioso (sem progresso)')
    
    # Configurações de sensibilidade
    parser.add_argument('--sensibilidade-cpf', type=float, default=0.80,
                        help='Sensibilidade para detecção de CPF (0.0-1.0)')
    parser.add_argument('--sensibilidade-rg', type=float, default=0.75,
                        help='Sensibilidade para detecção de RG (0.0-1.0)')
    parser.add_argument('--sensibilidade-telefone', type=float, default=0.75,
                        help='Sensibilidade para detecção de telefone (0.0-1.0)')
    parser.add_argument('--sensibilidade-email', type=float, default=0.85,
                        help='Sensibilidade para detecção de e-mail (0.0-1.0)')
    parser.add_argument('--sensibilidade-nome', type=float, default=0.70,
                        help='Sensibilidade para detecção de nome (0.0-1.0)')
    
    args = parser.parse_args()
    
    # Verifica se arquivo existe
    if not os.path.exists(args.entrada):
        print(f"Erro: Arquivo não encontrado: {args.entrada}")
        sys.exit(1)
    
    # Configuração
    config = {
        'cpf_sensibilidade': args.sensibilidade_cpf,
        'rg_sensibilidade': args.sensibilidade_rg,
        'telefone_sensibilidade': args.sensibilidade_telefone,
        'email_sensibilidade': args.sensibilidade_email,
        'nome_sensibilidade': args.sensibilidade_nome,
    }
    
    # Carrega labels se fornecido
    labels = None
    if args.labels:
        if not os.path.exists(args.labels):
            print(f"Erro: Arquivo de labels não encontrado: {args.labels}")
            sys.exit(1)
        labels = carregar_labels(args.labels)
    
    # Executa processamento
    sistema = SistemaIdentificacaoDadosSensiveis(config)
    
    sistema.processar_arquivo(
        args.entrada,
        coluna_texto=args.coluna_texto,
        labels=labels,
        verbose=not args.silencioso
    )
    
    # Gera e exibe relatório
    relatorio = sistema.gerar_relatorio(detalhado=args.detalhado)
    print(relatorio)
    
    # Exporta se solicitado
    if args.output:
        sistema.exportar_resultados(args.output, args.formato)
        print(f"\nResultados exportados para: {args.output}")
    
    # Retorna código de saída baseado nas métricas
    metricas = sistema.calcular_metricas()
    if metricas.f1_score >= 0.9:
        sys.exit(0)  # Sucesso: F1 >= 90%
    else:
        sys.exit(0)  # Ainda retorna 0 para não indicar erro


if __name__ == "__main__":
    main()
