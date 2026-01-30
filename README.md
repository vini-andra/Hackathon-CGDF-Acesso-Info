# Sistema de Identificação de Dados Sensíveis

## 1º Hackathon em Controle Social: Desafio Participa DF
### Categoria: Acesso à Informação

---

## 📋 Descrição

Este sistema foi desenvolvido para identificar automaticamente **dados pessoais sensíveis** em pedidos de acesso à informação, utilizando uma abordagem **híbrida** que combina:

- **Regex + Validadores**: Validação estrutural de documentos brasileiros (CPF, RG, etc.)
- **GLiNER (Machine Learning)**: Modelo de NER especializado em PII para detecção contextual
- **LLM (Opcional)**: Gemini API como camada de fallback para casos subjetivos

### ✨ Características Principais

- ✅ **Funciona sem API**: Sistema independente de quotas ou chaves de API
- ✅ **Alta Precisão**: Combina múltiplas técnicas de detecção
- ✅ **Formato Padrão**: Saída CSV no formato `ID,Predicao` (0 ou 1)
- ✅ **Multi-formato**: Suporta Excel, CSV, JSON, Parquet, etc.
- ✅ **Auto-detecção**: Identifica automaticamente colunas de ID e texto

### Tipos de Dados Detectados

| Tipo | Descrição | Método |
|------|-----------|--------|
| **Nome** | Identificação de pessoa natural | GLiNER + Dicionário |
| **CPF** | Cadastro de Pessoa Física | GLiNER + Regex + Validação |
| **CNPJ** | Cadastro Nacional da Pessoa Jurídica | GLiNER + Regex |
| **RG** | Registro Geral | Regex + Contexto |
| **Telefone** | Números de contato | GLiNER + Regex + DDD |
| **E-mail** | Endereço de correio eletrônico | GLiNER + Regex |
| **Endereço/CEP** | Localização | GLiNER + Regex |

---

## 🏗️ Estrutura do Projeto

```
sistema_identificacao_dados_sensiveis/
├── main.py                    # Script principal de execução
├── predict.py                 # Script de predição para submissão
├── requirements.txt           # Dependências do projeto
├── README.md                  # Esta documentação
├── src/
│   ├── __init__.py           # Módulo principal
│   ├── detectores.py         # Classes de detecção (híbrido)
│   ├── detector_gliner.py    # Detector GLiNER (ML)
│   ├── carregador.py         # Carregamento de dados multi-formato
│   └── metricas.py           # Métricas e geração de relatórios
├── dados/                     # Listas de nomes e sobrenomes
│   ├── nomes_proprios.json
│   └── sobrenomes.json
└── output/                    # Diretório para resultados
```

---

## 🚀 Instalação e Configuração

### Pré-requisitos

- **Python**: 3.9 ou superior
- **GPU (Opcional)**: CUDA compatível para aceleração do GLiNER

### Instalação

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou: venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### Dependências Principais

| Pacote | Descrição |
|--------|-----------|
| `pandas>=1.5.0` | Manipulação de dados |
| `openpyxl>=3.0.0` | Leitura de arquivos Excel |
| `gliner>=0.2.0` | Modelo de NER para PII |
| `torch>=2.0.0` | Backend de ML |

### Instalação Alternativa com Docker

Se você está enfrentando problemas com a instalação de `torch` ou `gliner`, pode usar Docker:

