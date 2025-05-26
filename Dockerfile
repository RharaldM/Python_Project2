FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Expor a porta do serviço
EXPOSE 8080

# Comando para iniciar a aplicação
CMD ["gunicorn", "wsgi:application", "-b", "0.0.0.0:8080", "--timeout", "120"]
