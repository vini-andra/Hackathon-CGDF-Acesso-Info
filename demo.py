#!/usr/bin/env python3
"""
Script de Demonstração e Teste
Sistema de Identificação de Dados Sensíveis - Hackathon Participa DF

Este script demonstra as capacidades do sistema usando dados de exemplo.
"""

import sys
import os

# Adiciona o diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.detectores import SistemaDeteccaoIntegrado
from src.carregador import CarregadorDados
from src.metricas import Avaliador, ResultadoClassificacao, GeradorRelatorio


def demo_deteccao_basica():
    """Demonstra detecção básica de dados pessoais."""
    print("=" * 80)
    print("  DEMONSTRAÇÃO 1: DETECÇÃO BÁSICA")
    print("=" * 80)
    
    sistema = SistemaDeteccaoIntegrado()
    
    textos_teste = [
        # Texto com múltiplos dados pessoais
        """
        Prezados, solicito acesso aos meus dados cadastrais.
        Nome: João da Silva Santos
        CPF: 123.456.789-09
        E-mail: joao.silva@email.com
        Telefone: (61) 99999-8888
        """,
        
        # Texto sem dados pessoais
        """
        Solicito informações sobre o processo administrativo nº 00123/2025.
        Gostaria de saber o andamento e previsão de conclusão.
        Atenciosamente.
        """,
        
        # Texto com dados parciais
        """
        Solicito cópia do contrato firmado entre a empresa XPTO Ltda
        e o Governo do Distrito Federal, referente ao pregão 15/2025.
        """,
        
        # Texto com CPF mascarado parcialmente
        """
        Informo que o servidor de matrícula 12345 apresentou o CPF
        110.100.179-87 para atualização cadastral.
        """
    ]
    
    for i, texto in enumerate(textos_teste, 1):
        print(f"\n--- Texto {i} ---")
        print(f"Conteúdo: {texto[:100].strip()}...")
        
        resultado = sistema.obter_resumo(texto)
        
        print(f"Contém dados pessoais: {'SIM' if resultado['contem_dados_pessoais'] else 'NÃO'}")
        print(f"Total de detecções: {resultado['total_deteccoes']}")
        
        if resultado['deteccoes']:
            print("Detecções encontradas:")
            for d in resultado['deteccoes']:
                print(f"  - {d.tipo}: '{d.valor}' (confiança: {d.confianca:.2f})")


def demo_processamento_arquivo(caminho_arquivo: str = None):
    """Demonstra processamento de arquivo."""
    print("\n" + "=" * 80)
    print("  DEMONSTRAÇÃO 2: PROCESSAMENTO DE ARQUIVO")
    print("=" * 80)
    
    if caminho_arquivo and os.path.exists(caminho_arquivo):
        print(f"\nProcessando arquivo: {caminho_arquivo}")
        
        # Carrega dados
        carregador = CarregadorDados()
        registros = list(carregador.carregar_arquivo(caminho_arquivo))
        
        print(f"Total de registros: {len(registros)}")
        print(f"Estatísticas: {carregador.estatisticas}")
        
        # Analisa com o sistema
        sistema = SistemaDeteccaoIntegrado()
        avaliador = Avaliador()
        
        contagem_com_dados = 0
        contagem_sem_dados = 0
        
        for registro in registros:
            resumo = sistema.obter_resumo(registro.texto)
            
            contem_dados = resumo['contem_dados_pessoais']
            if contem_dados:
                contagem_com_dados += 1
            else:
                contagem_sem_dados += 1
            
            # Cria resultado (sem labels reais, usamos a predição)
            resultado = ResultadoClassificacao(
                id=registro.id,
                texto=registro.texto,
                classificacao_real=contem_dados,  # Sem labels, assume a predição
                classificacao_predita=contem_dados,
                deteccoes=resumo['deteccoes'],
                confianca_media=resumo['confianca_media']
            )
            avaliador.adicionar_resultado(resultado)
        
        print(f"\nResultados:")
        print(f"  - Registros com dados pessoais detectados: {contagem_com_dados}")
        print(f"  - Registros sem dados pessoais detectados: {contagem_sem_dados}")
        
        # Mostra alguns exemplos
        print("\nExemplos de detecções:")
        for r in avaliador.resultados[:5]:
            if r.deteccoes:
                print(f"\n  ID {r.id}:")
                print(f"  Texto: {r.texto[:80]}...")
                for d in r.deteccoes[:3]:
                    print(f"    - {d.tipo}: '{d.valor}' (pos: {d.posicao_inicio}-{d.posicao_fim})")
    else:
        print("Arquivo não especificado ou não encontrado.")
        print("Para testar com arquivo, use: python demo.py <caminho_arquivo>")


