"""
Módulo de Carregamento de Dados Multi-Formato
Sistema de Identificação de Dados Sensíveis - Hackathon Participa DF

Suporta: xlsx, xls, csv, tsv, json, txt
"""

import pandas as pd
import json
import os
from pathlib import Path
from typing import Generator, Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class RegistroTexto:
    """Representa um registro de texto para análise."""
    id: Any                      # Identificador do registro
    texto: str                   # Texto para análise
    metadados: Dict = None       # Metadados adicionais
    fonte: str = ""              # Arquivo de origem
    linha_original: int = 0      # Linha no arquivo original


class CarregadorDados:
    """
    Carregador universal de dados para análise.
    
    Suporta múltiplos formatos de arquivo e extração de texto.
    """
    
    # Formatos suportados e seus handlers
    FORMATOS_SUPORTADOS = {
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.csv': 'csv',
        '.tsv': 'tsv',
        '.json': 'json',
        '.txt': 'texto',
        '.parquet': 'parquet',
    }
    
    def __init__(self, coluna_id: str = 'ID', coluna_texto: str = None):
        """
        Inicializa o carregador.
        
        Args:
            coluna_id: Nome da coluna que contém o identificador.
            coluna_texto: Nome da coluna que contém o texto (auto-detecta se None).
        """
        self.coluna_id = coluna_id
        self.coluna_texto = coluna_texto
        self.estatisticas = {
            'arquivos_processados': 0,
            'registros_carregados': 0,
            'erros': []
        }
    
    def carregar_arquivo(self, caminho: str) -> Generator[RegistroTexto, None, None]:
        """
        Carrega um arquivo e retorna registros.
        
        Args:
            caminho: Caminho para o arquivo.
            
        Yields:
            RegistroTexto para cada registro no arquivo.
        """
        caminho = Path(caminho)
        
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
        
        extensao = caminho.suffix.lower()
        
        if extensao not in self.FORMATOS_SUPORTADOS:
            raise ValueError(f"Formato não suportado: {extensao}. "
                           f"Suportados: {list(self.FORMATOS_SUPORTADOS.keys())}")
        
        tipo_formato = self.FORMATOS_SUPORTADOS[extensao]
        
        if tipo_formato == 'excel':
            yield from self._carregar_excel(caminho)
        elif tipo_formato == 'csv':
            yield from self._carregar_csv(caminho)
        elif tipo_formato == 'tsv':
            yield from self._carregar_csv(caminho, sep='\t')
        elif tipo_formato == 'json':
            yield from self._carregar_json(caminho)
        elif tipo_formato == 'texto':
            yield from self._carregar_texto(caminho)
        elif tipo_formato == 'parquet':
            yield from self._carregar_parquet(caminho)
        
        self.estatisticas['arquivos_processados'] += 1
    
    def _carregar_excel(self, caminho: Path) -> Generator[RegistroTexto, None, None]:
        """Carrega arquivo Excel."""
        try:
            # Tenta carregar todas as planilhas
            todas_planilhas = pd.read_excel(caminho, sheet_name=None)
            
            for nome_planilha, df in todas_planilhas.items():
                yield from self._processar_dataframe(df, str(caminho), nome_planilha)
                
        except Exception as e:
            self.estatisticas['erros'].append(f"Erro ao carregar {caminho}: {str(e)}")
            raise
    
    def _carregar_csv(self, caminho: Path, sep: str = ',') -> Generator[RegistroTexto, None, None]:
        """Carrega arquivo CSV/TSV."""
        try:
            # Tenta detectar encoding
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(caminho, sep=sep, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError(f"Não foi possível decodificar {caminho}")
            
            yield from self._processar_dataframe(df, str(caminho))
            
        except Exception as e:
            self.estatisticas['erros'].append(f"Erro ao carregar {caminho}: {str(e)}")
            raise
    
    def _carregar_json(self, caminho: Path) -> Generator[RegistroTexto, None, None]:
        """Carrega arquivo JSON."""
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            if isinstance(dados, list):
                df = pd.DataFrame(dados)
                yield from self._processar_dataframe(df, str(caminho))
            elif isinstance(dados, dict):
                # Se for dict com chave 'data' ou 'registros'
                if 'data' in dados:
                    df = pd.DataFrame(dados['data'])
                elif 'registros' in dados:
                    df = pd.DataFrame(dados['registros'])
                else:
                    # Trata como um único registro
                    df = pd.DataFrame([dados])
                yield from self._processar_dataframe(df, str(caminho))
                
        except Exception as e:
            self.estatisticas['erros'].append(f"Erro ao carregar {caminho}: {str(e)}")
            raise
    
    def _carregar_texto(self, caminho: Path) -> Generator[RegistroTexto, None, None]:
        """Carrega arquivo de texto simples."""
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Cada linha não vazia é um registro
            for idx, linha in enumerate(conteudo.split('\n'), 1):
                if linha.strip():
                    yield RegistroTexto(
                        id=idx,
                        texto=linha.strip(),
                        metadados={},
                        fonte=str(caminho),
                        linha_original=idx
                    )
                    self.estatisticas['registros_carregados'] += 1
                    
        except Exception as e:
            self.estatisticas['erros'].append(f"Erro ao carregar {caminho}: {str(e)}")
            raise
    
    def _carregar_parquet(self, caminho: Path) -> Generator[RegistroTexto, None, None]:
        """Carrega arquivo Parquet."""
        try:
            df = pd.read_parquet(caminho)
            yield from self._processar_dataframe(df, str(caminho))
        except Exception as e:
            self.estatisticas['erros'].append(f"Erro ao carregar {caminho}: {str(e)}")
            raise
    
    def _processar_dataframe(self, df: pd.DataFrame, fonte: str, 
                             planilha: str = None) -> Generator[RegistroTexto, None, None]:
        """Processa um DataFrame e gera registros."""
        
        # Detecta coluna de texto se não especificada
        coluna_texto = self.coluna_texto
        if coluna_texto is None:
            coluna_texto = self._detectar_coluna_texto(df)
        
        # Detecta coluna de ID
        coluna_id = self._detectar_coluna_id(df)
        
        for idx, row in df.iterrows():
            # Obtém texto
            texto = str(row.get(coluna_texto, ''))
            
            # Se não encontrou texto na coluna principal, concatena todas as colunas de texto
            if not texto.strip() and coluna_texto is None:
                texto = ' '.join(
                    str(v) for v in row.values 
                    if isinstance(v, str) and len(str(v)) > 10
                )
            
            if not texto.strip():
                continue
            
            # Obtém ID
            if coluna_id and coluna_id in row:
                registro_id = row[coluna_id]
            else:
                registro_id = idx + 1
            
            # Metadados
            metadados = {
                col: row[col] 
                for col in df.columns 
                if col not in [coluna_texto, coluna_id]
            }
            
            if planilha:
                metadados['planilha'] = planilha
            
            yield RegistroTexto(
                id=registro_id,
                texto=texto,
                metadados=metadados,
                fonte=fonte,
                linha_original=idx + 1
            )
            
            self.estatisticas['registros_carregados'] += 1
    
    def _detectar_coluna_texto(self, df: pd.DataFrame) -> str:
        """Detecta automaticamente a coluna que contém o texto principal."""
        
        # Nomes comuns para colunas de texto
        nomes_texto = [
            'texto', 'text', 'conteudo', 'content', 'descricao', 'description',
            'mensagem', 'message', 'pedido', 'solicitacao', 'manifestacao',
            'texto_mascarado', 'texto mascarado', 'body', 'corpo'
        ]
        
        # Busca por nome
        for col in df.columns:
            if col.lower().replace(' ', '_') in nomes_texto:
                return col
        
        # Busca pela coluna com textos mais longos (média)
        colunas_texto = []
        for col in df.columns:
            if df[col].dtype == 'object':
                media_len = df[col].astype(str).str.len().mean()
                colunas_texto.append((col, media_len))
        
        if colunas_texto:
            colunas_texto.sort(key=lambda x: x[1], reverse=True)
            return colunas_texto[0][0]
        
        # Retorna primeira coluna se nada encontrado
        return df.columns[0] if len(df.columns) > 0 else None
    
    def _detectar_coluna_id(self, df: pd.DataFrame) -> Optional[str]:
        """Detecta automaticamente a coluna de ID."""
        
        nomes_id = ['id', 'ID', 'Id', 'codigo', 'Codigo', 'CODIGO', 
                    'numero', 'Numero', 'NUMERO', 'protocolo']
        
        for col in df.columns:
            if col in nomes_id or col.lower() == 'id':
                return col
        
        return None


class CarregadorDiretorio:
    """Carrega múltiplos arquivos de um diretório."""
    
    def __init__(self, carregador: CarregadorDados = None):
        self.carregador = carregador or CarregadorDados()
    
    def carregar_diretorio(self, diretorio: str, 
                          recursivo: bool = False) -> Generator[RegistroTexto, None, None]:
        """
        Carrega todos os arquivos suportados de um diretório.
        
        Args:
            diretorio: Caminho do diretório.
            recursivo: Se True, busca em subdiretórios.
        """
        diretorio = Path(diretorio)
        
        if not diretorio.exists():
            raise FileNotFoundError(f"Diretório não encontrado: {diretorio}")
        
        padrao = '**/*' if recursivo else '*'
        
        for arquivo in diretorio.glob(padrao):
            if arquivo.is_file() and arquivo.suffix.lower() in CarregadorDados.FORMATOS_SUPORTADOS:
                try:
                    yield from self.carregador.carregar_arquivo(str(arquivo))
                except Exception as e:
                    print(f"Aviso: Erro ao processar {arquivo}: {e}")
                    continue


def carregar_dados_rapido(caminho: str, coluna_texto: str = None) -> List[RegistroTexto]:
    """
    Função utilitária para carregar dados rapidamente.
    
    Args:
        caminho: Caminho do arquivo ou diretório.
        coluna_texto: Nome da coluna de texto (opcional).
    
    Returns:
        Lista de RegistroTexto.
    """
    carregador = CarregadorDados(coluna_texto=coluna_texto)
    
    if os.path.isdir(caminho):
        carregador_dir = CarregadorDiretorio(carregador)
        return list(carregador_dir.carregar_diretorio(caminho))
    else:
        return list(carregador.carregar_arquivo(caminho))


if __name__ == "__main__":
    # Teste com arquivo de exemplo
    print("Testando carregador de dados...")
    
    carregador = CarregadorDados()
    
    # Teste de detecção de formato
    for ext in CarregadorDados.FORMATOS_SUPORTADOS:
        print(f"  Formato {ext}: suportado")
