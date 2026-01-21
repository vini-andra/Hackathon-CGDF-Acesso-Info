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
            '88888888888', '99999999999', '12345678909', '01234567890'
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
        
        # Padrão para nomes próprios
        self.padrao_nome = r'\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+(?:de|da|do|dos|das|e|di|del)\s+)?(?:[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+\s*){1,5})\b'
        
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
        """Carrega lista base de nomes brasileiros comuns."""
        nomes = {
            # Masculinos mais comuns
            'jose', 'joao', 'antonio', 'francisco', 'carlos', 'paulo', 'pedro',
            'lucas', 'luiz', 'marcos', 'luis', 'gabriel', 'rafael', 'daniel',
            'marcelo', 'bruno', 'eduardo', 'felipe', 'raimundo', 'rodrigo',
            'manoel', 'sebastiao', 'jorge', 'fernando', 'andre', 'fabio',
            'marcio', 'geraldo', 'alexandre', 'ricardo', 'mario', 'sergio',
            'claudio', 'jose', 'gilberto', 'roberto', 'ademir', 'ademar',
            'adilson', 'adriano', 'agnaldo', 'ailton', 'alan', 'alberto',
            'alex', 'alexandre', 'amauri', 'anderson', 'andre', 'angelo',
            # Femininos mais comuns
            'maria', 'ana', 'francisca', 'antonia', 'adriana', 'juliana',
            'marcia', 'fernanda', 'patricia', 'aline', 'sandra', 'camila',
            'amanda', 'bruna', 'jessica', 'leticia', 'julia', 'luciana',
            'vanessa', 'mariana', 'gabriela', 'beatriz', 'larissa', 'renata',
            'fabiana', 'cristiane', 'simone', 'carla', 'rosa', 'rita',
            'lucia', 'celia', 'marlene', 'vera', 'tereza', 'terezinha',
            'angela', 'neide', 'rosangela', 'lourdes', 'fatima', 'marta',
            'helena', 'regina', 'sonia', 'valdete', 'zelia', 'eliana',
            'eliane', 'elisabete', 'elizabeth', 'eva', 'glaucia', 'gloria',
            'iara', 'ines', 'irene', 'isabel', 'ivone', 'jacira',
            'jaqueline', 'joana', 'josefa', 'josiane', 'jucelia', 'jussara',
            'katia', 'keila', 'kelly', 'lara', 'laura', 'leila',
            'lidia', 'lilian', 'luiza', 'magda', 'margarida', 'marli',
            'madalena', 'miriam', 'monica', 'nadia', 'neusa', 'odete',
            'paula', 'priscila', 'raquel', 'rosana', 'roseli', 'rosilene',
            'silvia', 'solange', 'sueli', 'tania', 'tatiana', 'valeria',
            'vania', 'viviane', 'zenaide', 'zilma', 'zuleide'
        }
        return nomes
    
    def _carregar_sobrenomes_base(self) -> Set[str]:
        """Carrega lista base de sobrenomes brasileiros."""
        sobrenomes = {
            'silva', 'santos', 'oliveira', 'souza', 'rodrigues', 'ferreira',
            'alves', 'pereira', 'lima', 'gomes', 'costa', 'ribeiro',
            'martins', 'carvalho', 'almeida', 'lopes', 'soares', 'fernandes',
            'vieira', 'barbosa', 'rocha', 'dias', 'nascimento', 'andrade',
            'moreira', 'nunes', 'marques', 'machado', 'mendes', 'freitas',
            'cardoso', 'ramos', 'goncalves', 'santana', 'teixeira', 'araujo',
            'reis', 'moura', 'pinto', 'correia', 'campos', 'miranda',
            'melo', 'borges', 'azevedo', 'cunha', 'batista', 'matos',
            'viana', 'nogueira', 'coelho', 'pires', 'brito', 'tavares',
            'monteiro', 'cavalcante', 'fonseca', 'farias', 'antunes', 'bezerra',
            'macedo', 'figueiredo', 'aguiar', 'siqueira', 'guimaraes', 'leal',
            'abreu', 'amaral', 'assis', 'assumpcao', 'bastos', 'braga',
            'brandao', 'cabral', 'camargo', 'cardoso', 'carneiro', 'cerqueira',
            'chaves', 'correia', 'domingues', 'duarte', 'esteves', 'evangelista',
            'faria', 'fontes', 'franca', 'franco', 'freire', 'garcia',
            'henrique', 'leite', 'luz', 'magalhaes', 'malta', 'medeiros',
            'menezes', 'mesquita', 'neto', 'pacheco', 'paiva', 'paixao',
            'passos', 'penha', 'pessoa', 'queiroz', 'resende', 'rosa',
            'sales', 'sampaio', 'santiago', 'silveira', 'simoes', 'sena',
            'toledo', 'torres', 'trindade', 'vargas', 'vasconcelos', 'xavier'
        }
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
            
            # Aumenta se primeiro nome é conhecido
            if primeiro_nome in self.nomes_proprios:
                confianca += 0.25
            
            # Aumenta se último nome é sobrenome conhecido
            ultimo_nome = palavras_significativas[-1].lower()
            if ultimo_nome in self.sobrenomes:
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


class SistemaDeteccaoIntegrado:
    """
    Sistema integrado que combina todos os detectores.
    
    Coordena a execução de múltiplos detectores e consolida resultados.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o sistema com configuração opcional.
        
        Args:
            config: Dicionário com configurações de sensibilidade por tipo.
        """
        config = config or {}
        
        self.detectores = {
            'CPF': DetectorCPF(config.get('cpf_sensibilidade', 0.80)),
            'RG': DetectorRG(config.get('rg_sensibilidade', 0.75)),
            'TELEFONE': DetectorTelefone(config.get('telefone_sensibilidade', 0.75)),
            'EMAIL': DetectorEmail(config.get('email_sensibilidade', 0.85)),
            'NOME': DetectorNome(config.get('nome_sensibilidade', 0.70)),
            'ENDERECO': DetectorEndereco(config.get('endereco_sensibilidade', 0.80)),
        }
        
        self.tipos_ativos = set(self.detectores.keys())
    
    def configurar_tipos_ativos(self, tipos: List[str]):
        """Define quais tipos de dados devem ser detectados."""
        self.tipos_ativos = set(t.upper() for t in tipos if t.upper() in self.detectores)
    
    def analisar_texto(self, texto: str) -> List[DeteccaoEncontrada]:
        """
        Analisa um texto e retorna todas as detecções.
        
        Args:
            texto: Texto a ser analisado.
            
        Returns:
            Lista de DeteccaoEncontrada ordenada por posição.
        """
        todas_deteccoes = []
        
        for tipo, detector in self.detectores.items():
            if tipo in self.tipos_ativos:
                deteccoes = detector.detectar(texto)
                todas_deteccoes.extend(deteccoes)
        
        # Ordena por posição no texto
        todas_deteccoes.sort(key=lambda x: x.posicao_inicio)
        
        return todas_deteccoes
    
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
