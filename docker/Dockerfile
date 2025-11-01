# Use a imagem oficial do Python como base
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos de requisitos (se houver) e instala as dependências
# Para este projeto, as dependências são FastAPI e uvicorn[standard]
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Comando para rodar a aplicação será definido no docker-compose.yml
# Exemplo: CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
