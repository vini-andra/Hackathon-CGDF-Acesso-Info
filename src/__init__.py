"""
Sistema de Identificação de Dados Sensíveis
1º Hackathon em Controle Social - Desafio Participa DF

Módulos:
- detectores: Classes de detecção de dados pessoais
- carregador: Carregamento de dados multi-formato
- metricas: Cálculo de métricas e geração de relatórios
"""

from .detectores import (
    SistemaDeteccaoIntegrado,
    DetectorCPF,
    DetectorRG,
    DetectorTelefone,
    DetectorEmail,
    DetectorNome,
    DetectorEndereco,
    DetectorPlaca,
    DeteccaoEncontrada
)

from .carregador import (
    CarregadorDados,
    CarregadorDiretorio,
    RegistroTexto,
    carregar_dados_rapido
)

from .metricas import (
    Avaliador,
    ResultadoClassificacao,
    MetricasDesempenho,
    GeradorRelatorio
)

__version__ = "1.0.0"
__author__ = "Participante Hackathon Participa DF"

__all__ = [
    'SistemaDeteccaoIntegrado',
    'DetectorCPF',
    'DetectorRG',
    'DetectorTelefone',
    'DetectorEmail',
    'DetectorNome',
    'DetectorEndereco',
    'DetectorPlaca',
    'DeteccaoEncontrada',
    'CarregadorDados',
    'CarregadorDiretorio',
    'RegistroTexto',
    'carregar_dados_rapido',
    'Avaliador',
    'ResultadoClassificacao',
    'MetricasDesempenho',
    'GeradorRelatorio',
]
