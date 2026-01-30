FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fonte
COPY . .

# Diretório para dados de entrada/saída
VOLUME ["/app/dados_entrada", "/app/resultados"]

# Comando padrão
CMD ["python", "predict.py", "--help"]
