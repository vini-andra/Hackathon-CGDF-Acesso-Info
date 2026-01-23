"""
Módulo de Detecção com GLiNER Multi PII Domains
Sistema de Identificação de Dados Sensíveis - Hackathon Participa DF

Este módulo usa o modelo GLiNER especializado em PII para detecção
de dados pessoais com base em aprendizado de máquina.

Modelo: E3-JSI/gliner-multi-pii-domains-v1
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set
import re


@dataclass
class DeteccaoGLiNER:
    """Representa uma entidade detectada pelo GLiNER."""
    tipo: str               # Tipo normalizado (CPF, NOME, etc.)
    valor: str              # Texto da entidade
    posicao_inicio: int     # Posição inicial
    posicao_fim: int        # Posição final
    confianca: float        # Score do modelo
    tipo_original: str      # Label original do GLiNER
    metodo_deteccao: str = "gliner"


class DetectorGLiNER:
    """
    Detector de PII usando o modelo GLiNER Multi PII Domains.
    
    Este detector usa um modelo de ML treinado especificamente para
    identificar informações pessoais identificáveis (PII) em textos.
    """
    
    # Mapeamento de labels do GLiNER para tipos do sistema
    MAPEAMENTO_TIPOS = {
        # Nomes
        "person": "NOME",
        "name": "NOME",
        
        # Documentos brasileiros
        "cpf": "CPF",
        "cnpj": "CNPJ",
        
        # Contato
        "phone number": "TELEFONE",
        "mobile phone number": "TELEFONE",
        "landline phone number": "TELEFONE",
        "fax number": "TELEFONE",
        "email": "EMAIL",
        "email address": "EMAIL",
        
        # Endereço
        "address": "ENDERECO",
        "postal code": "ENDERECO_CEP",
        
        # Documentos de identidade
        "identity card number": "RG",
        "national id number": "RG",
        "identity document number": "RG",
        "passport number": "PASSAPORTE",
        "driver's license number": "CNH",
        
        # Dados financeiros
        "credit card number": "CARTAO_CREDITO",
        "bank account number": "CONTA_BANCARIA",
        "iban": "IBAN",
        
        # Dados de saúde
        "health insurance number": "PLANO_SAUDE",
        "health insurance id number": "PLANO_SAUDE",
        "medical condition": "DADOS_SAUDE",
        "medication": "DADOS_SAUDE",
        "blood type": "DADOS_SAUDE",
        
        # Outros
        "date of birth": "DATA_NASCIMENTO",
        "social security number": "INSS",
        "tax identification number": "CPF",  # No Brasil, geralmente é o CPF
        "username": "USUARIO",
        "ip address": "IP",
        "license plate number": "PLACA_VEICULO",
    }
    
    # Labels prioritários para detecção de PII brasileiro
    LABELS_PII_BR = [
        "person",
        "cpf",
        "cnpj",
        "phone number",
        "mobile phone number",
        "email",
        "email address",
        "address",
        "postal code",
        "date of birth",
        "identity card number",
        "driver's license number",
        "credit card number",
        "bank account number",
    ]
    
    def __init__(self, threshold: float = 0.5, device: str = None):
        """
        Inicializa o detector GLiNER.
        
        Args:
            threshold: Limiar de confiança para aceitar detecções (0.0 a 1.0)
            device: Dispositivo para inferência ('cuda', 'cpu', ou None para auto)
        """
        self.threshold = threshold
        self.device = device
        self._modelo = None
        self._modelo_carregado = False
    
    @property
    def modelo(self):
        """Lazy loading do modelo GLiNER."""
        if not self._modelo_carregado:
            self._carregar_modelo()
        return self._modelo
    
    def _carregar_modelo(self):
        """Carrega o modelo GLiNER do HuggingFace."""
        try:
            from gliner import GLiNER
            
            print("Carregando modelo GLiNER Multi PII Domains...")
            
            # Carrega o modelo
            self._modelo = GLiNER.from_pretrained(
                "E3-JSI/gliner-multi-pii-domains-v1"
            )
            
            # Move para GPU se disponível e não especificado
            if self.device is None:
                try:
                    import torch
                    if torch.cuda.is_available():
                        self._modelo = self._modelo.to("cuda")
                        print("  -> Usando GPU (CUDA)")
                    else:
                        print("  -> Usando CPU")
                except ImportError:
                    print("  -> Usando CPU (torch não detectou CUDA)")
            elif self.device:
                self._modelo = self._modelo.to(self.device)
                print(f"  -> Usando {self.device}")
            
            self._modelo_carregado = True
            print("Modelo GLiNER carregado com sucesso!")
            
        except ImportError as e:
            print(f"Erro: Biblioteca GLiNER não instalada. Execute: pip install gliner")
            raise ImportError(
                "GLiNER não está instalado. Instale com: pip install gliner torch"
            ) from e
        except Exception as e:
            print(f"Erro ao carregar modelo GLiNER: {e}")
            raise
    
    def detectar(self, texto: str, labels: List[str] = None) -> List[DeteccaoGLiNER]:
        """
        Detecta entidades PII no texto usando GLiNER.
        
        Args:
            texto: Texto para analisar
            labels: Lista de labels a detectar (usa LABELS_PII_BR se None)
            
        Returns:
            Lista de DeteccaoGLiNER com as entidades encontradas
        """
        if not texto or not texto.strip():
            return []
        
        labels = labels or self.LABELS_PII_BR
        
        try:
            # Faz a predição
            entidades = self.modelo.predict_entities(
                texto, 
                labels, 
                threshold=self.threshold
            )
            
            deteccoes = []
            for ent in entidades:
                # Mapeia o tipo
                tipo_original = ent.get("label", "").lower()
                tipo_normalizado = self.MAPEAMENTO_TIPOS.get(
                    tipo_original, 
                    tipo_original.upper().replace(" ", "_")
                )
                
                deteccoes.append(DeteccaoGLiNER(
                    tipo=tipo_normalizado,
                    valor=ent.get("text", ""),
                    posicao_inicio=ent.get("start", 0),
                    posicao_fim=ent.get("end", 0),
                    confianca=round(ent.get("score", 0.0), 4),
                    tipo_original=tipo_original,
                    metodo_deteccao="gliner"
                ))
            
            return deteccoes
            
        except Exception as e:
            print(f"Erro na detecção GLiNER: {e}")
            return []
    
    def detectar_todos_tipos(self, texto: str) -> List[DeteccaoGLiNER]:
        """
        Detecta todos os tipos de PII suportados.
        
        Args:
            texto: Texto para analisar
            
        Returns:
            Lista de DeteccaoGLiNER
        """
        return self.detectar(texto, labels=list(self.MAPEAMENTO_TIPOS.keys()))
    
    def esta_disponivel(self) -> bool:
        """
        Verifica se o GLiNER está disponível para uso.
        
        Returns:
            True se a biblioteca está instalada, False caso contrário
        """
        try:
            import gliner
            return True
        except ImportError:
            return False
    
    def liberar_memoria(self):
        """Libera a memória do modelo."""
        if self._modelo is not None:
            del self._modelo
            self._modelo = None
            self._modelo_carregado = False
            
            # Tenta liberar memória da GPU
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass


def verificar_instalacao():
    """Verifica se as dependências do GLiNER estão instaladas."""
    dependencias = {
        "gliner": False,
        "torch": False,
    }
    
    try:
        import gliner
        dependencias["gliner"] = True
    except ImportError:
        pass
    
    try:
        import torch
        dependencias["torch"] = True
    except ImportError:
        pass
    
    return dependencias


if __name__ == "__main__":
    # Teste básico
    print("Verificando instalação...")
    deps = verificar_instalacao()
    
    for dep, instalado in deps.items():
        status = "✓" if instalado else "✗"
        print(f"  {status} {dep}")
    
    if all(deps.values()):
        print("\nTestando detector...")
        detector = DetectorGLiNER(threshold=0.5)
        
        texto_teste = """
        Nome: João Silva Santos
        CPF: 123.456.789-00
        E-mail: joao.silva@email.com
        Telefone: (61) 99999-8888
        """
        
        deteccoes = detector.detectar(texto_teste)
        
        print(f"\nDetecções encontradas: {len(deteccoes)}")
        for d in deteccoes:
            print(f"  [{d.tipo}] '{d.valor}' (confiança: {d.confianca:.2%})")
    else:
        print("\nInstale as dependências com: pip install gliner torch")
