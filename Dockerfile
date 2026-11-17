FROM python:3.11-slim

WORKDIR /app

# Ensure logs appear immediately in terminal
ENV PYTHONUNBUFFERED=1

# Install requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend folders into the container
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Expose Streamlit default port
EXPOSE 8501

# Run using python -m streamlit (guarantees executable is always found)
CMD ["python", "-m", "streamlit", "run", "backend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]