# Image VOOXEN dérivée du fork trend-pulse @ d8e5fdb (v2.0.0) : ajoute FastAPI/uvicorn,
# n'embarque ni le tableau de bord Streamlit ni aucune clé LLM.
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e . "fastapi>=0.100,<1" "uvicorn>=0.24,<1"
COPY deploy/vooxen/vooxen_app.py deploy/vooxen/vooxen_worker.py /app/
RUN useradd -r -u 10001 tp && mkdir -p /app/data /app/backups && chown tp /app/data /app/backups
USER tp
ENV TREND_PULSE_DB=/app/data/history.db TZ=Europe/Paris PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "vooxen_app:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
