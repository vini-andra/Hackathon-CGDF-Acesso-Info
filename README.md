# Sistema de Identificação de Dados Sensíveis

## 1º Hackathon em Controle Social: Desafio Participa DF
### Categoria: Acesso à Informação

---

## 📋 Descrição

Este sistema foi desenvolvido para identificar automaticamente **dados pessoais sensíveis** em pedidos de acesso à informação, conforme definido no edital do Hackathon:

- **Nome** (identificação direta de pessoa natural)
- **CPF** (Cadastro de Pessoa Física)
- **RG** (Registro Geral)
- **Telefone** (números de contato)
- **E-mail** (endereço de correio eletrônico)
- **Endereço/CEP** (localização)

O objetivo é auxiliar na classificação de pedidos que, embora marcados como públicos, contenham dados pessoais e devam ser reclassificados como não públicos.

---

## 🏗️ Estrutura do Projeto

```
sistema_identificacao_dados_sensiveis/
├── main.py                    # Script principal de execução
├── requirements.txt           # Dependências do projeto
├── README.md                  # Esta documentação
├── src/
│   ├── __init__.py           # Módulo principal
│   ├── detectores.py         # Classes de detecção de dados pessoais
│   ├── carregador.py         # Carregamento de dados multi-formato
│   └── metricas.py           # Métricas e geração de relatórios
├── data/                      # Diretório para arquivos de entrada
├── output/                    # Diretório para resultados
├── models/                    # Configurações personalizadas
└── tests/                     # Testes automatizados
```

---

## 🚀 Instalação e Configuração

### Pré-requisitos

- **Python**: 3.9 ou superior
- **Sistema Operacional**: Linux, macOS ou Windows

### Instalação de Dependências

```bash
# Criar ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### Dependências Principais

- `pandas>=1.5.0` - Manipulação de dados
- `openpyxl>=3.0.0` - Leitura de arquivos Excel
- `scikit-learn>=1.0.0` - Métricas de avaliação (opcional)

---

## 📖 Uso Básico

### Execução via Linha de Comando

```bash
# Análise básica de um arquivo
python main.py dados.xlsx

# Especificando a coluna de texto
python main.py dados.csv --coluna-texto "Texto Mascarado"

# Com arquivo de labels para avaliação
python main.py dados.xlsx --labels rotulos.csv

# Exportando resultados
python main.py dados.xlsx --output resultados.json --formato json

# Ajustando sensibilidades
python main.py dados.xlsx --sensibilidade-cpf 0.9 --sensibilidade-nome 0.6
```

### Uso como Biblioteca Python

```python
from src import SistemaDeteccaoIntegrado, CarregadorDados

# Inicializa o sistema
sistema = SistemaDeteccaoIntegrado()

# Analisa um texto
texto = "Meu nome é João Silva, CPF 123.456.789-09, telefone (61) 99999-8888"
resultado = sistema.obter_resumo(texto)

print(f"Contém dados pessoais: {resultado['contem_dados_pessoais']}")
print(f"Total de detecções: {resultado['total_deteccoes']}")

for tipo, valores in resultado['por_tipo'].items():
    print(f"  {tipo}: {valores}")
```

---

## 📊 Métricas e Avaliação

O sistema calcula as seguintes métricas conforme especificado no edital:

### Matriz de Confusão

|                  | Predição: Positivo | Predição: Negativo |
|------------------|--------------------|--------------------|
| **Real: Positivo** | VP (Verdadeiro Positivo) | FN (Falso Negativo) |
| **Real: Negativo** | FP (Falso Positivo) | VN (Verdadeiro Negativo) |

### Fórmulas

- **Precisão**: `VP / (VP + FP)` - De todos os detectados, quantos realmente continham dados
- **Sensibilidade/Recall**: `VP / (VP + FN)` - De todos que continham dados, quantos foram detectados
- **F1-Score**: `2 × (Precisão × Sensibilidade) / (Precisão + Sensibilidade)` - Média harmônica

---

## 🔧 Configuração e Personalização

### Ajustando Sensibilidades

Cada detector pode ter sua sensibilidade ajustada (0.0 a 1.0):

```python
config = {
    'cpf_sensibilidade': 0.80,      # Padrão: 0.80
    'rg_sensibilidade': 0.75,       # Padrão: 0.75
    'telefone_sensibilidade': 0.75, # Padrão: 0.75
    'email_sensibilidade': 0.85,    # Padrão: 0.85
    'nome_sensibilidade': 0.70,     # Padrão: 0.70
    'endereco_sensibilidade': 0.80, # Padrão: 0.80
}

