"""
Módulo de Detecção de Dados Subjetivos com LLM (Gemini)
Sistema de Identificação de Dados Sensíveis - Hackathon Participa DF

Este módulo usa a API do Google Gemini para identificar informações sensíveis
subjetivas que são difíceis de detectar com regex ou modelos clássicos de NER,
como opiniões políticas, crenças religiosas, etc.
"""

import os
import json
import re
import logging
import google.generativeai as genai
from typing import List, Optional
from dataclasses import dataclass

# Importa classes base do módulo de detectores
# Ajuste o import conforme a estrutura do seu projeto
try:
    from .detectores import DetectorBase, DeteccaoEncontrada
except ImportError:
    # Fallback para testes isolados
    from detectores import DetectorBase, DeteccaoEncontrada


class DetectorLLM(DetectorBase):
    """
    Detector de dados sensíveis subjetivos usando LLM (Google Gemini).
    
    Categorias alvo:
    - OPINIAO_POLITICA
    - RELIGIAO (Crença religiosa/filosófica)
    - FILIACAO_SINDICAL
    - DADOS_SAUDE_SUBJETIVOS (Descrições de sintomas, tratamentos, etc.)
    - ORIENTACAO_SEXUAL
    - ORIGEM_RACIAL_ETNICA (Contextos descritivos)
    """
    
    def __init__(self, api_key: str = None, modelo_nome: str = "gemini-2.0-flash", sensibilidade: float = 0.5, max_length: int = 3000):
        """
        Inicializa o detector LLM.
        
        Args:
            api_key: Chave de API do Google.
            modelo_nome: Nome do modelo Gemini.
            sensibilidade: Limiar de confiança.
            max_length: Tamanho máximo do texto para análise (truncamento).
        """
        super().__init__("SUBJETIVO", sensibilidade)
        
        self.max_length = max_length
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            print("AVISO: API Key do Gemini não encontrada. O DetectorLLM não funcionará.")
            self._modelo = None
            return
            
        genai.configure(api_key=self.api_key)
        
        # Keywords para pré-filtro (heurística para economizar API)
        self.keywords_filtro = {
            'POLITICA': ['partido', 'eleição', 'voto', 'candidato', 'lula', 'bolsonaro', 'pt', 'esquerda', 'direita', 'comunista', 'fascista', 'socialismo', 'militante', 'ideologia'],
            'RELIGIAO': ['deus', 'igreja', 'fé', 'religião', 'crença', 'biblia', 'culto', 'pastor', 'padre', 'bencão', 'espírita', 'umbanda', 'candomblé', 'evangélico', 'católico'],
            'SAUDE': ['doença', 'doente', 'enfermo', 'paciente', 'tratamento', 'dor', 'remédio', 'medicamento', 'câncer', 'hiv', 'aids', 'depressão', 'ansiedade', 'terapia', 'laudo', 'atestado', 'cid', 'diagnóstico', 'sintoma'],
            'SINDICATO': ['sindicato', 'sindical', 'greve', 'assembleia', 'filiado', 'associação de classe'],
            'SEXUAL/ETNIA': ['gay', 'lésbica', 'homossexual', 'trans', 'travesti', 'lgbt', 'orientação sexual', 'negro', 'pardo', 'preto', 'indígena', 'raça', 'etnia']
        }
        
        # Configuração de segurança
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        self.modelo_nome = modelo_nome
        self._modelo = genai.GenerativeModel(
            model_name=self.modelo_nome,
            safety_settings=safety_settings
        )
        
    def _tem_palavras_candidatas(self, texto: str) -> bool:
        """Verifica se o texto contém palavras-chave que justifiquem o uso do LLM."""
        texto_lower = texto.lower()
        
        for categoria, keywords in self.keywords_filtro.items():
            for kw in keywords:
                if kw in texto_lower:
                    return True
        return False

    def avaliar_sensibilidade(self, texto: str) -> float:
        """
        Avalia se o texto contém dados sensíveis subjetivos.
        
        Esta é uma camada de FALLBACK - só deve ser chamada quando regex e GLiNER
        não encontraram nada.
        
        Returns:
            float: Score entre 0.0 (sem dados sensíveis) e 1.0 (alta sensibilidade)
        """
        if not self._modelo or not texto.strip():
            return 0.0
            
        # 1. Truncamento para evitar tokens excessivos
        texto_processado = texto[:self.max_length]
        
        # 2. Pré-filtro por palavras-chave
        if not self._tem_palavras_candidatas(texto_processado):
            return 0.0
            
        prompt = f"""
        Você é um detector de dados pessoais sensíveis.
        
        Analise o texto abaixo e determine se ele contém INFORMAÇÕES PESSOAIS SENSÍVEIS de natureza SUBJETIVA, tais como:
        - Opiniões políticas
        - Crenças religiosas ou filosóficas
        - Filiação sindical
        - Dados de saúde (doenças, sintomas, tratamentos)
        - Orientação sexual
        - Origem racial ou étnica
        
        Texto para análise:
        \"\"\"{texto_processado}\"\"\"
        
        Retorne APENAS um JSON (sem markdown, sem explicação) com um único campo:
        {{"score": 0.0}}
        
        Onde 'score' é um número entre 0.0 (sem dados sensíveis) e 1.0 (alta sensibilidade).
        """
        
        import time
        max_retries = 3
        
        for attempt in range(max_retries + 1):
            try:
                response = self._modelo.generate_content(prompt)
                
                if not response.parts:
                    print(f"AVISO: Resposta vazia ou bloqueada (LLM).")
                    return 0.0

                texto_resp = response.text
                
                # Extrai JSON
                match = re.search(r'(\{.*\})', texto_resp, re.DOTALL)
                json_str = match.group(1) if match else texto_resp

                try:
                    dados = json.loads(json_str)
                    score = float(dados.get("score", 0.0))
                    return max(0.0, min(1.0, score))  # Clamp entre 0 e 1
                    
                except (json.JSONDecodeError, ValueError, KeyError) as parse_err:
                    print(f"ERRO DE PARSE JSON (LLM): {parse_err}")
                    print(f"RAW RESPOSTA: {texto_resp[:500]}")
                    return 0.0
                
            except Exception as e:
                msg = str(e)
                if ("429" in msg or "quota" in msg.lower()) and attempt < max_retries:
                    print(f"Rate Limit (429) detectado. Tentativa {attempt+1}/{max_retries}. Aguardando 60s...")
                    time.sleep(60)
                    continue
                
                print(f"Erro na avaliação LLM: {e}")
                return 0.0
        
        return 0.0  # Falha após retries
    
    def detectar(self, texto: str) -> List[DeteccaoEncontrada]:
        """
        Método herdado de DetectorBase - DEPRECATED.
        Use avaliar_sensibilidade() ao invés.
        """
        return []

    def esta_ativo(self) -> bool:
        return self._modelo is not None
