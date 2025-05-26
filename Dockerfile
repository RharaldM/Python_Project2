FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar arquivos do aplicativo
COPY . .

# Expor a porta do serviço
EXPOSE 8080

# Comando para iniciar a aplicação e o keep-alive
CMD sh -c "python keep_alive.py & gunicorn wsgi:application -b 0.0.0.0:8080 --timeout 120"