sistema = SistemaDeteccaoIntegrado(config)
```

**Valores mais altos** = Menos detecções (mais precisão, menos recall)
**Valores mais baixos** = Mais detecções (menos precisão, mais recall)

---

## 🎓 Como Treinar e Adaptar o Sistema

### 1. Expandindo a Lista de Nomes

O detector de nomes usa uma lista base de nomes brasileiros. Para expandir:

```python
from src import DetectorNome

detector = DetectorNome()

# Adicionar novos nomes próprios
detector.adicionar_nomes(['Kayque', 'Thayná', 'Enzo', 'Valentina'])

# Adicionar novos sobrenomes
detector.adicionar_sobrenomes(['Tartaglia', 'Bolsonaro', 'Senna'])
```

### 2. Ajustando Padrões de Detecção

Para adicionar novos padrões de RG por estado:

```python
from src import DetectorRG

detector = DetectorRG()

# Adicionar padrão específico de um estado
detector.padroes.append(
    (r'\b(MG)-?(\d{2}\.?\d{3}\.?\d{3})\b', 0.95)  # Formato MG
)
```

### 3. Adicionando Contextos

Para melhorar a detecção baseada em contexto:

```python
from src import DetectorCPF

detector = DetectorCPF()

# Adicionar contextos que indicam presença de CPF
detector.contextos_positivos.append(r'n[úu]mero[\s\w]*contribuinte')
```

### 4. Criando um Novo Detector

```python
from src.detectores import DetectorBase, DeteccaoEncontrada
import re

class DetectorPlacaVeiculo(DetectorBase):
    """Detecta placas de veículos brasileiras."""
    
    def __init__(self, sensibilidade=0.85):
        super().__init__("PLACA_VEICULO", sensibilidade)
        
        # Padrão antigo (ABC-1234) e Mercosul (ABC1D23)
        self.padroes = [
            (r'\b[A-Z]{3}[-\s]?\d{4}\b', 0.90),
            (r'\b[A-Z]{3}\d[A-Z]\d{2}\b', 0.95),
        ]
    
    def detectar(self, texto):
        deteccoes = []
        for padrao, confianca in self.padroes:
            for match in re.finditer(padrao, texto, re.IGNORECASE):
                if confianca >= self.sensibilidade:
                    deteccoes.append(DeteccaoEncontrada(
                        tipo="PLACA_VEICULO",
                        valor=match.group(0),
                        posicao_inicio=match.start(),
                        posicao_fim=match.end(),
                        confianca=confianca,
                        contexto=self.extrair_contexto(texto, match.start(), match.end()),
                        metodo_deteccao="regex"
                    ))
        return deteccoes

# Adicionar ao sistema
sistema = SistemaDeteccaoIntegrado()
sistema.detectores['PLACA'] = DetectorPlacaVeiculo()
sistema.tipos_ativos.add('PLACA')
```

### 5. Treinamento com Dados Rotulados

Se você possui dados rotulados (com classificação real), pode otimizar as sensibilidades:

```python
from src import SistemaIdentificacaoDadosSensiveis
import itertools

def otimizar_sensibilidades(arquivo_dados, arquivo_labels):
    """Encontra as melhores sensibilidades por grid search."""
    
    # Carrega labels
    from main import carregar_labels
    labels = carregar_labels(arquivo_labels)
    
    melhor_f1 = 0
    melhor_config = {}
    
    # Grid de sensibilidades para testar
    valores = [0.6, 0.7, 0.8, 0.9]
    
    for cpf_s, nome_s, email_s in itertools.product(valores, valores, valores):
        config = {
            'cpf_sensibilidade': cpf_s,
            'nome_sensibilidade': nome_s,
            'email_sensibilidade': email_s,
            # ... outros
        }
        
        sistema = SistemaIdentificacaoDadosSensiveis(config)
        sistema.processar_arquivo(arquivo_dados, labels=labels, verbose=False)
        metricas = sistema.calcular_metricas()
        
        if metricas.f1_score > melhor_f1:
            melhor_f1 = metricas.f1_score
            melhor_config = config.copy()
            print(f"Novo melhor F1: {melhor_f1:.4f} com config: {config}")
    
    return melhor_config, melhor_f1

