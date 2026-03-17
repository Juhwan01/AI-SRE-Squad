FROM python:3.11-slim
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install fastapi uvicorn
COPY main.py .

# Swagger(/docs) 주소를 5초마다 체크하도록 설정
HEALTHCHECK --interval=5s --timeout=3s --retries=2 \
  CMD curl -f http://localhost:8000/docs || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]