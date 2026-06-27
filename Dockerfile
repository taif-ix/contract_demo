FROM python:3.12-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    antiword \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# SQL Server ODBC deps for pyodbc.
# unixodbc provides libodbc.so.2; msodbcsql18 provides the Microsoft SQL Server driver.
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
    > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
        unixodbc \
        unixodbc-dev \
        msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# install python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app and worker
COPY app ./app
COPY worker ./worker

# Cloud Run uses 8080
ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