def demo_metricas_simuladas():
    """Demonstra cálculo de métricas com dados simulados."""
    print("\n" + "=" * 80)
    print("  DEMONSTRAÇÃO 3: MÉTRICAS E RELATÓRIO")
    print("=" * 80)
    
    from src.detectores import DeteccaoEncontrada
    
    avaliador = Avaliador()
    
    # Simula resultados
    # 45 VPs
    for i in range(45):
        avaliador.adicionar_resultado(ResultadoClassificacao(
            id=i+1, texto=f"Texto com dados {i}",
            classificacao_real=True, classificacao_predita=True,
            deteccoes=[DeteccaoEncontrada(tipo="CPF", valor="123.456.789-09",
                                         posicao_inicio=0, posicao_fim=14, confianca=0.95)]
        ))
    
    # 49 VNs
    for i in range(49):
        avaliador.adicionar_resultado(ResultadoClassificacao(
            id=100+i, texto=f"Texto sem dados {i}",
            classificacao_real=False, classificacao_predita=False,
            deteccoes=[]
        ))
    
    # 3 FNs
    for i in range(3):
        avaliador.adicionar_resultado(ResultadoClassificacao(
            id=200+i, texto=f"Texto com dados não detectado {i}",
            classificacao_real=True, classificacao_predita=False,
            deteccoes=[]
        ))
    
    # 2 FPs
    for i in range(2):
        avaliador.adicionar_resultado(ResultadoClassificacao(
            id=300+i, texto=f"Texto sem dados detectado errado {i}",
            classificacao_real=False, classificacao_predita=True,
            deteccoes=[DeteccaoEncontrada(tipo="RG", valor="12345678",
                                         posicao_inicio=0, posicao_fim=8, confianca=0.75)]
        ))
    
    # Calcula métricas
    metricas = avaliador.calcular_metricas()
    
    # Gera relatório resumido
    print("\n" + GeradorRelatorio.gerar_relatorio_texto(metricas, detalhado=False))


def demo_configuracao_avancada():
    """Demonstra configuração avançada do sistema."""
    print("\n" + "=" * 80)
    print("  DEMONSTRAÇÃO 4: CONFIGURAÇÃO AVANÇADA")
    print("=" * 80)
    
    # Configuração com sensibilidades personalizadas
    config_alta_precisao = {
        'cpf_sensibilidade': 0.90,
        'rg_sensibilidade': 0.85,
        'telefone_sensibilidade': 0.85,
        'email_sensibilidade': 0.90,
        'nome_sensibilidade': 0.80,
    }
    
    config_alto_recall = {
        'cpf_sensibilidade': 0.60,
        'rg_sensibilidade': 0.55,
        'telefone_sensibilidade': 0.55,
        'email_sensibilidade': 0.70,
        'nome_sensibilidade': 0.50,
    }
    
    texto_teste = """
    Processo SEI 00123456789
    Servidor: Carlos Eduardo Souza
    Matrícula: 12345678
    Contato: 61 98765-4321
    """
    
    print(f"\nTexto de teste:\n{texto_teste}")
    
    print("\n--- Configuração ALTA PRECISÃO (menos detecções, mais confiáveis) ---")
    sistema_ap = SistemaDeteccaoIntegrado(config_alta_precisao)
    resultado_ap = sistema_ap.obter_resumo(texto_teste)
    print(f"Detecções: {resultado_ap['total_deteccoes']}")
    for d in resultado_ap['deteccoes']:
        print(f"  - {d.tipo}: '{d.valor}' (conf: {d.confianca:.2f})")
    
    print("\n--- Configuração ALTO RECALL (mais detecções, possíveis FPs) ---")
    sistema_ar = SistemaDeteccaoIntegrado(config_alto_recall)
    resultado_ar = sistema_ar.obter_resumo(texto_teste)
    print(f"Detecções: {resultado_ar['total_deteccoes']}")
    for d in resultado_ar['deteccoes']:
        print(f"  - {d.tipo}: '{d.valor}' (conf: {d.confianca:.2f})")


def main():
    """Função principal de demonstração."""
    print("\n" + "█" * 80)
    print("█" + " SISTEMA DE IDENTIFICAÇÃO DE DADOS SENSÍVEIS ".center(78) + "█")
    print("█" + " Hackathon Participa DF - Demonstração ".center(78) + "█")
    print("█" * 80)
    
    # Demo 1: Detecção básica
    demo_deteccao_basica()
    
    # Demo 2: Processamento de arquivo (se fornecido)
    if len(sys.argv) > 1:
        demo_processamento_arquivo(sys.argv[1])
    else:
        demo_processamento_arquivo()
    
    # Demo 3: Métricas simuladas
    demo_metricas_simuladas()
    
    # Demo 4: Configuração avançada
    demo_configuracao_avancada()
    
    print("\n" + "=" * 80)
    print("  FIM DA DEMONSTRAÇÃO")
    print("=" * 80)
    print("\nPara processar seus próprios dados:")
    print("  python main.py <arquivo.xlsx> [opções]")
    print("\nPara mais informações:")
    print("  python main.py --help")


if __name__ == "__main__":
    main()