#### Pré-requisitos
- [Docker](https://docs.docker.com/get-docker/) instalado
- [Docker Compose](https://docs.docker.com/compose/install/) instalado

#### Build da Imagem
```bash
docker-compose build
```

#### Execução com CLI Interativa
```bash
docker-compose run --rm acesso-info python cli.py
```

#### Execução com predict.py
```bash
# Processar arquivo específico
docker-compose run --rm acesso-info python predict.py dados_entrada/seu_arquivo.xlsx saida.csv

# Com GLiNER (padrão)
docker-compose run --rm acesso-info python predict.py dados_entrada/seu_arquivo.xlsx saida.csv

# Especificando coluna de texto
docker-compose run --rm acesso-info python predict.py dados_entrada/dados.xlsx saida.csv "Texto do Pedido"
```

#### Configuração do Gemini (Opcional)
Crie um arquivo `.env` na raiz do projeto:
```
GEMINI_API_KEY=sua_chave_aqui
```

#### Observações
- Os resultados são salvos em `./resultados/` no host
- Coloque arquivos de entrada em `./dados_entrada/`
- O modelo GLiNER (~2.3GB) será baixado no primeiro uso dentro do container
- A instalação tradicional continua sendo o método padrão - Docker é apenas uma alternativa

---

## 📖 Como Usar

### Formato de Dados de Entrada

O sistema aceita diversos formatos de arquivo. O arquivo deve conter:
- **Coluna ID**: Identificador único do registro
- **Coluna de Texto**: Texto a ser analisado (detecta automaticamente colunas como "Texto", "Texto Mascarado", "Descrição", etc.)

**Formatos suportados:**
- Excel: `.xlsx`, `.xls`
- CSV: `.csv`
- TSV: `.tsv`
- JSON: `.json`
- Texto: `.txt`
- Parquet: `.parquet`

### Formato de Saída

O sistema gera um arquivo CSV com o formato:

```csv
ID,Predicao
1,0
2,1
3,0
```

Onde:
- **`0`** = NÃO contém dados pessoais (pode ser público)
- **`1`** = Contém dados pessoais (NÃO deve ser público)

---

### Script de Predição (Para Submissão)

```bash
# Uso básico
python predict.py <arquivo_entrada> <arquivo_saida>

# Exemplos
python predict.py dados_teste.xlsx predicoes.csv
python predict.py pedidos.csv resultado.csv

# Especificando coluna de texto manualmente (opcional)
python predict.py dados.xlsx saida.csv "Texto do Pedido"
```

**Importante:**
- ✅ Funciona **mesmo sem API key do Gemini**
- ✅ Auto-detecta colunas de ID e texto
- ✅ Usa GLiNER (ML) + Regex para máxima precisão
- ⚠️ Se tiver API key, usa LLM como fallback adicional

---

### Configuração Opcional da API (LLM)

O sistema funciona perfeitamente **sem API**, mas você pode opcionalmente habilitar o LLM:

```bash
# Definir API key (opcional)
export GEMINI_API_KEY='sua-chave-aqui'

# Rodar normalmente
python predict.py dados.xlsx saida.csv
```

**Nota:** O LLM só é usado como última camada de fallback quando regex e GLiNER não detectam nada.

---

### Uso como Biblioteca Python

```python
from src.detectores import SistemaDeteccaoIntegrado

# Inicialização padrão (auto-detecta API key)
sistema = SistemaDeteccaoIntegrado()

# Analisar texto
texto = "Meu nome é João Silva, CPF 123.456.789-09"
resultado = sistema.obter_resumo(texto)

print(f"Contém dados: {resultado['contem_dados_pessoais']}")
print(f"Tipos detectados: {resultado['por_tipo']}")

# Verificação simples
if sistema.contem_dados_pessoais(texto):
    print("❌ NÃO publicar - contém dados pessoais")
else:
    print("✅ Pode publicar")
```

---

## 🤖 Modelo GLiNER Multi PII Domains

O sistema utiliza o modelo [`E3-JSI/gliner-multi-pii-domains-v1`](https://huggingface.co/E3-JSI/gliner-multi-pii-domains-v1) especializado em detecção de PII.

### Características

- **50+ tipos de PII** suportados
- **Suporte a português** e dados brasileiros (CPF, CNPJ)
- **GPU (CUDA)** para inferência rápida
- **Lazy loading** para economizar memória

### Arquitetura Híbrida

```
┌─────────────┐     ┌──────────────────┐
│   Texto     │────▶│  Regex           │────┐
└─────────────┘     └──────────────────┘    │
                                            ▼
┌─────────────┐     ┌──────────────────┐  ┌──────────────┐
│   Texto     │────▶│  GLiNER (ML)     │──▶│    Merge     │──▶ Resultado
└─────────────┘     └──────────────────┘  └──────────────┘
                                             │
                   ┌────────────────────┐    │ (se vazio)
                   │ LLM (Fallback)     │◀───┘
                   │ Score 0-1          │
                   └────────────────────┘
```

---

## 🔧 Configuração Avançada

### Ajustando Limiares de Sensibilidade

```python
config = {
    'cpf_sensibilidade': 0.80,       # Padrão: 0.80
    'rg_sensibilidade': 0.75,        # Padrão: 0.75
    'telefone_sensibilidade': 0.75,  # Padrão: 0.75
    'email_sensibilidade': 0.85,     # Padrão: 0.85
    'nome_sensibilidade': 0.70,      # Padrão: 0.70
    'endereco_sensibilidade': 0.80,  # Padrão: 0.80
    'gliner_threshold': 0.50,        # Padrão: 0.50
}

sistema = SistemaDeteccaoIntegrado(config)
```

### Desabilitando GLiNER (Economia de Memória)

```python
# Usa apenas Regex (mais leve, ~100MB RAM)
sistema = SistemaDeteccaoIntegrado(usar_gliner=False)
```

---

## 📊 Métricas de Avaliação

O sistema calcula as métricas conforme especificado no edital:

| Métrica | Fórmula | Descrição |
|---------|---------|-----------|
| **Precisão** | `VP / (VP + FP)` | Dos detectados, quantos realmente continham dados |
| **Recall** | `VP / (VP + FN)` | Dos que continham, quantos foram detectados |
| **F1-Score** | `2 × (P × R) / (P + R)` | Média harmônica |

---

## 📁 Formatos Suportados

| Formato | Extensão |
|---------|----------|
| Excel | `.xlsx`, `.xls` |
| CSV | `.csv` |
| TSV | `.tsv` |
| JSON | `.json` |
| Texto | `.txt` |
| Parquet | `.parquet` |

---

## ⚠️ Limitações e Considerações

1. **Primeira execução**: Download automático do modelo GLiNER (~1.2GB)
2. **Requisitos de hardware**: GLiNER funciona melhor com GPU (CUDA)
3. **Nomes estrangeiros**: Podem ter menor taxa de detecção
4. **API Gemini (opcional)**: 
   - Free tier tem limites baixos (15 req/min)
   - Sistema funciona perfeitamente sem API
   - LLM é apenas camada adicional de fallback

---

## 📄 Licenciamento

Este projeto utiliza diversas bibliotecas de código aberto.
Para detalhes sobre as licenças de terceiros, consulte o arquivo [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

---

## 👥 Autores

Desenvolvido para o 1º Hackathon em Controle Social do Distrito Federal - Janeiro/2026.

- Vinicius Armando Menezes de Andrade
- Joao Luiz de Jesus Amaro

