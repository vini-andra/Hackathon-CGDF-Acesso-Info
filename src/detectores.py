"""
Módulo de Detectores de Dados Pessoais Sensíveis
Sistema de Identificação de Dados Sensíveis - Hackathon Participa DF

Este módulo contém as classes de detecção para cada tipo de dado pessoal,
conforme definido no edital: Nome, CPF, RG, Telefone e E-mail.

Autor: Participante do Hackathon
Data: Janeiro/2026
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Set


@dataclass
class DeteccaoEncontrada:
    """Representa um dado pessoal detectado no texto."""
    tipo: str                   # Tipo do dado (CPF, RG, NOME, etc.)
    valor: str                  # Valor encontrado
    posicao_inicio: int         # Posição inicial no texto
    posicao_fim: int            # Posição final no texto
    confianca: float            # Nível de confiança (0.0 a 1.0)
    contexto: str = ""          # Trecho do texto ao redor
    validado: bool = False      # Se passou por validação adicional
    metodo_deteccao: str = ""   # Método usado para detectar


class DetectorBase(ABC):
    """Classe base abstrata para todos os detectores."""
    
    def __init__(self, nome_tipo: str, sensibilidade: float = 0.8):
        self.nome_tipo = nome_tipo
        self.sensibilidade = sensibilidade  # Ajusta limiar de confiança
    
    @abstractmethod
    def detectar(self, texto: str) -> List[DeteccaoEncontrada]:
        """Método principal de detecção - deve ser implementado."""
        pass
    
    def extrair_contexto(self, texto: str, inicio: int, fim: int, janela: int = 50) -> str:
        """Extrai o contexto ao redor de uma detecção."""
        ctx_inicio = max(0, inicio - janela)
        ctx_fim = min(len(texto), fim + janela)
        return texto[ctx_inicio:ctx_fim]
    
    def normalizar_texto(self, texto: str) -> str:
        """Normaliza o texto removendo acentos problemáticos."""
        return texto


class DetectorCPF(DetectorBase):
    """
    Detector de CPF (Cadastro de Pessoa Física).
    
    Formato padrão: XXX.XXX.XXX-XX
    Variações aceitas: com/sem pontuação, espaços
    """
    
    def __init__(self, sensibilidade: float = 0.8):
        super().__init__("CPF", sensibilidade)
        
        # Padrões de CPF (do mais específico ao mais genérico)
        self.padroes = [
            # Formato padrão com pontuação
            (r'\b(\d{3})[.\s]?(\d{3})[.\s]?(\d{3})[-.\s]?(\d{2})\b', 0.95),
            # Apenas 11 dígitos seguidos
            (r'\b(\d{11})\b', 0.70),
        ]
        
        # Contextos que aumentam confiança
        self.contextos_positivos = [
            r'cpf[\s:]*', r'c\.?p\.?f\.?[\s:]*', r'cadastro[\s\w]*pessoa[\s\w]*física',
            r'documento[\s:]*', r'inscri[çc][aã]o[\s:]*'
        ]
    
    def detectar(self, texto: str) -> List[DeteccaoEncontrada]:
        deteccoes = []
        texto_lower = texto.lower()
        
        for padrao, confianca_base in self.padroes:
            for match in re.finditer(padrao, texto, re.IGNORECASE):
                valor_bruto = match.group(0)
                
                # Extrai apenas os dígitos
                digitos = re.sub(r'\D', '', valor_bruto)
                
                # Ignora se não tem exatamente 11 dígitos
                if len(digitos) != 11:
                    continue
                
                # Ignora sequências óbvias
                if self._eh_sequencia_invalida(digitos):
                    continue
                
                # Calcula confiança ajustada
                confianca = confianca_base
                
                # Aumenta confiança se há contexto
                pos_inicio = match.start()
                trecho_antes = texto_lower[max(0, pos_inicio-30):pos_inicio]
                
                for ctx in self.contextos_positivos:
                    if re.search(ctx, trecho_antes):
                        confianca = min(1.0, confianca + 0.15)
                        break
                
                # Valida dígitos verificadores
                if self._validar_cpf(digitos):
                    confianca = min(1.0, confianca + 0.10)
                    validado = True
                else:
                    confianca = max(0.3, confianca - 0.20)
                    validado = False
                
                if confianca >= self.sensibilidade:
                    deteccoes.append(DeteccaoEncontrada(
                        tipo="CPF",
                        valor=valor_bruto,
                        posicao_inicio=match.start(),
                        posicao_fim=match.end(),
                        confianca=round(confianca, 3),
                        contexto=self.extrair_contexto(texto, match.start(), match.end()),
                        validado=validado,
                        metodo_deteccao="regex+validacao"
                    ))
        
        return self._remover_duplicatas(deteccoes)
    
    def _eh_sequencia_invalida(self, digitos: str) -> bool:
        """Verifica se é uma sequência inválida conhecida."""
        invalidos = [
            '00000000000', '11111111111', '22222222222', '33333333333',
            '44444444444', '55555555555', '66666666666', '77777777777',
            '88888888888', '99999999999', '01234567890'
        ]
        return digitos in invalidos
    
    def _validar_cpf(self, cpf: str) -> bool:
        """Valida CPF usando algoritmo de dígitos verificadores."""
        if len(cpf) != 11:
            return False
        
        # Calcula primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = (soma * 10) % 11
        digito1 = resto if resto < 10 else 0
        
        if digito1 != int(cpf[9]):
            return False
        
        # Calcula segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = (soma * 10) % 11
        digito2 = resto if resto < 10 else 0
        
        return digito2 == int(cpf[10])
    
    def _remover_duplicatas(self, deteccoes: List[DeteccaoEncontrada]) -> List[DeteccaoEncontrada]:
        """Remove detecções sobrepostas, mantendo a de maior confiança."""
        if not deteccoes:
            return []
        
        deteccoes.sort(key=lambda x: (-x.confianca, x.posicao_inicio))
        resultado = []
        posicoes_usadas = set()
        
        for d in deteccoes:
            pos_range = range(d.posicao_inicio, d.posicao_fim)
            if not any(p in posicoes_usadas for p in pos_range):
                resultado.append(d)
                posicoes_usadas.update(pos_range)
        
        return resultado


class DetectorRG(DetectorBase):
    """
    Detector de RG (Registro Geral).
    
    Formatos variam por estado, mas geralmente 7-9 dígitos.
    """
    
    def __init__(self, sensibilidade: float = 0.75):
        super().__init__("RG", sensibilidade)
        
        self.padroes = [
            # Formato com pontuação (ex: 12.345.678-9)
            (r'\b(\d{1,2})[.\s]?(\d{3})[.\s]?(\d{3})[-.\s]?([0-9xX])\b', 0.85),
            # Formato SSP/UF (ex: 1234567 SSP/DF)
            (r'\b(\d{7,9})[\s/-]*(ssp|sds|detran|pc|iml|igp)[/\s]*([a-z]{2})\b', 0.95),
            # 7-9 dígitos com contexto
            (r'\b(\d{7,9})\b', 0.50),
            # RG com dígitos espaçados (ex: 1 0 6 2 7 8 3 5 6)
            (r'\b\d[\s\.]\d[\s\.]\d[\s\.]\d[\s\.]\d[\s\.]\d[\s\.]\d(?:[\s\.]\d){0,2}\b', 0.90),
        ]
        
        self.contextos_positivos = [
            r'r\.?g\.?[\s:]*', r'registro[\s\w]*geral', r'identidade[\s:]*',
            r'documento[\s:]*', r'carteira[\s:]*', r'cédula[\s:]*'
        ]
        
        # Contextos que reduzem confiança (falsos positivos comuns)
        self.contextos_negativos = [
            r'processo', r'sei[\s:]*', r'protocolo', r'n[úu]mero[\s\w]*pedido',
            r'c[óo]digo', r'refer[êe]ncia', r'ano', r'data', r'cep'
        ]
    
    def detectar(self, texto: str) -> List[DeteccaoEncontrada]:
        deteccoes = []
        texto_lower = texto.lower()
        
        for padrao, confianca_base in self.padroes:
            for match in re.finditer(padrao, texto, re.IGNORECASE):
                valor_bruto = match.group(0)
                digitos = re.sub(r'\D', '', valor_bruto)
                
                # RG deve ter entre 7 e 9 dígitos
                if len(digitos) < 7 or len(digitos) > 9:
                    continue
                
                confianca = confianca_base
                pos_inicio = match.start()
                
                # Verifica contexto anterior
                trecho_antes = texto_lower[max(0, pos_inicio-40):pos_inicio]
                trecho_depois = texto_lower[match.end():min(len(texto), match.end()+40)]
                trecho_contexto = trecho_antes + " " + trecho_depois
                
                # Aumenta com contextos positivos
                for ctx in self.contextos_positivos:
                    if re.search(ctx, trecho_contexto):
                        confianca = min(1.0, confianca + 0.20)
                        break
                
                # Reduz com contextos negativos
                for ctx in self.contextos_negativos:
                    if re.search(ctx, trecho_contexto):
                        confianca = max(0.2, confianca - 0.25)
                        break
                
                if confianca >= self.sensibilidade:
                    deteccoes.append(DeteccaoEncontrada(
                        tipo="RG",
                        valor=valor_bruto,
                        posicao_inicio=match.start(),
                        posicao_fim=match.end(),
                        confianca=round(confianca, 3),
                        contexto=self.extrair_contexto(texto, match.start(), match.end()),
                        validado=False,
                        metodo_deteccao="regex+contexto"
                    ))
        
        return self._remover_duplicatas(deteccoes)
    
    def _remover_duplicatas(self, deteccoes: List[DeteccaoEncontrada]) -> List[DeteccaoEncontrada]:
        if not deteccoes:
            return []
        
        deteccoes.sort(key=lambda x: (-x.confianca, x.posicao_inicio))
        resultado = []
        posicoes_usadas = set()
        
        for d in deteccoes:
            pos_range = range(d.posicao_inicio, d.posicao_fim)
            if not any(p in posicoes_usadas for p in pos_range):
                resultado.append(d)
                posicoes_usadas.update(pos_range)
        
        return resultado


class DetectorTelefone(DetectorBase):
    """
    Detector de Telefone brasileiro.
    
    Formatos: (XX) XXXXX-XXXX, (XX) XXXX-XXXX, +55...
    """
    
    def __init__(self, sensibilidade: float = 0.75):
        super().__init__("TELEFONE", sensibilidade)
        
        self.padroes = [
            # Formato com DDD e código país: +55 (61) 99999-9999
            (r'\+55[\s.-]?\(?(\d{2})\)?[\s.-]?(\d{4,5})[\s.-]?(\d{4})\b', 0.98),
            # Formato com DDD: (61) 99999-9999 ou 61 99999-9999
            (r'\(?(\d{2})\)?[\s.-]?(\d{4,5})[\s.-]?(\d{4})\b', 0.85),
            # Apenas número: 99999-9999 ou 9999-9999
            (r'\b(\d{4,5})[\s.-](\d{4})\b', 0.65),
        ]
        
        self.contextos_positivos = [
            r'tel[efone\.]*[\s:]*', r'telefone[\s:]*', r'celular[\s:]*',
            r'contato[\s:]*', r'fone[\s:]*', r'whatsapp[\s:]*', r'zap[\s:]*',
            r'ligar[\s:]*', r'ligue[\s:]*'
        ]
        
        self.contextos_negativos = [
            r'processo', r'sei[\s:]*', r'protocolo', r'ano[\s:]*',
            r'c[óo]digo', r'cpf', r'cnpj', r'cep'
        ]
        
        # DDDs válidos do Brasil
        self.ddds_validos = {
            11, 12, 13, 14, 15, 16, 17, 18, 19,  # SP
            21, 22, 24,  # RJ
            27, 28,  # ES
            31, 32, 33, 34, 35, 37, 38,  # MG
            41, 42, 43, 44, 45, 46,  # PR
            47, 48, 49,  # SC
            51, 53, 54, 55,  # RS
            61,  # DF
            62, 64,  # GO
            63,  # TO
            65, 66,  # MT
            67,  # MS
            68,  # AC
            69,  # RO
            71, 73, 74, 75, 77,  # BA
            79,  # SE
            81, 82, 83, 84, 85, 86, 87, 88, 89,  # PE, AL, PB, RN, CE, PI
            91, 92, 93, 94, 95, 96, 97, 98, 99  # PA, AM, RR, AP, MA
        }
    
    def detectar(self, texto: str) -> List[DeteccaoEncontrada]:
        deteccoes = []
        texto_lower = texto.lower()
        
        for padrao, confianca_base in self.padroes:
            for match in re.finditer(padrao, texto, re.IGNORECASE):
                valor_bruto = match.group(0)
                digitos = re.sub(r'\D', '', valor_bruto)
                
                # Telefone deve ter 8, 9, 10 ou 11 dígitos
                if len(digitos) < 8 or len(digitos) > 13:
                    continue
                
                # Ignora sequências inválidas (repetições, padrões de CPF)
                if self._eh_sequencia_invalida(digitos):
                    continue
                
                confianca = confianca_base
                pos_inicio = match.start()
                
                # Verifica DDD se presente
                if len(digitos) >= 10:
                    ddd = int(digitos[:2])
                    if ddd in self.ddds_validos:
                        confianca = min(1.0, confianca + 0.10)
                    else:
                        confianca = max(0.3, confianca - 0.20)
                
                # Verifica contexto
                trecho_antes = texto_lower[max(0, pos_inicio-30):pos_inicio]
                trecho_depois = texto_lower[match.end():min(len(texto), match.end()+30)]
                
                for ctx in self.contextos_positivos:
                    if re.search(ctx, trecho_antes):
                        confianca = min(1.0, confianca + 0.15)
                        break
                
                for ctx in self.contextos_negativos:
                    if re.search(ctx, trecho_antes + trecho_depois):
                        confianca = max(0.2, confianca - 0.30)
                        break
                
                if confianca >= self.sensibilidade:
                    deteccoes.append(DeteccaoEncontrada(
                        tipo="TELEFONE",
                        valor=valor_bruto,
                        posicao_inicio=match.start(),
                        posicao_fim=match.end(),
                        confianca=round(confianca, 3),
                        contexto=self.extrair_contexto(texto, match.start(), match.end()),
                        validado=len(digitos) >= 10 and int(digitos[:2]) in self.ddds_validos,
                        metodo_deteccao="regex+ddd"
                    ))
        
        return self._remover_duplicatas(deteccoes)
    
    def _eh_sequencia_invalida(self, digitos: str) -> bool:
        """Verifica se é uma sequência inválida (não é telefone real)."""
        # Sequências repetidas
        if len(set(digitos)) == 1:
            return True
        
        # Padrões que provavelmente são CPF (11 dígitos que passam na validação)
        if len(digitos) == 11:
            # Verifica se é CPF válido
            try:
                soma = sum(int(digitos[i]) * (10 - i) for i in range(9))
                resto = (soma * 10) % 11
                digito1 = resto if resto < 10 else 0
                
                if digito1 == int(digitos[9]):
                    soma = sum(int(digitos[i]) * (11 - i) for i in range(10))
                    resto = (soma * 10) % 11
                    digito2 = resto if resto < 10 else 0
                    
                    if digito2 == int(digitos[10]):
                        return True  # É um CPF válido, não telefone
            except (ValueError, IndexError):
                pass
        
        return False
    
    def _remover_duplicatas(self, deteccoes: List[DeteccaoEncontrada]) -> List[DeteccaoEncontrada]:
        if not deteccoes:
            return []
        
        deteccoes.sort(key=lambda x: (-x.confianca, x.posicao_inicio))
        resultado = []
        posicoes_usadas = set()
        
        for d in deteccoes:
            pos_range = range(d.posicao_inicio, d.posicao_fim)
            if not any(p in posicoes_usadas for p in pos_range):
                resultado.append(d)
                posicoes_usadas.update(pos_range)
        
        return resultado


class DetectorEmail(DetectorBase):
    """
    Detector de E-mail.
    
    Padrão RFC 5322 simplificado para uso prático.
    """
    
    def __init__(self, sensibilidade: float = 0.85):
        super().__init__("EMAIL", sensibilidade)
        
        # Padrão de e-mail robusto
        self.padrao = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        
        self.contextos_positivos = [
            r'e-?mail[\s:]*', r'email[\s:]*', r'correio[\s\w]*eletr[ôo]nico',
            r'contato[\s:]*', r'enviar[\s\w]*para', r'escreva[\s\w]*para'
        ]
        
        # Domínios conhecidos para validação
        self.dominios_comuns = {
            'gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com', 'yahoo.com.br',
            'live.com', 'msn.com', 'icloud.com', 'uol.com.br', 'bol.com.br',
            'terra.com.br', 'globo.com', 'ig.com.br', 'oi.com.br', 'r7.com'
        }
        
        # Domínios governamentais
        self.dominios_gov = {'.gov.br', '.leg.br', '.jus.br', '.mil.br', '.df.gov.br'}
    
    def detectar(self, texto: str) -> List[DeteccaoEncontrada]:
        deteccoes = []
        texto_lower = texto.lower()
        
        for match in re.finditer(self.padrao, texto, re.IGNORECASE):
            valor = match.group(0).lower()
            
            # Extrai domínio
            dominio = valor.split('@')[1] if '@' in valor else ''
            
            # Define confiança base
            confianca = 0.90
            
            # Ajusta por tipo de domínio
            if dominio in self.dominios_comuns:
                confianca = 0.98
            elif any(valor.endswith(gov) for gov in self.dominios_gov):
                confianca = 0.95
            elif len(dominio.split('.')) < 2:
                confianca = 0.50  # Domínio suspeito
            
            # Verifica contexto
            pos_inicio = match.start()
            trecho_antes = texto_lower[max(0, pos_inicio-30):pos_inicio]
            
            for ctx in self.contextos_positivos:
                if re.search(ctx, trecho_antes):
                    confianca = min(1.0, confianca + 0.05)
                    break
            
            if confianca >= self.sensibilidade:
                deteccoes.append(DeteccaoEncontrada(
                    tipo="EMAIL",
                    valor=match.group(0),
                    posicao_inicio=match.start(),
                    posicao_fim=match.end(),
                    confianca=round(confianca, 3),
                    contexto=self.extrair_contexto(texto, match.start(), match.end()),
                    validado=dominio in self.dominios_comuns,
                    metodo_deteccao="regex+dominio"
                ))
        
        return deteccoes


class DetectorNome(DetectorBase):
    """
    Detector de Nomes de Pessoas.
    
    Usa combinação de:
    - Padrões de capitalização
    - Lista de nomes brasileiros comuns
    - Análise de contexto
    """
    
    def __init__(self, sensibilidade: float = 0.70):
        super().__init__("NOME", sensibilidade)
        
        # Nomes próprios brasileiros mais comuns (expandível)
        self.nomes_proprios = self._carregar_nomes_base()
        
        # Sobrenomes brasileiros comuns
        self.sobrenomes = self._carregar_sobrenomes_base()
        
        # Conectivos de nomes
        self.conectivos = {'de', 'da', 'do', 'das', 'dos', 'e', 'di', 'del'}
        
        # Padrão para nomes próprios - captura Nome Sobrenome com ou sem conectivos
        self.padrao_nome = r'\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+(?:de|da|do|dos|das|e|di|del|[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+))+)\b'
        
        # Contextos que indicam nomes
        self.contextos_positivos = [
            r'nome[\s:]*', r'chamad[oa][\s:]*', r'sr\.?a?[\s:]*', r'senhor[a]?[\s:]*',
            r'requerente[\s:]*', r'solicitante[\s:]*', r'autor[\s:]*', r'cidad[ãa]o[\s:]*',
            r'servidor[\s:]*', r'funcion[áa]rio[\s:]*', r'benefici[áa]rio[\s:]*'
        ]
        
        # Palavras que NÃO são nomes (falsos positivos comuns)
        self.nao_nomes = {
            'secretaria', 'departamento', 'coordenação', 'diretoria', 'gerência',
            'subsecretaria', 'superintendência', 'administração', 'governo',
            'ministério', 'tribunal', 'justiça', 'polícia', 'hospital',
            'universidade', 'faculdade', 'instituto', 'fundação', 'associação',
            'empresa', 'companhia', 'sociedade', 'organização', 'programa',
            'projeto', 'sistema', 'plataforma', 'serviço', 'unidade',
            'estado', 'distrito', 'federal', 'nacional', 'regional',
            'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
            'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
            'segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo'
        }
    
    def _carregar_nomes_base(self) -> Set[str]:
        """Carrega lista de nomes do arquivo JSON."""
        import json
        import os
        
        nomes = set()
        arquivo_json = os.path.join(os.path.dirname(__file__), '..', 'dados', 'nomes_proprios.json')
        
        if os.path.exists(arquivo_json):
            try:
                with open(arquivo_json, 'r', encoding='utf-8') as f:
                    nomes = set(json.load(f))
            except (json.JSONDecodeError, IOError):
                pass
        
        return nomes
    
    def _carregar_sobrenomes_base(self) -> Set[str]:
        """Carrega lista de sobrenomes do arquivo JSON."""
        import json
        import os
        
        sobrenomes = set()
        arquivo_json = os.path.join(os.path.dirname(__file__), '..', 'dados', 'sobrenomes.json')
        
        if os.path.exists(arquivo_json):
            try:
                with open(arquivo_json, 'r', encoding='utf-8') as f:
                    sobrenomes = set(json.load(f))
            except (json.JSONDecodeError, IOError):
                pass
        
        return sobrenomes
    
    def detectar(self, texto: str) -> List[DeteccaoEncontrada]:
        deteccoes = []
        texto_lower = texto.lower()
        
        for match in re.finditer(self.padrao_nome, texto):
            nome_candidato = match.group(0).strip()
            palavras = nome_candidato.split()
            
            # Precisa ter pelo menos 2 palavras (nome + sobrenome)
            if len(palavras) < 2:
                continue
            
            # Filtra conectivos
            palavras_significativas = [
                p for p in palavras if p.lower() not in self.conectivos
            ]
            
            if len(palavras_significativas) < 2:
                continue
            
            # Verifica se primeira palavra é um nome conhecido
            primeiro_nome = palavras_significativas[0].lower()
            
            # Verifica se contém palavras que não são nomes
            tem_nao_nome = any(
                p.lower() in self.nao_nomes for p in palavras_significativas
            )
            if tem_nao_nome:
                continue
            
            # Calcula confiança
            confianca = 0.50
            
            # Normaliza para comparação (remove acentos)
            primeiro_nome_norm = self._normalizar_texto(primeiro_nome)
            
            # Aumenta se primeiro nome é conhecido
            if primeiro_nome_norm in self.nomes_proprios or primeiro_nome in self.nomes_proprios:
                confianca += 0.25
            
            # Aumenta se último nome é sobrenome conhecido
            ultimo_nome = palavras_significativas[-1].lower()
            ultimo_nome_norm = self._normalizar_texto(ultimo_nome)
            if ultimo_nome_norm in self.sobrenomes or ultimo_nome in self.sobrenomes:
                confianca += 0.20
            
            # Verifica contexto
            pos_inicio = match.start()
            trecho_antes = texto_lower[max(0, pos_inicio-30):pos_inicio]
            
            for ctx in self.contextos_positivos:
                if re.search(ctx, trecho_antes):
                    confianca = min(1.0, confianca + 0.15)
                    break
            
            # Penaliza nomes muito curtos ou muito longos
            if len(nome_candidato) < 8:
                confianca -= 0.10
            if len(palavras_significativas) > 5:
                confianca -= 0.15
            
            if confianca >= self.sensibilidade:
                deteccoes.append(DeteccaoEncontrada(
                    tipo="NOME",
                    valor=nome_candidato,
                    posicao_inicio=match.start(),
                    posicao_fim=match.end(),
                    confianca=round(confianca, 3),
                    contexto=self.extrair_contexto(texto, match.start(), match.end()),
                    validado=primeiro_nome in self.nomes_proprios,
                    metodo_deteccao="regex+dicionario"
                ))
        
        return self._remover_duplicatas(deteccoes)
    
    def _normalizar_texto(self, texto: str) -> str:
        """Remove acentos para normalização na comparação."""
        import unicodedata
        # Normaliza para forma NFD (decomposta) e remove marcas de acento
        texto_norm = unicodedata.normalize('NFD', texto)
        texto_sem_acento = ''.join(c for c in texto_norm if unicodedata.category(c) != 'Mn')
        return texto_sem_acento.lower()
    
    def _remover_duplicatas(self, deteccoes: List[DeteccaoEncontrada]) -> List[DeteccaoEncontrada]:
        if not deteccoes:
            return []
        
        deteccoes.sort(key=lambda x: (-x.confianca, x.posicao_inicio))
        resultado = []
        posicoes_usadas = set()
        
        for d in deteccoes:
            pos_range = range(d.posicao_inicio, d.posicao_fim)
            if not any(p in posicoes_usadas for p in pos_range):
                resultado.append(d)
                posicoes_usadas.update(pos_range)
        
        return resultado
    
    def adicionar_nomes(self, nomes: List[str]):
        """Adiciona novos nomes à lista de nomes conhecidos."""
        self.nomes_proprios.update(n.lower() for n in nomes)
    
    def adicionar_sobrenomes(self, sobrenomes: List[str]):
        """Adiciona novos sobrenomes à lista."""
        self.sobrenomes.update(s.lower() for s in sobrenomes)


class DetectorEndereco(DetectorBase):
    """
    Detector de Endereços.
    
    Identifica CEPs e padrões de endereço brasileiro.
    """
    
    def __init__(self, sensibilidade: float = 0.80):
        super().__init__("ENDERECO", sensibilidade)
        
        self.padroes = [
            # CEP: 70000-000 ou 70000000
            (r'\b(\d{5})[-.\s]?(\d{3})\b', 'CEP', 0.85),
            # Endereço completo
            (r'\b(rua|av\.?|avenida|alameda|travessa|quadra|qd\.?|conjunto|conj\.?|bloco|bl\.?|lote|lt\.?)[\s,]+[^,\n]{5,50}', 'LOGRADOURO', 0.75),
        ]
        
        self.contextos_positivos = [
            r'endere[çc]o[\s:]*', r'resid[êe]ncia[\s:]*', r'mora[\s:]*',
            r'cep[\s:]*', r'localiza[çc][ãa]o[\s:]*'
        ]
    
    def detectar(self, texto: str) -> List[DeteccaoEncontrada]:
        deteccoes = []
        texto_lower = texto.lower()
        
        for padrao, subtipo, confianca_base in self.padroes:
            for match in re.finditer(padrao, texto, re.IGNORECASE):
                valor = match.group(0)
                confianca = confianca_base
                
                # Verifica contexto
                pos_inicio = match.start()
                trecho_antes = texto_lower[max(0, pos_inicio-30):pos_inicio]
                
                for ctx in self.contextos_positivos:
                    if re.search(ctx, trecho_antes):
                        confianca = min(1.0, confianca + 0.10)
                        break
                
                # Para CEP, valida faixa
                if subtipo == 'CEP':
                    digitos = re.sub(r'\D', '', valor)
                    cep_int = int(digitos) if digitos else 0
                    # CEPs válidos do Brasil
                    if not (1000000 <= cep_int <= 99999999):
                        confianca = max(0.3, confianca - 0.30)
                
                if confianca >= self.sensibilidade:
                    deteccoes.append(DeteccaoEncontrada(
                        tipo=f"ENDERECO_{subtipo}",
                        valor=valor,
                        posicao_inicio=match.start(),
                        posicao_fim=match.end(),
                        confianca=round(confianca, 3),
                        contexto=self.extrair_contexto(texto, match.start(), match.end()),
                        validado=subtipo == 'CEP',
                        metodo_deteccao="regex"
                    ))
        
        return deteccoes


class DetectorProcesso(DetectorBase):
    """
    Detector de Números de Processo, Protocolo e Ocorrências.
    
    Identifica:
    - Processos SEI: 00000-00000000/2024-00
    - Protocolos: 0000000000/2024
    - Ocorrências policiais: 16+ dígitos
    - CDAs e números administrativos
    """
    
    def __init__(self, sensibilidade: float = 0.70):
        super().__init__("PROCESSO", sensibilidade)
        
        self.padroes = [
            # Processo SEI completo: 00000-00000000/2024-00
            (r'\b(\d{5})-?(\d{8})/(\d{4})-(\d{2})\b', 'SEI', 0.95),
            
            # Processo SEI alternativo: 0000000000/2024-00
            (r'\b(\d{10,13})/(\d{4})-(\d{2})\b', 'SEI', 0.90),
            
            # Protocolo simples: 0000000000/2024
            (r'\b(\d{8,13})/(\d{4})\b', 'PROTOCOLO', 0.85),
            
            # Ocorrência policial (PMDF, PCDF): 16 dígitos
            (r'\b(\d{16})\b', 'OCORRENCIA', 0.80),
            
            # CDA ou número administrativo: 10 dígitos isolados
            (r'\b(\d{10})\b', 'CDA', 0.60),
        ]
        
        self.contextos_positivos = [
            r'processo[s]?[\s:]*n?[úu]?m?e?r?o?[\s:]*',
            r'protocolo[\s:]*',
            r'sei[\s:]*',
            r'ocorr[êe]ncia[\s:]*',
            r'n[úu]mero[\s:]*',
            r'cda[\s:]*',
            r'solicito[\s\w]*processo',
            r'acesso[\s\w]*processo',
        ]
        
        # Contextos que reduzem confiança (falsos positivos)
        self.contextos_negativos = [
            r'cpf', r'cnpj', r'telefone', r'fone', r'cep',
            r'ano[\s:]*', r'data[\s:]*'
        ]
    
    def detectar(self, texto: str) -> List[DeteccaoEncontrada]:
        deteccoes = []
        texto_lower = texto.lower()
        
        for padrao, subtipo, confianca_base in self.padroes:
            for match in re.finditer(padrao, texto, re.IGNORECASE):
                valor = match.group(0)
                confianca = confianca_base
                
                # Verifica contexto positivo
                pos_inicio = match.start()
                trecho_antes = texto_lower[max(0, pos_inicio-50):pos_inicio]
                trecho_depois = texto_lower[match.end():min(len(texto), match.end()+30)]
                trecho_contexto = trecho_antes + " " + trecho_depois
                
                for ctx in self.contextos_positivos:
                    if re.search(ctx, trecho_contexto):
                        confianca = min(1.0, confianca + 0.15)
                        break
                
                # Verifica contexto negativo
                for ctx in self.contextos_negativos:
                    if re.search(ctx, trecho_contexto):
                        confianca = max(0.2, confianca - 0.30)
                        break
                
                # Para CDA (10 dígitos), exige contexto mais forte
                if subtipo == 'CDA' and confianca < 0.75:
                    # Só aceita se tiver contexto explícito
                    tem_contexto = any(
                        re.search(ctx, trecho_contexto) 
                        for ctx in self.contextos_positivos
                    )
                    if not tem_contexto:
                        continue
                
                if confianca >= self.sensibilidade:
                    deteccoes.append(DeteccaoEncontrada(
                        tipo=f"PROCESSO_{subtipo}",
                        valor=valor,
                        posicao_inicio=match.start(),
                        posicao_fim=match.end(),
                        confianca=round(confianca, 3),
                        contexto=self.extrair_contexto(texto, match.start(), match.end()),
                        validado=subtipo in ['SEI', 'PROTOCOLO'],
                        metodo_deteccao="regex+contexto"
                    ))
        
        return self._remover_duplicatas(deteccoes)
    
    def _remover_duplicatas(self, deteccoes: List[DeteccaoEncontrada]) -> List[DeteccaoEncontrada]:
        if not deteccoes:
            return []
        
        deteccoes.sort(key=lambda x: (-x.confianca, x.posicao_inicio))
        resultado = []
        posicoes_usadas = set()
        
        for d in deteccoes:
            pos_range = range(d.posicao_inicio, d.posicao_fim)
            if not any(p in posicoes_usadas for p in pos_range):
                resultado.append(d)
                posicoes_usadas.update(pos_range)
        
        return resultado


class DetectorContexto(DetectorBase):
    """
    Detector baseado em Contexto e Palavras-chave.
    
    Identifica situações onde o texto em si é sensível, mesmo sem
    conter um dado estruturado explícito (ex: revelação de saúde,
    vulnerabilidade social, dados de menores).
    """
    
    def __init__(self, sensibilidade: float = 0.65):
        super().__init__("CONTEXTO", sensibilidade)
        
        self.padroes = [
            # Saúde e condições médicas
            (r'\b(laudo|atestada?o|exame|diagn[óo]stico|tratamento|cirurgia|interna[çc][ãa]o)\b', 'SAUDE', 0.85),
            (r'\b(c[âa]ncer|tumor|doen[çc]a|autismo|tea|defici[êe]ncia|hiv|aids|gravidez|gestante)\b', 'SAUDE', 0.90),
            (r'\b(psic[óo]log[oa]|psiquiatra|terapia|medicamento|rem[ée]dio|receita m[ée]dica)\b', 'SAUDE', 0.80),
            
            # Vulnerabilidade e Social
            (r'\b(bolsa fam[íi]lia|aux[íi]lio|benef[íi]cio|renda|vulnerabilidade|risco social)\b', 'SOCIAL', 0.75),
            (r'\b(medida protetiva|viol[êe]ncia|abuso|agress[ãa]o|boletim de ocorr[êe]ncia)\b', 'SENSIVEL', 0.90),
            (r'\b(menor de idade|crian[çc]a|adolescente|tutelad[oa])\b', 'MENOR', 0.85),
            
            # Documentos e Identificação (solicitação implícita)
            (r'\b(identidade|rg|carteira|documento|habilita[çc][ãa]o|cnh)\b', 'DOC_IMPLICITO', 0.70),
            (r'\b(meu cadastro|atualizar cadastro|fazer cadastro|meus dados)\b', 'CADASTRO', 0.75),
            
            # Administrativo Pessoal
            (r'\b(processo disciplinar|sindic[âa]ncia|pad|punido|advert[êe]ncia|demiss[ãa]o)\b', 'ADM_SENSIVEL', 0.85),
            (r'\b(aposentadoria|pens[ãa]o|folha de pagamento|contracheque|holerite)\b', 'FINANCEIRO', 0.80),
        ]
        
        self.contextos_positivos = [
            r'meu', r'minha', r'solicito', r'requerimento', r'cópia',
            r'acesso', r'enviar', r'encaminhar', r'me cadastrar'
        ]
        
        # Contextos que indicam generalidade (reduz chance de ser pessoal)
        self.contextos_negativos = [
            r'estat[íi]stica', r'quantitativo', r'quantos', r'total',
            r'dados gerais', r'levantamento', r'número de', r'lista de',
            r'todos os', r'quaisquer'
        ]
    
    def detectar(self, texto: str) -> List[DeteccaoEncontrada]:
        deteccoes = []
        texto_lower = texto.lower()
        
        for padrao, subtipo, confianca_base in self.padroes:
            for match in re.finditer(padrao, texto, re.IGNORECASE):
                valor = match.group(0)
                confianca = confianca_base
                
                # Verifica contexto pessoal (aumenta confiança)
                pos_inicio = match.start()
                trecho_antes = texto_lower[max(0, pos_inicio-50):pos_inicio]
                
                eh_pessoal = False
                for ctx in self.contextos_positivos:
                    if re.search(ctx, trecho_antes):
                        confianca = min(1.0, confianca + 0.15)
                        eh_pessoal = True
                        break
                
                # Verifica contexto genérico (reduz confiança)
                # Exceção: Se for SAUDE ou SENSIVEL, mantém alta mesmo se parecer genérico,
                # pois estatísticas de saúde detalhadas podem ser sensíveis
                eh_generico = False
                if subtipo not in ['SAUDE', 'SENSIVEL']:
                    for ctx in self.contextos_negativos:
                        if re.search(ctx, trecho_antes):
                            confianca = max(0.2, confianca - 0.40)
                            eh_generico = True
                            break
                
                # Para termos muito comuns (ex: documento), exige contexto pessoal
                if subtipo == 'DOC_IMPLICITO' and not eh_pessoal:
                    continue
                    
                if confianca >= self.sensibilidade:
                    deteccoes.append(DeteccaoEncontrada(
                        tipo=f"CONTEXTO_{subtipo}",
                        valor=valor,
                        posicao_inicio=match.start(),
                        posicao_fim=match.end(),
                        confianca=round(confianca, 3),
                        contexto=self.extrair_contexto(texto, match.start(), match.end()),
                        validado=eh_pessoal,
                        metodo_deteccao="palavra_chave"
                    ))
        
        return self._remover_duplicatas(deteccoes)
    
    def _remover_duplicatas(self, deteccoes: List[DeteccaoEncontrada]) -> List[DeteccaoEncontrada]:
        if not deteccoes:
            return []
        
        deteccoes.sort(key=lambda x: (-x.confianca, x.posicao_inicio))
        resultado = []
        posicoes_usadas = set()
        
        for d in deteccoes:
            pos_range = range(d.posicao_inicio, d.posicao_fim)
            if not any(p in posicoes_usadas for p in pos_range):
                resultado.append(d)
                posicoes_usadas.update(pos_range)
        
        return resultado



class DetectorPlaca(DetectorBase):
    """
    Detector de Placas de Veículos.
    
    Suporta:
    - Padrão Nacional Antigo: AAA-0000 ou AAA 0000
    - Padrão Mercosul: AAA0A00
    """
    
    def __init__(self, sensibilidade: float = 0.85):
        super().__init__("PLACA_VEICULO", sensibilidade)
        # Regex unificada:
        # (?P<placa>...) captura o grupo
        # \b inicia e termina palavra para evitar matches parciais indesejados
        # Padrão antigo: [A-Z]{3}[- ]?\d{4}
        # Padrão Mercosul: [A-Z]{3}\d[A-Z]\d{2}
        self.regex_placa = re.compile(
            r'(?P<placa>\b[A-Z]{3}[- ]?\d{4}\b|\b[A-Z]{3}[- ]?\d[A-Z]\d{2}\b)',
            re.IGNORECASE
        )

    def detectar(self, texto: str) -> List[DeteccaoEncontrada]:
        if not texto:
            return []
            
        deteccoes = []
        for match in self.regex_placa.finditer(texto):
            valor = match.group('placa')
            
            # Validação básica de tamanho já garantida pelo regex
            
            deteccoes.append(DeteccaoEncontrada(
                tipo=self.nome_tipo,
                valor=valor,
                posicao_inicio=match.start(),
                posicao_fim=match.end(),
                confianca=1.0, # Regex exato = confiança máxima
                metodo_deteccao="regex_placa"
            ))
            
        return self._remover_duplicatas(deteccoes)

    def _remover_duplicatas(self, deteccoes: List[DeteccaoEncontrada]) -> List[DeteccaoEncontrada]:
        if not deteccoes:
            return []
            
        # Remove sobreposições mantendo a mais longa (embora aqui tenham tam fixo praticamente)
        deteccoes.sort(key=lambda x: (x.posicao_inicio, -(x.posicao_fim - x.posicao_inicio)))
        
        resultado = []
        ultima_fim = -1
        
        for d in deteccoes:
            if d.posicao_inicio >= ultima_fim:
                resultado.append(d)
                ultima_fim = d.posicao_fim
                
        return resultado


class SistemaDeteccaoIntegrado:
    """
    Sistema integrado que combina todos os detectores.
    
    Coordena a execução de múltiplos detectores e consolida resultados.
    Suporta modo híbrido: GLiNER (ML) + Regex para máxima precisão.
    """
    
    def __init__(self, config: Optional[Dict] = None, usar_gliner: bool = True, usar_llm: bool = None):
        """
        Inicializa o sistema com configuração opcional.
        
        Args:
            config: Dicionário com configurações de sensibilidade por tipo.
            usar_gliner: Se True, usa GLiNER para detecção adicional (requer instalação).
            usar_llm: Se True, usa LLM (Gemini) para detecção subjetiva (requer API Key).
        """
        config = config or {}
        
        self.detectores = {
            'CPF': DetectorCPF(config.get('cpf_sensibilidade', 0.80)),
            'RG': DetectorRG(config.get('rg_sensibilidade', 0.75)),
            'TELEFONE': DetectorTelefone(config.get('telefone_sensibilidade', 0.75)),
            'EMAIL': DetectorEmail(config.get('email_sensibilidade', 0.85)),
            'NOME': DetectorNome(config.get('nome_sensibilidade', 0.70)),
            'ENDERECO': DetectorEndereco(config.get('endereco_sensibilidade', 0.80)),
            'PROCESSO': DetectorProcesso(config.get('processo_sensibilidade', 0.70)),
            'PLACA_VEICULO': DetectorPlaca(config.get('placa_sensibilidade', 0.85)),
            'CONTEXTO': DetectorContexto(config.get('contexto_sensibilidade', 0.65)),
        }
        
        self.tipos_ativos = set(self.detectores.keys())
        
        # Configuração do GLiNER
        self.usar_gliner = usar_gliner
        self.gliner_threshold = config.get('gliner_threshold', 0.5)
        self._detector_gliner = None
        self._gliner_disponivel = None

        # Configuração do LLM (Gemini) - auto-detecta disponibilidade
        if usar_llm is None:
            # Auto-detecta: só habilita se API key estiver disponível
            import os
            usar_llm = bool(os.environ.get("GEMINI_API_KEY"))
        
        self.usar_llm = usar_llm
        self._detector_llm = None
        self._llm_disponivel = None
    
    @property
    def detector_gliner(self):
        """Lazy loading do detector GLiNER."""
        if self._detector_gliner is None and self.usar_gliner:
            try:
                from .detector_gliner import DetectorGLiNER
                self._detector_gliner = DetectorGLiNER(threshold=self.gliner_threshold)
                self._gliner_disponivel = True
            except ImportError:
                self._gliner_disponivel = False
                print("Aviso: GLiNER não disponível. Usando apenas detecção por regex.")
        return self._detector_gliner
    
    @property
    def gliner_disponivel(self) -> bool:
        """Verifica se o GLiNER está disponível."""
        if self._gliner_disponivel is None:
            try:
                from .detector_gliner import DetectorGLiNER
                self._gliner_disponivel = DetectorGLiNER().esta_disponivel()
            except ImportError:
                self._gliner_disponivel = False
        return self._gliner_disponivel
    
    @property
    def detector_llm(self):
        """Lazy loading do detector LLM."""
        if self._detector_llm is None and self.usar_llm:
            try:
                from .detector_llm import DetectorLLM
                self._detector_llm = DetectorLLM()
                # Verifica se a API Key estava presente
                if not self._detector_llm.esta_ativo():
                    print("Aviso: Falha ao inicializar LLM (API Key ausente?).")
                    self._llm_disponivel = False
                else:
                    self._llm_disponivel = True
            except ImportError:
                self._llm_disponivel = False
                print("Aviso: Módulo detector_llm não encontrado.")
        return self._detector_llm

    @property
    def llm_disponivel(self) -> bool:
        """Verifica se o LLM está disponível."""
        if self._llm_disponivel is None:
            # Tenta carregar para verificar status
            _ = self.detector_llm
        return self._llm_disponivel is True
    
    def configurar_tipos_ativos(self, tipos: List[str]):
        """Define quais tipos de dados devem ser detectados."""
        self.tipos_ativos = set(t.upper() for t in tipos if t.upper() in self.detectores)
    
    def analisar_texto(self, texto: str) -> List[DeteccaoEncontrada]:
        """
        Analisa um texto e retorna todas as detecções.
        
        Usa abordagem híbrida: GLiNER (ML) + Regex para máxima cobertura e precisão.
        
        Args:
            texto: Texto a ser analisado.
            
        Returns:
            Lista de DeteccaoEncontrada ordenada por posição.
        """
        todas_deteccoes = []
        
        # 1. Detecção por Regex (sempre executado)
        for tipo, detector in self.detectores.items():
            if tipo in self.tipos_ativos:
                deteccoes = detector.detectar(texto)
                todas_deteccoes.extend(deteccoes)
        
        # 2. Detecção por GLiNER (se disponível e habilitado)
        if self.usar_gliner and self.detector_gliner is not None:
            try:
                deteccoes_gliner = self.detector_gliner.detectar(texto)
                
                for dg in deteccoes_gliner:
                    # Verifica se já existe detecção similar (pelo valor e posição)
                    ja_detectado = False
                    for td in todas_deteccoes:
                        # Considera duplicata se há sobreposição significativa
                        if self._deteccoes_sobrepostas(td, dg):
                            # Mantém a de maior confiança, atualiza se GLiNER for melhor
                            if dg.confianca > td.confianca:
                                td.metodo_deteccao = f"hibrido({td.metodo_deteccao}+gliner)"
                            ja_detectado = True
                            break
                    
                    if not ja_detectado:
                        # Converte DeteccaoGLiNER para DeteccaoEncontrada
                        nova_deteccao = DeteccaoEncontrada(
                            tipo=dg.tipo,
                            valor=dg.valor,
                            posicao_inicio=dg.posicao_inicio,
                            posicao_fim=dg.posicao_fim,
                            confianca=dg.confianca,
                            contexto=self._extrair_contexto(texto, dg.posicao_inicio, dg.posicao_fim),
                            validado=False,
                            metodo_deteccao="gliner"
                        )
                        todas_deteccoes.append(nova_deteccao)
            except Exception as e:
                # Falha silenciosa do GLiNER - regex já capturou
                pass
        
        # 3. Detecção por LLM (APENAS SE NADA FOI ENCONTRADO - última camada)
        if len(todas_deteccoes) == 0 and self.usar_llm and self.detector_llm is not None and self.detector_llm.esta_ativo():
            try:
                score_sensibilidade = self.detector_llm.avaliar_sensibilidade(texto)
                
                # Se o score for alto (> 0.7), adiciona uma detecção genérica
                if score_sensibilidade >= 0.7:
                    deteccao_llm = DeteccaoEncontrada(
                        tipo="SUBJETIVO_LLM",
                        valor="[Conteúdo sensível detectado por IA]",
                        posicao_inicio=0,
                        posicao_fim=len(texto),
                        confianca=score_sensibilidade,
                        contexto=texto[:200],  # Primeiros 200 chars como contexto
                        validado=False,
                        metodo_deteccao=f"llm-fallback-{self.detector_llm.modelo_nome}"
                    )
                    todas_deteccoes.append(deteccao_llm)
                    
            except Exception as e:
                print(f"Erro na avaliação LLM: {e}")
                pass
        
        # Ordena por posição no texto
        todas_deteccoes.sort(key=lambda x: x.posicao_inicio)
        
        return todas_deteccoes
    
    def _deteccoes_sobrepostas(self, d1, d2) -> bool:
        """Verifica se duas detecções estão sobrepostas."""
        # Considera sobreposição se há interseção de posições
        inicio_max = max(d1.posicao_inicio, d2.posicao_inicio)
        fim_min = min(d1.posicao_fim, d2.posicao_fim)
        return inicio_max < fim_min
    
    def _extrair_contexto(self, texto: str, inicio: int, fim: int, janela: int = 50) -> str:
        """Extrai o contexto ao redor de uma detecção."""
        ctx_inicio = max(0, inicio - janela)
        ctx_fim = min(len(texto), fim + janela)
        return texto[ctx_inicio:ctx_fim]
    
    def contem_dados_pessoais(self, texto: str) -> bool:
        """Verifica se o texto contém algum dado pessoal."""
        return len(self.analisar_texto(texto)) > 0
    
    def obter_resumo(self, texto: str) -> Dict:
        """Retorna um resumo das detecções no texto."""
        deteccoes = self.analisar_texto(texto)
        
        resumo = {
            'total_deteccoes': len(deteccoes),
            'contem_dados_pessoais': len(deteccoes) > 0,
            'por_tipo': {},
            'confianca_media': 0.0,
            'deteccoes': deteccoes
        }
        
        for d in deteccoes:
            tipo = d.tipo.split('_')[0]  # Remove subtipo
            if tipo not in resumo['por_tipo']:
                resumo['por_tipo'][tipo] = []
            resumo['por_tipo'][tipo].append(d.valor)
        
        if deteccoes:
            resumo['confianca_media'] = sum(d.confianca for d in deteccoes) / len(deteccoes)
        
        return resumo


if __name__ == "__main__":
    # Teste básico
    sistema = SistemaDeteccaoIntegrado()
    
    texto_teste = """
    Prezados, solicito informações sobre o processo.
    Nome: João Silva Santos
    CPF: 123.456.789-09
    E-mail: joao.silva@email.com
    Telefone: (61) 99999-8888
    """
    
    resultado = sistema.obter_resumo(texto_teste)
    print(f"Detecções encontradas: {resultado['total_deteccoes']}")
    print(f"Contém dados pessoais: {resultado['contem_dados_pessoais']}")
    for tipo, valores in resultado['por_tipo'].items():
        print(f"  {tipo}: {valores}")
