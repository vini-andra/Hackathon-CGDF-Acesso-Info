# Contexto do Projeto - Hackathon Participa DF

## 🎯 Objetivo Principal
Desenvolver um modelo de machine learning capaz de identificar automaticamente, em textos de pedidos de acesso à informação (e-SIC/Participa DF), a presença de **dados pessoais** (nome, CPF, RG, telefone, e-mail), seguindo as definições do edital e as diretrizes da **LGPD**.

## 🏆 Competição
- **Nome**: 1º Hackathon em Controle Social – Desafio Participa DF
- **Categoria**: Acesso à Informação
- **Organizador**: Controladoria-Geral do DF

## 📊 Dados de Referência
- **Dataset principal**: `AMOSTRA_e-SIC.xlsx` (disponibilizado pela Controladoria-Geral do DF)
- **Conteúdo**: Textos mascarados/sintéticos simulando casos reais de pedidos de acesso à informação

## ✅ Requisitos da Aplicação
1. **Entrada**: Receber textos brutos de pedidos
2. **Pré-processamento**: Limpeza, tokenização, etc.
3. **Classificação**: Modelo binário ("contém dados pessoais" vs "não contém dados pessoais")
4. **Marcação**: Idealmente, marcar os trechos sensíveis identificados
5. **Interface**: API e/ou script de linha de comando
6. **Documentação**: README com passos claros de instalação e execução

## 📈 Critérios de Avaliação
- **Desempenho**: Precisão, Recall, F1-Score
- **Documentação**: Clareza e completude do README
- **Facilidade de execução**: Deve ser facilmente executável pelo avaliador

## 🔧 Stack Técnica
- **Linguagem**: Python
- **Foco**: Machine Learning para NLP
- **Requisitos**: Código modular, boas práticas, organização do repositório

## 📌 Tipos de Dados Pessoais a Detectar
1. Nome completo
2. CPF
3. RG
4. Telefone
5. E-mail
6. Outros dados sensíveis conforme LGPD

---

## 📚 Fontes e Referências Adicionais

### Links Importantes

#### 1. Página Oficial do Hackathon
- **URL**: https://cg.df.gov.br/w/1-hackathon-em-controle-social-desafio-participa-df
- **Descrição**: Página oficial com todas as informações do 1º Hackathon em Controle Social

#### 2. Edital Completo
- **URL**: https://cg.df.gov.br/documents/d/cg/dodf-1-hackathon-em-controle-social-desafio-participa-df
- **Descrição**: Documento oficial com regras, critérios de avaliação e requisitos

#### 3. Amostra de Dados (e-SIC)
- **URL**: https://www.cg.df.gov.br/documents/d/cg/amostra_e-sic
- **Descrição**: Conjunto amostral de pedidos de acesso à informação (descaracterizados)

#### 4. PEP 8 - Guia de Estilo Python
- **URL**: https://peps.python.org/pep-0008/
- **Descrição**: Guia oficial de boas práticas e estilo de código Python

---

## 📋 Informações Extraídas do Site Oficial

### Sobre o Desafio
- **Organizador**: Controladoria-Geral do Distrito Federal (CGDF)
- **Objetivo**: Aproximar governo e sociedade por meio da tecnologia

### Categoria: Acesso à Informação
> Desenvolver um modelo capaz de identificar automaticamente pedidos públicos que contenham dados pessoais.

### Premiação (Categoria Acesso à Informação)
- 🥇 1º lugar: R$ 8.000
- 🥈 2º lugar: R$ 5.000
- 🥉 3º lugar: R$ 2.000

### Regras de Submissão
- Enviar solução pelo **GitHub ou GitLab**
- Documentação clara no README
- Seguir LGPD (Lei nº 13.709/2018)

### Contato
- **E-mail**: desafioparticipadf@cg.df.gov.br

---

### Arquivos de Referência no Projeto
- `AMOSTRA_e-SIC.xlsx` - Dataset principal com textos mascarados
- `dados/nomes_proprios.json` - Lista de nomes para detecção
- `dados/sobrenomes.json` - Lista de sobrenomes para detecção
