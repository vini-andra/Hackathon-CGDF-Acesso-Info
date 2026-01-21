"""
Módulo de Métricas e Avaliação
Sistema de Identificação de Dados Sensíveis - Hackathon Participa DF

Calcula métricas de desempenho: VP, VN, FP, FN, Precisão, Recall, F1
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import json
from datetime import datetime


@dataclass
class ResultadoClassificacao:
    """Resultado da classificação de um registro."""
    id: Any                          # ID do registro
    texto: str                       # Texto analisado
    classificacao_real: bool         # True se realmente contém dados pessoais
    classificacao_predita: bool      # True se o modelo detectou dados pessoais
    deteccoes: List = field(default_factory=list)  # Detecções encontradas
    confianca_media: float = 0.0     # Confiança média das detecções
    
    @property
    def verdadeiro_positivo(self) -> bool:
        """É VP: contém dados E foi detectado."""
        return self.classificacao_real and self.classificacao_predita
    
    @property
    def verdadeiro_negativo(self) -> bool:
        """É VN: não contém dados E não foi detectado."""
        return not self.classificacao_real and not self.classificacao_predita
    
    @property
    def falso_positivo(self) -> bool:
        """É FP: não contém dados MAS foi detectado."""
        return not self.classificacao_real and self.classificacao_predita
    
    @property
    def falso_negativo(self) -> bool:
        """É FN: contém dados MAS não foi detectado."""
        return self.classificacao_real and not self.classificacao_predita
    
    @property
    def tipo_resultado(self) -> str:
        """Retorna o tipo de resultado (VP, VN, FP, FN)."""
        if self.verdadeiro_positivo:
            return "VP"
        elif self.verdadeiro_negativo:
            return "VN"
        elif self.falso_positivo:
            return "FP"
        else:
            return "FN"


@dataclass
class MetricasDesempenho:
    """Métricas de desempenho do modelo."""
    
    # Contagens brutas
    total_registros: int = 0
    verdadeiros_positivos: int = 0
    verdadeiros_negativos: int = 0
    falsos_positivos: int = 0
    falsos_negativos: int = 0
    
    # Métricas derivadas (calculadas)
    precisao: float = 0.0
    sensibilidade: float = 0.0  # Recall
    f1_score: float = 0.0
    acuracia: float = 0.0
    especificidade: float = 0.0
    
    # Intervalo de confiança (95%)
    ic_precisao: Tuple[float, float] = (0.0, 0.0)
    ic_sensibilidade: Tuple[float, float] = (0.0, 0.0)
    ic_f1: Tuple[float, float] = (0.0, 0.0)
    
    # Detalhes
    detalhes_por_tipo: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def calcular(self):
        """Calcula todas as métricas derivadas."""
        vp = self.verdadeiros_positivos
        vn = self.verdadeiros_negativos
        fp = self.falsos_positivos
        fn = self.falsos_negativos
        
        # Precisão: VP / (VP + FP)
        if (vp + fp) > 0:
            self.precisao = vp / (vp + fp)
        else:
            self.precisao = 0.0
        
        # Sensibilidade/Recall: VP / (VP + FN)
        if (vp + fn) > 0:
            self.sensibilidade = vp / (vp + fn)
        else:
            self.sensibilidade = 0.0
        
        # F1-Score: 2 * (Precisão * Sensibilidade) / (Precisão + Sensibilidade)
        if (self.precisao + self.sensibilidade) > 0:
            self.f1_score = 2 * (self.precisao * self.sensibilidade) / (self.precisao + self.sensibilidade)
        else:
            self.f1_score = 0.0
        
        # Acurácia: (VP + VN) / Total
        total = vp + vn + fp + fn
        if total > 0:
            self.acuracia = (vp + vn) / total
        else:
            self.acuracia = 0.0
        
        # Especificidade: VN / (VN + FP)
        if (vn + fp) > 0:
            self.especificidade = vn / (vn + fp)
        else:
            self.especificidade = 0.0
        
        # Intervalos de confiança (Wilson score interval, 95%)
        self.ic_precisao = self._calcular_ic_wilson(vp, vp + fp)
        self.ic_sensibilidade = self._calcular_ic_wilson(vp, vp + fn)
        self.ic_f1 = self._calcular_ic_bootstrap()
    
    def _calcular_ic_wilson(self, sucessos: int, total: int, z: float = 1.96) -> Tuple[float, float]:
        """Calcula intervalo de confiança usando Wilson score interval."""
        if total == 0:
            return (0.0, 0.0)
        
        p = sucessos / total
        denominador = 1 + z**2 / total
        centro = (p + z**2 / (2 * total)) / denominador
        
        import math
        margem = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominador
        
        return (max(0, centro - margem), min(1, centro + margem))
    
    def _calcular_ic_bootstrap(self) -> Tuple[float, float]:
        """Calcula IC aproximado para F1-Score."""
        # Aproximação simples baseada nas outras métricas
        margem = 0.05 * (1 - self.f1_score) if self.f1_score > 0 else 0.1
        return (max(0, self.f1_score - margem), min(1, self.f1_score + margem))
    
    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            'total_registros': self.total_registros,
            'verdadeiros_positivos': self.verdadeiros_positivos,
            'verdadeiros_negativos': self.verdadeiros_negativos,
            'falsos_positivos': self.falsos_positivos,
            'falsos_negativos': self.falsos_negativos,
            'precisao': round(self.precisao, 4),
            'sensibilidade': round(self.sensibilidade, 4),
            'f1_score': round(self.f1_score, 4),
            'acuracia': round(self.acuracia, 4),
            'especificidade': round(self.especificidade, 4),
            'ic_precisao': (round(self.ic_precisao[0], 4), round(self.ic_precisao[1], 4)),
            'ic_sensibilidade': (round(self.ic_sensibilidade[0], 4), round(self.ic_sensibilidade[1], 4)),
            'ic_f1': (round(self.ic_f1[0], 4), round(self.ic_f1[1], 4)),
            'timestamp': self.timestamp
        }


class Avaliador:
    """
    Avaliador de desempenho do sistema de detecção.
    
    Compara resultados do modelo com classificações reais.
    """
    
    def __init__(self):
        self.resultados: List[ResultadoClassificacao] = []
        self.metricas: Optional[MetricasDesempenho] = None
    
    def adicionar_resultado(self, resultado: ResultadoClassificacao):
        """Adiciona um resultado de classificação."""
        self.resultados.append(resultado)
    
    def calcular_metricas(self) -> MetricasDesempenho:
        """Calcula métricas com base nos resultados."""
        metricas = MetricasDesempenho()
        
        metricas.total_registros = len(self.resultados)
        
        for r in self.resultados:
            if r.verdadeiro_positivo:
                metricas.verdadeiros_positivos += 1
            elif r.verdadeiro_negativo:
                metricas.verdadeiros_negativos += 1
            elif r.falso_positivo:
                metricas.falsos_positivos += 1
            else:
                metricas.falsos_negativos += 1
        
        # Detalhes por tipo de dado
        detalhes_tipo = {}
        for r in self.resultados:
            for d in r.deteccoes:
                tipo = d.tipo.split('_')[0]
                if tipo not in detalhes_tipo:
                    detalhes_tipo[tipo] = {'detectados': 0, 'exemplos': []}
                detalhes_tipo[tipo]['detectados'] += 1
                if len(detalhes_tipo[tipo]['exemplos']) < 3:
                    detalhes_tipo[tipo]['exemplos'].append(d.valor)
        
        metricas.detalhes_por_tipo = detalhes_tipo
        metricas.calcular()
        
        self.metricas = metricas
        return metricas
    
    def obter_lista_erros(self) -> Dict[str, List[ResultadoClassificacao]]:
        """Retorna listas separadas de FP e FN para análise."""
        erros = {
            'falsos_positivos': [],
            'falsos_negativos': []
        }
        
        for r in self.resultados:
            if r.falso_positivo:
                erros['falsos_positivos'].append(r)
            elif r.falso_negativo:
                erros['falsos_negativos'].append(r)
        
        return erros
    
    def limpar(self):
        """Limpa resultados anteriores."""
        self.resultados = []
        self.metricas = None


class GeradorRelatorio:
    """
    Gera relatórios visuais e textuais dos resultados.
    """
    
    @staticmethod
    def gerar_relatorio_texto(metricas: MetricasDesempenho, 
                              resultados: List[ResultadoClassificacao] = None,
                              detalhado: bool = True) -> str:
        """
        Gera relatório em formato texto.
        
        Args:
            metricas: Métricas calculadas.
            resultados: Lista de resultados (opcional, para detalhes).
            detalhado: Se True, inclui detalhes de cada classificação.
        """
        linhas = []
        
        # Cabeçalho
        linhas.append("=" * 80)
        linhas.append("  RELATÓRIO DE DESEMPENHO - SISTEMA DE IDENTIFICAÇÃO DE DADOS SENSÍVEIS")
        linhas.append("=" * 80)
        linhas.append(f"  Data/Hora: {metricas.timestamp}")
        linhas.append(f"  Total de Registros Analisados: {metricas.total_registros}")
        linhas.append("")
        
        # Matriz de Confusão Visual
        linhas.append("┌" + "─" * 78 + "┐")
        linhas.append("│" + "  MATRIZ DE CONFUSÃO".center(78) + "│")
        linhas.append("├" + "─" * 39 + "┬" + "─" * 38 + "┤")
        linhas.append("│" + "".center(39) + "│" + " PREDIÇÃO DO MODELO".center(38) + "│")
        linhas.append("│" + "".center(39) + "├" + "─" * 18 + "┬" + "─" * 19 + "┤")
        linhas.append("│" + "".center(39) + "│" + " POSITIVO".center(18) + "│" + " NEGATIVO".center(19) + "│")
        linhas.append("├" + "─" * 20 + "┬" + "─" * 18 + "┼" + "─" * 18 + "┼" + "─" * 19 + "┤")
        
        vp = metricas.verdadeiros_positivos
        vn = metricas.verdadeiros_negativos
        fp = metricas.falsos_positivos
        fn = metricas.falsos_negativos
        
        linhas.append("│" + " REAL".center(20) + "│" + " POSITIVO".center(18) + "│" + 
                     f" VP = {vp}".center(18) + "│" + f" FN = {fn}".center(19) + "│")
        linhas.append("│" + "".center(20) + "├" + "─" * 18 + "┼" + "─" * 18 + "┼" + "─" * 19 + "┤")
        linhas.append("│" + "".center(20) + "│" + " NEGATIVO".center(18) + "│" + 
                     f" FP = {fp}".center(18) + "│" + f" VN = {vn}".center(19) + "│")
        linhas.append("└" + "─" * 20 + "┴" + "─" * 18 + "┴" + "─" * 18 + "┴" + "─" * 19 + "┘")
        linhas.append("")
        
        # Legenda
        linhas.append("  Legenda:")
        linhas.append("    VP (Verdadeiro Positivo): Contém dados pessoais E foi detectado ✓")
        linhas.append("    VN (Verdadeiro Negativo): Não contém dados E não foi detectado ✓")
        linhas.append("    FP (Falso Positivo): Não contém dados MAS foi detectado ✗")
        linhas.append("    FN (Falso Negativo): Contém dados MAS não foi detectado ✗")
        linhas.append("")
        
        # Métricas Principais
        linhas.append("┌" + "─" * 78 + "┐")
        linhas.append("│" + "  MÉTRICAS DE DESEMPENHO".center(78) + "│")
        linhas.append("├" + "─" * 78 + "┤")
        
        # Barra visual para precisão
        precisao_bar = GeradorRelatorio._barra_progresso(metricas.precisao, 30)
        linhas.append(f"│  Precisão:     {metricas.precisao*100:6.2f}%  {precisao_bar}  IC 95%: [{metricas.ic_precisao[0]*100:.1f}%, {metricas.ic_precisao[1]*100:.1f}%]  │")
        
        # Barra visual para sensibilidade
        recall_bar = GeradorRelatorio._barra_progresso(metricas.sensibilidade, 30)
        linhas.append(f"│  Sensibilidade:{metricas.sensibilidade*100:6.2f}%  {recall_bar}  IC 95%: [{metricas.ic_sensibilidade[0]*100:.1f}%, {metricas.ic_sensibilidade[1]*100:.1f}%]  │")
        
        # Barra visual para F1
        f1_bar = GeradorRelatorio._barra_progresso(metricas.f1_score, 30)
        linhas.append(f"│  F1-Score:     {metricas.f1_score*100:6.2f}%  {f1_bar}  IC 95%: [{metricas.ic_f1[0]*100:.1f}%, {metricas.ic_f1[1]*100:.1f}%]  │")
        
        linhas.append("├" + "─" * 78 + "┤")
        
        # Métricas adicionais
        acuracia_bar = GeradorRelatorio._barra_progresso(metricas.acuracia, 30)
        linhas.append(f"│  Acurácia:     {metricas.acuracia*100:6.2f}%  {acuracia_bar}".ljust(78) + "│")
        
        espec_bar = GeradorRelatorio._barra_progresso(metricas.especificidade, 30)
        linhas.append(f"│  Especificidade:{metricas.especificidade*100:5.2f}%  {espec_bar}".ljust(78) + "│")
        
        linhas.append("└" + "─" * 78 + "┘")
        linhas.append("")
        
        # Fórmulas utilizadas
        linhas.append("┌" + "─" * 78 + "┐")
        linhas.append("│" + "  FÓRMULAS UTILIZADAS (Conforme Edital)".center(78) + "│")
        linhas.append("├" + "─" * 78 + "┤")
        linhas.append("│  Precisão = VP / (VP + FP) = {} / ({} + {}) = {:.4f}".format(
            vp, vp, fp, metricas.precisao).ljust(77) + "│")
        linhas.append("│  Sensibilidade = VP / (VP + FN) = {} / ({} + {}) = {:.4f}".format(
            vp, vp, fn, metricas.sensibilidade).ljust(77) + "│")
        linhas.append("│  F1-Score = 2 × (Precisão × Sensibilidade) / (Precisão + Sensibilidade)".ljust(77) + "│")
        linhas.append("│           = 2 × ({:.4f} × {:.4f}) / ({:.4f} + {:.4f}) = {:.4f}".format(
            metricas.precisao, metricas.sensibilidade, 
            metricas.precisao, metricas.sensibilidade, metricas.f1_score).ljust(77) + "│")
        linhas.append("└" + "─" * 78 + "┘")
        linhas.append("")
        
        # Detalhes por tipo de dado detectado
        if metricas.detalhes_por_tipo:
            linhas.append("┌" + "─" * 78 + "┐")
            linhas.append("│" + "  DETECÇÕES POR TIPO DE DADO PESSOAL".center(78) + "│")
            linhas.append("├" + "─" * 78 + "┤")
            
            for tipo, info in sorted(metricas.detalhes_por_tipo.items()):
                linha = f"│  {tipo}: {info['detectados']} detecção(ões)"
                if info['exemplos']:
                    exemplos = ', '.join(str(e)[:20] for e in info['exemplos'][:3])
                    linha += f"  Ex: {exemplos}"
                linhas.append(linha.ljust(78) + "│")
            
            linhas.append("└" + "─" * 78 + "┘")
            linhas.append("")
        
        # Detalhes de cada resultado
        if detalhado and resultados:
            linhas.append("")
            linhas.append("=" * 80)
            linhas.append("  DETALHES POR REGISTRO")
            linhas.append("=" * 80)
            
            # Agrupa por tipo de resultado
            por_tipo = {'VP': [], 'VN': [], 'FP': [], 'FN': []}
            for r in resultados:
                por_tipo[r.tipo_resultado].append(r)
            
            for tipo_nome, lista in [('FN', por_tipo['FN']), ('FP', por_tipo['FP']), 
                                     ('VP', por_tipo['VP']), ('VN', por_tipo['VN'])]:
                if not lista:
                    continue
                
                icone = "⚠️" if tipo_nome in ['FN', 'FP'] else "✓"
                linhas.append("")
                linhas.append(f"  [{tipo_nome}] - {len(lista)} registro(s) {icone}")
                linhas.append("  " + "-" * 76)
                
                for r in lista[:10]:  # Limita a 10 por tipo
                    texto_resumo = r.texto[:100].replace('\n', ' ') + ('...' if len(r.texto) > 100 else '')
                    linhas.append(f"  ID: {r.id}")
                    linhas.append(f"  Texto: {texto_resumo}")
                    
                    if r.deteccoes:
                        deteccoes_str = []
                        for d in r.deteccoes[:5]:
                            deteccoes_str.append(f"{d.tipo}='{d.valor}' (conf:{d.confianca:.2f}, pos:{d.posicao_inicio})")
                        linhas.append(f"  Detecções: {'; '.join(deteccoes_str)}")
                    else:
                        linhas.append("  Detecções: Nenhuma")
                    
                    linhas.append("")
                
                if len(lista) > 10:
                    linhas.append(f"  ... e mais {len(lista) - 10} registro(s)")
        
        linhas.append("")
        linhas.append("=" * 80)
        linhas.append("  FIM DO RELATÓRIO")
        linhas.append("=" * 80)
        
        return '\n'.join(linhas)
    
    @staticmethod
    def _barra_progresso(valor: float, tamanho: int = 20) -> str:
        """Gera uma barra de progresso visual."""
        preenchido = int(valor * tamanho)
        vazio = tamanho - preenchido
        return "[" + "█" * preenchido + "░" * vazio + "]"
    
    @staticmethod
    def gerar_csv_resultados(resultados: List[ResultadoClassificacao], 
                             caminho: str = None) -> str:
        """
        Gera CSV com resultados detalhados.
        
        Args:
            resultados: Lista de resultados.
            caminho: Caminho para salvar (opcional).
        
        Returns:
            String CSV.
        """
        linhas = ["ID,Texto_Resumo,Real,Predito,Tipo_Resultado,Num_Deteccoes,Deteccoes,Confianca_Media"]
        
        for r in resultados:
            texto_resumo = r.texto[:50].replace('"', "'").replace('\n', ' ')
            deteccoes_str = "|".join(f"{d.tipo}:{d.valor}" for d in r.deteccoes)
            
            linha = f'"{r.id}","{texto_resumo}",{int(r.classificacao_real)},{int(r.classificacao_predita)},{r.tipo_resultado},{len(r.deteccoes)},"{deteccoes_str}",{r.confianca_media:.3f}'
            linhas.append(linha)
        
        csv_str = '\n'.join(linhas)
        
        if caminho:
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(csv_str)
        
        return csv_str
    
    @staticmethod
    def gerar_json_metricas(metricas: MetricasDesempenho, caminho: str = None) -> str:
        """
        Gera JSON com métricas.
        
        Args:
            metricas: Métricas calculadas.
            caminho: Caminho para salvar (opcional).
        
        Returns:
            String JSON.
        """
        json_str = json.dumps(metricas.to_dict(), indent=2, ensure_ascii=False)
        
        if caminho:
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str


if __name__ == "__main__":
    # Teste do sistema de métricas
    avaliador = Avaliador()
    
    # Simula alguns resultados
    from detectores import DeteccaoEncontrada
    
    # VP - detectou corretamente
    avaliador.adicionar_resultado(ResultadoClassificacao(
        id=1,
        texto="Meu CPF é 123.456.789-09",
        classificacao_real=True,
        classificacao_predita=True,
        deteccoes=[DeteccaoEncontrada(tipo="CPF", valor="123.456.789-09", 
                                      posicao_inicio=10, posicao_fim=24, 
                                      confianca=0.95)]
    ))
    
    # VN - não detectou corretamente
    avaliador.adicionar_resultado(ResultadoClassificacao(
        id=2,
        texto="Solicito informações sobre o processo.",
        classificacao_real=False,
        classificacao_predita=False,
        deteccoes=[]
    ))
    
    # FP - detectou errado
    avaliador.adicionar_resultado(ResultadoClassificacao(
        id=3,
        texto="O protocolo é 12345678",
        classificacao_real=False,
        classificacao_predita=True,
        deteccoes=[DeteccaoEncontrada(tipo="RG", valor="12345678", 
                                      posicao_inicio=14, posicao_fim=22,
                                      confianca=0.75)]
    ))
    
    metricas = avaliador.calcular_metricas()
    relatorio = GeradorRelatorio.gerar_relatorio_texto(metricas, avaliador.resultados)
    print(relatorio)
