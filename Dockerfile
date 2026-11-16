# ---------- Build stage ----------
FROM python:3.11-slim AS builder
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Runtime stage ----------
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY backend/app.py .
COPY backend/models.py .
COPY backend/utils.py .
COPY backend/requirements.txt .
ENV PYTHONUNBUFFERED=1
EXPOSE 8501
CMD ["streamlit","run","app.py","--server.port=8501","--server.address=0.0.0.0"]