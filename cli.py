#!/usr/bin/env python3
import os
import sys
import glob
from typing import List, Optional

# Adiciona diretório atual ao path para importação
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from main import SistemaIdentificacaoDadosSensiveis

# Constantes de cores para terminal (se suportado)
class Cores:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def exibir_banner():
    print(f"{Cores.HEADER}{Cores.BOLD}")
    print("=" * 60)
    print("   SISTEMA DE IDENTIFICAÇÃO DE DADOS SENSÍVEIS")
    print("   Hackathon Participa DF")
    print("=" * 60)
    print(f"{Cores.ENDC}")

def listar_arquivos(diretorio: str = "dados") -> List[str]:
    extensoes = ['*.json', '*.csv', '*.xlsx', '*.txt']
    arquivos = []
    
    # Busca na raiz e em subpastas comuns
    caminhos = ['.', 'dados', 'entradas']
    
    for caminho in caminhos:
        if os.path.exists(caminho):
            for ext in extensoes:
                padrao = os.path.join(caminho, ext)
                arquivos.extend(glob.glob(padrao))
    
    # Remove duplicatas e normaliza paths
    return sorted(list(set(arquivos)))

def perguntar_selecao(opcoes: List[str], prompt: str) -> str:
    while True:
        try:
            print(f"\n{prompt}")
            for i, opcao in enumerate(opcoes):
                print(f"  {Cores.BLUE}[{i+1}]{Cores.ENDC} {opcao}")
            
            escolha = input(f"\n{Cores.BOLD}>> Digite o número da opção (ou 's' para sair): {Cores.ENDC}")
            
            if escolha.lower() == 's':
                sys.exit(0)
                
            idx = int(escolha) - 1
            if 0 <= idx < len(opcoes):
                return opcoes[idx]
            else:
                print(f"{Cores.WARNING}Opção inválida! Tente novamente.{Cores.ENDC}")
        except ValueError:
            print(f"{Cores.WARNING}Entrada inválida! Digite um número.{Cores.ENDC}")

def perguntar_texto(prompt: str, default: str = None) -> str:
    dica = f" [{default}]" if default else ""
    resposta = input(f"{Cores.BOLD}{prompt}{dica}: {Cores.ENDC}")
    return resposta.strip() or default

def configurar_sensibilidade() -> dict:
    print(f"\n{Cores.HEADER}--- Configuração de Sensibilidade ---{Cores.ENDC}")
    
    opcoes = ["Padrão (Recomendado)", "Personalizada"]
    escolha = perguntar_selecao(opcoes, "Escolha o modo:")
    
    config = {}
    
    if escolha == "Personalizada":
        print(f"\n{Cores.BLUE}Defina os valores de sensibilidade (0.0 a 1.0):{Cores.ENDC}")
        try:
            config['cpf_sensibilidade'] = float(perguntar_texto("CPF", "0.80"))
            config['rg_sensibilidade'] = float(perguntar_texto("RG", "0.75"))
            config['telefone_sensibilidade'] = float(perguntar_texto("Telefone", "0.75"))
            config['email_sensibilidade'] = float(perguntar_texto("E-mail", "0.85"))
            config['nome_sensibilidade'] = float(perguntar_texto("Nome", "0.70"))
        except ValueError:
            print(f"{Cores.WARNING}Valor inválido! Usando padrão.{Cores.ENDC}")
            return {}
            
    return config

def main():
    limpar_tela()
    exibir_banner()
    
    # 1. Seleção de Arquivo
    print(f"{Cores.GREEN}Passo 1: Seleção do Arquivo{Cores.ENDC}")
    arquivos = listar_arquivos()
    
    if not arquivos:
        print(f"{Cores.FAIL}Nenhum arquivo de dados encontrado em ./, ./dados ou ./ArquivosTeste{Cores.ENDC}")
        caminho_arquivo = input("Digite o caminho completo do arquivo: ").strip()
    else:
        arquivos.append("Outro (Digitar caminho)")
        escolha = perguntar_selecao(arquivos, "Selecione o arquivo para analisar:")
        
        if escolha == "Outro (Digitar caminho)":
            caminho_arquivo = input("Digite o caminho completo do arquivo: ").strip()
        else:
            caminho_arquivo = escolha
            
    if not os.path.exists(caminho_arquivo):
        print(f"{Cores.FAIL}Arquivo não encontrado!{Cores.ENDC}")
        return

    # 2. Configuração
    print(f"\n{Cores.GREEN}Passo 2: Configuração{Cores.ENDC}")
    config = configurar_sensibilidade()
    
    # 3. Execução
    print(f"\n{Cores.GREEN}Passo 3: Processamento{Cores.ENDC}")
    print("Iniciando análise...")
    
    try:
        sistema = SistemaIdentificacaoDadosSensiveis(config)
        resultados = sistema.processar_arquivo(caminho_arquivo, verbose=True)
        
        # 4. Relatório
        print(f"\n{Cores.GREEN}Passo 4: Resultados{Cores.ENDC}")
        metricas = sistema.calcular_metricas()
        
        print(f"\n{Cores.BOLD}Resumo:{Cores.ENDC}")
        print(f"Total de registros: {metricas.total_registros}")
        print(f"Dados Pessoais Detectados: {metricas.verdadeiros_positivos + metricas.falsos_positivos}")
        
        salvar = perguntar_texto("\nDeseja salvar o relatório completo? (s/n)", "s")
        if salvar.lower() == 's':
            nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
            output_dir = "resultados"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            output_default = os.path.join(output_dir, f"relatorio_{nome_base}.txt")
            output_path = perguntar_texto("Nome do arquivo de saída", output_default)
            
            sistema.exportar_resultados(output_path, formato='txt')
            print(f"{Cores.BLUE}Relatório salvo em: {os.path.abspath(output_path)}{Cores.ENDC}")
            
            # Pergunta sobre JSON
            salvar_json = perguntar_texto("Salvar também em JSON (dados estruturados)? (s/n)", "n")
            if salvar_json.lower() == 's':
                 json_path = output_path.replace('.txt', '.json')
                 sistema.exportar_resultados(json_path, formato='json')
                 print(f"{Cores.BLUE}JSON salvo em: {os.path.abspath(json_path)}{Cores.ENDC}")

    except Exception as e:
        print(f"{Cores.FAIL}Erro durante a execução: {e}{Cores.ENDC}")
        import traceback
        traceback.print_exc()

    print(f"\n{Cores.HEADER}Finalizado!{Cores.ENDC}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