# Uso
config_otima, f1 = otimizar_sensibilidades('dados.xlsx', 'labels.csv')
print(f"Configuração ótima: {config_otima}")
```

---

## 📁 Formatos de Arquivo Suportados

| Formato | Extensão | Descrição |
|---------|----------|-----------|
| Excel | `.xlsx`, `.xls` | Planilhas Microsoft Excel |
| CSV | `.csv` | Valores separados por vírgula |
| TSV | `.tsv` | Valores separados por tabulação |
| JSON | `.json` | JavaScript Object Notation |
| Texto | `.txt` | Arquivo de texto simples |
| Parquet | `.parquet` | Apache Parquet (big data) |

---

## 📈 Exemplo de Saída

```
================================================================================
  RELATÓRIO DE DESEMPENHO - SISTEMA DE IDENTIFICAÇÃO DE DADOS SENSÍVEIS
================================================================================
  Data/Hora: 2026-01-28T14:30:00
  Total de Registros Analisados: 99

┌──────────────────────────────────────────────────────────────────────────────┐
│                          MATRIZ DE CONFUSÃO                                  │
├───────────────────────────────────┬──────────────────────────────────────────┤
│                                   │           PREDIÇÃO DO MODELO             │
│                                   ├──────────────────┬───────────────────────┤
│                                   │    POSITIVO      │       NEGATIVO        │
├────────────────────┬──────────────┼──────────────────┼───────────────────────┤
│  REAL              │   POSITIVO   │     VP = 45      │       FN = 3          │
│                    ├──────────────┼──────────────────┼───────────────────────┤
│                    │   NEGATIVO   │     FP = 2       │       VN = 49         │
└────────────────────┴──────────────┴──────────────────┴───────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                        MÉTRICAS DE DESEMPENHO                                │
├──────────────────────────────────────────────────────────────────────────────┤
│  Precisão:      95.74%  [████████████████████████████░░]  IC 95%: [85.5%, 99.5%]
│  Sensibilidade: 93.75%  [████████████████████████████░░]  IC 95%: [83.2%, 98.7%]
│  F1-Score:      94.74%  [████████████████████████████░░]  IC 95%: [89.5%, 97.0%]
├──────────────────────────────────────────────────────────────────────────────┤
│  Acurácia:      94.95%  [████████████████████████████░░]
│  Especificidade:96.08%  [█████████████████████████████░]
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Tipos de Dados Detectados

### CPF (Cadastro de Pessoa Física)
- Formato com pontuação: `123.456.789-09`
- Formato sem pontuação: `12345678909`
- Validação de dígitos verificadores

### RG (Registro Geral)
- Formatos variados por estado
- Com e sem pontuação
- Análise de contexto

### Telefone
- Com DDD: `(61) 99999-8888`
- Com código país: `+55 61 99999-8888`
- Validação de DDDs brasileiros

### E-mail
- Padrão RFC 5322 simplificado
- Validação de domínios conhecidos

### Nome
- Detecção por dicionário de nomes brasileiros
- Análise de padrões de capitalização
- Contexto semântico

---

## ⚠️ Limitações Conhecidas

1. **Nomes**: Pode não detectar nomes estrangeiros ou muito incomuns
2. **RG**: Formatos variam muito entre estados
3. **Telefone**: Números sem DDD têm menor confiança
4. **Contexto**: Números de protocolo podem ser confundidos com documentos

---

## 📝 Licença

Este software foi desenvolvido para o 1º Hackathon em Controle Social do Distrito Federal e está sujeito às regras do edital.

---

## 👥 Autores

Desenvolvido por participante(s) do Hackathon Participa DF - Janeiro/2026.

Vinicius Armando Menezes de Andrade
Joao Luiz de Jesus Amaro

---

## 📧 Contato

Para dúvidas sobre o Hackathon: desafioparticipadf@cg.df.gov.br
