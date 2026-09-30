FROM python:3.11-slim-bookworm

# IFC geometry and scientific wheels need these shared libraries on Debian.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    OPENBLAS_NUM_THREADS=2 \
    OMP_NUM_THREADS=2

WORKDIR /workspace/it2-bim-dt
COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

# Keep the application separate from persistent model/reproduction volumes.
RUN useradd --create-home --uid 1000 it2 \
    && mkdir -p /workspace/it2-reproduction /workspace/it2-bim-dt/data/ifc \
    && chown -R it2:it2 /workspace
COPY --chown=it2:it2 . .
USER it2
EXPOSE 8501
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"
CMD ["python", "-m", "streamlit", "run", "app/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--server.maxUploadSize=100"]
