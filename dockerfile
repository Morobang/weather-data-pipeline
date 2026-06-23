# ============================================================
# Start from the official Airflow image
# Python 3.11 baked in
# ============================================================
FROM apache/airflow:2.9.1-python3.11

# ============================================================
# Switch to root to install system dependencies
# ============================================================
USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# Switch back to airflow user for pip installs
# Never install Python packages as root
# ============================================================
USER airflow

# ============================================================
# Copy requirements and install
# ============================================================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt