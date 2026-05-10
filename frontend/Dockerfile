FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8501
CMD ["python", "app.py"]
